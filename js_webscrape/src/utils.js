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
export const getPlayerIds = () => {
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
 * Loads players Ids and their names as a dict.
 */
export const loadPlayerNames = () => {
    const data = loadAndProcessJSON('../../sources/players.json');
    const playerDict = {};

    if (!data) {
        console.error("Could not load player data.");
        return [];
    }

    Object.entries(data).forEach(([name, info]) => {
        playerDict[name] = info.id;
    });

    return playerDict; 
};

/**
 * Generates a flat list of all URLs for specified tournament and player with 4 rounds and 18 holes.
 * @param {string} tournamentId - The unique ID for the tournament (e.g., 'R2026556')
 * @param {Array} playerObjects - An array of objects containing player information (e.g., [{ id: '57366', name: 'Cameron Young' }])
 */
export const generateTourCastUrlsForPlayer = (tournamentId, playerObjects) => {
    // const rounds = [1, 2, 3, 4];
    // const holes = Array.from({ length: 18 }, (_, i) => i + 1);
    const rounds = [1]; // TODO: for testing
    const holes = [1]; // TODO: for testing

    // Use flatMap to create one long list of 72 urls per player
    return playerObjects.flatMap(player =>
        rounds.flatMap(r =>
            holes.map(h => ({
                playerId: player.id,
                playerName: player.name,
                round: r,
                hole: h,
                url: `https://tourcast.pgatour.com/tourcast.html?id=${tournamentId}#/hole-view?pid=${player.id}&round=${r}&hole=${h}&gv=false`
            }))
        )
    );
};

/**
 * Generates a URL for specified tournament and player with round 1 and hole 1 to test if player is in tournament.
 * @param {string} tournamentId - The unique ID for the tournament (e.g., 'R2026556')
 * @param {string} playerId - The unique ID for the player (e.g., '57366')
 */
export const generateTestUrlForPlayer = (tournamentId, playerId) => {
    return `https://tourcast.pgatour.com/tourcast.html?id=${tournamentId}#/hole-view?pid=${playerId}&round=1&hole=1&gv=false`;
};

/**
 * Generate browser and page.
 */