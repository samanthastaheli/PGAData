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
  const url = "https://tourcast.pgatour.com/tourcast.html?id=R2026556#/hole-view?pid=57366&round=1&hole=1&gv=false";

  console.log("Navigating to Tourcast...");
  await page.goto(url, { waitUntil: "networkidle2" });

  // 1. Dismiss Pop-up
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

  // 2. Identify all shot buttons
  const shotButtonSelector = 'div[class*="shot_shotNum"]';
  await page.waitForSelector(shotButtonSelector);
  
  // Get the count of shots available
  const shotCount = await page.evaluate((sel) => {
    return document.querySelectorAll(sel).length;
  }, shotButtonSelector);

  console.log(`Detected ${shotCount} shots. Starting loop...`);
  const allShotsData = [];

  // 3. Loop through each shot
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

    // 4. Scrape the data for the current shot
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

  // --- SAVE TO JSON FILE ---
  const fileName = 'hole_1_cam_young_data.json';
  try {
    // stringify(data, replacer, whitespace) - the '2' makes it readable
    fs.writeFileSync(fileName, JSON.stringify(allShotsData, null, 2));
    console.log(`Successfully saved data to ${fileName}`);
  } catch (err) {
    console.error("Error writing to JSON file:", err);
  }

  console.log('--- ALL HOLE DATA ---');
  console.table(allShotsData);

  await browser.close();
};

getHoleData();