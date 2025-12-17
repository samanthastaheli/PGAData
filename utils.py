import requests
from bs4 import BeautifulSoup
import os
from lxml import etree, html
import json
import pandas

BASE_URL = "https://www.pgatour.com"

# region Helper Functions

def make_request(url):
    res = requests.get(url)
    if res.status_code == 200:
        print("Success!")
        return res.content
    else:
        raise ValueError(f"Request failed with code: {res.status_code}")

def save_html_to_file(content, filepath):
    soup = BeautifulSoup(content, "html.parser")
    with open(filepath, "w") as file:
        file.write(soup.prettify())

def load_json(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

def get_script_id_dict(content, filename=None):
    # Parse request content
    # all stat data is located in a script tag with id '__NEXT_DATA__'
    tree = html.fromstring(content)
    script_tags = tree.xpath("id('__NEXT_DATA__')")[0]
    data_dict = json.loads(script_tags.text)

    if filename:
        with open(filename, "w") as f:
            json.dump(data_dict, f, indent=4)

    return data_dict

def get_script_queries_dict(url):
    # Get url and make request
    content = make_request(url)
    data_dict = get_script_id_dict(content)
    return data_dict['props']['pageProps']['dehydratedState']['queries']



# endregion

def request_stats(url, filepath):
    # Get info from stats page

    content = make_request(url)
    # print(res.content)
    # save_html_to_file(res.content, "sources/stats.html")
    get_script_id_dict(content, filepath)

# region player ids json