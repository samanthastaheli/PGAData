"""
Clean up the scraped JSON data. Turn the JSON into csv files.
"""

import json
import csv
import pandas as pd

def main():
    filename = "js_webscrape\src\scraped_data\R2026556_data_2.json"
    # df = pd.read_json(filename)
    with open(filename, 'r') as file:
        data = json.load(file)

    header = ["tournament", "player", "round", "hole", "shotDist", "toHole", "location", "shotNumber"]

    with open("golf_shots.csv", "w", newline="") as f:
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

    print("Success! 'golf_shots.csv' has been created.")





if __name__ == "__main__":
    main()