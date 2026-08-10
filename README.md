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

## Models

### Predictive Player Stat Models

There are 7 models created. They are saved in the `models/predict_player_stats/saved_models` directory. Google collab notebooks were used to create these models. Copies of these notebooks are saved to the `models/predict_player_stats` directory. There are only 6 notebooks because one of the notebooks, `models\predict_player_stats\pga_tournament_model_hole_scores.ipynb`, is used to create two models, a hole scores classification and regression model. 

#### Models Created 

1. Champion classifier
   * Classifies the champion of the 2026 Players Championship.
   * Code location: `models\predict_player_stats\pga_tournament_model_champion_classifier.ipynb`
   * Model location: `models\predict_player_stats\saved_models\model_champion_classifier.pt`
1. Hole scores classification
   * Predicts a players score for each hole using a classification model. 
   * Code location: `models\predict_player_stats\pga_tournament_model_hole_scores.ipynb`
   * Model location: `models\predict_player_stats\saved_models\model_hole_scores_classification.pt`
2. Hole scores regression 
   * Predicts a players score for each hole using a regression model. 
   * Code location: `models\predict_player_stats\pga_tournament_model_hole_scores.ipynb`
   * Model location: `models\predict_player_stats\saved_models\model_hole_scores_regression.pt`
3. Locations
   * Predicts the location of every shot using a classification model. 
   * Code location: `models\predict_player_stats\pga_tournament_model_locations.ipynb`
   * Model location: `models\predict_player_stats\saved_models\model_locations.pt`
4. Locations simplified
   * Predicts a more generalized location of every shot using a classification model. 
   * The simplified locations are: Green, Fairway, Bunker, In Hole, Rough, Penalty/Water, and Other.
   * Code location: `models\predict_player_stats\pga_tournament_model_locations_simplified.ipynb`
   * Model location: `models\predict_player_stats\saved_models\model_locations_simplified.pt`
5. Shot distance
   * Predicts the shot distance of every shot using a regression model. 
   * Code location: `models\predict_player_stats\pga_tournament_model_shot_dist.ipynb`
   * Model location: `models\predict_player_stats\saved_models\model_shot_dist.pt`
6. Shot distance and locations
   * Predicts the shot distance and location of every shot using a multi-task learning model.
   * Code location: `models\predict_player_stats\pga_tournament_model_shot_dist_and_locations.ipynb`
   * Model location: `models\predict_player_stats\saved_models\model_shot_dist_and_locations.pt`

#### Model Results

| Model                                                  | Avg Loss | Learning Rate | Avg Absolute Error | Accuracy | Error Rate | Training Data                                      | Testing Data                                  | Features                                                                                                            |
| ------------------------------------------------------ | -------- | ------------- | ------------------ | -------- | ---------- | -------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Champion Classifier                                    | 0.2026   | 0.003         | \-                 | \-       | \-         | The Players Championship 2021-2025                 | The Players Championship 2026                 | driving_accuracy_%', 'GIR_%', 'putts_per_gir', 'total_strokes','under_5_make_%', '5_to_10_make_%', 'over_10_make_%' |
| Hole Scores Classifier                                 | 1.3055   | 0.0001        | 0.9                | \-       | \-         | Cameron Young's The Players Championship 2021-2025 | Cameron Young's The Players Championship 2026 | GIR_%', 'putts_per_gir'                                                                                             |
| Hole Scores Regression                                 | 0.9035   | 0.001         | 0.94               | \-       | \-         | Cameron Young's The Players Championship 2021-2025 | Cameron Young's The Players Championship 2026 | GIR_%', 'putts_per_gir'                                                                                             |
| Shot Locations Classifier                              | 0.8711   | 0.0001        | \-                 | 38.41%   | 61.59%     | The Players Championship 2021-2025                 | The Players Championship 2026                 | GIR_%', 'putts_per_gir', 'shot_number', 'hole_yardage', 'to_hole_yards', 'shot_dist_yards'                          |
| Shot Locations Simplified Classifier                   | 0.1794   | 0.0001        | \-                 | 26.55%   | 73.45%     | The Players Championship 2021-2025                 | The Players Championship 2026                 | GIR_%', 'putts_per_gir', 'shot_number', 'hole_yardage', 'to_hole_yards', 'shot_dist_yards'                          |
| Shot Distance Regression                               | 0.0158   | 1.22E-08      | 8.15               | \-       | \-         | The Players Championship 2021-2025                 | The Players Championship 2026                 | GIR_%', 'putts_per_gir', 'shot_number', 'hole_yardage', 'to_hole_yards', 'locations'                                |
| Shot Distance Regression and Shot Locations Classifier | 1.1588   | 3.13E-06      | 94.6               | 36.56%   | 63.44%     | Cameron Young's The Players Championship 2021-2025 | Cameron Young's The Players Championship 2026 | GIR_%', 'putts_per_gir', 'shot_number', 'hole_yardage', 'to_hole_yards'                                             |
| Shot Distance Regression and Shot Locations Classifier | 0.9998   | 1.00E-04      | 100.55             | 39.27%   | 60.73%     | The Players Championship 2021-2025                 | The Players Championship 2026                 | GIR_%', 'putts_per_gir', 'shot_number', 'hole_yardage', 'to_hole_yards'                                             |

