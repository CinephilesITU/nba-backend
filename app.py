from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import random
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Frontend ile iletişimi açar

# ---------------------------------------------------------
# 1. VERİTABANI BAĞLANTISI
# ---------------------------------------------------------

# Railway veya Local ortam kontrolü
USE_CLOUD_DB = os.environ.get('USE_CLOUD_DB', 'false').lower() == 'true'

def get_db_connection():
    try:
        if USE_CLOUD_DB:
            # Railway MySQL Bağlantısı
            conn = mysql.connector.connect(
                host=os.environ.get('MYSQLHOST', 'maglev.proxy.rlwy.net'),
                port=int(os.environ.get('MYSQLPORT', 22162)),
                user=os.environ.get('MYSQLUSER', 'root'),
                password=os.environ.get('MYSQL_ROOT_PASSWORD', 'dyChflihNewcQAbTgjZoBiHPiLSoWsTt'),
                database=os.environ.get('MYSQL_DATABASE', 'nba_db')
            )
        else:
            # Local MySQL Bağlantısı
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

# Yardımcı fonksiyon: Decimal/None -> Float dönüşümü
def safe_float(val):
    try:
        return float(val) if val is not None else 0.0
    except:
        return 0.0

# Yardımcı fonksiyon: Pagination hesaplama
def paginate(page, per_page, total_items):
    total_pages = (total_items + per_page - 1) // per_page  # Yukarı yuvarlama
    return {
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

@app.route('/')
def home():
    return "NBA Backend Calisiyor (SQL Versiyon - vFinal)!"

# ---------------------------------------------------------
# HEALTH CHECK - Sunucu ve DB durumu
# ---------------------------------------------------------
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "unknown",
        "environment": "cloud" if USE_CLOUD_DB else "local"
    }
    
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            health["database"] = "connected"
            cursor.close()
            conn.close()
        else:
            health["database"] = "disconnected"
            health["status"] = "unhealthy"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    status_code = 200 if health["status"] == "healthy" else 503
    return jsonify(health), status_code

# ---------------------------------------------------------
# 2. OYUNCULAR (PLAYERS)
# ---------------------------------------------------------

