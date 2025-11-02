// data/mockPlayers.js

// Proposal'a göre: playerID, teamID, playerName, position, headshotUrl 
const mockPlayers = [
    {
        playerid: 203954,
        teamid: 1610612737, // Atlanta Hawks'ın ID'si (mockTeams.js'ten)
        playername: "Trae Young",
        position: "G",
        headshoturl: "https://example.com/trae_young.png"
    },
    {
        playerid: 1628369,
        teamid: 1610612738, // Boston Celtics'in ID'si
        playername: "Jayson Tatum",
        position: "F-G",
        headshoturl: "https://example.com/jayson_tatum.png"
    },
    {
        playerid: 2544,
        teamid: 1610612747, // Los Angeles Lakers'ın ID'si
        playername: "LeBron James",
        position: "F",
        headshoturl: "https://example.com/lebron_james.png"
    },
    {
        playerid: 1629027,
        teamid: 1610612747, // Los Angeles Lakers
        playername: "Rui Hachimura",
        position: "F",
        headshoturl: "https://example.com/rui_hachimura.png"
    }
];

module.exports = {
    mockPlayers
};