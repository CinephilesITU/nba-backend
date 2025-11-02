// routes/playerRoutes.js

const express = require('express');
const router = express.Router();

// Player Controller'ı çağırıyoruz
const { 
    getAllPlayers, 
    getPlayerById 
} = require('../controllers/playerController');
// Ana rota: '/' (http://localhost:5001/api/v1/players anlamına gelecek)
// Ana rota: '/' (Tüm oyuncular)
router.get('/', getAllPlayers);

// YENİ ROTA: '/:id' (Tek bir oyuncu)
router.get('/:id', getPlayerById);

module.exports = router;