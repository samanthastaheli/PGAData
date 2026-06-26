import puppeteer from "puppeteer";
import fs from "fs"; // file system module
import { getPlayerIds, generateTourCastUrlsForPlayer, generateTestUrlForPlayer, loadPlayerNames, scrapeYears, loadAndProcessJSON } from './utils.js';
import chalk from 'chalk'; // change color in terminal

// const YOUR_FILE_PATH = 'C:\\Users\\Sam\\repos\\PGAImages\\'; // TODO: change this path for your machine 
const YOUR_FILE_PATH = "C:\\Users\\Edge\\source\\repos\\PGAImagesTest\\"; // TODO: remove after testing
const SHOT_BUTTON_SELECTOR = 'button[class*="shot_shotNum"]';
const CLOSE_SELECTOR = 'button[class*="informationContent_close"]';

// ***************************************************************************************
// region Helper Functions
// ***************************************************************************************

const startBrowser = async () => {
  const browser = await puppeteer.launch({
    args: [
      "--no-sandbox", 
      "--disable-setuid-sandbox", 
      "--disable-dev-shm-usage", 
      "--disable-blink-features=AutomationControlled", 
      // "--disable-features=IsolateOrigins,site-per-process"
    ],
    headless: false, // Headless must be true for Docker
    defaultViewport: { width: 1280, height: 800 },
  });
  return browser;
}

const startPage = async (browser) => {
  const page = await browser.newPage();
  return page;
}

const navigateToUrl = async (url, page) => {
  console.log(chalk.magenta(`Navigating to ${url}`));
  await page.goto(url, { waitUntil: "networkidle2" });
}


const dismissPopUp = async (page) => {
  try {
    const closeSelector = 'button[class*="informationContent_close"]';
    await page.waitForSelector(closeSelector, { visible: true, timeout: 8000 });
    await page.evaluate((sel) => {
      const btn = document.querySelector(sel);
      if (btn) btn.click();
    }, CLOSE_SELECTOR);
    console.log(chalk.bgBlue.white("Pop-up dismissed."));
    
  } catch (error) {
    console.log(chalk.bgMagenta.white("No pop-up detected."));
  }

  await new Promise(r => setTimeout(r, 1000)); // * sleep 
}

/**
 * Checks if shots are available on the page.
 * @param {object} page - The Puppeteer page instance
 * @param {number} holeNum - The current hole number for logging
 * @returns {boolean} - Returns true if shots exist, false otherwise
 */
const checkForShots = async (page, holeNum) => {
    try {
        await page.waitForSelector(SHOT_BUTTON_SELECTOR, { timeout: 8000 });
      return true; 
    } catch (error) {
      console.log(chalk.magenta(`No shots found for hole ${holeNum}, skipping.`));
      return false;
    }
};

const getShotData = async (page) => {
  const shotCount = await page.evaluate((sel) => document.querySelectorAll(sel).length, SHOT_BUTTON_SELECTOR);
  const allShotsData = [];

  // Loop through each shot
  for (let i = 0; i < shotCount; i++) {
    // Re-fetch buttons each iteration to avoid stale references
    const shotLabel = await page.evaluate((index, sel) => {
      const btns = document.querySelectorAll(sel);
      const target = btns[index];
      if (target) {
        const opts = { bubbles: true, cancelable: true, view: window };
        target.dispatchEvent(new PointerEvent('pointerdown', opts));
        target.dispatchEvent(new PointerEvent('pointerup', opts));
        target.click();
        return target.textContent.trim();
      }
      return null;
    }, i, SHOT_BUTTON_SELECTOR);

    // Wait for the UI data container to match the shot number we just clicked
    try {
      await page.waitForFunction((expected) => {
        const root = document.querySelector('[class*="primaryPlayerController_shotsContainer"]');
        return root && root.textContent.includes(`Shot ${expected}`);
      }, { timeout: 5000 }, shotLabel);
    } catch (error) {
      console.log(chalk.red(`Error: ${error}, Timed out waiting for Shot ${shotLabel} UI to update.`));
    }

    // Scrape the data for the current shot
    const data = await page.evaluate(() => {
      const rootContainer = document.querySelector('[class*="primaryPlayerController_shotsContainer"]');
      if (!rootContainer) return null;

      const rows = rootContainer.querySelectorAll('[class*="primaryPlayerController_shotsData"]');
      const results = {};

      rows.forEach(div => {
        const fullText = div.textContent.trim(); 
        const label = div.querySelector('span')?.textContent.trim();
        const value = fullText.replace(label, '').trim();

        if (label?.includes('Shot')) results.shotDist = value;
        else if (label === 'To Hole') results.toHole = value;
        else if (label === 'Loc') results.location = value;
      });

      return results;
    });

    if (data) {
      data.shotNumber = shotLabel; // Add the shot ID to the object
      allShotsData.push(data);
      console.log(chalk.magenta(`Scraped Shot ${shotLabel}:`), data);
    }
  }
  return allShotsData;
};

