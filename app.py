from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import random

app = Flask(__name__)
CORS(app) 

# ---------------------------------------------------------
# 1. VERİTABANI BAĞLANTISI
# ---------------------------------------------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",        
            password="",        # BURAYA KENDİ ŞİFRENİ YAZ
            database="nba_db" 
        )
        return conn
    except mysql.connector.Error as err:
        print(f"HATA: Veritabanına bağlanılamadı. Detay: {err}")
        return None

@app.route('/')
def home():
    return "NBA Backend Calisiyor (SQL Versiyon - vFinal GOLD)!"

# ---------------------------------------------------------
# 2. OYUNCULAR (PLAYERS)
# ---------------------------------------------------------

# A. TÜM OYUNCULARI LİSTELE
@app.route('/api/v1/players', methods=['GET'])
def get_players():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    
    cursor = conn.cursor(dictionary=True)
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

# B. TEK OYUNCU DETAYI (BLK_X HATASI ÇÖZÜLDÜ + YUVARLAMA)
@app.route('/api/v1/players/<int:id>', methods=['GET'])
def get_player_by_id(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    # Season/Location parametrelerini kullanıyoruz
    season_param = request.args.get('season', 'REGULAR')
    table_name = "PlayerPlayoffsPerformance" if season_param == 'PLAYOFF' else "PlayerRegularSeasonPerformance"
    
    try:
        cursor.execute("SELECT * FROM PLAYERS WHERE playerID = %s", (id,))
        player = cursor.fetchone()
        
        if player:
            # BLK_X HATASI ÇÖZÜMÜ: Sadece güvenli sütunları istiyoruz ve yuvarlıyoruz.
            sql_stats = f"""
                SELECT 
                    playerID, teamID, teamName, location, GP_X, 
                    ROUND(MIN_X, 1) as MIN_X, ROUND(PTS, 1) as PTS, ROUND(REB, 1) as REB, 
                    ROUND(AST, 1) as AST, ROUND(steal, 1) as steal, 
                    ROUND(efficiency, 1) as efficiency
                FROM {table_name} 
                WHERE playerID = %s LIMIT 1
            """
            cursor.execute(sql_stats, (id,))
            stats = cursor.fetchone()
            
            player['stats'] = stats
            return jsonify({"status": "success", "data": {"player": player}})
        else:
            return jsonify({"status": "fail", "message": "Oyuncu bulunamadı"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# C. YENİ OYUNCU EKLE (CREATE) - [ADMIN PAGE İÇİN]
@app.route('/api/v1/players', methods=['POST'])
def add_player():
    data = request.json
    if not data.get('playerName') or not data.get('teamID'):
        return jsonify({"error": "Eksik veri: playerName ve teamID zorunlu"}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    new_id = random.randint(1000000, 9999999)
    
    # 1. Oyuncu Bilgisi Ekleme
    sql_player = """INSERT INTO PLAYERS (playerID, playerName, teamID, position, headshotUrl) 
             VALUES (%s, %s, %s, %s, %s)"""
    val_player = (new_id, data['playerName'], data['teamID'], data.get('position', 'Unknown'), data.get('headshotUrl', ''))
    
    # 2. Oyuncuya Sıfır İstatistik Ekleme (Foreign Key Hatasını Önlemek ve Transaction Göstermek İçin)
    # Not: PlayerStats tablosunun PK'si farklı ise bu başarısız olabilir.
    sql_stats = """INSERT INTO PlayerRegularSeasonPerformance (playerID, teamID, teamName, location, GP_X) 
                   VALUES (%s, %s, 'Unknown', 'OVERALL', 0)"""
    val_stats = (new_id, data['teamID'])

    try:
        # İŞLEM BAŞLANGICI
        cursor.execute(sql_player, val_player) # 1. Adım: Oyuncuyu Ekle
        cursor.execute(sql_stats, val_stats)   # 2. Adım: İlk istatistiği Ekle (Hata olursa buraya kadar olan her şey geri alınır)
        
        conn.commit() # İKİ İŞLEM DE BAŞARILIYSA KAYDET
        return jsonify({"status": "success", "message": "Oyuncu ve temel istatistiği başarıyla eklendi!", "id": new_id}), 201
    except Exception as e:
        conn.rollback() # HATA OLURSA YAPILAN HER ŞEYİ İPTAL ET (Transaction)
        return jsonify({"error": f"Transaction Hatası: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# D. OYUNCU GÜNCELLE (UPDATE) - [ADMIN PAGE İÇİN]
@app.route('/api/v1/players/<int:id>', methods=['PUT'])
def update_player(id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    fields = []
    values = []
    
    if 'playerName' in data:
        fields.append("playerName = %s")
        values.append(data['playerName'])
    if 'teamID' in data:
        fields.append("teamID = %s")
        values.append(data['teamID'])
    if 'position' in data:
        fields.append("position = %s")
        values.append(data['position'])
        
    if not fields:
        return jsonify({"error": "Güncellenecek veri yok"}), 400
        
    values.append(id)
    sql = f"UPDATE PLAYERS SET {', '.join(fields)} WHERE playerID = %s"
    
    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        return jsonify({"status": "success", "message": "Oyuncu güncellendi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# E. OYUNCU SİL (DELETE) - [ADMIN PAGE İÇİN]
@app.route('/api/v1/players/<int:id>', methods=['DELETE'])
def delete_player(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM PlayerRegularSeasonPerformance WHERE playerID = %s", (id,))
        cursor.execute("DELETE FROM PlayerPlayoffsPerformance WHERE playerID = %s", (id,))
        cursor.execute("DELETE FROM PLAYERS WHERE playerID = %s", (id,))
        conn.commit()
        return jsonify({"status": "success", "message": f"Oyuncu (ID: {id}) silindi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# F. OYUNCU ARAMA (SEARCH)
@app.route('/api/v1/players/search', methods=['GET'])
def search_players():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    query = request.args.get('q', '')
    if len(query) < 2: return jsonify({"error": "En az 2 harf giriniz"}), 400
        
    sql = "SELECT * FROM PLAYERS WHERE playerName LIKE %s LIMIT 10"
    search_term = f"%{query}%"
    
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
# 3. TAKIMLAR (TEAMS)
# ---------------------------------------------------------

# A. TAKIMLARI LİSTELE
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

# B. TAKIM DETAYI VE KADROSU (YUVARLAMA + GERÇEK İSTATİSTİKLER)
@app.route('/api/v1/teams/<int:id>', methods=['GET'])
def get_team_detail(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    season_param = request.args.get('season', 'REGULAR')
    player_stats_table = "PlayerPlayoffsPerformance" if season_param == 'PLAYOFF' else "PlayerRegularSeasonPerformance"
    
    try:
        # 1. Takım Bilgisi
        cursor.execute("SELECT * FROM TEAMS WHERE teamID = %s", (id,))
        team = cursor.fetchone()
        
        if team:
            # 2. Takım Sıralaması (TeamStats)
            cursor.execute("SELECT * FROM TeamRegularSeasonPerformance WHERE teamID = %s", (id,))
            team_stats = cursor.fetchone()
            team['stats'] = team_stats
            
            # 3. KADRO (ROSTER) - ORTALAMA PUANLAR (YUVARLAMA VAR)
            sql_roster = f"""
                SELECT 
                    p.playerID, p.playerName, p.position, p.headshotUrl, 
                    ROUND(AVG(s.PTS), 1) as avg_pts,
                    ROUND(AVG(s.AST), 1) as avg_ast,
                    ROUND(AVG(s.REB), 1) as avg_reb
                FROM PLAYERS p
                LEFT JOIN {player_stats_table} s ON p.playerID = s.playerID
                WHERE p.teamID = %s
                GROUP BY p.playerID, p.playerName, p.position, p.headshotUrl
            """
            cursor.execute(sql_roster, (id,))
            roster = cursor.fetchall()
            
            # Decimal -> Float çevirimi
            for player in roster:
                for key in ['avg_pts', 'avg_ast', 'avg_reb']:
                    try:
                        player[key] = float(player[key]) if player[key] is not None else 0.0
                    except:
                        player[key] = 0.0
                
            team['roster'] = roster
            
            return jsonify({"status": "success", "data": {"team": team}})
        else:
            return jsonify({"status": "fail", "message": "Takım bulunamadı"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# C. YENİ TAKIM EKLE (CREATE) - [ADMIN PAGE İÇİN]
@app.route('/api/v1/teams', methods=['POST'])
def add_team():
    data = request.json
    if not data.get('teamName') or not data.get('teamID') or not data.get('conference'):
        return jsonify({"error": "Eksik veri: teamName, teamID ve conference zorunlu."}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    sql = """INSERT INTO TEAMS (teamID, teamName, teamAbbreviation, logoUrl, conference) 
             VALUES (%s, %s, %s, %s, %s)"""
    val = (data['teamID'], data['teamName'], data.get('teamAbbreviation', 'N/A'), data.get('logoUrl', ''), data['conference'])
    
    try:
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success", "message": "Takım başarıyla eklendi!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# D. TAKIM GÜNCELLE (UPDATE) - [ADMIN PAGE İÇİN]
@app.route('/api/v1/teams/<int:id>', methods=['PUT'])
def update_team(id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    fields = []
    values = []
    
    if 'teamName' in data: fields.append("teamName = %s"); values.append(data['teamName'])
    if 'conference' in data: fields.append("conference = %s"); values.append(data['conference'])
        
    if not fields: return jsonify({"error": "Güncellenecek veri yok"}), 400
        
    values.append(id)
    sql = f"UPDATE TEAMS SET {', '.join(fields)} WHERE teamID = %s"
    
    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        return jsonify({"status": "success", "message": "Takım güncellendi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# E. TAKIM SİL (DELETE) - [ADMIN PAGE İÇİN]
@app.route('/api/v1/teams/<int:id>', methods=['DELETE'])
def delete_team(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    try:
        # Önce bu takıma ait oyuncuları silmemiz gerekir (Foreign Key)
        # Bu, çok riskli ve uzun bir işlem olduğu için:
        # Ya CASCADE ayarını DB'de yaptık ya da sadece takımı siliyoruz (DB hatası verecek)
        cursor.execute("DELETE FROM TEAMS WHERE teamID = %s", (id,))
        
        conn.commit()
        return jsonify({"status": "success", "message": f"Takım (ID: {id}) silindi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 4. İSTATİSTİK VE ANALİZ (STATS)
# ---------------------------------------------------------

# A. LİDERLER (Top Performers)
@app.route('/api/v1/stats/leaders', methods=['GET'])
def get_leaders():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    category = request.args.get('category', 'PTS')
    valid_columns = ['PTS', 'AST', 'REB', 'efficiency', 'steal']
    if category not in valid_columns: return jsonify({"error": "Gecersiz kategori"}), 400

    table_name = "PlayerRegularSeasonPerformance"
    
    sql = f"""
        SELECT 
            p.playerName, p.headshotUrl, ROUND(AVG(s.{category}), 1) as value
        FROM {table_name} s
        JOIN PLAYERS p ON s.playerID = p.playerID
        GROUP BY p.playerID, p.playerName, p.headshotUrl
        ORDER BY value DESC LIMIT 5
    """
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        
        for r in results:
            if r['value'] is not None: r['value'] = float(r['value'])

        return jsonify({"status": "success", "category": category, "data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# B. COMPLEX QUERY
@app.route('/api/v1/stats/complex', methods=['GET'])
def get_complex_stats():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    sql = """
    SELECT 
        t.teamName, t.conference, COUNT(p.playerID) as StarPlayerCount, ROUND(AVG(stats.efficiency), 1) as AvgTeamEfficiency
    FROM TEAMS t
    JOIN PLAYERS p ON t.teamID = p.teamID
    JOIN PlayerRegularSeasonPerformance stats ON p.playerID = stats.playerID
    WHERE stats.efficiency > (SELECT AVG(efficiency) FROM PlayerRegularSeasonPerformance)
    GROUP BY t.teamName, t.conference
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
    app.run(debug=True, host="0.0.0.0", port=5001)
