import requests
from bs4 import BeautifulSoup
import os
from lxml import etree, html
import json
import pandas
from datetime import datetime 

from python_webscrape.src.utils import load_json, save_json_to_file, BASE_URL

def main():
    courses_json_data = load_json("sources\courses.json")
    new_data = {}

    # create new json file of keys: tournament id and value: name and url
    for value in courses_json_data.values():
        new_id = value["tournamentId"].replace("R2025", "")
        new_url = value["url"].replace("2025", "<year>")
        new_data[new_id] = {"name": value["tournamentName"], "url": new_url}

    save_json_to_file(new_data, "sources/tournaments.json")
if __name__ == "__main__":
    # main()
    data = load_json("sources/tournaments.json")
    print(len(data))