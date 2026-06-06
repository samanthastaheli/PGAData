import requests
from bs4 import BeautifulSoup
import os
from lxml import etree, html
import json
import pandas

from utils import make_request, get_script_id_dict, BASE_URL, load_json, save_html_to_file


# region Hole Locations

def get_hole_locations():
    # url = "https://www.pgatour.com/tournaments/2026/cadillac-championship/R2026556/course-stats"
    tour_info = [["011", 2026], ["011", 2025], ["011", 2024], ["011", 2023], ["556", 2026], ["023", 2025]]
    for id, year in tour_info:
        url = f"https://www.pgatour.com/tournaments/{year}/the-players-championship/R{year}{id}/course-stats"
        content = make_request(url)
        data_dict = get_script_id_dict(content)
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
                                    hole_locations[item["courseHoleNum"]] = {
                                        "parValue": item["parValue"],
                                        "yards": item["yards"],
                                        "pin": item["pinGreen"]
                                    }

        # Save to json file
        with open(f"data\hole_locations\R{year}{id}_hole_locations.json", "w") as file:
            json.dump(hole_locations, file, indent=4)

# endregion

# region Tour Cast

def get_tour_cast():
    # url = "https://www.pgatour.com/tournaments/2026/cadillac-championship/R2026556/tourcast"
    # url = "https://tourcast.pgatour.com/tourcast.html?id=R2026556#/hole-view?pid=&round=1&hole=17&gv=false"
    url = "https://tourcast.pgatour.com/tourcast.html?id=R2026556#/hole-view?pid=57366&round=1&hole=15&gv=false" # Cam Young Hole 15
    content = make_request(url)
    save_html_to_file(content, "data/cadillac_championship/tour_cast.html")
    # data_dict = get_script_id_dict(content, filename="data/cadillac_championship/tour_cast_raw2.json")

# endregion

if __name__ == "__main__":
    get_hole_locations()
    # get_tour_cast()
    