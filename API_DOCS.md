# 🏀 NBA Backend API Documentation

**Base URL:** `https://nba-backend-391303839683.europe-west1.run.app`

---

## 📊 Genel Bilgiler

### Response Formatı
Tüm API'ler JSON formatında döner:
```json
{
  "status": "success",
  "results": 10,
  "pagination": {...},
  "data": {...}
}
```

### Pagination (Sayfalama)
Liste endpoint'leri sayfalama destekler:
- `page`: Sayfa numarası (varsayılan: 1)
- `per_page`: Sayfa başına kayıt (varsayılan: 20, max: 100)

---

## 1. 🏥 Health Check

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/health` | Sunucu ve veritabanı durumu |

**Örnek Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "cloud",
  "timestamp": "2025-12-17T15:25:00"
}
```

---

## 2. 🏀 Teams (Takımlar)

### Tüm Takımları Listele
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/teams` | Tüm takımları listeler |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| page | int | Sayfa numarası |
| per_page | int | Sayfa başına kayıt |
| conference | string | `East` veya `West` |

**Örnek:**
```
GET /api/v1/teams?conference=East&page=1&per_page=10
```

---

### Takım Detayı
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/teams/{teamID}` | Takım detayı + kadro |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| season | string | `REGULAR` veya `PLAYOFF` |

**Örnek:**
```
GET /api/v1/teams/1610612738?season=REGULAR
```

**Response içeriği:**
- Takım bilgileri (isim, logo, konferans)
- Takım sıralaması (winRank, defRatingRank...)
- Kadro listesi (her oyuncunun ortalama istatistikleri)

---

### Takım Sıralamaları (Standings)
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/teams/standings` | Konferans sıralaması |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| conference | string | `East` veya `West` |
| season | string | `REGULAR` veya `PLAYOFF` |

**Örnek:**
```
GET /api/v1/teams/standings?conference=East&season=REGULAR
```

---

### Takım Arena Bilgisi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/teams/{teamID}/arena` | Arena detayları |

**Response:**
- Şehir, eyalet, arena adı
- Kapasite
- Koordinatlar (latitude, longitude)
- Saat dilimi

---

### Takım Maç Programı
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/teams/{teamID}/fixtures` | Takımın maçları |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| limit | int | Maksimum maç sayısı |

---

## 3. 👤 Players (Oyuncular)

### Tüm Oyuncuları Listele
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/players` | Tüm oyuncuları listeler |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| page | int | Sayfa numarası |
| per_page | int | Sayfa başına kayıt |
| team_id | int | Takım ID'sine göre filtrele |
| position | string | Pozisyona göre filtrele |

---

### Oyuncu Arama
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/players/search` | İsme göre arama |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| q | string | Arama terimi (min 2 karakter) |

**Örnek:**
```
GET /api/v1/players/search?q=LeBron
```

---

### Oyuncu Detayı
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/players/{playerID}` | Oyuncu bilgisi + istatistikler |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| season | string | `REGULAR` veya `PLAYOFF` |
| location | string | `HOME`, `AWAY` veya `OVERALL` |

**Örnek:**
```
GET /api/v1/players/2544?season=REGULAR&location=OVERALL
```

**Response istatistikleri:**
- PTS, AST, REB, steal, TOV
- FG_PCT, FG3_PCT, FT_PCT
- efficiency, GP_X, MIN_X

---

## 4. 📈 Stats (İstatistikler)

### Kategori Liderleri
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/stats/leaders` | En iyi oyuncular |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| category | string | `PTS`, `AST`, `REB`, `steal`, `efficiency`, `FG_PCT` |
| season | string | `REGULAR` veya `PLAYOFF` |
| limit | int | Kaç oyuncu (varsayılan: 5) |

**Örnek:**
```
GET /api/v1/stats/leaders?category=PTS&season=REGULAR&limit=10
```

---

### Takım Karşılaştırma
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/stats/team-comparison` | İki takımı karşılaştır |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| team1 | int | İlk takım ID |
| team2 | int | İkinci takım ID |
| season | string | `REGULAR` veya `PLAYOFF` |

**Örnek:**
```
GET /api/v1/stats/team-comparison?team1=1610612738&team2=1610612747
```

---

## 5. 📅 Fixtures (Maçlar)

### Tüm Maçlar
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/fixtures` | Tüm maçları listele |

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| page | int | Sayfa numarası |
| per_page | int | Sayfa başına kayıt |
| round | int | Hafta/round numarası |
| team | string | Takım adı filtresi |

---

### Maç Detayı
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/fixtures/{matchID}` | Tek maç detayı |

---

## 6. 🏟️ Arenas

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/arenas` | Tüm arena bilgileri |

---

## 7. 🔐 Admin Panel API'leri

> ⚠️ Bu API'ler POST/PUT/DELETE kullanır. Postman ile test edilmeli.

### Dashboard
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/admin/dashboard` | Özet istatistikler |

### Takım Yönetimi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/v1/admin/teams` | Yeni takım ekle |
| PUT | `/api/v1/admin/teams/{id}` | Takım güncelle |
| DELETE | `/api/v1/admin/teams/{id}` | Takım sil |

**POST Body örneği:**
```json
{
  "teamID": 123456,
  "teamName": "Yeni Takım",
  "teamAbbreviation": "YT",
  "conference": "East",
  "logoUrl": "https://..."
}
```

### Oyuncu Yönetimi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/v1/players` | Yeni oyuncu ekle |
| PUT | `/api/v1/players/{id}` | Oyuncu güncelle |
| DELETE | `/api/v1/players/{id}` | Oyuncu sil |

**POST Body örneği:**
```json
{
  "playerName": "Yeni Oyuncu",
  "teamID": 1610612738,
  "position": "Guard",
  "headshotUrl": "https://..."
}
```

### Maç Yönetimi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/v1/admin/fixtures` | Yeni maç ekle |
| PUT | `/api/v1/admin/fixtures/{id}` | Maç güncelle |
| DELETE | `/api/v1/admin/fixtures/{id}` | Maç sil |

### Arena Yönetimi
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/v1/admin/arenas` | Yeni arena ekle |
| PUT | `/api/v1/admin/arenas/{id}` | Arena güncelle |
| DELETE | `/api/v1/admin/arenas/{id}` | Arena sil |

### Oyuncu İstatistikleri
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/v1/admin/players/{id}/stats` | İstatistik ekle/güncelle |
| DELETE | `/api/v1/admin/players/{id}/stats` | İstatistik sil |

### Takım Sıralaması
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/v1/admin/teams/{id}/ranking` | Sıralama ekle/güncelle |

---

## 📋 Örnek Team ID'ler

| Takım | ID |
|-------|-----|
| Boston Celtics | 1610612738 |
| Los Angeles Lakers | 1610612747 |
| Golden State Warriors | 1610612744 |
| Miami Heat | 1610612748 |
| Dallas Mavericks | 1610612742 |

## 📋 Örnek Player ID'ler

| Oyuncu | ID |
|--------|-----|
| LeBron James | 2544 |
| Kevin Durant | 201142 |
| Stephen Curry | 201939 |
| Giannis Antetokounmpo | 203507 |
| Luka Doncic | 1629029 |
