# 🏀 NBA Analytics Backend - Proje Devir ve Teknik Rehber

Bu doküman, NBA İstatistik Projesi'nin Backend mimarisini, veritabanı yapısını, geliştirilen API endpoint'lerini ve **Antigravity** ortamına geçiş için gerekli teknik detayları içerir.

---

## 1. Proje Özeti ve Geliştirici Rolü

* **Proje Adı:** NBA Stats Backend API
* **Amaç:** NBA takımları, oyuncuları ve sezonluk performans verileri (Regular Season & Playoffs) üzerinde CRUD işlemleri, gelişmiş filtreleme ve analitik sorgular (Aggregation) sunan bir RESTful API geliştirmek.
* **Mevcut Durum:** Proje DigitalOcean (Ubuntu) sunucusunda canlıya alınmış (`Production`), temel fonksiyonları tamamlanmış ve frontend ile entegre çalışmaktadır.
* **Geliştirici Rolü (Kullanıcı):** Database & Backend Architect.
    * **Kritik Kısıt:** Projede kesinlikle **ORM (SQLAlchemy vb.) KULLANILMAMIŞTIR.** Tüm işlemler **Raw SQL (Saf SQL)** sorguları ve `mysql.connector` kütüphanesi ile manuel olarak yönetilmektedir. Bu, veritabanı hakimiyetini kanıtlamak için bilinçli bir tercihtir.

---

## 2. Teknoloji Yığını (Tech Stack)

* **Dil:** Python 3.x
* **Framework:** Flask (Micro-framework)
* **Veritabanı:** MySQL (Relational DB)
* **Sürücü:** `mysql-connector-python`
* **Sunucu:** Linux (Ubuntu) / DigitalOcean Droplet
* **Veri Formatı:** JSON

---

## 3. Veritabanı Mimarisi (Schema Overview)

Sistem ilişkisel (Relational) bir yapı üzerine kuruludur.

1.  **`TEAMS`**: Takım temel bilgileri (ID, İsim, Konferans, Logo).
2.  **`PLAYERS`**: Oyuncu temel bilgileri (ID, İsim, TakımID, Pozisyon).
3.  **Performans Tabloları (Ayrıştırılmış Yapı):**
    * `PlayerRegularSeasonPerformance`: Normal sezon oyuncu istatistikleri.
    * `PlayerPlayoffsPerformance`: Playoff dönemi oyuncu istatistikleri.
    * `TeamRegularSeasonPerformance`: Takımların sezonluk sıralama verileri.
    * `TeamPlayoffsPerformance`: Takımların playoff sıralama verileri.

> **Önemli Not:** Tablo isimleri Linux sunucularda büyük/küçük harf duyarlıdır (Case Sensitive). Kod içerisinde tablo adları (`TEAMS`, `PLAYERS`) ile veritabanındaki adların birebir eşleşmesi kritik önem taşır.

---

## 4. API Mimarisi ve Endpoint'ler

Tüm endpoint'ler `/api/v1` prefix'i ile başlar.

### A. Takımlar (Teams) Modülü

* **Listeleme:** `GET /teams`
    * *Özellik:* `?conference=East` parametresi ile filtreleme yapar. Filtre yoksa tümünü getirir.
* **Detay (Complex Logic):** `GET /teams/<id>`
    * *Parametre:* `?season=REGULAR` veya `?season=PLAYOFF`
    * *İşleyiş:*
        1.  `TEAMS` tablosundan takım bilgisini çeker.
        2.  Seçilen sezona göre (`Regular` veya `Playoff` tablosu) takımın sıralamasını (`winRank`) çeker.
        3.  **Aggregation:** `PLAYERS` tablosunu performans tablosuyla `LEFT JOIN` yaparak birleştirir.
        4.  Oyuncuların o takımdaki istatistiklerini (`AVG(PTS)`, `AVG(AST)` vb.) hesaplar.
    * *Kritik Müdahale:* MySQL `ONLY_FULL_GROUP_BY` moduna uyumlu olması için `GROUP BY` tüm seçim sütunlarını içerir.

