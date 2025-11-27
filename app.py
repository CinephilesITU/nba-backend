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
            password="",
            database="nba_db"   
        )
        return conn
    except mysql.connector.Error as err:
        print(f"HATA: Veritabanına bağlanılamadı. Detay: {err}")
        return None

# YARDIMCI FONKSİYON: İSTATİSTİKLERİ YUVARLA
def round_stats(stats_dict):
    """Sözlük içindeki float değerleri virgülden sonra 1 basamağa yuvarlar."""
    if not stats_dict:
        return stats_dict
    
    # Yuvarlanacak alanlar
    target_keys = ['PTS', 'AST', 'REB', 'efficiency', 'steal', 'BLK', 'MIN_X', 'GP_X', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'avg_pts']
    
    for key, value in stats_dict.items():
        if key in target_keys and value is not None:
            try:
                # Sayıya çevir ve yuvarla
                stats_dict[key] = round(float(value), 1)
            except:
                pass # Sayı değilse dokunma
    return stats_dict

@app.route('/')
def home():
    return "NBA Backend Calisiyor (SQL Versiyon - Yuvarlama Fix)!"

# ---------------------------------------------------------
# 2. OYUNCULAR (PLAYERS)
# ---------------------------------------------------------

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

# TEK OYUNCU DETAYI (YUVARLAMA EKLENDİ)
@app.route('/api/v1/players/<int:id>', methods=['GET'])
def get_player_by_id(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Oyuncu Bilgisi (İsmi tam alıyoruz)
        cursor.execute("SELECT * FROM PLAYERS WHERE playerID = %s", (id,))
        player = cursor.fetchone()
        
        if player:
            # 2. İstatistikler
            sql_stats = """
                SELECT playerID, teamID, teamName, location, GP_X, MIN_X, 
                       PTS, REB, AST, steal, TOV, efficiency,
                       FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT, FTM, FTA, FT_PCT,
                       offensiveREB, defensiveREB, PLUS_MINUS
                FROM PlayerRegularSeasonPerformance 
                WHERE playerID = %s 
                LIMIT 1
            """
            cursor.execute(sql_stats, (id,))
            stats = cursor.fetchone()
            
            # BURADA YUVARLAMA YAPIYORUZ
            if stats:
                stats = round_stats(stats)

            player['stats'] = stats
            return jsonify({"status": "success", "data": {"player": player}})
        else:
            return jsonify({"status": "fail", "message": "Oyuncu bulunamadı"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# YENİ OYUNCU EKLE
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

# OYUNCU GÜNCELLE
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

# OYUNCU SİL
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

# OYUNCU ARAMA
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

# TAKIM DETAYI (KADRO PUANLARI YUVARLANDI)
@app.route('/api/v1/teams/<int:id>', methods=['GET'])
def get_team_detail(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Takım Bilgisi
        cursor.execute("SELECT * FROM TEAMS WHERE teamID = %s", (id,))
        team = cursor.fetchone()
        
        if team:
            # 2. Takım Sıralaması
            cursor.execute("SELECT * FROM TeamRegularSeasonPerformance WHERE teamID = %s", (id,))
            team_stats = cursor.fetchone()
            team['stats'] = team_stats
            
            # 3. KADRO (ROSTER) - ORTALAMA PUAN
            sql_roster = """
                SELECT p.playerID, p.playerName, p.position, p.headshotUrl, AVG(s.PTS) as avg_pts
                FROM PLAYERS p
                LEFT JOIN PlayerRegularSeasonPerformance s ON p.playerID = s.playerID
                WHERE p.teamID = %s
                GROUP BY p.playerID, p.playerName, p.position, p.headshotUrl
            """
            cursor.execute(sql_roster, (id,))
            roster = cursor.fetchall()
            
            # YUVARLAMA İŞLEMİ BURADA
            for player in roster:
                if player['avg_pts']:
                    player['avg_pts'] = round(float(player['avg_pts']), 1)
                else:
                    player['avg_pts'] = 0.0
                
            team['roster'] = roster
            
            return jsonify({"status": "success", "data": {"team": team}})
        else:
            return jsonify({"status": "fail", "message": "Takım bulunamadı"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 4. İSTATİSTİK VE ANALİZ (STATS)
# ---------------------------------------------------------

# LİDERLER (YUVARLAMA EKLENDİ)
@app.route('/api/v1/stats/leaders', methods=['GET'])
def get_leaders():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    category = request.args.get('category', 'PTS')
    valid_columns = ['PTS', 'AST', 'REB', 'efficiency', 'steal']
    
    if category not in valid_columns: 
        return jsonify({"error": "Gecersiz kategori. (PTS, AST, REB, efficiency, steal)"}), 400

    table_name = "PlayerRegularSeasonPerformance"
    
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
        
        # YUVARLAMA BURADA
        for r in results:
            if r['value']: r['value'] = round(float(r['value']), 1)

        return jsonify({"status": "success", "category": category, "data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# COMPLEX QUERY
@app.route('/api/v1/stats/complex', methods=['GET'])
def get_complex_stats():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    # YUVARLAMA SQL İÇİNDE YAPILIYOR (AVG(...))
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