The table shows the average loss, learning rates, and data used for all the models created. Notably, the regression model for predicting hole scores was better than the classification model. The multi-task learning model did not perform as well as when the location and shot distance models were trained separately. Although the model did improve when trained on all the data, not just Cameron Young's data. 

### Image Segmentation Models

The image segmentation models were not as successful as the predictive player stats. That is due to the lack of segmented images data and complexity of trying to segment the images. The segmented images were created by hand in Canva. The color palette is shown in Figure 1. The dataset of segmented images are saved to `models\image_segmentation\dataset`. 

![](models\image_segmentation\dataset\readme_images\segmentation_color_palette.png)

<p align="center">Figure 1: Segmented images color palette with classes, class IDs, and RGB values.</p>

You will notice there are two versions of the dataset, one with the UI (user interface) included as a segment and one that has no UI included. This was due to <model here> predicting images as mostly UI, so the UI segments were removed and the model was trained and tested again. While this helped the model to segment other classes, it was still not accurate. An example of the images are seen in Figure 2.

![](models\image_segmentation\dataset\with_ui\segmented_tournament_R2021011_player_25804_hole_1_round_1.png)
![](models\image_segmentation\dataset\segmented_tournament_R2021011_player_25804_hole_1_round_1_no_ui.png)

<p align="center">Figure 2: Segmented Image with UI (top), Segmented Image without UI (bottom)</p>

#### Models Used

1. ResNet50
   * Used to cluster hole images. 
   * Code location: `models\image_segmentation\computer_vision_on_tourcast_screenshots.ipynb`.
2. SAM (segment anything model)
   * Code location: `models\image_segmentation\image_segmentation_sam.ipynb`
3. SAM 2.1
   * Code location: `models\image_segmentation\image_segmentation_sam_2.ipynb`
4. SMP (segment model python)
   * Code location: `models\image_segmentation\image_segmentation_smp.ipynb`
5. YOLO (you only look once) v8 Segmentation
   * Code location: `models\image_segmentation\image_segmentation_yolov8_seg.ipynb`
  
The most successful model was SAM 2.1. Although it was still not accurate it segmented a few things as seen in Figure 3.

![](models\image_segmentation\dataset\readme_images\output_sam_2.png)

<p align="center">Figure 3: Test results of trained SAM 2.1 model.</p>

## Code Resources

* [Python Webscraping Tutorial](https://www.geeksforgeeks.org/python/python-web-scraping-tutorial/)
* [Python LXML and BeautifulSoup Tutorial](https://www.geeksforgeeks.org/python/how-to-use-lxml-with-beautifulsoup-in-python/)

## Webscraped Sites

* [pgatour.com](https://www.pgatour.com/stats)
* [datagolf.com](https://datagolf.com/)