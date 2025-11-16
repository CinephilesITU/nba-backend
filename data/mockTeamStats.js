// data/mockTeamStats.js
// 'getTeamLeaderboard' fonksiyonu için geçici veri
// YENİ: Filtreleme yapabilmek için 'conferencename' eklendi.

const mockTeamStats = [
    { 
        teamid: 1610612738, 
        teamname: "Boston Celtics", 
        conferencename: "East", // Filtre için
        w: 64, 
        def_rating_rank: 2, 
        stl_rank: 20 
    },
    { 
        teamid: 1610612747, 
        teamname: "Los Angeles Lakers", 
        conferencename: "West", // Filtre için
        w: 47, 
        def_rating_rank: 17, 
        stl_rank: 14 
    },
    { 
        teamid: 1610612737, 
        teamname: "Atlanta Hawks", 
        conferencename: "East", // Filtre için
        w: 36, 
        def_rating_rank: 27, 
        stl_rank: 3 
    },
    { 
        teamid: 1610612745, // Örnek olarak 4. bir takım
        teamname: "Houston Rockets", 
        conferencename: "West", // Filtre için
        w: 41, 
        def_rating_rank: 10, 
        stl_rank: 2 
    }
];

module.exports = { mockTeamStats };