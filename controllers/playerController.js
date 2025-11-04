// controllers/playerController.js

// Sahte oyuncu verimizi çağırıyoruz
const { mockPlayers } = require('../data/mockPlayers');
const { mockPlayerRegularStats } = require('../data/mockPlayerRegularStats');
const { mockPlayerPlayoffStats } = require('../data/mockPlayerPlayoffStats');
// const db = require('../db'); //  veritabanı bağlantısı

// "Tüm oyuncuları getir" fonksiyonu
const getAllPlayers = (req, res) => {
    try {
        res.status(200).json({
            status: "success",
            results: mockPlayers.length,
            data: {
                players: mockPlayers,
            }
        });
    } catch (err) {
        res.status(500).json({
            status: "error",
            message: "Sunucuda bir hata oluştu"
        });
    }
};
const getPlayerById = (req, res) => {
    try {
        // 1. İstek atılan ID'yi al (req.params.id)
        // Gelen ID string'dir, onu sayıya (integer) çevirmemiz lazım
        const id = parseInt(req.params.id);

        // 2. mockPlayers dizisi içinde bu ID'ye sahip oyuncuyu bul
        const player = mockPlayers.find(p => p.playerid === id);

        // 3. Oyuncuyu bulursak...
        if (player) {
            res.status(200).json({
                status: "success",
                data: {
                    player: player,
                }
            });
        } else {
            // 4. Oyuncuyu bulamazsak... (404 Not Found hatası)
            res.status(404).json({
                status: "fail",
                message: "Bu ID ile bir oyuncu bulunamadı"
            });
        }

    } catch (err) {
        res.status(500).json({
            status: "error",
            message: "Sunucuda bir hata oluştu"
        });
    }
};

module.exports = {
    getAllPlayers,
    getPlayerById
};