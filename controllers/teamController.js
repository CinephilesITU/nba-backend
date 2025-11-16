// controllers/teamController.js

// db baglantisi
const pool = require('../db'); 

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

module.exports = {
    getAllTeams,
    getTeamById
};