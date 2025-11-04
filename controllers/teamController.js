// controllers/teamController.js

// 1. Mock verilerini (sahte verileri) çağır
//    (Eğer bu dosyalar yoksa, bir önceki adıma dönüp oluşturmalısın)
const { mockTeams } = require('../data/mockTeams');
const { mockTeamStats } = require('../data/mockTeamStats');
const { mockOpponentStats } = require('../data/mockOpponentStats');

// 2. Fonksiyon: Tüm takımları getir
const getAllTeams = (req, res) => {
    // Bu fonksiyon sende zaten olmalı, tüm takımları listeler
    try {
        res.status(200).json({
            status: "success",
            results: mockTeams.length,
            data: {
                teams: mockTeams,
            }
        });
    } catch (err) {
        res.status(500).json({
            status: "error",
            message: "Sunucuda bir hata oluştu"
        });
    }
};


// 3. EKSİK FONKSİYON: ID'ye göre tek takımı getir
//    Hatanın sebebi bu fonksiyonun eksik olmasıydı.
const getTeamById = (req, res) => {
    try {
        const id = parseInt(req.params.id);
        
        // 1. Takımın temel bilgilerini bul
        const teamInfo = mockTeams.find(t => t.teamid === id);
        
        if (!teamInfo) {
            // Eğer takımı bulamazsa 404 hatası ver
            return res.status(404).json({
                status: "fail",
                message: "Bu ID ile bir takım bulunamadı"
            });
        }
        
        // 2. Takımın istatistiklerini bul
        const teamStats = mockTeamStats.find(s => s.teamid === id) || null;
        
        // 3. Rakip istatistiklerini bul
        const opponentStats = mockOpponentStats.find(o => o.teamid === id) || null;
        
        // 4. Tüm veriyi birleştir
        const fullTeamData = {
            ...teamInfo, // Temel bilgiler (isim, logo...)
            teamStats: teamStats,
            opponentStats: opponentStats
        };
        
        // 5. Birleştirilmiş veriyi döndür
        res.status(200).json({
            status: "success",
            data: {
                team: fullTeamData,
            }
        });
        
    } catch (err) {
        console.error(err.message);
        res.status(500).json({
            status: "error",
            message: "Sunucuda bir hata oluştu"
        });
    }
};


// 4. Her iki fonksiyonu da dışa aktar (export et)
//    Senin hatan 33. satırda 'getTeamById' tanımlı değilken
//    buraya yazmandı. Şimdi fonksiyonu tanımladığımız için
//    bu kod doğru çalışacak.
module.exports = {
    getAllTeams,
    getTeamById
};