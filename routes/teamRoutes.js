// routes/teamRoutes.js

const express = require('express');
const router = express.Router();

// 1. GÜNCELLEME:
// Controller'dan artık 3 fonksiyonu da çağırıyoruz.
// (Arkadaşının 'teamController' objesi yerine bu daha temizdir)
const { 
    getAllTeams, 
    getTeamById,
    getTeamLeaderboard // Bizim bu commit için eklediğimiz YENİ fonksiyon
} = require('../controllers/teamController');


// 2. ARKADAŞININ EKLEDİKLERİ (Bunlar doğru ve kalmalı)
// Ana rota: '/' (Tüm takımlar)
router.get('/', getAllTeams);

// ID'ye göre tek takım rotası
router.get('/:id', getTeamById);


// 3. YENİ ÖZELLİK (Bu satır eksikti)
// Liderlik Tablosu Rotası (Hem sıralama hem filtreleme yapar)
// Örn: /leaderboard/W?conference=East
router.get('/leaderboard/:stat', getTeamLeaderboard);


module.exports = router;