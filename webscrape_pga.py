import requests
from bs4 import BeautifulSoup
import os

# https://www.geeksforgeeks.org/python/python-web-scraping-tutorial/

def request_stats():
    url = "https://www.pgatour.com/stats"

    res = requests.get(url)
    print(res.status_code)
    # print(res.content)
    save_xml_to_file(res.content, "stats.xml")

def save_xml_to_file(content, filepath):
    soup = BeautifulSoup(content, "html.parser")
    with open(filepath, "w") as file:
        file.write(soup.prettify())


# Get info from stats page
# <a role="link" class="chakra-linkbox__overlay css-1hnz6hu" href="/player/46046/scottie-scheffler/stats">Scottie Scheffler</a>
# <span class="chakra-text css-nxrnrc">68.131</span>


if __name__ == "__main__":
    request_stats()