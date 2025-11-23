// index.js (Temizlenmiş Hali)

const express = require('express');
const cors = require('cors');
const morgan = require('morgan'); // Morgan'ı kurduysan kalsın, kurmadıysan bu satırı sil

const teamRoutes = require('./routes/teamRoutes');
const playerRoutes = require('./routes/playerRoutes');
const errorHandler = require('./middleware/errorHandler');

const app = express();
const PORT = 5001; 

// Ara katmanlar (Middleware)
app.use(cors());
app.use(morgan('dev')); // Morgan'ı kurduysan kalsın, kurmadıysan bu satırı sil
app.use(express.json());


// --- API Yolları (Routes) ---

// 1. Test yolu (Bu kalsın, çalışıp çalışmadığını anlarız)
app.get('/', (req, res) => {
    res.json({ message: 'Cinephiles NBA Backend Projesine Hoş Geldiniz! (Refactored)' });
});

// /api/v1/teams ile başlayan BÜTÜN istekleri
// teamRoutes (routes/teamRoutes.js) dosyasına yönlendir.
app.use('/api/v1/teams', teamRoutes);
app.use('/api/v1/players', playerRoutes);
app.use(errorHandler);
// Sunucuyu çalıştır
app.listen(PORT, () => {
    console.log(`Refactored Sunucu http://localhost:${PORT} adresinde çalışıyor...`);
});