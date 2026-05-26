"""
Clean up the scraped JSON data. Turn the JSON into csv files.
"""

import os
import json
import csv
import pandas as pd


def create_csv_from_json(tour_id):
    """
    Create the csv file for the tournament ID json file.
    """
    json_filename = f"js_webscrape\src\scraped_data\{tour_id}_data.json"
    csv_filename = f"data\scraped_tournament_data\{tour_id}_data.csv"
    header = ["tournament", "player", "round", "hole", "shotNumber", "shotDist", "toHole", "location"]

    with open(json_filename, 'r') as file:
        data = json.load(file)

    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # tournament, player, round, hole, shotDist, toHole, location, shotNumber 
        for player_id, rounds in data.items():
            for round_num, holes in rounds.items():
                for hole_num, shots in holes.items():
                    for shot in shots:
                        # Use .get() in case 'toHole' or 'location' are missing (like shot #5)
                        writer.writerow(
                            [
                                "R2026556",
                                player_id,
                                round_num,
                                hole_num,
                                shot.get("shotNumber"),
                                shot.get("shotDist"),
                                shot.get("toHole", ""),
                                shot.get("location", ""),
                            ]
                        )

    print(f"Success! {csv_filename} has been created.")


def get_tour_ids():
    """
    Get all tournament IDs that are in js_webscrape\src\scraped_data folder.
    """
    data_files = os.listdir("js_webscrape\src\scraped_data")
    tour_ids = []

    for file in data_files:
        tour_ids.append(file.split("_")[0])

    return tour_ids

def main():
    # tour_ids = ["R2026556", "R2026480"]
    tour_ids = get_tour_ids()

    for tour_id in tour_ids:
        create_csv_from_json(tour_id)
    

if __name__ == "__main__":
    main()