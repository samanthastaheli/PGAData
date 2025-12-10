import requests
from bs4 import BeautifulSoup
import os
from lxml import etree, html
import json

# https://www.geeksforgeeks.org/python/python-web-scraping-tutorial/
# https://www.geeksforgeeks.org/python/how-to-use-lxml-with-beautifulsoup-in-python/
BASE_URL = "https://www.pgatour.com"

# region Helper Functions

def make_request(url):
    res = requests.get(url)
    if res.status_code == 200:
        print("Success!")
        return res.content
    else:
        raise ValueError(f"Request failed with code: {res.status_code}")

def save_xml_to_file(content, filepath):
    soup = BeautifulSoup(content, "html.parser")
    with open(filepath, "w") as file:
        file.write(soup.prettify())

def load_json(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

# endregion

def request_stats():
    # Get info from stats page
    url = "https://www.pgatour.com/stats"

    content = make_request(url)
    # print(res.content)
    # save_xml_to_file(res.content, "sources/stats.html")
    return content

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

def get_player_stats():
    """
    Every players stats page has:
    Stat
    Value
    Rank
    Supporting Stat
    Value (but its Value Type)

    html stored in: <script id="__NEXT_DATA__" type="application/json">
    "statId":"337","rank":"11","value":"30' 2","title":"Approaches from 175-200 yards","category":["APPROACH"],"aboveOrBelow":"EVEN","fieldAverage":"","supportingStat":{
    """
    players_dict = load_json("sources/players.json")
    player_one = next(iter(players_dict))
    full_url = BASE_URL + players_dict[player_one]["url"]
    print(f"full url: {full_url}")
    content = make_request(full_url)

    tree = html.fromstring(content)
    script_tags = tree.xpath("id('__NEXT_DATA__')")[0]
    data_dict = json.loads(script_tags.text)
    # Save to json file
    # with open("sources/data_dict.json", "w") as file:
    #     json.dump(data_dict, file, indent=4)

    print(data_dict.keys())
    queries = data_dict['props']['pageProps']['dehydratedState']['queries']
    for i, q in enumerate(queries):
        looking_for = 'playerProfileStatsFull'
        print(i)
        q_data = q['state']['data']
        if isinstance(q_data, dict):
            if looking_for in q_data.keys():
                print(q_data[looking_for])
                with open("sources/playerProfileStatsFull_dict.json", "w") as file:
                    json.dump(q_data[looking_for], file, indent=4)

        # if "statid" in q:
        #     print(q)



if __name__ == "__main__":
    # request_stats()
    # get_player_ids()
    get_player_stats()
    # content = make_request("https://www.pgatour.com/stats/detail/02675")
    # save_xml_to_file(content, "sources/stats_detail.html")

    # data = json.loads(content)
    # stats = data['props']['pageProps']['dehydratedState']['queries']
    # player_stats = next(q for q in stats if 'playerProfileStatsFull' in q['queryHash'])
    # print(player_stats)
    # Access stats like player_stats['state']['data']['playerProfileStatsFull']
