// controllers/teamController.js

// Sahte verimizi buraya da çağırmamız gerekiyor, çünkü işi burada yapacağız.
const { mockTeams } = require('../data/mockTeams'); // '../' bir üst klasöre çık demektir

// "Tüm takımları getir" fonksiyonu
const getAllTeams = (req, res) => {
    try {
        // Bu, index.js içindeki app.get('/api/v1/teams'...) bloğunun
        // içindeki mantığın BİREBİR AYNISI.
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

// Başka bir fonksiyon eklediğimizde buraya ekleyeceğiz, örn: getTeamById

// Bu fonksiyonu "routes" dosyasının kullanabilmesi için "export" etmeliyiz.
module.exports = {
    getAllTeams,
    // Diğer fonksiyonlar buraya eklenecek...
};