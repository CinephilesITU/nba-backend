from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import random

app = Flask(__name__)
CORS(app) # Frontend ile iletişimi açar

# ---------------------------------------------------------
# 1. VERİTABANI BAĞLANTISI
# ---------------------------------------------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",        # Kullanıcı adı
            password="",        # Şifre 
            database="nba_db" 
        )
        return conn
    except mysql.connector.Error as err:
        print(f"HATA: Veritabanına bağlanılamadı. Detay: {err}")
        return None

@app.route('/')
def home():
    return "NBA Backend Calisiyor (SQL Versiyon)!"

# ---------------------------------------------------------
# 2. READ: TÜM OYUNCULARI LİSTELE (GET)
# ---------------------------------------------------------
@app.route('/api/v1/players', methods=['GET'])
def get_players():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Yeni şemaya göre tablo adı: PLAYERS (veya Players)
    sql = "SELECT * FROM PLAYERS LIMIT 100"
    
    try:
        cursor.execute(sql)
        players = cursor.fetchall()
        return jsonify({"status": "success", "results": len(players), "data": {"players": players}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 3. READ: TEK OYUNCU DETAYI (GET) - HOME/AWAY/OVERALL DESTEKLİ
# ---------------------------------------------------------
@app.route('/api/v1/players/<int:id>', methods=['GET'])
def get_player_by_id(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    # URL'den location parametresini al. (Örn: ?location=AWAY)
    # Eğer parametre gelmezse varsayılan olarak 'OVERALL' kabul et.
    location_param = request.args.get('location', 'OVERALL') 
    
    try:
        # 1. ADIM: Oyuncu Kimlik Bilgisini Çek (PLAYERS Tablosu)
        sql_player = "SELECT * FROM PLAYERS WHERE playerID = %s"
        cursor.execute(sql_player, (id,))
        player = cursor.fetchone()
        
        if player:
            # 2. ADIM: İstatistikleri Çek (Duruma Göre Sorgu Değişir)
            
            if location_param == 'OVERALL':
                # Eğer GENEL isteniyorsa: HOME ve AWAY verilerini SQL ile birleştirip ortalamasını alıyoruz.
                # Maç sayısını (GP) topluyoruz, diğerlerinin ortalamasını (AVG) alıyoruz.
                sql_stats = """
                    SELECT 
                        SUM(GP_X) as GP_X,
                        AVG(MIN_X) as MIN_X,
                        AVG(PTS) as PTS,
                        AVG(REB) as REB,
                        AVG(AST) as AST,
                        AVG(steal) as steal,
                        AVG(BLK_X) as BLK_X,
                        AVG(efficiency) as efficiency,
                        AVG(FG_PCT) as FG_PCT,
                        AVG(FG3_PCT) as FG3_PCT,
                        AVG(FT_PCT) as FT_PCT,
                        'OVERALL' as location
                    FROM PlayerRegularSeasonPerformance 
                    WHERE playerID = %s
                    GROUP BY playerID
                """
                cursor.execute(sql_stats, (id,))
            
            else:
                # Eğer spesifik bir yer (HOME veya AWAY) isteniyorsa: Direkt o satırı çek.
                sql_stats = """
                    SELECT * FROM PlayerRegularSeasonPerformance 
                    WHERE playerID = %s AND location = %s 
                    LIMIT 1
                """
                cursor.execute(sql_stats, (id, location_param))
            
            stats = cursor.fetchone()
            
            # İstatistik verisi varsa oyuncu objesine ekle
            if stats:
                player['stats'] = stats
            else:
                player['stats'] = None # Veri yoksa boş dön
                
            return jsonify({"status": "success", "data": {"player": player}})
            
        else:
            return jsonify({"status": "fail", "message": "Oyuncu bulunamadı"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ---------------------------------------------------------
# 4. READ: TÜM TAKIMLARI LİSTELE (GET)
# ---------------------------------------------------------
@app.route('/api/v1/teams', methods=['GET'])
def get_teams():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM TEAMS")
        teams = cursor.fetchall()
        return jsonify({"status": "success", "results": len(teams), "data": {"teams": teams}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 5. CREATE: YENİ OYUNCU EKLEME (POST)
# ---------------------------------------------------------
@app.route('/api/v1/players', methods=['POST'])
def add_player():
    data = request.json
    
    # Validasyon
    if not data.get('playerName') or not data.get('teamID'):
        return jsonify({"error": "Eksik veri: playerName ve teamID zorunlu"}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    # Yeni bir ID uret
    new_id = random.randint(1000000, 9999999)
    
    # Yeni şemaya uygun INSERT sorgusu
    sql = """INSERT INTO PLAYERS (playerID, playerName, teamID, position, headshotUrl) 
             VALUES (%s, %s, %s, %s, %s)"""
    
    val = (new_id, data['playerName'], data['teamID'], data.get('position', 'Unknown'), data.get('headshotUrl', ''))
    
    try:
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success", "message": "Oyuncu eklendi", "id": new_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 6. DELETE: OYUNCU SİLME (DELETE)
# ---------------------------------------------------------
@app.route('/api/v1/players/<int:id>', methods=['DELETE'])
def delete_player(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    try:
        # Önce bu oyuncunun istatistiklerini sil (Foreign Key hatası almamak için)
        cursor.execute("DELETE FROM PlayerRegularSeasonPerformance WHERE playerID = %s", (id,))
        cursor.execute("DELETE FROM PlayerPlayoffsPerformance WHERE playerID = %s", (id,))
        
        # Sonra oyuncuyu sil
        cursor.execute("DELETE FROM PLAYERS WHERE playerID = %s", (id,))
        
        conn.commit()
        return jsonify({"status": "success", "message": f"Oyuncu (ID: {id}) silindi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 7. COMPLEX QUERY (ZOR SORGULAR)
# (Join 4 Table, Nested Query, Group By)
# ---------------------------------------------------------
@app.route('/api/v1/stats/complex', methods=['GET'])
def get_complex_stats():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    # SENARYO: Lig ortalamasından daha verimli (Efficiency) oynayan oyuncuların
    # bulunduğu takımları listele ve bu takımlardaki "Yıldız Oyuncu" sayısını getir.
    # Konferansa göre grupla.
    
    sql = """
    SELECT 
        t.teamName,
        t.conference,
        COUNT(p.playerID) as StarPlayerCount,
        AVG(stats.efficiency) as AvgTeamEfficiency
    FROM TEAMS t
    JOIN PLAYERS p ON t.teamID = p.teamID
    JOIN PlayerRegularSeasonPerformance stats ON p.playerID = stats.playerID
    WHERE stats.efficiency > (
        SELECT AVG(efficiency) FROM PlayerRegularSeasonPerformance -- NESTED QUERY
    )
    GROUP BY t.teamName, t.conference -- GROUP BY
    ORDER BY StarPlayerCount DESC
    """
    
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        return jsonify({"status": "success", "results": len(results), "data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 8. SEARCH: İSİM İLE OYUNCU ARAMA (LIKE Query)
# ---------------------------------------------------------
@app.route('/api/v1/players/search', methods=['GET'])
def search_players():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    # URL'den aranan ismi al: /api/v1/players/search?q=LeBron
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify({"error": "En az 2 harf giriniz"}), 400
        
    # SQL LIKE Operatörü Kullanımı
    # % işareti "bununla başlayan/biten/içeren" demektir.
    sql = "SELECT * FROM PLAYERS WHERE playerName LIKE %s LIMIT 10"
    search_term = f"%{query}%" # Örn: %LeBron%
    
    try:
        cursor.execute(sql, (search_term,))
        results = cursor.fetchall()
        return jsonify({"status": "success", "results": len(results), "data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 9. TOP PERFORMERS: KATEGORİYE GÖRE SIRALAMA
# ---------------------------------------------------------
@app.route('/api/v1/stats/leaders', methods=['GET'])
def get_leaders():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    # Kategori: PTS, AST, REB, efficiency (Varsayılan: PTS)
    category = request.args.get('category', 'PTS')
    season = request.args.get('season', 'REGULAR')
    
    # Güvenlik Kontrolü (SQL Injection önlemek için)
    valid_columns = ['PTS', 'AST', 'REB', 'efficiency', 'STL', 'BLK_X']
    if category not in valid_columns:
        return jsonify({"error": "Gecersiz kategori"}), 400

    table_name = "PlayerRegularSeasonPerformance" if season == 'REGULAR' else "PlayerPlayoffsPerformance"

    # JOIN işlemi: İstatistik tablosundan sayıları, PLAYERS tablosundan isimleri çekiyoruz.
    # OVERALL ortalamasına göre sıralıyoruz.
    sql = f"""
        SELECT p.playerName, p.headshotUrl, AVG(s.{category}) as value
        FROM {table_name} s
        JOIN PLAYERS p ON s.playerID = p.playerID
        GROUP BY p.playerID, p.playerName, p.headshotUrl
        ORDER BY value DESC
        LIMIT 5
    """
    
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        return jsonify({"status": "success", "category": category, "data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # Node.js backend ile ayni portta (5001) calistiriyoruz
    app.run(debug=True,host="0.0.0.0",port=5001)
