import puppeteer from "puppeteer";
import fs from "fs"; // file system module
import { loadPlayerIds, generateTourCastUrls } from './utils.js';


const dismissPopUp = async (page) => {
  try {
    const closeSelector = 'div[class*="informationContent_close"]';
    await page.waitForSelector(closeSelector, { visible: true, timeout: 8000 });
    await page.evaluate((sel) => {
      const btn = document.querySelector(sel);
      if (btn) btn.click();
    }, closeSelector);
    console.log("Pop-up dismissed.");
    
  } catch (e) {
    console.log("No pop-up detected.");
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
        console.log(`No shots found for hole ${holeNum}, skipping.`);
        return false;
    }
};

const getShotData = async () => {
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
    } catch (e) {
      console.log(`Timed out waiting for Shot ${shotLabel} UI to update.`);
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
      console.log(`Scraped Shot ${shotLabel}:`, data);
    }
  }
  return allShotsData;
};

/**
 * Safely nests and saves hole data into the master tournament object.
 * @param {object} masterObj - The main finalTournamentData object
 * @param {object} task - The current task (contains playerId, round, hole)
 * @param {array} shotData - The array of shots scraped from the page
 */
const updateTournamentData = (masterObj, task, shotData) => {
    const { playerId, round, hole } = task;

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

    console.log(`Saved: Player ${playerId} | Round ${round} | Hole ${hole}`);
    
    return masterObj;
};

const getHoleData = async () => {
  const start = performance.now();
  
  // Get urls
  const currentTournamentId = "R2026556" // cadillac tournament
  const urls = generateTourCastUrls(currentTournamentId)

  const finalTournamentData = {};

  for (const item of urls) { 
    // Start new browser instance for each hole
    const browser = await puppeteer.launch({
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
      headless: false, // Headless must be true for Docker
      defaultViewport: { width: 1280, height: 800 },
    });
    const page = await browser.newPage();

    // Navigate to url
    // for player in player id list try and see if they are actually in the tournament
    try {
      console.log(`Navigating to Player ${item.playerId} Hole ${item.hole} Round ${item.round}...`);
      console.log(`URL: ${item.url}`);
      await page.goto(item.url, { waitUntil: "networkidle2" });

      // Dismiss Pop-up
      await dismissPopUp(page)

      // if no shot buttons then not correct player 
      const hasShots = await checkForShots(page, task.hole);

      // If false skip this hole and move to the next one
      if (!hasShots) {
          continue; 
      }

      // Get the count of shots available
      const shotsData = getShotData();

      // Update the master object using the utility
      updateTournamentData(finalTournamentData, task, allShotsData);

      await browser.close();

    } catch (e) {
      console.log("Player", item.playerId, "not found.");
      continue;
    }
  }

  // Save the master object to the JSON file outside the loop
  const fileName = `${currentTournamentId}_data.json`;
  try {
    fs.writeFileSync(fileName, JSON.stringify(finalTournamentData, null, 2));
    console.log(`Successfully saved all 18 holes to ${fileName}`);
  } catch (err) {
    console.error("Error writing to JSON file:", err);
  }

  // await browser.close();
  // End time 
  const end = performance.now();
  const elapsed = (end - start) / 1000; 
  console.log(`Execution time: ${elapsed.toFixed(3)} seconds`);
};

getHoleData();