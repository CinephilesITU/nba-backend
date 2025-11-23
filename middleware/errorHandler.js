// middleware/errorHandler.js

const errorHandler = (err, req, res, next) => {
    // Hata kodunu belirle (Eğer hata kodunu biz belirlemediysek 500 kullan)
    const statusCode = err.statusCode || 500;

    // Konsola detaylı hatayı yazdır
    console.error(err.stack);

    // İstemciye (Postman/Frontend) standart bir JSON yanıtı gönder
    res.status(statusCode).json({
        status: 'error',
        statusCode: statusCode,
        message: err.message || 'Sunucu tarafında bilinmeyen bir hata oluştu.'
    });
};

module.exports = errorHandler;