// data/mockPlayers.js
// Bu, SQL'deki 'Player' tablosunu taklit eder.

const mockPlayers = [
    {
        playerid: 203954,
        teamid: 1610612737, // Atlanta Hawks
        playername: "Trae Young",
        position: "G",
        headshoturl: "https://cdn.nba.com/headshots/nba/latest/1040x760/203954.png"
    },
    {
        playerid: 1628369,
        teamid: 1610612738, // Boston Celtics
        playername: "Jayson Tatum",
        position: "F-G",
        headshoturl: "https://cdn.nba.com/headshots/nba/latest/1040x760/1628369.png"
    },
    {
        playerid: 2544,
        teamid: 1610612747, // Los Angeles Lakers
        playername: "LeBron James",
        position: "F",
        headshoturl: "https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png"
    },
    {
        playerid: 1629027,
        teamid: 1610612747, // Los Angeles Lakers
        playername: "Rui Hachimura",
        position: "F",
        headshoturl: "https://cdn.nba.com/headshots/nba/latest/1040x760/1629027.png"
    }
];

module.exports = {
    mockPlayers
};