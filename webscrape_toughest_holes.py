"""
Get the data from toughest holes PGA Tour webpage.
"""
import requests
from bs4 import BeautifulSoup
import os
from lxml import etree, html
import json
import pandas
from datetime import datetime 

from utils import make_request, get_script_id_dict, get_script_queries_dict, save_html_to_file, request_stats, load_json, BASE_URL

URL = "https://www.pgatour.com/stats/course/toughest-holes"

def get_toughest_holes_stats():
    """
    """
    queries = get_script_queries_dict(URL)
    data_columns = ["rank", "courseName"]
    rows = None
    
    for q in queries:
        if "headers" in q["state"]["data"].keys():
            headers = []
            for h in q["state"]["data"]["headers"]:
                h = h.lower()
                if " " in h:
                    h_list = h.split(" ")
                    h = h_list[0] + "".join(w.capitalize() for w in h_list[1:])
                headers.append(h)
            data_columns += headers
        if "rows" in q["state"]["data"].keys():
            rows = q["state"]["data"]["rows"]

    # initialize pandas dataframe
    dataframe = pandas.DataFrame(columns=data_columns)
    new_rows = []

    for row in rows:
        new_row = []
        new_row.append(row["rank"])
        new_row.append(row["displayName"])

        for item in row["values"]:
            new_row.append(item["value"])

        new_rows.append(new_row)

    # Add new rows to dataframe
    for row in new_rows:
        dataframe.loc[len(dataframe)] = row

    # save the dataframe
    dataframe.to_csv('data/toughest_holes_stats.csv', header=True, index=False)



if __name__ == "__main__":
    get_toughest_holes_stats()
