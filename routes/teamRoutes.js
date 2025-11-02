// routes/teamRoutes.js

const express = require('express');
const router = express.Router(); // Express'in yönlendirici özelliğini kullanıyoruz

// Controller'ımızı (işi yapacak olanı) çağırıyoruz
const teamController = require('../controllers/teamController');

// --- ROTALAR ---

// Ana rota: '/'
// Bu dosya /api/v1/teams'e bağlandığı için
// buradaki '/' aslında http://localhost:5001/api/v1/teams anlamına gelecek.
router.get('/', teamController.getAllTeams); 
// Dikkat et: getAllTeams() şeklinde ÇAĞIRMIYORUZ.
// Sadece referansını veriyoruz. Express, istek gelince onu çalıştıracak.

// Başka bir rota eklersek (örn: tek bir takımı id ile getirme)
// router.get('/:id', teamController.getTeamById);

// Bu router'ı ana index.js dosyasının kullanabilmesi için "export" ediyoruz.
module.exports = router;