// data/mockPlayerRegularStats.js
// Bu, SQL'deki 'PlayerStats' tablosunun 'SeasonType' = 'Regular Season' olan kısmıdır.

const mockPlayerRegularStats = [
    {
        playerid: 203954, // Trae Young
        seasontype: "Regular Season", gp: 73, pts: 25.7, reb: 3.0, ast: 10.8,
    },
    {
        playerid: 1628369, // Jayson Tatum
        seasontype: "Regular Season", gp: 74, pts: 26.9, reb: 8.1, ast: 4.9,
    },
    {
        playerid: 2544, // LeBron James
        seasontype: "Regular Season", gp: 71, pts: 25.7, reb: 7.3, ast: 8.3,
    },
    {
        playerid: 1629027, // Rui Hachimura
        seasontype: "Regular Season", gp: 68, pts: 13.6, reb: 4.3, ast: 1.2,
    }
];

module.exports = { mockPlayerRegularStats };