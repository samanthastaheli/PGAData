import puppeteer from "puppeteer";
import fs from "fs"; // file system module
import { getPlayerIds, generateTourCastUrlsForPlayer, generateTestUrlForPlayer, loadPlayers } from './utils.js';
import chalk from 'chalk'; // change color in terminal

// ***************************************************************************************
// region Helper Functions
// ***************************************************************************************

const startBrowser = async () => {
  const browser = await puppeteer.launch({
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
      headless: false, // Headless must be true for Docker
      defaultViewport: { width: 1280, height: 800 },
    });
    const page = await browser.newPage();
    return page;
}

const navigateToUrl = async (url, page) => {
  console.log(chalk.magenta(`Navigating to ${url}`));
  await page.goto(url, { waitUntil: "networkidle2" });
}

const dismissPopUp = async (page) => {
  try {
    const closeSelector = 'div[class*="informationContent_close"]';
    await page.waitForSelector(closeSelector, { visible: true, timeout: 8000 });
    await page.evaluate((sel) => {
      const btn = document.querySelector(sel);
      if (btn) btn.click();
    }, closeSelector);
    console.log(chalk.bgBlue.white("Pop-up dismissed."));
    
  } catch (error) {
    console.log(chalk.red(`Error: ${error}, No pop-up detected.`));
  }

  await new Promise(r => setTimeout(r, 1000));
}

/**
 * Checks if shots are available on the page.
 * @param {object} page - The Puppeteer page instance
 * @param {number} holeNum - The current hole number for logging
 * @returns {boolean} - Returns true if shots exist, false otherwise
 */
const checkForShots = async (page, holeNum) => {
    const shotButtonSelector = 'div[class*="shot_shotNum"]';
    
    try {
        await page.waitForSelector(shotButtonSelector, { timeout: 5000 });
        return true; 
    } catch (e) {
        console.log(chalk.magenta(`No shots found for hole ${holeNum}, skipping.`));
        return false;
    }
};

const getShotData = async (page) => {
  const shotCount = await page.evaluate((sel) => document.querySelectorAll(sel).length, shotButtonSelector);
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
    }, i, shotButtonSelector);

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
      console.log(chalk.pink(`Scraped Shot ${shotLabel}:`), data);
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
    const { playerId, round, hole } = holeInfo;

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

    console.log(chalk.pink(`Saved: Player ${playerId} | Round ${round} | Hole ${hole}`));
    
    return masterObj;
};

/**
 * Generate an array of players IDs that are in the tournament.
 * @param {string} tournamentId - The unique ID for the tournament (e.g., 'R2026556')
 */
const getPlayersInTournament = async (tournamentId) => {
  // TODO: this method didn't work so try using this url to get the list from here:
  // for player in player id list try and see if they are actually in the tournament
  // const playersInTournament = [];
  const url = "https://www.pgatour.com/tournaments/2026/cadillac-championship/R2026556/leaderboard"
  
  const page = await startBrowser();
  await navigateToUrl(url, page);
  
  // extract data
  await page.waitForSelector('.chakra-text.css-1v9q6zy');
  const playersInTournament = await page.$$eval('.chakra-text.css-1v9q6zy', elements => {
    return elements.map(el => el.innerText.trim());
  });

  // get player IDs 
  const playerIds = [];
  const playersDict = loadPlayers();
  for (const playerName in playersInTournament) {
    
  }
  
  console.log(chalk.magenta("Players in tournament:", playersInTournament))

  return playersInTournament;
}

// endregion Helper Functions

// ***************************************************************************************
// region Main Function
// ***************************************************************************************

const getHoleData = async () => {
  const start = performance.now();
  
  // * Get urls
  const currentTournamentId = "R2026556" // cadillac tournament
  // const currentTournamentId = "R2026480" // Truist Championship
  const playersInTournament = await getPlayersInTournament(currentTournamentId);
  const urls = generateTourCastUrlsForPlayer(currentTournamentId, playersInTournament)
  console.log(chalk.blue(`Generated URLs for ${urls.length} holes across all players and rounds.`));
  const finalTournamentData = {};

  // for (const holeInfo of urls) { 
  //   // * Start new browser instance for each hole
  //   const page = await startBrowser();

  //   // * Navigate to url
  //   try {
  //     console.log(`Navigating to Player ${holeInfo.playerId} Hole ${holeInfo.hole} Round ${holeInfo.round}...`);
  //     await navigateToUrl(holeInfo.url, page);

  //     // * Dismiss Pop-up
  //     await dismissPopUp(page);

  //     // if no shot buttons then not correct player 
  //     const hasShots = await checkForShots(page, holeInfo.hole);

  //     // If false skip this hole and move to the next one
  //     if (!hasShots) {
  //         continue;
  //     }

  //     // * Get the count of shots available
  //     const shotsData = getShotData(page);

  //     // * Update the master object with the new hole data
  //     updateTournamentData(finalTournamentData, holeInfo, allShotsData);

  //     await browser.close();

  //   } catch (error) {
  //     console.log(chalk.red(`Error: ${error}, Player ${holeInfo.playerId} not found.`));
  //     continue;
  //   }
  // }

  // // * Save the master object to the JSON file outside the loop
  // const fileName = `${currentTournamentId}_data.json`;
  // try {
  //   fs.writeFileSync(fileName, JSON.stringify(finalTournamentData, null, 2));
  //   console.log("Successfully saved all 18 holes to", chalk.pink(`${fileName}`));
  // } catch (error) {
  //   console.error("Error writing to JSON file:", error);
  // }

  // // End time 
  // const end = performance.now();
  // const elapsed = (end - start) / 1000; 
  // console.log(chalk.green(`Execution time: ${elapsed.toFixed(3)} seconds`));
};


getHoleData(); // * main function call

// endregion Main Function