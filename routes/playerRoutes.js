// routes/playerRoutes.js

const express = require('express');
const router = express.Router();

// Controller'dan ÜÇ fonksiyonu da çağır
const { 
    getAllPlayers, 
    getPlayerById,
    getPlayerLeaderboard // YENİ
} = require('../controllers/playerController');


// --- VERİTABANI GEREKTİREN YOLLAR ---
// (XAMPP çalışana kadar 500 hatası vermeleri normaldir)
router.get('/', getAllPlayers);
router.get('/:id', getPlayerById);

// --- MOCK DATA KULLANAN YENİ YOL ---
// (Bu, XAMPP çalışmasa bile çalışacaktır)
router.get('/leaderboard/:stat', getPlayerLeaderboard);


module.exports = router;