/**
 * Safely nests and saves hole data into the master tournament object.
 * @param {object} masterObj - The main finalTournamentData object
 * @param {object} holeInfo - The current holeInfo (contains playerId, round, hole)
 * @param {array} shotData - The array of shots scraped from the page
 */
const updateTournamentData = (masterObj, holeInfo, shotData) => {
    const { playerId, playerName, round, hole } = holeInfo;

    // 1. Ensure the Player exists
    if (!masterObj[playerId]) {
        masterObj[playerId] = {};
    }

    // 2. Ensure the Round exists for that player
    const roundKey = `Round_${round}`;
    if (!masterObj[playerId][roundKey]) {
        masterObj[playerId][roundKey] = {};
    }

    // 3. Save the data to the Hole
    masterObj[playerId][roundKey][`Hole_${hole}`] = shotData;

    console.log(chalk.magenta(`Saved: Player ${playerId} | Round ${round} | Hole ${hole}`));
    
    return masterObj;
};

/**
 * Generate an array of object of players names and IDs that are in the tournament.
 * @param {string} tournamentInfo - An object containing the tournament ID and name
 * @param {object} browser - The Puppeteer browser instance
 * @returns {array} - An array of player objects with names and IDs.
 */
const getPlayersInTournament = async (tournamentInfo, browser) => {
  const year = tournamentInfo.id.substring(1, 5)
  const url = `https://www.pgatour.com/tournaments/${year}/${tournamentInfo.name.replace(/\s+/g, '-').toLowerCase()}/${tournamentInfo.id}/leaderboard`;

  const page = await startPage(browser);
  await navigateToUrl(url, page);
  
  // extract data
  await page.waitForSelector('.chakra-text.css-1v9q6zy');
  const playersInTournamentNames = await page.$$eval('.chakra-text.css-1v9q6zy', elements => {
    return elements.map(el => el.innerText.trim());
  });

  // get player IDs 
  const playersInTournament = []; // with be name and id 
  const playersDict = loadPlayerNames();

  for (const playerName of playersInTournamentNames) {
    const playerId = playersDict[playerName];
    if (playerId) {
      playersInTournament.push({ name: playerName, id: playerId});
    } else {
      console.log(chalk.red(`Player ${playerName} not found in player dictionary.`));
    }
  }

  console.log(chalk.magenta("Number of Players in tournament:", playersInTournament.length))

  await page.close();
  
  return playersInTournament;
}

/**
 * Get all tournament IDs and names as a dict.
 */
const getTournamentInfo = async (browser) => {
  const tournamentJson = loadAndProcessJSON('../../sources/tournaments.json');
  // const tournamentJson = loadAndProcessJSON('../../sources/tournaments_test.json'); // TODO: change back after testing
  const tournaments = []; // object with id and name
  const years = scrapeYears();

  for (const [tournamentId, tournamentInfo] of Object.entries(tournamentJson)) {
    // test if tournament tour cast url will work
    for (const year of years) {
      const testUrl = `https://www.pgatour.com/tournaments/${year}/${tournamentInfo.name.replace(/\s+/g, '-').toLowerCase()}/R${year}${tournamentId}/course-stats`;

      const page = await startPage(browser);
      try {
        await navigateToUrl(testUrl, page);

        const isPageLoaded = await page.waitForSelector('svg[aria-label="Spinner"]', { 
          hidden: true, 
          timeout: 8000 
        })
        .then(() => true)   // If it succeeds, return true
        .catch(() => false); // If it times out or fails, return false
        
        if (isPageLoaded) {
          const foundTourCastTab = await page.evaluate(() => {
            // Look for the anchor tag with the specific label
            const link = document.querySelector('a[aria-label="TOURCAST"]');
            if (!link) return false;

            // Check if the element is actually visible to a human
            const style = window.getComputedStyle(link);
            return style.display !== 'none' && style.visibility !== 'hidden' && link.offsetWidth > 0;
          });
          if (foundTourCastTab) {
            tournaments.push({ id: `R${year}${tournamentId}`, name: tournamentInfo.name });
            console.log(chalk.green(`Found TOURCAST for ${tournamentInfo.name} ${year}`));
          } else {
            console.log(chalk.yellow(`No TOURCAST found for ${tournamentInfo.name} ${year}`));
          }
        } else {
          console.log(chalk.yellow(`No page loaded for ${tournamentInfo.name} ${year}`));
        }
      } catch (error) {
        console.log(chalk.red(`Error: ${error} while checking ${tournamentInfo.name} ${year}`));
      } finally { 
        await page.close();
      }
    }
  }

  console.log(chalk.blue(`Total tournaments with TOURCAST: ${tournaments.length}`));

  return tournaments;
}

