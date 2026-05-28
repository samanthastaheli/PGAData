"""
Clean up the scraped JSON data. Turn the JSON into csv files.
"""

import os
import json
import csv
import pandas as pd


def get_json_data(tour_id):
    json_filename = f"js_webscrape\src\scraped_data\{tour_id}_data.json"
    with open(json_filename, 'r') as file:
        data = json.load(file)
    return data

def create_csv_from_json(tour_ids):
    """
    Create the csv file for the tournament ID json file.
    """
    # csv_filename = f"data\scraped_tournament_data\{tour_id}_data.csv"
    csv_filename = "data\\scraped_tournament_data\\tournament_shots_data.csv"
    header = ["tournament", "player", "round", "hole", "shotNumber", "shotDist", "toHole", "location"]

    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # get every tournament data
        for tour_id in tour_ids:
            data = get_json_data(tour_id)

            # tournament, player, round, hole, shotDist, toHole, location, shotNumber 
            for player_id, rounds in data.items():
                for round, holes in rounds.items():
                    for hole, shots in holes.items():
                        for shot in shots:
                            # Get round and hole numbers only
                            round_num = round.split("_")[1]
                            hole_num = hole.split("_")[1]

                            # Get toHole and location
                            default_to_hole = 0
                            default_location = "In Hole"

                            to_hole_val = shot.get("toHole")
                            location_val = shot.get("location")

                            # set to_hole and loc to default if empty
                            if to_hole_val is None or to_hole_val == "":
                                to_hole_val = default_to_hole
                                
                            if location_val is None or location_val == "":
                                location_val = default_location

                            writer.writerow(
                                [
                                    tour_id,
                                    player_id,
                                    round_num,
                                    hole_num,
                                    shot.get("shotNumber"),
                                    shot.get("shotDist"),
                                    to_hole_val,
                                    location_val,
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
    create_csv_from_json(tour_ids)


if __name__ == "__main__":
    main()