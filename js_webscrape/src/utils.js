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
    return playerIds; 
};

/**
 * Loads players Ids and their names as a dict.
 */
export const loadPlayers = () => {
    const data = loadAndProcessJSON('../../sources/players.json');
    const playerDict = {};

    if (!data) {
        console.error("Could not load player data.");
        return [];
    }

    Object.entries(data).forEach(([name, info]) => {
        playerDict[info.id] = name;
    });

    return playerDict; 
};

/**
 * Generates a flat list of all URLs for specified players, rounds, and holes.
 * @param {string} tournamentId - The unique ID for the tournament (e.g., 'R2026556')
 */
export const generateTourCastUrls = (tournamentId) => {
    const rounds = [1, 2, 3, 4];
    const holes = Array.from({ length: 18 }, (_, i) => i + 1);
    const playerIds = loadPlayerIds()
    // Use flatMap to create one long list of 72 tasks per player
    return playerIds.flatMap(pid =>
        rounds.flatMap(r =>
            holes.map(h => ({
                playerId: pid,
                round: r,
                hole: h,
                url: `https://tourcast.pgatour.com/tourcast.html?id=${tournamentId}#/hole-view?pid=${pid}&round=${r}&hole=${h}&gv=false`
            }))
        )
    );
};

/**
 * Generate browser and page.
 */