// routes/teamRoutes.js

const express = require('express');
const router = express.Router();

// Team controller'dan gelen fonksiyonlar
const { 
    getAllTeams, 
    getTeamById,
    getTeamLeaderboard
} = require('../controllers/teamController');

// YENİ 1:
const { getPlayersByTeamId } = require('../controllers/playerController');


// --- ROTALAR ---

// Ana rota: '/' (Tüm takımlar)
router.get('/', getAllTeams);

// DİKKAT: Liderlik rotasını :id'li rotadan ÖNCEYE ALDIK
// Sebebi: Express'in 'leaderboard' kelimesini bir ID sanmasını önlemek
router.get('/leaderboard/:stat', getTeamLeaderboard);

// YENİ 2:
// Bir takıma ait oyuncuları getirir (Örn: /teams/1610612747/players)
router.get('/:teamId/players', getPlayersByTeamId);

// ID'ye göre tek takım rotası (EN SONDA OLMALI)
router.get('/:id', getTeamById);


module.exports = router;