### B. Oyuncular (Players) Modülü

* **Listeleme:** `GET /players` (Limit 100)
* **Detay:** `GET /players/<id>`
    * *Parametreler:* `?season=PLAYOFF`, `?location=HOME/AWAY`
    * *Dinamik Yapı:* Kullanıcı isteğine göre sorgu dinamik olarak `PlayerRegularSeasonPerformance` veya `PlayerPlayoffsPerformance` tablosuna yönlendirilir.
* **Arama (Search):** `GET /players/search?q=LeBron`
    * *Logic:* SQL `LIKE %...%` operatörü ile isim bazlı arama yapar.
* **CRUD İşlemleri:**
    * `POST /players`: Yeni oyuncu ekler.
    * `PUT /players/<id>`: Oyuncu bilgilerini günceller.
    * `DELETE /players/<id>`: Oyuncuyu ve ilişkili tüm istatistiklerini (Cascade mantığıyla manuel) siler.

### C. İstatistikler (Stats & Leaders)

* **Liderler:** `GET /stats/leaders`
    * *Parametre:* `?category=PTS` (veya AST, REB)
    * *Logic:* Tüm oyuncular arasında ortalaması en yüksek 5 oyuncuyu getirir.
    * *Veri Temizliği:* Veritabanından gelen küsuratlı sayıları (`34.12345`) `ROUND()` fonksiyonu ile temizler.

---

## 5. Kritik Teknik Çözümler ve "Workarounds"

Proje geliştirilirken karşılaşılan engeller ve Antigravity'nin bilmesi gereken çözümler:

1.  **Decimal to Float Serialization Hatası:**
    * *Sorun:* MySQL `AVG()` fonksiyonu `Decimal` tipinde veri döndürür. Python `json.dumps` bu tipi tanımaz ve kod patlar.
    * *Çözüm:* Veriyi JSON'a çevirmeden önce bir döngü ile `float()` tipine cast ediyoruz.

2.  **Dinamik Tablo Seçimi:**
    * Kodlarımızda "Season Switch" özelliği vardır.
    * `if season == 'PLAYOFF': table = 'PlayerPlayoffsPerformance'` mantığıyla sorgular runtime'da değişir.

3.  **`BLK_X` (Blok) Sütunu Sorunu:**
    * *Mevcut Durum:* Veritabanındaki tablolarda `BLK_X` sütunu eksik olduğu veya veri yüklenmediği için, takım detay sorgusunda Blok verisi çekilirken "Unknown Column" hatası alınıyordu.
    * *Geçici Çözüm:* Kodun çökmemesi için SQL sorgusundan `BLK_X` çıkarıldı.
    * *Gelecek Adım:* Veritabanına `ALTER TABLE ADD COLUMN BLK_X` işlemi yapılmalı ve veri basılmalı. Sonrasında koda tekrar eklenebilir.

---

## 6. Antigravity İçin Aksiyon Planı (Next Steps)

Projeyi devraldığında sırasıyla şunları kontrol etmelisin:

1.  **Bağlantı Ayarları:** `get_db_connection()` fonksiyonundaki host, user ve password bilgilerini yeni ortama göre güncelle.
2.  **Tablo Kontrolü:** `TEAMS` ve `teams` (Büyük/Küçük harf) durumunu kontrol et.
3.  **Blok Verisi:** `BLK_X` sütunu veritabanına eklendiğinde, `get_team_detail` fonksiyonundaki yorum satırına alınan blok hesaplamasını geri aç.
4.  **Güvenlik:** SQL Injection koruması için tüm sorgularda `%s` parametresi (Parameterized Queries) kullanmaya devam et. Asla f-string içine doğrudan user input koyma (Tablo isimleri hariç, onlar bizden gidiyor).

**Özet:** Bu proje, modern bir backend'in sahip olması gereken dinamik filtreleme, arama ve detaylandırma özelliklerine sahiptir ancak "Old School" bir yöntemle (Raw SQL) yazılarak veritabanı hakimiyeti ön plana çıkarılmıştır.