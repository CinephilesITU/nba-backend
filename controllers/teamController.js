// controllers/teamController.js

// db baglantisi
const pool = require('../db'); 
const { mockTeamStats } = require('../data/mockTeamStats'); //
// butun takimlar
const getAllTeams = async (req, res) => {
    try {
        const query = "SELECT TeamID, TeamName, TeamAbbreviation, LogoURL FROM Team";
        const [rows] = await pool.query(query);

        res.status(200).json({
            status: "success",
            results: rows.length,
            data: {
                teams: rows,
            }
        });
    } catch (err) {
        console.error("Takimlari alirken hata:", err);
        res.status(500).json({
            status: "error",
            message: "Sunucuda bir hata oluştu"
        });
    }
};

// id'ye gore tek takim
const getTeamById = async (req, res) => {
    try {
        const id = parseInt(req.params.id);

        // takim, takim istatistik ve rakip istatistik tablolari joinlendi
        const query = `
            SELECT * 
            FROM Team t
            LEFT JOIN TeamStats ts ON t.TeamID = ts.TeamID
            LEFT JOIN OpponentStats os ON t.TeamID = os.TeamID
            WHERE t.TeamID = ?
        `;
        
        const [rows] = await pool.query(query, [id]);

        // takim yoksa hata ver
        if (rows.length > 0) {
            res.status(200).json({
                status: "success",
                data: {
                    team: rows[0],
                }
            });
        } else {
            res.status(404).json({
                status: "fail",
                message: "Bu ID ile bir takim bulunamadi"
            });
        }

    } catch (err) {
        console.error(`ID'si ${req.params.id} olan takimi alirken hata:`, err);
        res.status(500).json({
            status: "error",
            message: "Sunucuda bir hata oluştu"
        });
    }
};

// --- 2. YENİ MOCK DATA FONKSİYONU (Commit için Geliştirme) ---


const getTeamLeaderboard = (req, res) => {
    try {
        // 1. Sıralama parametresini al (Örn: W, DEF_RATING_RANK)
        const stat = req.params.stat.toLowerCase(); 

        // 2. FİLTRELEME parametresini al (Örn: East, West) (Bu isteğe bağlıdır)
        const { conference } = req.query; 

        let teams = [...mockTeamStats]; 

        // 3. (YENİ ADIM) Önce Konferansa Göre FİLTRELE
        if (conference) {
            teams = teams.filter(t => t.conferencename.toLowerCase() === conference.toLowerCase());
        }

        // 4. Sonra SIRALA
        if (stat.includes('_rank')) {
            // Sıralama (Rank) ise: 1, 2, 3... (Küçükten Büyüğe)
            teams.sort((a, b) => a[stat] - b[stat]); 
        } else {
            // Değer (Value) ise: 64, 47... (Büyükten Küçüğe)
            teams.sort((a, b) => b[stat] - a[stat]);
        }

        // 5. İlk 5'i (veya daha azı) al
        const leaderboard = teams.slice(0, 5); 

        res.status(200).json({
            status: "success",
            stat: stat.toUpperCase(),
            filter: conference || "All", // Filtre uygulandı mı?
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


// --- 3. TÜM FONKSİYONLARI DIŞA AKTAR ---
module.exports = {
    getAllTeams,
    getTeamById,
    getTeamLeaderboard // YENİ EKLENDİ
};