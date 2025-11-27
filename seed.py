# seed_raw.py (YENİ VERİ YÜKLEYİCİ - ORM YOK)
import mysql.connector
import pandas as pd
import math

# Veritabanı Ayarları
db_config = {
    'host': "localhost",
    'user': "root",
    'password': "baris0624",
    'database': "nba_db"
}

def clean_nan(value):
    """Pandas'tan gelen NaN değerlerini None (SQL NULL) yapar"""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value

def load_data():
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("Veritabanına bağlanıldı...")

        # 1. CSV'yi Oku (Dosya yolunu kendine göre düzelt)
        df = pd.read_csv('final_data.csv') 
        # Sadece genel (OVERALL) verileri alalım, şimdilik basit olsun
        df = df[df['LOCATION'] == 'OVERALL'] 

        # Kümeler (Tekrarı önlemek için)
        added_teams = set()
        added_players = set()

        for index, row in df.iterrows():
            # --- TAKIM EKLEME ---
            t_id = int(row['TEAM_ID'])
            if t_id not in added_teams:
                sql_team = """INSERT IGNORE INTO TEAMS 
                              (teamID, teamName, teamAbbreviation, logoUrl, conference) 
                              VALUES (%s, %s, %s, %s, %s)"""
                val_team = (
                    t_id, 
                    row.get('TEAM_NAME_y', row['TEAM_NAME_x']), 
                    row['TEAM_ABBREVIATION'], 
                    row.get('Logo_URL', ''),
                    row.get('Conference', 'East') # CSV'de yoksa default East
                )
                cursor.execute(sql_team, val_team)
                added_teams.add(t_id)

            # --- OYUNCU EKLEME ---
            p_id = int(row['PLAYER_ID'])
            if p_id not in added_players:
                sql_player = """INSERT IGNORE INTO PLAYERS 
                                (playerID, playerName, teamID, position, headshotUrl) 
                                VALUES (%s, %s, %s, %s, %s)"""
                val_player = (
                    p_id,
                    row['PLAYER_NAME'],
                    t_id,
                    row.get('POSITION', 'Unknown'),
                    row.get('HEADSHOT_URL', '')
                )
                cursor.execute(sql_player, val_player)
                added_players.add(p_id)

            # --- İSTATİSTİK EKLEME (PlayerRegularSeasonPerformance) ---
            # Not: app.py'de kullanılan tablo adı bu. 
            sql_stats = """INSERT INTO PlayerRegularSeasonPerformance 
                           (playerID, teamID, teamName, location, GP_X, MIN_X, PTS, efficiency) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            # Burada CSV sütun adlarını kontrol etmelisin
            val_stats = (
                p_id,
                t_id,
                row.get('TEAM_NAME_y', ''),
                'HOME', # CSV'den location çekmek lazım, şimdilik dummy
                clean_nan(row.get('GP_y', 0)),
                clean_nan(row.get('MIN_x', 0)),
                clean_nan(row.get('PTS', 0)),
                clean_nan(row.get('Efficiency', 0))
            )
            # Not: Gerçek projede tüm 20 sütunu buraya yazman lazım.
            # Şimdilik app.py çalışsın diye temel sütunları ekledim.
            try:
                cursor.execute(sql_stats, val_stats)
            except mysql.connector.Error as err:
                print(f"Hata (Stats): {err}")

        conn.commit()
        print(f"BAŞARILI: {len(added_teams)} Takım ve {len(added_players)} Oyuncu yüklendi.")

    except mysql.connector.Error as err:
        print(f"HATA: {err}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    load_data()