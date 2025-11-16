// controllers/playerController.js

// Sahte veri importlarını siliyoruz. Onların yerine veritabanı bağlantımızı çağırıyoruz.
const pool = require('../db'); // db.js'den gelen MySQL bağlantı havuzu

const { mockPlayerRegularStats } = require('../data/mockPlayerRegularStats'); // GEÇİCİ

// Fonksiyonu 'async' olarak işaretliyoruz çünkü veritabanı işlemleri zaman alır.
const getAllPlayers = async (req, res) => {
    try {
        // SQL sorgumuzu yazıyoruz.
        const query = "SELECT * FROM Player";

        // Veritabanından veriyi çekiyoruz. 'await' ile işlemin bitmesini bekliyoruz.
        const [rows] = await pool.query(query);

        // Başarılı bir şekilde veriyi istemciye (frontend'e) gönderiyoruz.
        res.status(200).json({
            status: "success",
            results: rows.length,
            data: {
                players: rows,
            }
        });
    } catch (err) {
        console.error("Tüm oyuncuları alırken hata:", err); // Hatayı konsola yazdır
        res.status(500).json({
            status: "error",
            message: "Sunucuda bir hata oluştu"
        });
    }
};

// "ID'ye göre tek bir oyuncu getir" fonksiyonu
const getPlayerById = async (req, res) => {
    try {
        // 1. İstek atılan ID'yi al
        const id = parseInt(req.params.id);

        // 2. SQL sorgusunu yaz. SQL Injection'ı önlemek için '?' kullanıyoruz.
        const query = "SELECT * FROM Player WHERE PlayerID = ?";

        // 3. Veritabanından sorguyu çalıştır. ID'yi ikinci parametre olarak güvenli bir şekilde gönderiyoruz.
        const [rows] = await pool.query(query, [id]);

        // 4. Oyuncuyu bulursak... (rows dizisinde en az bir eleman varsa)
        if (rows.length > 0) {
            res.status(200).json({
                status: "success",
                data: {
                    player: rows[0], // Dönen dizinin ilk elemanı bizim oyuncumuzdur.
                }
            });
        } else {
            // 5. Oyuncuyu bulamazsak...
            res.status(404).json({
                status: "fail",
                message: "Bu ID ile bir oyuncu bulunamadı"
            });
        }

    } catch (err) {
        console.error(`ID'si ${req.params.id} olan oyuncuyu alırken hata:`, err);
        res.status(500).json({
            status: "error",
            message: "Sunucuda bir hata oluştu"
        });
    }
};


// --- YENİ FONKSİYON: Liderlik Tablosu (Mock Data Kullanıyor) ---
const getPlayerLeaderboard = (req, res) => {
    try {
        const stat = req.params.stat.toUpperCase(); 
        
        // Veriyi mock dosyadan oku
        let players = [...mockPlayerRegularStats]; 

        // Veriyi sırala
        players.sort((a, b) => b[stat.toLowerCase()] - a[stat.toLowerCase()]);
        
        const leaderboard = players.slice(0, 5); // İlk 5'i al

        res.status(200).json({
            status: "success",
            stat: stat,
            results: leaderboard.length,
            data: {
                leaderboard: leaderboard,
            }
        });

    } catch (err) {
        console.error(err.message);
        res.status(400).json({
            status: "error",
            message: "İstatistik bulunamadı veya geçersiz."
        });
    }
};

// 3. 'module.exports' Satırını Güncelle:
//    Dosyanın en altındaki 'module.exports' satırını
//    aşağıdaki gibi 3 fonksiyonu da içerecek şekilde GÜNCELLE:
module.exports = {
    getAllPlayers,
    getPlayerById,
    getPlayerLeaderboard // YENİ EKLENDİ
};
