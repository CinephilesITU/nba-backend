// data/mockPlayerPlayoffStats.js
// Bu, SQL'deki 'PlayerStats' tablosunun 'SeasonType' = 'Playoffs' olan kısmıdır.

const mockPlayerPlayoffStats = [
    {
        playerid: 1628369, // Jayson Tatum
        seasontype: "Playoffs", gp: 19, pts: 25.0, reb: 9.7, ast: 6.3,
    },
    {
        playerid: 2544, // LeBron James
        seasontype: "Playoffs", gp: 5, pts: 27.8, reb: 6.8, ast: 8.8,
    },
    {
        playerid: 1629027, // Rui Hachimura
        seasontype: "Playoffs", gp: 5, pts: 11.8, reb: 3.8, ast: 0.8,
    }
    // Not: Trae Young (203954) playoff oynamadığı için burada kaydı yok.
];

module.exports = { mockPlayerPlayoffStats };