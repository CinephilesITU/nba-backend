// data/mockTeams.js
// Bu, SQL'deki 'Team' tablosunu taklit eder.
// (Not: 'conference' adını da ekliyoruz, çünkü SQL sorgumuzda
// 'Team' ve 'Conference' tablolarını JOIN edecektik.)

const mockTeams = [
    {
        teamid: 1610612737,
        teamname: "Atlanta Hawks",
        teamabbreviation: "ATL",
        logourl: "https://cdn.nba.com/logos/nba/1610612737/primary/L/logo.svg",
        conferenceid: 1, // Doğu Konferansı (Varsayım)
        conferencename: "East"
    },
    {
        teamid: 1610612738,
        teamname: "Boston Celtics",
        teamabbreviation: "BOS",
        logourl: "https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg",
        conferenceid: 1,
        conferencename: "East"
    },
    {
        teamid: 1610612747,
        teamname: "Los Angeles Lakers",
        teamabbreviation: "LAL",
        logourl: "https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg",
        conferenceid: 2, // Batı Konferansı (Varsayım)
        conferencename: "West"
    }
];

module.exports = {
    mockTeams
};