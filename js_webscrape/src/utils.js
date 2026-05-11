import fs from 'fs';

/**
 * Reads a JSON file and returns the parsed data.
 * @param {string} filePath - Path to your .json file
 */
const loadAndProcessJSON = (filePath) => {
  try {
    // 1. Read the file (utf-8 ensures it returns a string, not a Buffer)
    const rawData = fs.readFileSync(filePath, 'utf-8');

    // 2. Parse the string into a JS Object
    const jsonData = JSON.parse(rawData);

    // 3. Return the data so you can loop through it elsewhere
    return jsonData;

  } catch (error) {
    console.error(`Error reading or parsing ${filePath}:`, error.message);
    return null;
  }
};

/**
 * Loads players Ids as an array.
 */
export const loadPlayerIds = () => {
    const data = loadAndProcessJSON('../../sources/players.json');

    if (!data) {
        console.error("Could not load player data.");
        return [];
    }

    // 1. Object.values(data) gives us: [{id: "01001", ...}, {id: "12855", ...}]
    // 2. .map(p => p.id) extracts just the ID strings
    const playerIds = Object.values(data).map(player => player.id);

    console.log(`Successfully extracted ${playerIds.length} IDs.`);
    return playerIds; // Result: ["01001", "12855", "12856", ...]
};

const playerIds = loadPlayerIds()
console.log("Player IDs:")
console.log(playerIds)