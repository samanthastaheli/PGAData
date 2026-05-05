import puppeteer from "puppeteer";
import fs from "fs"; // file system module

const getHoleData = async () => {
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    // Headless must be true for standard Docker environments
    headless: false, 
    defaultViewport: { width: 1280, height: 800 },
  });

  const page = await browser.newPage();
  // const url = "https://tourcast.pgatour.com/tourcast.html?id=R2026556#/hole-view?pid=57366&round=1&hole=1&gv=false";
  const urls = Array.from({ length: 18 }, (_, i) => ({
    hole: i + 1,
    url: `https://tourcast.pgatour.com/tourcast.html?id=R2026556#/hole-view?pid=57366&round=1&hole=${i + 1}&gv=false`
  }));

  const finalTournamentData = {};

  for (const item of urls) { 
    console.log(`Navigating to Hole ${item.hole}...`);
    await page.goto(item.url, { waitUntil: "networkidle2" });

    // Dismiss Pop-up
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

    // Identify all shot buttons
    const shotButtonSelector = 'div[class*="shot_shotNum"]';
    try {
        await page.waitForSelector(shotButtonSelector, { timeout: 5000 });
    } catch (e) {
        console.log(`No shots found for hole ${item.hole}, skipping.`);
        continue; 
    }
    
    // Get the count of shots available
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
    // Save this holes data to the master object
    finalTournamentData[`Hole_${item.hole}`] = allShotsData;
    console.log(`Finished Hole ${item.hole}`);
  }

  // Save the master object to the JSON file outside the loop
  const fileName = 'cam_young_full_round.json';
  try {
    fs.writeFileSync(fileName, JSON.stringify(finalTournamentData, null, 2));
    console.log(`Successfully saved all 18 holes to ${fileName}`);
  } catch (err) {
    console.error("Error writing to JSON file:", err);
  }

  await browser.close();
};

getHoleData();