# A. TÜM OYUNCULARI LİSTELE (Pagination + Filtreleme destekli)
@app.route('/api/v1/players', methods=['GET'])
def get_players():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Pagination parametreleri
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Maksimum 100
    offset = (page - 1) * per_page
    
    # Opsiyonel filtreler
    team_id = request.args.get('team_id')
    position = request.args.get('position')
    
    try:
        # Toplam kayıt sayısını al
        if team_id:
            cursor.execute("SELECT COUNT(*) as total FROM PLAYERS WHERE teamID = %s", (team_id,))
        elif position:
            cursor.execute("SELECT COUNT(*) as total FROM PLAYERS WHERE position LIKE %s", (f"%{position}%",))
        else:
            cursor.execute("SELECT COUNT(*) as total FROM PLAYERS")
        
        total_items = cursor.fetchone()['total']
        
        # Sayfalanmış veriyi al
        if team_id:
            sql = "SELECT * FROM PLAYERS WHERE teamID = %s LIMIT %s OFFSET %s"
            cursor.execute(sql, (team_id, per_page, offset))
        elif position:
            sql = "SELECT * FROM PLAYERS WHERE position LIKE %s LIMIT %s OFFSET %s"
            cursor.execute(sql, (f"%{position}%", per_page, offset))
        else:
            sql = "SELECT * FROM PLAYERS LIMIT %s OFFSET %s"
            cursor.execute(sql, (per_page, offset))
            
        players = cursor.fetchall()
        
        return jsonify({
            "status": "success", 
            "results": len(players), 
            "pagination": paginate(page, per_page, total_items),
            "data": {"players": players}
        })
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
                # Agregation (Toplama) - BLK_X olmadan
                sql_stats = f"""
                    SELECT 
                        SUM(GP_X) as GP_X, AVG(MIN_X) as MIN_X, AVG(PTS) as PTS, AVG(REB) as REB, 
                        AVG(AST) as AST, AVG(steal) as steal, AVG(TOV) as TOV,
                        AVG(FG_PCT) as FG_PCT, AVG(FG3_PCT) as FG3_PCT, AVG(FT_PCT) as FT_PCT,
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
            
            # Decimal -> Float dönüşümü
            if stats:
                for key in stats:
                    if key not in ['location', 'season_type', 'teamName']:
                        stats[key] = safe_float(stats[key])
            
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

# D. OYUNCU GÜNCELLE (UPDATE)
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
    if 'headshotUrl' in data:
        fields.append("headshotUrl = %s")
        values.append(data['headshotUrl'])
        
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

# A. TAKIMLARI LİSTELE (Pagination + Konferans Filtreli)
@app.route('/api/v1/teams', methods=['GET'])
def get_teams():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    # Pagination parametreleri
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    
    conf_param = request.args.get('conference')
    
    try:
        # Toplam sayı
        if conf_param:
            cursor.execute("SELECT COUNT(*) as total FROM TEAMS WHERE conference = %s", (conf_param,))
        else:
            cursor.execute("SELECT COUNT(*) as total FROM TEAMS")
        total_items = cursor.fetchone()['total']
        
        # Sayfalanmış veri
        if conf_param:
            cursor.execute("SELECT * FROM TEAMS WHERE conference = %s LIMIT %s OFFSET %s", (conf_param, per_page, offset))
        else:
            cursor.execute("SELECT * FROM TEAMS LIMIT %s OFFSET %s", (per_page, offset))
        
        teams = cursor.fetchall()
        return jsonify({
            "status": "success", 
            "results": len(teams), 
            "pagination": paginate(page, per_page, total_items),
            "data": {"teams": teams}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# B. TAKIM DETAYI VE KADROSU (FİNAL VERSİYON)
@app.route('/api/v1/teams/<int:id>', methods=['GET'])
def get_team_detail(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    # URL'den sezon parametresini al (Varsayılan: REGULAR)
    season_param = request.args.get('season', 'REGULAR')
    
    # Hangi tablolara bakacağımızı seçiyoruz
    if season_param == 'PLAYOFF':
        team_stats_table = "TeamPlayoffsPerformance"
        player_stats_table = "PlayerPlayoffsPerformance"
    else:
        team_stats_table = "TeamRegularSeasonPerformance"
        player_stats_table = "PlayerRegularSeasonPerformance"
    
    try:
        # 1. ADIM: Takım Temel Bilgisi
        cursor.execute("SELECT * FROM TEAMS WHERE teamID = %s", (id,))
        team = cursor.fetchone()
        
        if team:
            # 2. ADIM: Takım İstatistikleri
            sql_team_stats = f"SELECT * FROM {team_stats_table} WHERE teamID = %s"
            cursor.execute(sql_team_stats, (id,))
            team_stats = cursor.fetchone()
            
            team['stats'] = team_stats if team_stats else {}
            
            # 3. ADIM: Kadro (Roster) ve Gerçek Ortalamalar - BLK_X olmadan
            sql_roster = f"""
                SELECT 
                    p.playerID, 
                    p.playerName, 
                    p.position, 
                    p.headshotUrl, 
                    AVG(s.PTS) as avg_pts,
                    AVG(s.AST) as avg_ast,
                    AVG(s.REB) as avg_reb,
                    AVG(s.steal) as avg_stl,
                    AVG(s.efficiency) as avg_eff
                FROM PLAYERS p
                LEFT JOIN {player_stats_table} s ON p.playerID = s.playerID
                WHERE p.teamID = %s
                GROUP BY p.playerID, p.playerName, p.position, p.headshotUrl
            """
            cursor.execute(sql_roster, (id,))
            roster = cursor.fetchall()

            # Decimal -> Float Dönüşümü
            final_roster = []
            for player in roster:
                player['avg_pts'] = safe_float(player['avg_pts'])
                player['avg_ast'] = safe_float(player['avg_ast'])
                player['avg_reb'] = safe_float(player['avg_reb'])
                player['avg_stl'] = safe_float(player['avg_stl'])
                player['avg_eff'] = safe_float(player['avg_eff'])
                final_roster.append(player)
            
            team['roster'] = final_roster
            team['season_type'] = season_param 

            return jsonify({"status": "success", "data": {"team": team}})
        else:
            return jsonify({"status": "fail", "message": "Takım bulunamadı"}), 404
            
    except Exception as e:
        print(f"DEBUG HATASI (get_team_detail): {str(e)}")
        return jsonify({"error": f"Sunucu Hatası: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# C. TAKIM SIRALAMALARI (STANDINGS) - YENİ
@app.route('/api/v1/teams/standings', methods=['GET'])
def get_team_standings():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    conf_param = request.args.get('conference')  # East veya West
    season_param = request.args.get('season', 'REGULAR')
    
    # Sezona göre tablo seç
    stats_table = "TeamPlayoffsPerformance" if season_param == 'PLAYOFF' else "TeamRegularSeasonPerformance"
    
    try:
        if conf_param:
            sql = f"""
                SELECT t.teamID, t.teamName, t.teamAbbreviation, t.logoUrl, t.conference,
                       s.winRank, s.defRatingRank, s.defRebRank, s.stealRank, s.blockRank
                FROM TEAMS t
                LEFT JOIN {stats_table} s ON t.teamID = s.teamID
                WHERE t.conference = %s
                ORDER BY s.winRank ASC
            """
            cursor.execute(sql, (conf_param,))
        else:
            sql = f"""
                SELECT t.teamID, t.teamName, t.teamAbbreviation, t.logoUrl, t.conference,
                       s.winRank, s.defRatingRank, s.defRebRank, s.stealRank, s.blockRank
                FROM TEAMS t
                LEFT JOIN {stats_table} s ON t.teamID = s.teamID
                ORDER BY t.conference, s.winRank ASC
            """
            cursor.execute(sql)
            
        standings = cursor.fetchall()
        return jsonify({
            "status": "success", 
            "season": season_param,
            "results": len(standings), 
            "data": {"standings": standings}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# D. TAKIM ARENA BİLGİSİ - YENİ
@app.route('/api/v1/teams/<int:id>/arena', methods=['GET'])
def get_team_arena(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    try:
        # Takım bilgisi
        cursor.execute("SELECT teamID, teamName, teamAbbreviation, logoUrl FROM TEAMS WHERE teamID = %s", (id,))
        team = cursor.fetchone()
        
        if not team:
            return jsonify({"status": "fail", "message": "Takım bulunamadı"}), 404
        
        # Arena bilgisi (LIMIT 1 eklendi - birden fazla kayıt olabilir)
        sql = """
            SELECT arenaDetailID, city, state, arena, capacity, 
                   latitude, longitude, us_time_zone, division, elevation_m
            FROM TeamArenaDetails 
            WHERE teamID = %s
            LIMIT 1
        """
        cursor.execute(sql, (id,))
        arena = cursor.fetchone()
        
        if arena:
            # Decimal -> Float dönüşümü
            arena['latitude'] = safe_float(arena['latitude'])
            arena['longitude'] = safe_float(arena['longitude'])
        
        team['arena'] = arena if arena else {}
        return jsonify({"status": "success", "data": {"team": team}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# E. TAKIM MAÇ PROGRAMI (FIXTURES) - YENİ
@app.route('/api/v1/teams/<int:id>/fixtures', methods=['GET'])
def get_team_fixtures(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    limit = request.args.get('limit', 20, type=int)
    
    try:
        # Takım adını al
        cursor.execute("SELECT teamName FROM TEAMS WHERE teamID = %s", (id,))
        team = cursor.fetchone()
        
        if not team:
            return jsonify({"status": "fail", "message": "Takım bulunamadı"}), 404
        
        team_name = team['teamName']
        
        # Takımın maçlarını getir (home veya away olarak)
        sql = """
            SELECT f.matchID, f.matchNumber, f.roundNumber, f.matchDate, 
                   f.homeTeam, f.awayTeam, f.result,
                   a.arena, a.city
            FROM TeamFixtures f
            JOIN TeamArenaDetails a ON f.arenaDetailID = a.arenaDetailID
            WHERE f.homeTeam = %s OR f.awayTeam = %s
            ORDER BY f.matchDate DESC
            LIMIT %s
        """
        cursor.execute(sql, (team_name, team_name, limit))
        fixtures = cursor.fetchall()
        
        # datetime objelerini string'e çevir
        for fixture in fixtures:
            if fixture['matchDate']:
                fixture['matchDate'] = fixture['matchDate'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "status": "success",
            "team": team_name,
            "results": len(fixtures),
            "data": {"fixtures": fixtures}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 4. FIXTURES (MAÇLAR) - YENİ MODÜL
# ---------------------------------------------------------

# A. TÜM MAÇLARI LİSTELE (Pagination destekli)
@app.route('/api/v1/fixtures', methods=['GET'])
def get_all_fixtures():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    # Pagination parametreleri
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    
    round_num = request.args.get('round')
    team = request.args.get('team')
    
    try:
        # Filtre koşulları
        conditions = []
        params = []
        
        if round_num:
            conditions.append("f.roundNumber = %s")
            params.append(round_num)
        
        if team:
            conditions.append("(f.homeTeam LIKE %s OR f.awayTeam LIKE %s)")
            params.extend([f"%{team}%", f"%{team}%"])
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Toplam sayı
        count_sql = f"SELECT COUNT(*) as total FROM TeamFixtures f {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total_items = cursor.fetchone()['total']
        
        # Sayfalanmış veri
        base_sql = f"""
            SELECT f.matchID, f.matchNumber, f.roundNumber, f.matchDate, 
                   f.homeTeam, f.awayTeam, f.result,
                   a.arena, a.city, a.teamID
            FROM TeamFixtures f
            JOIN TeamArenaDetails a ON f.arenaDetailID = a.arenaDetailID
            {where_clause}
            ORDER BY f.matchDate DESC 
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        
        cursor.execute(base_sql, tuple(params))
        fixtures = cursor.fetchall()
        
        # datetime objelerini string'e çevir
        for fixture in fixtures:
            if fixture['matchDate']:
                fixture['matchDate'] = fixture['matchDate'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "status": "success",
            "results": len(fixtures),
            "pagination": paginate(page, per_page, total_items),
            "data": {"fixtures": fixtures}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# B. TEK MAÇ DETAYI
@app.route('/api/v1/fixtures/<int:id>', methods=['GET'])
def get_fixture_detail(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql = """
            SELECT f.matchID, f.matchNumber, f.roundNumber, f.matchDate, 
                   f.homeTeam, f.awayTeam, f.result,
                   a.arena, a.city, a.state, a.capacity, a.teamID
            FROM TeamFixtures f
            JOIN TeamArenaDetails a ON f.arenaDetailID = a.arenaDetailID
            WHERE f.matchID = %s
        """
        cursor.execute(sql, (id,))
        fixture = cursor.fetchone()
        
        if fixture:
            if fixture['matchDate']:
                fixture['matchDate'] = fixture['matchDate'].strftime('%Y-%m-%d %H:%M:%S')
            return jsonify({"status": "success", "data": {"fixture": fixture}})
        else:
            return jsonify({"status": "fail", "message": "Maç bulunamadı"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 5. ARENAS (ARENALAR) - YENİ MODÜL
# ---------------------------------------------------------

# A. TÜM ARENALARI LİSTELE
@app.route('/api/v1/arenas', methods=['GET'])
def get_all_arenas():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql = """
            SELECT a.arenaDetailID, a.city, a.state, a.arena, a.capacity,
                   a.latitude, a.longitude, a.us_time_zone, a.division, a.elevation_m,
                   t.teamID, t.teamName, t.teamAbbreviation, t.logoUrl
            FROM TeamArenaDetails a
            JOIN TEAMS t ON a.teamID = t.teamID
            ORDER BY t.teamName
        """
        cursor.execute(sql)
        arenas = cursor.fetchall()
        
        # Decimal -> Float dönüşümü
        for arena in arenas:
            arena['latitude'] = safe_float(arena['latitude'])
            arena['longitude'] = safe_float(arena['longitude'])
        
        return jsonify({
            "status": "success",
            "results": len(arenas),
            "data": {"arenas": arenas}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# 6. İSTATİSTİK VE ANALİZ (STATS)
# ---------------------------------------------------------

# A. LİDERLER (Top Performers)
@app.route('/api/v1/stats/leaders', methods=['GET'])
def get_leaders():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    category = request.args.get('category', 'PTS')
    season = request.args.get('season', 'REGULAR')
    limit = request.args.get('limit', 5, type=int)
    
    # Geçerli sütunlar (BLK_X yok)
    valid_columns = ['PTS', 'AST', 'REB', 'efficiency', 'steal', 'TOV', 'FG_PCT', 'FG3_PCT', 'FT_PCT']
    if category not in valid_columns: 
        return jsonify({"error": f"Geçersiz kategori. Geçerli değerler: {', '.join(valid_columns)}"}), 400

    table_name = "PlayerRegularSeasonPerformance" if season == 'REGULAR' else "PlayerPlayoffsPerformance"
    
    sql = f"""
        SELECT 
            p.playerID,
            p.playerName, 
            p.headshotUrl,
            p.position,
            t.teamName,
            t.teamAbbreviation,
            ROUND(AVG(s.{category}), 1) as value,
            ROUND(AVG(s.PTS), 1) as avg_pts,
            ROUND(AVG(s.AST), 1) as avg_ast,
            ROUND(AVG(s.REB), 1) as avg_reb
        FROM {table_name} s
        JOIN PLAYERS p ON s.playerID = p.playerID
        JOIN TEAMS t ON p.teamID = t.teamID
        GROUP BY p.playerID, p.playerName, p.headshotUrl, p.position, t.teamName, t.teamAbbreviation
        ORDER BY value DESC 
        LIMIT %s
    """
    try:
        cursor.execute(sql, (limit,))
        results = cursor.fetchall()
        
        # Decimal -> Float dönüşümü
        for row in results:
            row['value'] = safe_float(row['value'])
            row['avg_pts'] = safe_float(row['avg_pts'])
            row['avg_ast'] = safe_float(row['avg_ast'])
            row['avg_reb'] = safe_float(row['avg_reb'])

        return jsonify({
            "status": "success", 
            "category": category,
            "season": season,
            "data": results
        })
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
        t.teamName, t.conference, COUNT(p.playerID) as StarPlayerCount, 
        ROUND(AVG(stats.efficiency), 2) as AvgTeamEfficiency
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
        
        # Decimal -> Float dönüşümü
        for row in results:
            row['AvgTeamEfficiency'] = safe_float(row['AvgTeamEfficiency'])
        
        return jsonify({"status": "success", "results": len(results), "data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# C. TAKIM KARŞILAŞTIRMA - YENİ
@app.route('/api/v1/stats/team-comparison', methods=['GET'])
def get_team_comparison():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    team1_id = request.args.get('team1', type=int)
    team2_id = request.args.get('team2', type=int)
    season = request.args.get('season', 'REGULAR')
    
    if not team1_id or not team2_id:
        return jsonify({"error": "team1 ve team2 parametreleri zorunlu"}), 400
    
    stats_table = "TeamPlayoffsPerformance" if season == 'PLAYOFF' else "TeamRegularSeasonPerformance"
    player_stats_table = "PlayerPlayoffsPerformance" if season == 'PLAYOFF' else "PlayerRegularSeasonPerformance"
    
    try:
        comparison = {}
        
        for team_id in [team1_id, team2_id]:
            # Takım bilgisi
            cursor.execute("SELECT * FROM TEAMS WHERE teamID = %s", (team_id,))
            team = cursor.fetchone()
            
            if not team:
                return jsonify({"error": f"Takım bulunamadı: {team_id}"}), 404
            
            # Takım sıralaması
            cursor.execute(f"SELECT * FROM {stats_table} WHERE teamID = %s", (team_id,))
            team_stats = cursor.fetchone()
            team['ranking'] = team_stats if team_stats else {}
            
            # Takım oyuncu ortalamaları
            sql_avg = f"""
                SELECT 
                    ROUND(AVG(PTS), 1) as team_avg_pts,
                    ROUND(AVG(AST), 1) as team_avg_ast,
                    ROUND(AVG(REB), 1) as team_avg_reb,
                    ROUND(AVG(efficiency), 1) as team_avg_eff
                FROM {player_stats_table} s
                JOIN PLAYERS p ON s.playerID = p.playerID
                WHERE p.teamID = %s
            """
            cursor.execute(sql_avg, (team_id,))
            averages = cursor.fetchone()
            
            # Decimal -> Float
            for key in averages:
                averages[key] = safe_float(averages[key])
            
            team['averages'] = averages
            comparison[f"team{1 if team_id == team1_id else 2}"] = team
        
        return jsonify({
            "status": "success",
            "season": season,
            "data": comparison
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# =========================================================
# 7. ADMIN PANEL API'LERİ
# =========================================================

# ---------------------------------------------------------
# A. TAKIMLAR (TEAMS) - ADMIN CRUD
# ---------------------------------------------------------

# Yeni Takım Ekle
@app.route('/api/v1/admin/teams', methods=['POST'])
def admin_add_team():
    data = request.json
    required = ['teamID', 'teamName', 'teamAbbreviation', 'conference']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Eksik alan: {field}"}), 400
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    sql = """INSERT INTO TEAMS (teamID, teamName, teamAbbreviation, logoUrl, conference) 
             VALUES (%s, %s, %s, %s, %s)"""
    val = (data['teamID'], data['teamName'], data['teamAbbreviation'], 
           data.get('logoUrl', ''), data['conference'])
    
    try:
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success", "message": "Takım eklendi", "teamID": data['teamID']}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Takım Güncelle
@app.route('/api/v1/admin/teams/<int:id>', methods=['PUT'])
def admin_update_team(id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    fields = []
    values = []
    
    if 'teamName' in data:
        fields.append("teamName = %s")
        values.append(data['teamName'])
    if 'teamAbbreviation' in data:
        fields.append("teamAbbreviation = %s")
        values.append(data['teamAbbreviation'])
    if 'logoUrl' in data:
        fields.append("logoUrl = %s")
        values.append(data['logoUrl'])
    if 'conference' in data:
        fields.append("conference = %s")
        values.append(data['conference'])
        
    if not fields:
        return jsonify({"error": "Güncellenecek veri yok"}), 400
        
    values.append(id)
    sql = f"UPDATE TEAMS SET {', '.join(fields)} WHERE teamID = %s"
    
    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "fail", "message": "Takım bulunamadı"}), 404
        return jsonify({"status": "success", "message": "Takım güncellendi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Takım Sil
@app.route('/api/v1/admin/teams/<int:id>', methods=['DELETE'])
def admin_delete_team(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    try:
        # Önce ilişkili verileri sil (CASCADE mantığı)
        cursor.execute("DELETE FROM PlayerRegularSeasonPerformance WHERE teamID = %s", (id,))
        cursor.execute("DELETE FROM PlayerPlayoffsPerformance WHERE teamID = %s", (id,))
        cursor.execute("DELETE FROM PLAYERS WHERE teamID = %s", (id,))
        cursor.execute("DELETE FROM TeamRegularSeasonPerformance WHERE teamID = %s", (id,))
        cursor.execute("DELETE FROM TeamPlayoffsPerformance WHERE teamID = %s", (id,))
        
        # Arena ve Fixtures için
        cursor.execute("SELECT arenaDetailID FROM TeamArenaDetails WHERE teamID = %s", (id,))
        arena_ids = cursor.fetchall()
        for arena in arena_ids:
            cursor.execute("DELETE FROM TeamFixtures WHERE arenaDetailID = %s", (arena[0],))
        cursor.execute("DELETE FROM TeamArenaDetails WHERE teamID = %s", (id,))
        
        # Son olarak takımı sil
        cursor.execute("DELETE FROM TEAMS WHERE teamID = %s", (id,))
        conn.commit()
        return jsonify({"status": "success", "message": f"Takım (ID: {id}) ve ilişkili tüm veriler silindi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# B. MAÇLAR (FIXTURES) - ADMIN CRUD
# ---------------------------------------------------------

# Yeni Maç Ekle
@app.route('/api/v1/admin/fixtures', methods=['POST'])
def admin_add_fixture():
    data = request.json
    required = ['arenaDetailID', 'homeTeam', 'awayTeam', 'matchDate']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Eksik alan: {field}"}), 400
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    sql = """INSERT INTO TeamFixtures (arenaDetailID, matchNumber, roundNumber, matchDate, homeTeam, awayTeam, result) 
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    val = (data['arenaDetailID'], data.get('matchNumber', 0), data.get('roundNumber', 0),
           data['matchDate'], data['homeTeam'], data['awayTeam'], data.get('result', ''))
    
    try:
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success", "message": "Maç eklendi", "matchID": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Maç Güncelle
@app.route('/api/v1/admin/fixtures/<int:id>', methods=['PUT'])
def admin_update_fixture(id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    fields = []
    values = []
    
    updatable = ['arenaDetailID', 'matchNumber', 'roundNumber', 'matchDate', 'homeTeam', 'awayTeam', 'result']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = %s")
            values.append(data[field])
        
    if not fields:
        return jsonify({"error": "Güncellenecek veri yok"}), 400
        
    values.append(id)
    sql = f"UPDATE TeamFixtures SET {', '.join(fields)} WHERE matchID = %s"
    
    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "fail", "message": "Maç bulunamadı"}), 404
        return jsonify({"status": "success", "message": "Maç güncellendi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Maç Sil
@app.route('/api/v1/admin/fixtures/<int:id>', methods=['DELETE'])
def admin_delete_fixture(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM TeamFixtures WHERE matchID = %s", (id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "fail", "message": "Maç bulunamadı"}), 404
        return jsonify({"status": "success", "message": f"Maç (ID: {id}) silindi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# C. ARENALAR (ARENAS) - ADMIN CRUD
# ---------------------------------------------------------

# Yeni Arena Ekle
@app.route('/api/v1/admin/arenas', methods=['POST'])
def admin_add_arena():
    data = request.json
    if 'teamID' not in data:
        return jsonify({"error": "Eksik alan: teamID"}), 400
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    sql = """INSERT INTO TeamArenaDetails 
             (teamID, city, state, arena, capacity, latitude, longitude, us_time_zone, division, elevation_m) 
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    val = (data['teamID'], data.get('city', ''), data.get('state', ''), data.get('arena', ''),
           data.get('capacity', 0), data.get('latitude', 0), data.get('longitude', 0),
           data.get('us_time_zone', ''), data.get('division', ''), data.get('elevation_m', 0))
    
    try:
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success", "message": "Arena eklendi", "arenaDetailID": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Arena Güncelle
@app.route('/api/v1/admin/arenas/<int:id>', methods=['PUT'])
def admin_update_arena(id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    fields = []
    values = []
    
    updatable = ['teamID', 'city', 'state', 'arena', 'capacity', 'latitude', 'longitude', 
                 'us_time_zone', 'division', 'elevation_m']
    for field in updatable:
        if field in data:
            fields.append(f"{field} = %s")
            values.append(data[field])
        
    if not fields:
        return jsonify({"error": "Güncellenecek veri yok"}), 400
        
    values.append(id)
    sql = f"UPDATE TeamArenaDetails SET {', '.join(fields)} WHERE arenaDetailID = %s"
    
    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"status": "fail", "message": "Arena bulunamadı"}), 404
        return jsonify({"status": "success", "message": "Arena güncellendi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Arena Sil
@app.route('/api/v1/admin/arenas/<int:id>', methods=['DELETE'])
def admin_delete_arena(id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    try:
        # Önce ilişkili maçları sil
        cursor.execute("DELETE FROM TeamFixtures WHERE arenaDetailID = %s", (id,))
        cursor.execute("DELETE FROM TeamArenaDetails WHERE arenaDetailID = %s", (id,))
        conn.commit()
        return jsonify({"status": "success", "message": f"Arena (ID: {id}) ve ilişkili maçlar silindi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# D. OYUNCU İSTATİSTİKLERİ - ADMIN CRUD
# ---------------------------------------------------------

# Oyuncu İstatistiği Ekle/Güncelle
@app.route('/api/v1/admin/players/<int:player_id>/stats', methods=['POST'])
def admin_add_player_stats(player_id):
    data = request.json
    
    if 'teamID' not in data or 'location' not in data:
        return jsonify({"error": "Eksik alanlar: teamID ve location zorunlu"}), 400
    
    season = data.get('season', 'REGULAR')
    table_name = "PlayerPlayoffsPerformance" if season == 'PLAYOFF' else "PlayerRegularSeasonPerformance"
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    # Takım adını al
    cursor.execute("SELECT teamName FROM TEAMS WHERE teamID = %s", (data['teamID'],))
    team = cursor.fetchone()
    team_name = team[0] if team else ''
    
    sql = f"""INSERT INTO {table_name} 
              (playerID, teamID, teamName, location, GP_X, MIN_X, FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT, 
               FTM, FTA, FT_PCT, offensiveREB, defensiveREB, REB, AST, TOV, steal, PF, PTS, PLUS_MINUS, efficiency)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE
              GP_X = VALUES(GP_X), MIN_X = VALUES(MIN_X), FGM = VALUES(FGM), FGA = VALUES(FGA),
              FG_PCT = VALUES(FG_PCT), FG3M = VALUES(FG3M), FG3A = VALUES(FG3A), FG3_PCT = VALUES(FG3_PCT),
              FTM = VALUES(FTM), FTA = VALUES(FTA), FT_PCT = VALUES(FT_PCT), offensiveREB = VALUES(offensiveREB),
              defensiveREB = VALUES(defensiveREB), REB = VALUES(REB), AST = VALUES(AST), TOV = VALUES(TOV),
              steal = VALUES(steal), PF = VALUES(PF), PTS = VALUES(PTS), PLUS_MINUS = VALUES(PLUS_MINUS),
              efficiency = VALUES(efficiency)"""
    
    val = (player_id, data['teamID'], team_name, data['location'],
           data.get('GP_X', 0), data.get('MIN_X', 0), data.get('FGM', 0), data.get('FGA', 0),
           data.get('FG_PCT', 0), data.get('FG3M', 0), data.get('FG3A', 0), data.get('FG3_PCT', 0),
           data.get('FTM', 0), data.get('FTA', 0), data.get('FT_PCT', 0), data.get('offensiveREB', 0),
           data.get('defensiveREB', 0), data.get('REB', 0), data.get('AST', 0), data.get('TOV', 0),
           data.get('steal', 0), data.get('PF', 0), data.get('PTS', 0), data.get('PLUS_MINUS', 0),
           data.get('efficiency', 0))
    
    try:
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success", "message": f"Oyuncu istatistiği kaydedildi ({season})"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Oyuncu İstatistiği Sil
@app.route('/api/v1/admin/players/<int:player_id>/stats', methods=['DELETE'])
def admin_delete_player_stats(player_id):
    season = request.args.get('season', 'REGULAR')
    location = request.args.get('location')  # Opsiyonel
    
    table_name = "PlayerPlayoffsPerformance" if season == 'PLAYOFF' else "PlayerRegularSeasonPerformance"
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    try:
        if location:
            cursor.execute(f"DELETE FROM {table_name} WHERE playerID = %s AND location = %s", (player_id, location))
        else:
            cursor.execute(f"DELETE FROM {table_name} WHERE playerID = %s", (player_id,))
        
        conn.commit()
        return jsonify({"status": "success", "message": f"Oyuncu (ID: {player_id}) istatistikleri silindi ({season})"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# E. TAKIM İSTATİSTİKLERİ - ADMIN CRUD
# ---------------------------------------------------------

# Takım Sıralaması Ekle/Güncelle
@app.route('/api/v1/admin/teams/<int:team_id>/ranking', methods=['POST'])
def admin_add_team_ranking(team_id):
    data = request.json
    
    season = data.get('season', 'REGULAR')
    table_name = "TeamPlayoffsPerformance" if season == 'PLAYOFF' else "TeamRegularSeasonPerformance"
    
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor()
    
    sql = f"""INSERT INTO {table_name} (teamID, winRank, defRatingRank, defRebRank, stealRank, blockRank)
              VALUES (%s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE
              winRank = VALUES(winRank), defRatingRank = VALUES(defRatingRank),
              defRebRank = VALUES(defRebRank), stealRank = VALUES(stealRank), blockRank = VALUES(blockRank)"""
    
    val = (team_id, data.get('winRank', 0), data.get('defRatingRank', 0),
           data.get('defRebRank', 0), data.get('stealRank', 0), data.get('blockRank', 0))
    
    try:
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success", "message": f"Takım sıralaması kaydedildi ({season})"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# F. ADMIN DASHBOARD - Özet Bilgiler
# ---------------------------------------------------------

@app.route('/api/v1/admin/dashboard', methods=['GET'])
def admin_dashboard():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Baglantisi Yok"}), 500
    cursor = conn.cursor(dictionary=True)
    
    try:
        stats = {}
        
        cursor.execute("SELECT COUNT(*) as count FROM TEAMS")
        stats['total_teams'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM PLAYERS")
        stats['total_players'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM TeamFixtures")
        stats['total_fixtures'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM TeamArenaDetails")
        stats['total_arenas'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM PlayerRegularSeasonPerformance")
        stats['total_regular_stats'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM PlayerPlayoffsPerformance")
        stats['total_playoff_stats'] = cursor.fetchone()['count']
        
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)

