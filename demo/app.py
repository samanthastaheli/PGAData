import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import kagglehub
from kagglehub import KaggleDatasetAdapter
import re

# GREEN = "#56985F"
# GREEN = "#59A365"
GREEN = "#579E62"
PURPLE = "#78439D"
BLUE = "#3498db"
LIGHT_GREEN = "#9FCF77"
# region Page Config
st.set_page_config(
    page_title="PGA Tour Metrics",
    page_icon="⛳",
    layout="wide"
)

# endregion 

# region Import Data

@st.cache_data
def load_raw_pga_data():
    file_path = "tournament_shots_data.csv"
    # Pulling your exact Kaggle version dataset
    raw_df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "samanthastaheli/tournamentshots/versions/9",
        file_path,
        pandas_kwargs={"encoding": "latin1"}
    )
    return raw_df


# region Helper Functions

def parse_golf_distance_to_yards(val):
    # Convert to string and clean up whitespaces
    val = str(val).strip().lower()

    # Handle clean zeros or empty rows
    if val in ['0', '0.0', 'nan', '']:
        return 0.0

    # Check 1: If it's explicitly in yards (e.g., "334 yds")
    if 'yd' in val:
        match = re.search(r'([\d.]+)', val)
        return float(match.group(1)) if match else 0.0

    # Check 2: If it's in feet/inches (e.g., "5 ft 11 in." or "79 ft 5 in.")
    if 'ft' in val or 'in' in val:
        # Extract feet if present
        ft_match = re.search(r'(\d+)\s*ft', val)
        feet = float(ft_match.group(1)) if ft_match else 0.0

        # Extract inches if present
        in_match = re.search(r'(\d+)\s*in', val)
        inches = float(in_match.group(1)) if in_match else 0.0

        # Convert total feet and inches into decimal yards (3 feet in a yard, 36 inches in a yard)
        total_yards = (feet / 3.0) + (inches / 36.0)
        return round(total_yards, 3) # Rounding to 3 decimal places for precision

    # Check 3: Fallback if it's a raw number string without units
    try:
        return float(val)
    except ValueError:
        return 0.0

def categorize_locations(row):
    start_loc = str(row["shot_started_from"]).lower().strip()
    end_loc = str(row["location"]).lower().strip()

    # Shot 1 on Par 4s/5s is a Drive (On Par 3s, Shot 1 is technically an Approach)
    try:
        shot_num = int(float(row["shot_number"]))
    except (ValueError, TypeError):
        shot_num = None

    # if row["shot_number"] == 1 or str(row["shot_number"]).strip() == "1" or int(float(row["shot_number"])) == 1:
    if shot_num == 1:
        shot_class = "Tee"
        # if row["par"] == 3:
        #     shot_class = "Tee"
        # else:
        #     shot_class = "Tee"
    elif "green" in start_loc:
        shot_class = "Putt"
    else:
        shot_class = "Approach"

    return shot_class

def categorize_positions(row):
    start_loc = str(row["shot_started_from"]).lower().strip()
    end_loc = str(row["location"]).lower().strip()

    # Shot 1 on Par 4s/5s is a Drive (On Par 3s, Shot 1 is technically an Approach)
    if row["shot_number"] == 1:
        shot_pos = "tee"
    elif "green" in start_loc:
        shot_pos = "putt"
    elif "fairway" in start_loc:
        shot_pos = "fairway"
    elif "rough" in start_loc:
        shot_pos = "rough"
    elif "bunker" in start_loc:
        shot_pos = "sand"
    else:
        shot_pos = "approach"

    return shot_pos

def add_new_columns(df):
    # Sort chronologically so shifts align perfectly within each hole
    df = df.sort_values(by=['tournament_id', 'round', 'hole', 'player_id', 'shot_number']).copy()

    # Get the *previous* landing location (where the current shot is being hit from)
    df['shot_started_from'] = df.groupby(['tournament_id', 'round', 'hole', 'player_id'])['location'].shift(1)

    # For the very first shot of a hole, the previous location is blank (NaN),
    # which means they are hitting from the Tee Box.
    df['shot_started_from'] = df['shot_started_from'].fillna('tee')

    # Track the holed status as an independent variable
    df["is_holed"] = df["location"].str.lower().str.contains("in hole", na=False)

    # Force shot_number to be numeric, turning rogue text/strings into NaN safely
    df["shot_number"] = pd.to_numeric(df["shot_number"], errors="coerce")

    # Drop rows where shot_number became NaN to protect the max calculation
    df = df.dropna(subset=["shot_number"])

    return df

