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
# 3. READ: TEK OYUNCU DETAYI (GET)
# ---------------------------------------------------------
@app.route('/api/v1/players/<int:id>', methods=['GET'])
def get_player_by_id(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Oyuncuyu bul
    sql_player = "SELECT * FROM PLAYERS WHERE playerID = %s"
    
    try:
        cursor.execute(sql_player, (id,))
        player = cursor.fetchone()
        
        if player:
            # İstatistiklerini çekelim (PlayerRegularSeasonPerformance tablosundan)
            sql_stats = "SELECT * FROM PlayerRegularSeasonPerformance WHERE playerID = %s LIMIT 1"
            cursor.execute(sql_stats, (id,))
            stats = cursor.fetchone()
            
            # Oyuncu verisine istatistikleri de ekle
            player['stats'] = stats
            
            return jsonify({"status": "success", "data": {"player": player}})
        else:
            return jsonify({"status": "fail", "message": "Oyuncu bulunamadı"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

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

if __name__ == '__main__':
    # Node.js backend ile ayni portta (5001) calistiriyoruz
    app.run(debug=True,host:"0.0.0.0",port=5001)
