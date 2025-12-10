import requests
from bs4 import BeautifulSoup
import os
from lxml import etree
import json

# https://www.geeksforgeeks.org/python/python-web-scraping-tutorial/
# https://www.geeksforgeeks.org/python/how-to-use-lxml-with-beautifulsoup-in-python/

def request_stats():
    # Get info from stats page
    url = "https://www.pgatour.com/stats"

    res = requests.get(url)
    print(res.status_code)
    # print(res.content)
    # save_xml_to_file(res.content, "sources/stats.html")
    return res.content

def save_xml_to_file(content, filepath):
    soup = BeautifulSoup(content, "html.parser")
    with open(filepath, "w") as file:
        file.write(soup.prettify())

def request_player_stats():
    url = "https://www.pgatour.com/player/46046/scottie-scheffler/stats"
    # "/player/"

def get_player_ids():
    """
    Player info is in stats html as:
    <a role="link" class="chakra-linkbox__overlay css-1hnz6hu" href="/player/46046/scottie-scheffler/stats">Scottie Scheffler</a>
    <span class="chakra-text css-nxrnrc">68.131</span>
    """
    players = dict()
    
    with open('sources/stats.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'lxml')
    hrefs = [a.get("href") for a in soup.find_all("a", href=True)]
    
    for url in hrefs:
        if "/player/" in url:
            print(f"href: {url}")
            items = url.split("/")
            id = items[2]
            player = items[3]
            player = player.replace("-", " ").title()
            if player not in players.keys():
                players[player] = {"id": id, "url": url}

    # Save to json file
    with open("sources/players.json", "w") as file:
        json.dump(players, file, indent=4)

if __name__ == "__main__":
    # request_stats()
    get_player_ids()