// data/mockTeams.js

// Proposal'daki TEAMS tablosunun  verisine benzetilmiş sahte veriler
const mockTeams = [
    {
        teamid: 1610612737,
        teamname: "Atlanta Hawks",
        logourl: "https://example.com/hawks_logo.png",
        teamabbreviate: "ATL",
        conference: "East"
    },
    {
        teamid: 1610612738,
        teamname: "Boston Celtics",
        logourl: "https://example.com/celtics_logo.png",
        teamabbreviate: "BOS",
        conference: "East"
    },
    {
        teamid: 1610612747,
        teamname: "Los Angeles Lakers",
        logourl: "https://example.com/lakers_logo.png",
        teamabbreviate: "LAL",
        conference: "West"
    }
];

// Bu veriyi başka dosyalarda kullanmak için "export" ediyoruz.
module.exports = {
    mockTeams
};