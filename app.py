from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import random

app = Flask(__name__)
CORS(app) # Frontend ile iletişimi açar

# ---------------------------------------------------------
# 1. VERİTABANI BAĞLANTISI (Hardcoded / Sabit Şifreli)
# ---------------------------------------------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",        # Kullanıcı adı
            password="",        # Şifreniz varsa buraya yazın
            database="nba_db" 
        )
        return conn
    except mysql.connector.Error as err:
        print(f"HATA: Veritabanına bağlanılamadı. Detay: {err}")
        return None

@app.route('/')
def home():
    return "NBA Backend Calisiyor (SQL Versiyon - vFinal)!"

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

# B. TEK OYUNCU DETAYI (HOME/AWAY/OVERALL/SEASON Destekli)
@app.route('/api/v1/players/<int:id>', methods=['GET'])
def get_player_by_id(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    location_param = request.args.get('location', 'OVERALL') 
    season_param = request.args.get('season', 'REGULAR')
    
    table_name = "PlayerPlayoffsPerformance" if season_param == 'PLAYOFF' else "PlayerRegularSeasonPerformance"
    
    try:
        # 1. Oyuncu Bilgisi
        cursor.execute("SELECT * FROM PLAYERS WHERE playerID = %s", (id,))
        player = cursor.fetchone()
        
        if player:
            # 2. İstatistikler
            if location_param == 'OVERALL':
                # Agregation (Toplama)
                sql_stats = f"""
                    SELECT 
                        SUM(GP_X) as GP_X, AVG(MIN_X) as MIN_X, AVG(PTS) as PTS, AVG(REB) as REB, 
                        AVG(AST) as AST, AVG(steal) as steal, AVG(BLK_X) as BLK_X, 
                        AVG(efficiency) as efficiency, '{location_param}' as location, '{season_param}' as season_type
                    FROM {table_name} 
                    WHERE playerID = %s GROUP BY playerID
                """
                cursor.execute(sql_stats, (id,))
            else:
                # Direkt Sorgu
                sql_stats = f"SELECT * FROM {table_name} WHERE playerID = %s AND location = %s LIMIT 1"
                cursor.execute(sql_stats, (id, location_param))
            
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

# C. YENİ OYUNCU EKLE (CREATE)
@app.route('/api/v1/players', methods=['POST'])
def add_player():
    data = request.json
    if not data.get('playerName') or not data.get('teamID'):
        return jsonify({"error": "Eksik veri: playerName ve teamID zorunlu"}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    new_id = random.randint(1000000, 9999999)
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

# D. OYUNCU GÜNCELLE (UPDATE) - SENDE EKSİKTİ, EKLENDİ
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

# E. OYUNCU SİL (DELETE)
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

# B. TAKIM DETAYI (SADECE TEAMS TABLOSU - DEBUG MODU)
@app.route('/api/v1/teams/<int:id>', methods=['GET'])
def get_team_detail(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Takım bilgisi
        cursor.execute("SELECT * FROM TEAMS WHERE teamID = %s", (id,))
        team = cursor.fetchone()

        if not team:
            return jsonify({"status": "fail", "message": "Takım bulunamadı"}), 404

        # 2. Playoff performansı
        cursor.execute("""
            SELECT *
            FROM TeamPlayoffPerformance
            WHERE teamID = %s
        """, (id,))
        playoff_stats = cursor.fetchone()

        team["playoff_stats"] = playoff_stats

        return jsonify({"status": "success", "data": {"team": team}})

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
    season = request.args.get('season', 'REGULAR')
    valid_columns = ['PTS', 'AST', 'REB', 'efficiency', 'STL', 'BLK_X']
    if category not in valid_columns: return jsonify({"error": "Gecersiz kategori"}), 400

    table_name = "PlayerRegularSeasonPerformance" if season == 'REGULAR' else "PlayerPlayoffsPerformance"
    
    sql = f"""
        SELECT p.playerName, p.headshotUrl, AVG(s.{category}) as value
        FROM {table_name} s
        JOIN PLAYERS p ON s.playerID = p.playerID
        GROUP BY p.playerID, p.playerName, p.headshotUrl
        ORDER BY value DESC LIMIT 5
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

# B. COMPLEX QUERY
@app.route('/api/v1/stats/complex', methods=['GET'])
def get_complex_stats():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    sql = """
    SELECT 
        t.teamName, t.conference, COUNT(p.playerID) as StarPlayerCount, AVG(stats.efficiency) as AvgTeamEfficiency
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
