# 🏀 NBA Project API Documentation

Bu proje, NBA oyuncu ve takım istatistiklerini yöneten bir RESTful API sunar.

## 🔗 Base URL
`http://127.0.0.1:5000/api`

## 📌 Endpoints (Uç Noktalar)

### 1. Oyuncular (Players)
| Metot | URL | Açıklama |
|-------|-----|----------|
| `GET` | `/players` | Tüm oyuncuları listeler. |
| `GET` | `/players/<id>` | ID'si verilen oyuncunun detaylarını ve istatistiklerini (Normal Sezon + Playoff) getirir. |
| `GET` | `/players/search?q=LeBron` | İsme göre oyuncu arar. |
| `POST` | `/players` | Yeni oyuncu ekler. (Body: `playerName`, `teamID` zorunlu) |
| `PUT` | `/players/<id>` | Oyuncu bilgilerini günceller. |
| `DELETE`| `/players/<id>` | Oyuncuyu siler. |

### 2. Takımlar (Teams)
| Metot | URL | Açıklama |
|-------|-----|----------|
| `GET` | `/teams` | Tüm takımları listeler. |
| `GET` | `/teams/<id>` | Takım detayını, kadrosunu ve sıralama bilgilerini getirir. |

### 3. İstatistikler & Sıralama (Stats)
| Metot | URL | Açıklama |
|-------|-----|----------|
| `GET` | `/stats/top?category=PTS` | Belirli bir kategoride en iyi oyuncuları getirir. |
| `GET` | `/stats/top?category=EFF` | En verimli oyuncuları getirir. |

---
**Validasyon Kuralları:**
* `playerName`: En az 2 karakter olmalıdır.
* `PTS`, `AST` vb. istatistikler negatif olamaz.