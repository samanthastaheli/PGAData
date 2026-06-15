# PGAData
Collect PGA data.

## Web Scrape Process

The webscrape process has two parts, get JSON data and get CSV data. JSON data is collected using JavaScript. CSV data is collected using Python.

### 1. Get JSON Data 

1. Navigate to the directory `js_webscrape/src`.
2. Download Node JS.
3. Download node packages by running the following.
   1. `npm install puppeteer chalk`
4. Update the screenshot file save path on line 6 in `js_webscrape/src/scrape.js` to a path where you can save the images of the Tour Cast website.
5. Run the web scrapping javascript code by running: `node scrape.js`
   1. This will save every tournament data as a JSON file in the `js_webscrape/src/scraped_data` directory.
   2. To scrape specific tournaments, navigate to line 267 (`const tournamentIds = await getTournamentInfo(browser);`) in `scrape.js` and comment that line out and specify the tournaments needed in the array bellow. For a list of tournament IDs go to `sources/tournaments.json`.
   3. To scrape specific players, navigate to line 275 (`const playersInTournament = await getPlayersInTournament(currentTournament, browser);`) in `scrape.js` and comment that line out and specify the players needed in the array bellow. For a list of player IDs go to `sources/players.json`.

### 2. Get CSV Data

1. Collect the hole information by running the python file: `python_webscrape/src/webscrape_hole_locations.py`
2. Run the python file: `python_webscrape/src/clean_scraped_data.py`. This will create a CSV file here `data/scraped_tournament_data/tournament_shots_data.csv`.

## Kaggle

The most recent collected datasets are uploaded to Kaggle for ease of use in Google Collab or Jupyter notebooks. 

[Tournament Shots](https://www.kaggle.com/datasets/samanthastaheli/tournamentshots)

[Tournament Tour Cast Hole Images](https://www.kaggle.com/datasets/samanthastaheli/tournamenttourcastholeimages)

## Code Resources

* [Python Webscraping Tutorial](https://www.geeksforgeeks.org/python/python-web-scraping-tutorial/)
* [Python LXML and BeautifulSoup Tutorial](https://www.geeksforgeeks.org/python/how-to-use-lxml-with-beautifulsoup-in-python/)

## Webscraped Sites

* [pgatour.com](https://www.pgatour.com/stats)
* [datagolf.com](https://datagolf.com/)