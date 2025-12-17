import requests
from bs4 import BeautifulSoup
import os
from lxml import etree, html
import json
import pandas
from datetime import datetime 

from utils import make_request, get_script_id_dict, get_script_queries_dict, save_html_to_file, request_stats, load_json, BASE_URL



def get_course_ids():
    """
    Courses stats url:
    https://www.pgatour.com/tournaments/2025/u.s-open/R2025026/course-stats
    """
    courses = dict()
    
    content = make_request("https://www.pgatour.com/stats/course/toughest-course")
    data_dict = get_script_id_dict(content)
    year = datetime.now().year

    # work way through dict to get stat info
    queries = data_dict['props']['pageProps']['dehydratedState']['queries']
    for i, q in enumerate(queries):
        print(i)
        q_data = q['state']['data']
        if "rows" in q_data.keys():
            for i, row in enumerate(q_data["rows"]):
                print(i)
                name = row["displayName"]
                url_tournament_name = row["tournamentName"].lower().replace(" ", "-").replace("s.", "s")
                courses[name] = {
                    "tournamentId": row["tournamentId"],
                    "tournamentName": row["tournamentName"],
                    "url": f"{BASE_URL}/tournaments/{year}/{url_tournament_name}/{row['tournamentId']}/course-stats"
                    }

    # Save to json file
    with open("sources/courses.json", "w") as file:
        json.dump(courses, file, indent=4)


def get_courses_stats():
    """
    Every course stats page has:
    Hole
    Par
    Yards
    Avg
    Rank
    +/-
    Eagles
    Birdies
    Pars
    Bogeys
    DBL+
    """
    courses_dict = load_json("sources/courses.json")

    # initialize pandas dataframe
    data_columns = [
        "courseId", "courseName", "courseCode", "tournamentId", "courseParTotal", 
        "courseYardsTotal", "hole", "par", "yards", "scoringAverage", "scoringAverageDiff", 
        "scoringDiffTendency", "eagles", "birdies", "pars", "bogeys", "doubleBogey", "rank",
        "pinGreenLeftToRightCoords", "pinGreenBottomToTopCoords"
    ]
    dataframe = pandas.DataFrame(columns=data_columns)
    new_rows = []

    # Get every courses info
    for course_name, value in courses_dict.items():
        tour_id = value["tournamentId"]
        
        queries = get_script_queries_dict(value["url"])
        for q in queries:
            looking_for = 'courses'
            q_data = q['state']['data']
            if isinstance(q_data, dict):
                if looking_for in q_data.keys():
                    if "tournamentId" in q_data[looking_for][0].keys():
                        course_stats_dict = q_data[looking_for][0]
                        course_id = course_stats_dict["courseId"]
                        course_code = course_stats_dict["courseCode"]
                        total_par = course_stats_dict["par"]
                        total_yards = course_stats_dict["yardage"]
                        for stats in course_stats_dict['roundHoleStats']:
                            if stats["roundHeader"] == "All Rounds":
                                for h_stat in stats["holeStats"]:
                                    if h_stat["__typename"] == "CourseHoleStats":
                                        new_row = get_course_new_row(
                                            course_name, course_id, course_code, tour_id, 
                                            total_par, total_yards, data_columns, h_stat
                                        )
                                        new_rows.append(new_row)

    # Add new rows to dataframe
    for row in new_rows:
        dataframe.loc[len(dataframe)] = row

    # save the dataframe
    dataframe.to_csv('data/course_stats.csv', header=True, index=False)


