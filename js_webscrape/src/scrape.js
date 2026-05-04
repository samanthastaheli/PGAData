import puppeteer from "puppeteer";

const getHoleData = async () => {
  // Start a Puppeteer session with:
  // - a visible browser (`headless: false` - easier to debug because you'll see the browser in action)
  // - no default viewport (`defaultViewport: null` - website page will in full width and height)
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    headless: false,
    defaultViewport: null,
  });

  // Open a new page
  const page = await browser.newPage();

  const url = "https://tourcast.pgatour.com/tourcast.html?id=R2026556#/hole-view?pid=57366&round=1&hole=1&gv=false"
  // On this new page:
  // - open the "http://holeData.toscrape.com/" website
  // - wait until the dom content is loaded (HTML is ready)
  await page.goto(url, {
    waitUntil: "domcontentloaded",
  });

  // Wait for and click the Close button on the pop-up if it appears
  try {
      console.log("Waiting for pop-up...");
      // const closeSelector = 'div[aria-label="Close"]';
      const closeSelector = 'div[class*="informationContent_close"]';
      await page.waitForSelector(closeSelector, { visible: true, timeout: 5000 });
      await page.evaluate((sel) => {
        const btn = document.querySelector(sel);
        if (btn) btn.click();
    }, closeSelector);
    
    console.log("Pop-up dismissed successfully.");
  } catch (e) {
      console.log("Close button not found or already closed.");
  }

  // Small delay for the overlay animation to finish
  await new Promise(r => setTimeout(r, 1000));

  // Click shot 1 button 
  // "shot_shotNum__aNmlh shot_selected__ToMFP shot_includeVideo__nIcFc"
 await page.evaluate(() => {
    // Look for the specific div class from your screenshot
    const shotButtons = Array.from(document.querySelectorAll('div[class*="shot_shotNum"]'));
    const shotOne = shotButtons.find(el => el.textContent.trim() === '1');

    if (shotOne) {
        // Dispatching a full PointerEvent sequence often bypasses "stuck" buttons
        const opts = { bubbles: true, cancelable: true, view: window };
        shotOne.dispatchEvent(new PointerEvent('pointerdown', opts));
        shotOne.dispatchEvent(new PointerEvent('pointerup', opts));
        shotOne.click();
    }
  });

  // Wait for the 'notSelected' class to disappear from the '1' button
  await page.waitForFunction(() => {
      const btn = Array.from(document.querySelectorAll('div[class*="shot_shotNum"]'))
                      .find(el => el.textContent.trim() === '1');
      return btn && !btn.className.includes('notSelected');
  }, { timeout: 5000 });

  // Give the UI a moment to update the data after the click
  await new Promise(r => setTimeout(r, 1000));

  // Debugging page
  await page.waitForSelector('[class*="primaryPlayerController_shotsData"]');
  // await page.screenshot({ path: 'debug3.png' });

  // Get shot data
  // Use page.evaluate to run code in the browser context
  const shotData = await page.evaluate(() => {
      // Focus specifically on the container seen in image_4a3e42.png
      const rootContainer = document.querySelector('[class*="primaryPlayerController_shotsContainer"]');
      if (!rootContainer) return { error: "Main container not found" };

      const rows = rootContainer.querySelectorAll('[class*="primaryPlayerController_shotsData"]');
      const results = {};

      rows.forEach(div => {
          // Use textContent instead of innerText to get text even if hidden by a pop-up
          const fullText = div.textContent.trim(); 
          const label = div.querySelector('span')?.textContent.trim();
          const value = fullText.replace(label, '').trim();

          if (label?.includes('Shot')) results.shotDist = value;
          else if (label === 'To Hole') results.toHole = value;
          else if (label === 'Loc') results.location = value;
      });

      return results;
  });

  // Display the scraped data
  console.log('Scraped Data:', shotData);

  // Click on the "Next page" button
  // await page.click(".pager > .next > a");

  // Close the browser
  await browser.close();
};

// Start the scraping
getHoleData();