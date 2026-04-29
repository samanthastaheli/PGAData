import requests
from bs4 import BeautifulSoup
import os
from lxml import etree, html
import json
import pandas

from utils import make_request, get_script_id_dict, BASE_URL, load_json, save_html_to_file


# region Hole Locations

def get_hole_locations():
    content = make_request("https://www.pgatour.com/tournaments/2026/cadillac-championship/R2026556/course-stats")
    data_dict = get_script_id_dict(content, filename="data/cadillac_championship/hole_locations.json")
    # save_html_to_file(content, "data/cadillac_championship/hole_locations.html")
    
    hole_locations = {}
    # work way through dict to get stat info
    # "state" > "data" > "courses" > "roundHoleStats" > "holeStats" > "CourseHoleStats"
    queries = data_dict['props']['pageProps']['dehydratedState']['queries']
    for i, q in enumerate(queries):
        q_data = q['state']['data']
        if isinstance(q_data, dict):
            if "courses" in q_data.keys():
                if isinstance(q_data["courses"], list):
                    if "roundHoleStats" in q_data["courses"][0]:
                        hole_stats = q_data["courses"][0]["roundHoleStats"][0]["holeStats"]
                        for item in hole_stats:
                            if item["__typename"] == "CourseHoleStats":
                                print(item["courseHoleNum"])
                                hole_locations[item["courseHoleNum"]] = {
                                    "parValue": item["parValue"],
                                    "yards": item["yards"],
                                    "pin": item["pinGreen"]
                                }

    # Save to json file
    with open("data\cadillac_championship/hole_locations.json", "w") as file:
        json.dump(hole_locations, file, indent=4)

# endregion


# endregion

if __name__ == "__main__":
    get_hole_locations()
    