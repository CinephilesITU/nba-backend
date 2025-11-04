// data/mockOpponentStats.js
// Bu, SQL'deki 'OpponentStats' tablosunu taklit eder.

const mockOpponentStats = [
    {
        teamid: 1610612737, // Atlanta Hawks
        opp_pts_off_tov: 17.5, opp_pts_2nd_chance: 15.6, opp_pts_paint: 54.9
    },
    {
        teamid: 1610612738, // Boston Celtics
        opp_pts_off_tov: 15.0, opp_pts_2nd_chance: 12.8, opp_pts_paint: 47.3
    },
    {
        teamid: 1610612747, // Los Angeles Lakers
        opp_pts_off_tov: 15.9, opp_pts_2nd_chance: 14.5, opp_pts_paint: 53.0
    }
];

module.exports = { mockOpponentStats };