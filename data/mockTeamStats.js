// data/mockTeamStats.js
// Bu, SQL'deki 'TeamStats' tablosunu taklit eder.

const mockTeamStats = [
    {
        teamid: 1610612737, // Atlanta Hawks
        gp: 82, w: 36, l: 46, w_pct: 0.439,
        def_rating_rank: 27, dreb_rank: 19, stl_rank: 3, blk_rank: 18
    },
    {
        teamid: 1610612738, // Boston Celtics
        gp: 82, w: 64, l: 18, w_pct: 0.780,
        def_rating_rank: 2, dreb_rank: 1, stl_rank: 20, blk_rank: 1
    },
    {
        teamid: 1610612747, // Los Angeles Lakers
        gp: 82, w: 47, l: 35, w_pct: 0.573,
        def_rating_rank: 17, dreb_rank: 18, stl_rank: 14, blk_rank: 11
    }
];

module.exports = { mockTeamStats };