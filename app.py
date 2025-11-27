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

# B. TEK OYUNCU DETAYI (HOME/AWAY/OVERALL/SEASON Destekli)
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
# 3. TAKIMLAR (TEAMS)
# ---------------------------------------------------------

# A. TAKIMLARI LİSTELE (Konferans Filtreli)
@app.route('/api/v1/teams', methods=['GET'])
def get_teams():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    conf_param = request.args.get('conference')
    
    try:
        if conf_param:
            cursor.execute("SELECT * FROM TEAMS WHERE conference = %s", (conf_param,))
        else:
            cursor.execute("SELECT * FROM TEAMS")
        teams = cursor.fetchall()
        return jsonify({"status": "success", "results": len(teams), "data": {"teams": teams}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# B. TAKIM DETAYI (BASİTLEŞTİRİLMİŞ GERÇEK VERİ - JOIN/AVG YOK)
@app.route('/api/v1/teams/<int:id>', methods=['GET'])
def get_team_detail(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. ADIM: Takım Temel Bilgisi
        print(f"DEBUG: Takım ID {id} sorgulanıyor...")
        cursor.execute("SELECT * FROM TEAMS WHERE teamID = %s", (id,))
        team = cursor.fetchone()
        
        if team:
            print(f"DEBUG: Takım bulundu -> {team.get('teamName')}")

            # 2. ADIM: Takım Sıralaması (Basit Sorgu)
            # Eğer bu tablo boşsa veya hata verirse try-except ile yakalarız
            try:
                cursor.execute("SELECT * FROM TeamRegularSeasonPerformance WHERE teamID = %s", (id,))
                team_stats = cursor.fetchone()
                team['stats'] = team_stats if team_stats else {}
            except Exception as e:
                print(f"DEBUG: İstatistik tablosu hatası: {e}")
                team['stats'] = {} # Hata olursa boş geç, tüm işlemi durdurma

            # 3. ADIM: Kadro (SADECE PLAYERS TABLOSU)
            # Burada istatistik tablosuna JOIN yapmıyoruz. Sadece isimleri çekiyoruz.
            # Böylece 'Decimal' hatası veya 'GROUP BY' hatası riskini sıfıra indiriyoruz.
            sql_roster = """
                SELECT playerID, playerName, position, headshotUrl 
                FROM PLAYERS 
                WHERE teamID = %s
            """
            cursor.execute(sql_roster, (id,))
            roster = cursor.fetchall()
            
            # Frontend'in beklediği ama bizim şu an çekmediğimiz veriler için 
            # dummy (boş) değerler ekleyelim ki arayüz bozulmasın.
            final_roster = []
            for player in roster:
                player['avg_pts'] = 0.0 # Şimdilik 0 gönderiyoruz
                player['avg_ast'] = 0.0
                player['avg_reb'] = 0.0
                final_roster.append(player)

            team['roster'] = final_roster
            team['season_type'] = 'REGULAR_SIMPLE'

            return jsonify({"status": "success", "data": {"team": team}})
        else:
            print("DEBUG: Takım ID veritabanında yok.")
            return jsonify({"status": "fail", "message": "Takım bulunamadı"}), 404
            
    except Exception as e:
        print(f"DEBUG GENEL HATA: {str(e)}")
        return jsonify({"error": f"Sunucu Hatası: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 4. İSTATİSTİK VE ANALİZ (STATS)
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
    app.run(debug=True,host="0.0.0.0",port=5001)
