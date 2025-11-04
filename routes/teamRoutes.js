// routes/teamRoutes.js

const express = require('express');
const router = express.Router();

// -----------------------------------------------------------------
// HATA BURADAYDI:
// Muhtemelen aşağıdaki 'require' satırını silmiştin veya
// 'teamController' yerine { getAllTeams, getTeamById } yazmıştın.
// 'teamController' adında bir değişkene ihtiyacımız var.

const teamController = require('../controllers/teamController');

// -----------------------------------------------------------------


// Ana rota: '/' (Tüm takımlar)
// 'teamController.getAllTeams'i çağırır
router.get('/', teamController.getAllTeams);

// ID'ye göre tek takım rotası (Senin hatan bu satırdaydı)
// 'teamController.getTeamById'i çağırır
router.get('/:id', teamController.getTeamById);


module.exports = router;