def get_hole_scores(df):
    # Group by player, round, and hole, then find the highest shot number
    shots_per_hole = df.groupby(['tournament_id', 'player', 'round', 'hole'])['shot_number'].max().reset_index()

    # Rename the column to make it clear it represents the hole score
    shots_per_hole.rename(columns={'shot_number': 'total_shots'}, inplace=True)
    return shots_per_hole

def get_total_scores(df):
    hole_scores = get_hole_scores(df)

    # Sum the hole scores to get the total tournament score for each player
    total_scores = hole_scores.groupby(['player', 'tournament_id'])['total_shots'].sum().reset_index()
    total_scores.rename(columns={'total_shots': 'total_strokes'}, inplace=True)

    return total_scores

def get_top_players(df, amount=3):
    total_scores = get_total_scores(df)

    # Sort by strokes ascending (lowest score is best) and grab the top players amount
    top_players = total_scores.sort_values(by='total_strokes', ascending=True).head(amount)

    return top_players

def get_top_players_by_tournament(df, amount=3):
    total_scores = get_total_scores(df)

    return total_scores.groupby('tournament_id').apply(
        lambda x: x.nsmallest(amount, 'total_strokes')
    ).reset_index(drop=True)

# endregion

# ------------------------------------------------------------------
# region Stat Functions
# ------------------------------------------------------------------

# region Driving Accuracy 
def get_drive_accuracy(dataframe):
    # Get drives only
    drives_df = df[(df['shot_type'] == 'Tee') & (df['par'] != 3)].copy()

    # If fairway in location then True, else False
    drives_df['hit_fairway'] = drives_df['location'].str.lower().str.contains('fairway', na=False)

    # Get new df with driving accuracy and sort by driving accuracy
    player_accuracy_df = pd.DataFrame({
        'driving_accuracy_%': (drives_df.groupby(['tournament_id', 'player'])['hit_fairway'].mean() * 100).round(2),
        'total_drives_tracked': drives_df.groupby(['tournament_id', 'player'])['hit_fairway'].count(),
        'avg_drive_distance': drives_df.groupby(['tournament_id', 'player'])['shot_dist_yards'].mean()
    }).reset_index()
    player_accuracy_df = player_accuracy_df.sort_values(by='driving_accuracy_%', ascending=False).reset_index(drop=True)

    return player_accuracy_df

