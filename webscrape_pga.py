import requests
from bs4 import BeautifulSoup
import os
from lxml import etree, html
import json
import pandas

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

def get_script_id_dict(content, filename=None):
    tree = html.fromstring(content)
    script_tags = tree.xpath("id('__NEXT_DATA__')")[0]
    data_dict = json.loads(script_tags.text)

    if filename:
        with open(filename, "w") as f:
            json.dump(data_dict, f, indent=4)

    return data_dict

# endregion

def request_stats(url, filepath):
    # Get info from stats page

    content = make_request(url)
    # print(res.content)
    # save_xml_to_file(res.content, "sources/stats.html")
    get_script_id_dict(content, filepath)

# region player ids json

def get_player_ids():
    """
    Player info is in stats html as:
    <a role="link" class="chakra-linkbox__overlay css-1hnz6hu" href="/player/46046/scottie-scheffler/stats">Scottie Scheffler</a>
    <span class="chakra-text css-nxrnrc">68.131</span>
    """
    players = dict()
    
    content = make_request("https://www.pgatour.com/players")
    data_dict = get_script_id_dict(content)

    # work way through dict to get stat info
    queries = data_dict['props']['pageProps']['dehydratedState']['queries']
    for i, q in enumerate(queries):
        q_data = q['state']['data']
        if "players" in q_data.keys():
            if isinstance(q_data["players"], list):
                if len(q_data["players"]) > 15:
                    for player in q_data["players"]:
                        name = player["displayName"]
                        players[name] = {
                            "id": player["id"],
                            "firstName": player["firstName"],
                            "lastName": player["lastName"],
                            "url": f"{BASE_URL}/player/{player['id']}/{player['firstName'].lower()}-{player['lastName'].lower()}/stats"
                            }

    # Save to json file
    with open("sources/players.json", "w") as file:
        json.dump(players, file, indent=4)

# endregion

# region player stats

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

    # initialize pandas dataframe
    data_columns = [
        "playerId", "player", "statId", "title", "value", 
        "rank", "category", "aboveOrBelow", "fieldAverage", 
        "supportingStatDescription", "supportingStatValue", 
        "supportingValueDescription", "supportingValueValue"
    ]
    dataframe = pandas.DataFrame(columns=data_columns)
    new_rows = []

    # Get every players info
    for player_name, value in players_dict.items():
        player_id = value["id"]

        # Get url and make request
        content = make_request(value["url"])

        # Parse request content
        # all stat data is located in a script tag with id '__NEXT_DATA__'
        tree = html.fromstring(content)
        script_tags = tree.xpath("id('__NEXT_DATA__')")[0]
        data_dict = json.loads(script_tags.text)

        # with open(f"sources/player_{player_id}_script_stats.json", "w") as f:
        #     json.dump(data_dict, f, indent=4)

        # work way through dict to get stat info
        queries = data_dict['props']['pageProps']['dehydratedState']['queries']
        for q in queries:
            looking_for = 'playerProfileStatsFull'
            q_data = q['state']['data']
            if isinstance(q_data, dict):
                if looking_for in q_data.keys():
                    if q_data[looking_for] == []:
                        # add nones if no stats available 
                        new_row = [None for _ in range(len(data_columns)-2)]
                        new_row.insert(0, player_name)
                        new_row.insert(0, player_id)
                    else:
                        player_stats_dict = q_data[looking_for][0]
                        stats_list = player_stats_dict['stats']
                        for stats in stats_list:
                            new_row = get_player_new_row(player_name, player_id, data_columns, stats)
                            new_rows.append(new_row)

    # Add new rows to dataframe
    for row in new_rows:
        dataframe.loc[len(dataframe)] = row

    # save the dataframe
    dataframe.to_csv('data/player_stats.csv', header=True, index=False)


def get_player_new_row(player_name, player_id, data_columns, stats):
    # initialize new row
    new_row = data_columns.copy()

    # Add player info
    new_row[new_row.index("playerId")] = player_id
    new_row[new_row.index("player")] = player_name

    for key, value in stats.items():
        if key == "statId":
            new_row[new_row.index("statId")] = value
        elif key == "rank":
            new_row[new_row.index("rank")] = value
        elif key == "value":
            new_row[new_row.index("value")] = value
        elif key == "title":
            new_row[new_row.index("title")] = value
        elif key == "category":
            new_row[new_row.index("category")] = value
        elif key == "aboveOrBelow":
            new_row[new_row.index("aboveOrBelow")] = value
        elif key == "fieldAverage":
            new_row[new_row.index("fieldAverage")] = value
        elif key == "supportingStat":
            if value:
                new_row[new_row.index("supportingStatDescription")] = value["description"]
                new_row[new_row.index("supportingStatValue")] = value["value"]
            else:
                new_row[new_row.index("supportingStatDescription")] = value
                new_row[new_row.index("supportingStatValue")] = value
        elif key == "supportingValue":
            if value:
                new_row[new_row.index("supportingValueDescription")] = value["description"]
                new_row[new_row.index("supportingValueValue")] = value["value"]
            else:
                new_row[new_row.index("supportingValueDescription")] = value
                new_row[new_row.index("supportingValueValue")] = value
        else:
            print(f"\033[33mWARNING\033[0m Unknown key: {key}")

    # Check every column got filled
    for i in range(len(data_columns)):
        new_row[i] != data_columns[i]
    return new_row

# endregion

if __name__ == "__main__":
    # url = "https://www.pgatour.com/stats"
    # url = "https://www.pgatour.com/player/64828/lilia-vu/stats"
    # request_stats(url, "sources/stats_unavailable.json")
    # players_url = "https://www.pgatour.com/players"
    # request_stats(players_url, filepath="sources/players_script_id.json")
    # get_player_ids()
    get_player_stats()
    # content = make_request("https://www.pgatour.com/stats/detail/02675")
    # save_xml_to_file(content, "sources/stats_detail.html")

    # data = json.loads(content)
    # stats = data['props']['pageProps']['dehydratedState']['queries']
    # player_stats = next(q for q in stats if 'playerProfileStatsFull' in q['queryHash'])
    # print(player_stats)
    # Access stats like player_stats['state']['data']['playerProfileStatsFull']