def get_course_new_row(course_name, course_id, course_code, tour_id, total_par, total_yards, data_columns, stats):
    """
    Needed:
    "courseId", "courseName", "courseCode", "tournamentId", "courseParTotal", 
    "courseYardsTotal", "hole", "par", "yards", "scoringAverage", "scoringAverageDiff", 
    "scoringDiffTendency", "eagles", "birdies", "pars", "bogeys", "doubleBogey", "rank",
    "pinGreenLeftToRightCoords", "pinGreenBottomToTopCoords"
    """
    # initialize new row
    new_row = data_columns.copy()

    # keys we don't need the values for
    unneeded_keys = ["__typename", "holeImage", "live", "averagePaceOfPlay", "holePickleGreenLeftToRight", "holePickle"] 

    # Add course info
    new_row[new_row.index("courseId")] = course_id
    new_row[new_row.index("courseName")] = course_name
    new_row[new_row.index("courseCode")] = course_code
    new_row[new_row.index("tournamentId")] = tour_id
    new_row[new_row.index("courseParTotal")] = total_par
    new_row[new_row.index("courseYardsTotal")] = float(total_yards.replace(",", ""))

    for key, value in stats.items():
        if key == "courseHoleNum":
            new_row[new_row.index("hole")] = int(value)
        elif key == "parValue":
            new_row[new_row.index("par")] = int(value)
        elif key == "yards":
            new_row[new_row.index("yards")] = int(value)
        elif key == "scoringAverage":
            new_row[new_row.index("scoringAverage")] = float(value)
        elif key == "scoringAverageDiff":
            new_row[new_row.index("scoringAverageDiff")] = float(value)
        elif key == "scoringDiffTendency":
            new_row[new_row.index("scoringDiffTendency")] = value
        elif key == "eagles":
            new_row[new_row.index("eagles")] = int(value)
        elif key == "birdies":
            new_row[new_row.index("birdies")] = int(value)
        elif key == "pars":
            new_row[new_row.index("pars")] = int(value)
        elif key == "bogeys":
            new_row[new_row.index("bogeys")] = int(value)
        elif key == "doubleBogey":
            new_row[new_row.index("doubleBogey")] = int(value)
        elif key == "rank":
            new_row[new_row.index("rank")] = int(value)
        elif key == "pinGreen":
            lr = value["leftToRightCoords"]
            lr_value = tuple((float(lr["x"]), float(lr["y"]), float(lr["z"])))
            bt = value["bottomToTopCoords"]
            bt_value = tuple((float(bt["x"]), float(bt["y"]), float(bt["z"])))
            new_row[new_row.index("pinGreenLeftToRightCoords")] = lr_value
            new_row[new_row.index("pinGreenBottomToTopCoords")] = bt_value
        elif key in unneeded_keys:
            pass
        else:
            print(f"\033[33mWARNING\033[0m Unknown key: {key}")

    # Check every column got filled
    for i in range(len(data_columns)):
        new_row[i] != data_columns[i]
    return new_row

def get_course_stats_from_data_golf():
    content = make_request("https://datagolf.com/course-table")
    # filepath = "temp/data_golf_course_table.html"
    # save_html_to_file(content, filepath)
    tree = html.fromstring(content)
    script_tags = tree.xpath("///script")
    looking_for = "var reload_data = JSON.parse('"
    new_rows = []
    dataframe = None
    for tag in script_tags:
        if tag.text:
            if looking_for in tag.text:
                lines = tag.text.split(";")
                for line in lines:
                    if looking_for in line:
                        line = line[:-2]
                        line = line.replace(looking_for, "")
                        line = line.strip()
                        line_dict = json.loads(line)
                        # with open("temp/data_golf_courses.json", "w") as f:
                        #     json.dump(line_dict, f, indent=4)
                        course_data_list = line_dict["data"]
                        data_columns = course_data_list[0].keys()
                        dataframe = pandas.DataFrame(columns=data_columns)
                        for course_dict in course_data_list:
                            assert course_dict.keys() == data_columns
                            new_rows.append(course_dict.values())

    # Add new rows to dataframe
    for row in new_rows:
        dataframe.loc[len(dataframe)] = row

    # save the dataframe
    dataframe.to_csv('data/data_golf_course_table.csv', header=True, index=False)


if __name__ == "__main__":
    # url = "https://www.pgatour.com/tournaments/2025/u.s-open/R2025026/course-stats"
    # request_stats(url, "temp/course_oak.json")
    # get_course_ids()
    # get_courses_stats()
    get_course_stats_from_data_golf()