def plot_top_players_drive_accuracy(data, num_players):
    # Isolate top slice based on slider adjustment
    top_accuracy = data.head(num_players)

    # Compute baseline fields
    baseline_accuracy = data['driving_accuracy_%'].mean()
    baseline_distance = data['avg_drive_distance'].mean()

    # Reshape metrics using your pandas melt logic
    melted_df = pd.melt(
        top_accuracy,
        id_vars=['player'],
        value_vars=['driving_accuracy_%', 'avg_drive_distance'],
        var_name='Metric',
        value_name='Value'
    )

    # Match your original sizing/styling configs
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(16, 7))

    sns.barplot(
        data=melted_df,
        x='player',
        y='Value',
        hue='Metric',
        palette=[GREEN, '#34495e'],
        edgecolor='black',
        alpha=0.85,
        ax=ax
    )

    # Add numeric strings above bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f', fontsize=8, fontweight='bold', padding=3)

    # Inject your custom threshold guidelines
    ax.axhline(y=baseline_accuracy, color=GREEN, linestyle='--', linewidth=2, alpha=0.8,
               label=f'Field Accuracy Baseline ({baseline_accuracy:.1f}%)')
    ax.axhline(y=baseline_distance, color='#2c3e50', linestyle='--', linewidth=2, alpha=0.8,
               label=f'Field Distance Baseline ({baseline_distance:.1f} yds)')

    # Labels and cleanup
    ax.set_title(f"Top {num_players} Players: Accuracy vs Distance", fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel("Player", fontsize=11, labelpad=8)
    ax.set_ylabel("Value", fontsize=11, labelpad=8)
    plt.xticks(rotation=42, ha='right')
    
    max_val = melted_df['Value'].max()
    ax.set_ylim(0, max_val * 1.15)
    ax.legend(title="Metrics", frameon=True, facecolor='white', edgecolor='none')
    
    plt.tight_layout()
    
    # Direct render inside your web view
    st.pyplot(fig)

def plot_drive_accuracy_distribution(data):
    # Create an isolated figure and axis container for Streamlit
    fig, ax = plt.subplots(figsize=(10, 5))

    # Pass the 'ax' parameter so Seaborn draws directly on our Streamlit figure
    sns.histplot(
        data=data,
        x='driving_accuracy_%',
        kde=True,
        bins=30,
        color=GREEN,
        edgecolor='white',
        ax=ax
    )

    # Apply formatting labels natively to the axis
    ax.set_title("Driving Accuracy Distribution", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Driving Accuracy Percentage (%)", fontsize=12, labelpad=10)
    ax.set_ylabel("Number of Players (Count)", fontsize=12, labelpad=10)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    plt.tight_layout()
    
    # Render the chart in the Streamlit application canvas
    st.pyplot(fig)

# region GIR

def get_gir(df):
    green_shots = df[df['location'].str.lower().str.contains('green', na=False)].copy()

    # Find the first shot that hit the green for every player on every hole
    # (Using groupby + min ensures we catch the exact shot number they reached the surface)
    first_green_shot = green_shots.groupby(['tournament_id', 'round', 'hole', 'player', 'par'])['shot_number'].min().reset_index()
    first_green_shot.rename(columns={'shot_number': 'shot_reached_green'}, inplace=True)

    # Apply the official GIR condition: shot_reached_green <= (par - 2)
    first_green_shot['GIR'] = first_green_shot['shot_reached_green'] <= (first_green_shot['par'] - 2)

    # return first_green_shot[['player', 'par', 'shot_reached_green', 'GIR']]
    return first_green_shot

def get_gir_percentage(df):
    gir = get_gir(df)

    # Calculate final GIR %
    player_gir_df = gir.groupby(['tournament_id', 'player'])['GIR'].mean().reset_index()

    # Get the percentage
    player_gir_df['GIR_%'] = (player_gir_df['GIR'] * 100).round(2)
    player_gir_df = player_gir_df.sort_values(by='GIR_%', ascending=False).reset_index(drop=True)

    # Clean up temporary aggregation column
    player_gir_df.drop(columns=['GIR'], inplace=True)
    return player_gir_df

def plot_top_players_gir(players_gir_data, num_players):
    fig, ax = plt.subplots(figsize=(10, 5))

    top_gir = players_gir_data.head(num_players)

    # 2. Set up style and sizing
    sns.set_theme(style="whitegrid")

    # 3. Plot horizontal bars (notice we swap x and y)
    bars = ax.barh(
        top_gir['player'].astype(str),
        top_gir['GIR_%'],
        color=LIGHT_GREEN,
        edgecolor='black',
        alpha=0.85
    )

    # 4. Invert the Y-axis so the #1 player sits proudly at the very top
    ax.invert_yaxis()

    # 5. Add text percentage values to the right tip of each bar
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 1,
            bar.get_y() + bar.get_height()/2,
            f"{width:.1f}%",
            ha='left',
            va='center',
            fontsize=9,
            fontweight='bold'
        )

    # 6. Labels and Formatting
    ax.set_title(f"Top {num_players} Players: Greens in Regulation (GIR %)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Greens in Regulation Percentage (%)", fontsize=12, labelpad=10)
    ax.set_ylabel("Player", fontsize=12, labelpad=10)
    ax.set_xlim(0, 115)  # Add room on the right edge for percentage text labels

    st.pyplot(fig)


def plot_ball_striking_dist(data):
    fig, ax = plt.subplots(figsize=(10, 5))

    # 1. Create a light gray background box plot to show the baseline quartile markers
    sns.boxplot(
        data=data,
        x='GIR_%',
        color='#e2e8f0',
        width=0.4,
        fliersize=0
    )

    # 2. Overlay every individual player as a distinct point so you see the raw density
    sns.stripplot(
        data=data,
        x='GIR_%',
        color='#e74c3c',  # Vibrant red dots for players
        size=6,
        alpha=0.7,
        jitter=0.15
    )

    # 3. Add a vertical line showcasing the overall field average
    field_mean = data['GIR_%'].mean()
    ax.axvline(field_mean, color='black', linestyle='--', linewidth=1.5, label=f'Field Avg: {field_mean:.1f}%')

    # 4. Labels and Formatting
    ax.set_title("Tournament Ball-Striking Profile: Distribution of Player GIR %", fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("GIR Percentage (%)", fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(axis='x', linestyle=':', alpha=0.6)

    st.pyplot(fig)

# region Scrambling %

def get_scrambling_percentage(df):
    # Identify missed GIR and final scores
    hole_scores = get_hole_scores(df)
    green_shots = df[df['location'].str.lower().str.contains('green', na=False)].copy()
    first_green_shot = green_shots.groupby(['tournament_id', 'round', 'hole', 'player', 'par'])['shot_number'].min().reset_index()
    first_green_shot.rename(columns={'shot_number': 'shot_reached_green'}, inplace=True)

    # Merge hole scores and green data together
    scramble_base = pd.merge(hole_scores, first_green_shot, on=['tournament_id', 'round', 'hole', 'player'], how='left')

    # If 'shot_reached_green' is NaN, it means they never hit the green at all
    # Let's fill those with a high dummy number so it safely counts as a missed GIR.
    scramble_base['shot_reached_green'] = scramble_base['shot_reached_green'].fillna(99)

    # Run scrambling flags

    # Flag 1: Did the player miss the green in regulation?
    scramble_base['missed_GIR'] = scramble_base['shot_reached_green'] > (scramble_base['par'] - 2)

    # Flag 2: Did the player make par or better?
    scramble_base['saved_par'] = scramble_base['total_shots'] <= scramble_base['par']

    # Isolate ONLY the opportunities where the player actually missed the green
    scramble_opportunities = scramble_base[scramble_base['missed_GIR'] == True].copy()

    # Compile scrambling dataframe

    # Create the new standalone DataFrame
    player_scrambling_df = pd.DataFrame({
        'scrambling_%': (scramble_opportunities.groupby(['tournament_id', 'player'])['saved_par'].mean() * 100).round(2),
        'scramble_opportunities': scramble_opportunities.groupby(['tournament_id', 'player'])['saved_par'].count(),
        'scramble_saves': scramble_opportunities.groupby(['tournament_id', 'player'])['saved_par'].sum()
    }).reset_index()

    # Sort from best scrambler to worst
    player_scrambling_df = player_scrambling_df.sort_values(by='scrambling_%', ascending=False).reset_index(drop=True)
    return player_scrambling_df

# region Sand Saves

def get_player_sand_saves(df):
    hole_scores = get_hole_scores(df)

    # Make sure shots are in order
    df_sorted = df.sort_values(by=['tournament_id', 'round', 'hole', 'player', 'shot_number']).copy()

    # Look at the next shot's location using .shift(-1)
    df_sorted['next_location'] = df_sorted.groupby(['tournament_id', 'round', 'hole', 'player'])['location'].shift(-1)

    # Filter for shots hit from a bunker that landed on the green (Using 'bunker' catches green-side sand shots)
    sand_to_green = df_sorted[
        df_sorted['location'].str.lower().str.contains('bunker', na=False) &
        df_sorted['next_location'].str.lower().str.contains('green', na=False)
    ].copy()

    # Mark these holes as having a valid sand-save opportunity
    sand_to_green['had_sand_opportunity'] = True

    # Keep just one record per hole for players who hit out of the sand to the green
    sand_opportunities = sand_to_green.drop_duplicates(subset=['round', 'hole', 'player', 'par'])

    # Merge and flag sand saves
    sand_base = pd.merge(
        hole_scores,
        sand_opportunities[['tournament_id', 'round', 'hole', 'player', 'had_sand_opportunity', 'par']],
        on=['tournament_id', 'round', 'hole', 'player'],
        how='inner' # 'inner' drops any holes where they never went bunker-to-green
    )

    # A sand save is successful if their final score is less than or equal to par
    sand_base['is_sand_save'] = sand_base['total_shots'] <= sand_base['par']

    # Create leaderboard
    player_sand_saves_df = pd.DataFrame({
        'sand_save_%': (sand_base.groupby(['tournament_id', 'player'])['is_sand_save'].mean() * 100).round(2),
        'sand_opportunities': sand_base.groupby(['tournament_id', 'player'])['is_sand_save'].count(),
        'sand_saves_made': sand_base.groupby(['tournament_id', 'player'])['is_sand_save'].sum()
    }).reset_index()

    # Sort the table from best sand-scrambler to worst
    return player_sand_saves_df.sort_values(by='sand_save_%', ascending=False).reset_index(drop=True)

def plot_sand_saves(sand_saves_data, num_players):
    # Plot
    top_sand_players = sand_saves_data.head(num_players)

    # Set up the plotting canvas
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(15, 6))

    # Plot the performance line
    ax.plot(
        top_sand_players['player'].astype(str), # X-axis: Player IDs as strings
        top_sand_players['sand_save_%'], # Y-axis: Sand Save %
        color='#e67e22',                
        marker='o', # Distinct dots at each player node
        linewidth=2.5,
        markersize=7,
        label='Player Sand Save %'
    )

    # Add a horizontal line representing the overall field average
    field_sand_avg = sand_saves_data['sand_save_%'].mean()
    ax.axhline(
        y=field_sand_avg,
        color='#7f8c8d',
        linestyle='--',
        linewidth=1.5,
        label=f'Field Avg ({field_sand_avg:.1f}%)'
    )

    ax.set_title(f"Top {num_players} Players: Sand Save Percentage Curve", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Player", fontsize=12, labelpad=10)
    ax.set_ylabel("Sand Save Efficiency (%)", fontsize=12, labelpad=10)
    ax.tick_params(axis='x', rotation=45)
    ax.set_ylim(0, 110)
    ax.legend(loc='upper right', frameon=True, facecolor='white')

    st.pyplot(fig)

# region Putt %

def get_putt_percentages(df):
    # Get putts
    putts_df = df[df['shot_type'] == 'Putt'].copy()

    hole_putts = putts_df.groupby(["tournament_id", "round", "hole", "par", "player"]).size().reset_index(name="total_putts")
    hole_putts.head()

    # Create boolean flags for putt numbers
    hole_putts['is_1_putt'] = hole_putts['total_putts'] == 1
    hole_putts['is_2_putt'] = hole_putts['total_putts'] == 2
    hole_putts['is_3_putt'] = hole_putts['total_putts'] == 3
    hole_putts['is_3+_putt'] = hole_putts['total_putts'] > 3

    # Calculate percentage of 1, 2, 3, 3+ putts
    return pd.DataFrame({
        '1_putt_%': (hole_putts.groupby(['tournament_id', 'player'])['is_1_putt'].mean() * 100).round(2),
        '2_putt_%': (hole_putts.groupby(['tournament_id', 'player'])['is_2_putt'].mean() * 100).round(2),
        '3_putt_%': (hole_putts.groupby(['tournament_id', 'player'])['is_3_putt'].mean() * 100).round(2),
        '3+_putt_%': (hole_putts.groupby(['tournament_id', 'player'])['is_3+_putt'].mean() * 100).round(2),
    }).reset_index()

def plot_putt_percentages(putt_percentages):
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    plots = [
        ('1_putt_%', '1 Putt %'),
        ('2_putt_%', '2 Putt %'),
        ('3_putt_%', '3 Putt %'),
        ('3+_putt_%', '3+ Putt %')
    ]

    for ax, (col, title) in zip(axs.flatten(), plots):
        ax.hist(putt_percentages[col], bins=15, edgecolor='black')
        ax.set_title(title)
        ax.set_xlabel('Percentage')
        ax.set_ylabel('Number of Players')
        ax.set_xlim(0, 100)

    plt.tight_layout()
    st.pyplot(fig)

def get_putt_make_shot_dist_percentages(df):
    putts_only_df = df[df["shot_type"] == "Putt"].copy()
    putts_only_df["is_made"] = putts_only_df["location"].str.lower().str.contains("in hole", na=False)

    # Create boolean flags for putt distances
    putts_only_df['is_under_5'] = putts_only_df['to_hole_yards'] > 5/3
    putts_only_df['is_5_10'] = (putts_only_df['to_hole_yards'] <= 5/3) & (putts_only_df['to_hole_yards'] >= 10/3)
    putts_only_df['is_over_10'] = putts_only_df['to_hole_yards'] < 10/3

    # Calculate percentage of 1, 2, 3, 3+ putts
    putt_make_percentages = pd.DataFrame({
        'under_5_make_%': (putts_only_df.groupby(['tournament_id', 'player'])['is_under_5'].mean() * 100).round(2),
        '5_to_10_make_%': (putts_only_df.groupby(['tournament_id', 'player'])['is_5_10'].mean() * 100).round(2),
        'over_10_make_%': (putts_only_df.groupby(['tournament_id', 'player'])['is_over_10'].mean() * 100).round(2),
    }).reset_index()

    # Clean up any players who had 0 putts in a specific distance bin (fills NaN with 0)
    percentage_cols = ['under_5_make_%', '5_to_10_make_%', 'over_10_make_%']
    putt_make_percentages[percentage_cols] = putt_make_percentages[percentage_cols].fillna(0.0)

    # Sort by the best short-range putters
    return putt_make_percentages.sort_values(by='under_5_make_%', ascending=False).reset_index(drop=True)

def get_player_putts_per_gir(df):
    # Get putts
    putts_df = df[df['shot_type'] == 'Putt'].copy()

    # Group by player and round to count their total putts
    round_putts = putts_df.groupby(["tournament_id", "round", "player"]).size().reset_index(name="total_putts")

    # Get average putts per round
    player_putts_per_round = round_putts.groupby(["tournament_id", "player"])["total_putts"].mean().reset_index(name="putts_per_round")
    player_putts_per_round["putts_per_round"] = player_putts_per_round["putts_per_round"].round(2)

    # Get Putts per GIR

    # Count the number of putts taken on every hole
    hole_putts = putts_df.groupby(["tournament_id", "round", "hole", "player"]).size().reset_index(name='hole_putt_count')

    # Get 'GIR' boolean column (True/False)
    gir_df = get_gir(df)
    gir_putts_base = pd.merge(
        gir_df[['tournament_id', 'round', 'hole', 'player', 'GIR']],
        hole_putts,
        on=['tournament_id', 'round', 'hole', 'player'],
        how='left'
    )

    # Fill NaN with 0 for holes where they holed out from off the green and took 0 putts
    gir_putts_base['hole_putt_count'] = gir_putts_base['hole_putt_count'].fillna(0)

    # Isolate only the holes where the player successfully made a GIR
    gir_only_holes = gir_putts_base[gir_putts_base['GIR'] == True]

    # Calculate the final average putts per GIR
    # player_putts_per_gir = gir_only_holes.groupby(['tournament_id', 'player']).size().reset_index(name='putts_per_gir') # total counts
    return gir_only_holes.groupby(['tournament_id', 'player'])['hole_putt_count'].mean().reset_index(name='putts_per_gir') # average

# region Shot Make Distance

def get_avg_shot_make_distance(df):
    hole_shots = df[df['location'] == 'In Hole'].copy()

    avg_in_hole_dist = hole_shots.groupby(["tournament_id", "player"])["shot_dist_yards"].mean().reset_index(name="avg_in_hole_shot_dist")

    # convert yards to feet
    avg_in_hole_dist['avg_in_hole_shot_dist_feet'] = (avg_in_hole_dist['avg_in_hole_shot_dist'] * 3).round(2)

    # sort
    return avg_in_hole_dist.sort_values(by="avg_in_hole_shot_dist_feet", ascending=False)

def plot_shot_make_dist_histogram(avg_in_hole_dist):
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create the histogram + KDE overlay
    sns.histplot(
        data=avg_in_hole_dist,
        x="avg_in_hole_shot_dist_feet",
        kde=True,
        line_kws={"linewidth": 3, "color": "#e74c3c"}, # Bold red line for the KDE curve
        bins=50,                  # Adjust bin count depending on your dataset size
        ax=ax
    )

    # Gte x tick spacing
    x_min = int(avg_in_hole_dist["avg_in_hole_shot_dist_feet"].min())
    x_max = int(avg_in_hole_dist["avg_in_hole_shot_dist_feet"].max())
    tick_spacing = np.arange(x_min, x_max + 2, step=1)
    ax.set_xticks(tick_spacing)

    ax.set_title("Distribution of Average In Hole Shot Distance", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Average Shot Distance (Feet)", fontsize=12, labelpad=10)
    ax.set_ylabel("Frequency", fontsize=12, labelpad=10)

    st.pyplot(fig)

# endregion
# region Import Data

# Loading spin banner
with st.spinner("Downloading and parsing data loops from Kaggle..."):
    df_raw = load_raw_pga_data()
    df = df_raw.copy()
    # Add new columns needed
    df = add_new_columns(df)
    df["shot_dist_yards"] = df["shot_dist"].apply(parse_golf_distance_to_yards)
    df["to_hole_yards"] = df["to_hole"].apply(parse_golf_distance_to_yards)
    df["shot_type"] = df.apply(categorize_locations, axis=1)
    df["shot_pos"] = df.apply(categorize_positions, axis=1)

# endregion 

# region Sidebar
st.sidebar.header("Dashboard Controls")

# Allow the user to see all tournaments or zoom into a specific tournament ID (e.g., R2025011)
unique_tournaments = ["All Data"] + list(df['tournament_id'].unique())
selected_tid = st.sidebar.selectbox("Select Tournament ID", unique_tournaments)

# Filter raw dataframe before passing it to accuracy compiler
if selected_tid != "All Data":
    working_df = df[df['tournament_id'] == selected_tid]
    app_title = f"⛳ PGA Tour Player Metrics for Tournament: {selected_tid}"
else:
    working_df = df
    app_title = "⛳ PGA Tour Player Metrics"

# Slider to let user choose how many top players to display
num_players = st.sidebar.slider("Number of Top Players to Display", 5, 30, 20)


# region Main Dashboard Layout
st.title(app_title)
st.markdown("---")

st.markdown("## Driving Accuracy")
# st.markdown("Evaluating the relationship between fairway-finding precision and overall yardage off the tee.")
player_accuracy_df = get_drive_accuracy(working_df)

# KPI Summary Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Field Avg Accuracy", f"{player_accuracy_df['driving_accuracy_%'].mean():.1f}%")
with col2:
    st.metric("Field Avg Distance", f"{player_accuracy_df['avg_drive_distance'].mean():.1f} yds")
with col3:
    # st.metric("Total Active Players", len(player_accuracy_df))
    player_count = player_accuracy_df['player'].nunique()
    st.metric("Total Active Players", player_count)

st.markdown("### Driving Accuracy Distribution")
if not player_accuracy_df.empty:
    plot_drive_accuracy_distribution(player_accuracy_df)
else:
    st.error("No driving data found in the selected criteria.")

st.markdown("### Top Players Performance Comparison")
if not player_accuracy_df.empty:
    plot_top_players_drive_accuracy(player_accuracy_df, num_players)
else:
    st.error("No driving data found in the selected criteria.")

# Interactive Data Logging Display
st.markdown("#### Leaderboard Metrics Log")
st.dataframe(player_accuracy_df.reset_index(drop=True), width='stretch')

st.markdown("---")
st.markdown("## Greens in Regulation (GIR)")
gir = get_gir_percentage(working_df)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Field Avg GIR", f"{gir['GIR_%'].mean():.1f}%")

if not gir.empty:
    plot_top_players_gir(gir, num_players)
else:
    st.error("No GIR data found in selected criteria.")

st.markdown("---")
st.markdown("## Scrambling Percentage")
st.markdown("$$Scrambling \ Percentage = \\frac{Number \ Par \ Saves \ When \ Miss \ GIR}{Total \ Num \ Holes \ Where \ GIR \ Missed} \\times 100$$")
scrambles = get_scrambling_percentage(working_df)
st.dataframe(scrambles.sort_values("player").reset_index(drop=True), width='stretch')

st.markdown("---")
st.markdown("## Sand Saves")
sand_saves_df = get_player_sand_saves(working_df)

if not sand_saves_df.empty:
    plot_sand_saves(sand_saves_df, num_players)
else:
    st.error("No sand saves data found in selected criteria.")

st.markdown("---")
st.markdown("## Putting Analysis")
st.markdown("### Putt Percentages")
st.markdown("Percentages for one putts, two putts, three putts, and more than three putts.")
putt_percentage_df = get_putt_percentages(working_df)

if not putt_percentage_df.empty:
    plot_putt_percentages(putt_percentage_df)
else:
    st.error("No putting data found in selected criteria.")
st.dataframe(putt_percentage_df.reset_index(drop=True), width='stretch')

st.markdown("### Putt Make Percentages by Distance")
putt_make_percentage_df = get_putt_make_shot_dist_percentages(working_df)
st.dataframe(putt_make_percentage_df.sort_values("player").reset_index(drop=True), width='stretch')

st.markdown("---")
st.markdown("## Shot Make Distance")
st.markdown("The average distance it takes to make the shot in the hole.")
shot_make_df = get_avg_shot_make_distance(working_df)

if not shot_make_df.empty:
    plot_shot_make_dist_histogram(shot_make_df)
else:
    st.error("No data found in selected criteria.")