// endregion Helper Functions

// ***************************************************************************************
// region Main Function
// ***************************************************************************************

const getHoleData = async () => {
  const start = performance.now();
  const browser = await startBrowser();
  
  // * Get urls
  const tournamentIds = await getTournamentInfo(browser);
  // To scrape specific tournaments, comment out the line above and use the array below.
  // const tournamentIds = [
  //   { id: "R2023011", name: "THE PLAYERS Championship" },
    // { id: "R2022011", name: "THE PLAYERS Championship" },
    // { id: "R2021011", name: "THE PLAYERS Championship" },
  // ];
  for (const currentTournament of tournamentIds) { 
    const playersInTournament = await getPlayersInTournament(currentTournament, browser);
    // To scrape specific players in a tournament, comment out the line above and use the array below.
    // const playersInTournament = [{name: "Cameron Young", id: "57366"}]; 
    const urls = generateTourCastUrlsForPlayer(currentTournament.id, playersInTournament);
    console.log(chalk.blue(`Generated URLs for ${urls.length} holes across all players and rounds.`));
    const finalTournamentData = {};

    for (const holeInfo of urls) { 
      // * Create new page instance for each hole
      const page = await startPage(browser);

      try {
        // * Navigate to url
        console.log(`Navigating to Player ${holeInfo.playerId} Hole ${holeInfo.hole} Round ${holeInfo.round}...`);
        await navigateToUrl(holeInfo.url, page);

        // * Wait for page to load by waiting for a key element
        await page.waitForSelector('[class*="primaryPlayerController_"]', { timeout: 15000 });
        
        // * Dismiss Pop-up
        await dismissPopUp(page);

        // if no shot buttons then not correct player
        const hasShots = await checkForShots(page, holeInfo.hole);

        // If false skip this hole and move to the next one
        if (!hasShots) {
          // continue; // skip to next hole
          if (holeInfo.hole === 1) {
            console.log(chalk.red(`No shots for Hole 1, likely page is not working. Skipping all holes for this player.`));
            break; // exit the hole loop and move to the next player
          } else {
            continue; 
          }
        }

        // * Move mouse to have birds eye view of hole for screenshot
        
        const { width, height } = page.viewport();

        const x = width / 2;
        const y = height / 2;

        await page.keyboard.down('Control');

        await page.mouse.move(x, y);
        await page.mouse.down();

        await page.mouse.move(x, y + 400, {
          steps: 30,
        });

        await page.mouse.up();
        await page.keyboard.up('Control');

        // * Save screenshot of hole
        try {
          await page.screenshot({ path: `${YOUR_FILE_PATH}tournament_${currentTournament.id}_player_${holeInfo.playerId}_hole_${holeInfo.hole}_round_${holeInfo.round}.png`, fullPage: true });
          console.log(chalk.green(`Screenshot saved for Player ${holeInfo.playerId} Hole ${holeInfo.hole} Round ${holeInfo.round}.`));
        } catch (error) {
          console.error(chalk.red(`Error saving screenshot for Player ${holeInfo.playerId} Hole ${holeInfo.hole} Round ${holeInfo.round}: ${error}`));
        }

        // * Get the count of shots available
        const shotsData = await getShotData(page);

        // * Update the master object with the new hole data
        updateTournamentData(finalTournamentData, holeInfo, shotsData);

      } catch (error) {
        console.log(chalk.red(`Error: ${error}`));
        continue;
      } finally {
        // This block always runs, ensuring your browser tabs close and counter increments
        await page.close(); 
      }
    }

    // * Save the master object to the JSON file outside the loop
    const fileName = `scraped_data/${currentTournament.id}_data.json`;
    try {
      fs.writeFileSync(fileName, JSON.stringify(finalTournamentData, null, 2));
      console.log("Successfully saved all 18 holes to", chalk.magenta(`${fileName}`));
    } catch (error) {
      console.error("Error writing to JSON file:", error);
    }
  }
   
  // End time 
  const end = performance.now();
  const elapsed = (end - start) / 1000; 
  console.log(chalk.green(`Execution time: ${elapsed.toFixed(3)} seconds`));

  // await browser.close(); // TODO: figure out what this isn't closing properly
};


getHoleData(); // * main function call

// endregion Main Function