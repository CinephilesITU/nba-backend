import pandas as pd
from app import app, db
from models import Team, Player, PlayerRegularSeason, PlayerPlayoffs

def load_data():
    # 1. CSV dosyasını oku
    filename = 'final_data.csv'
    try:
        df = pd.read_csv(filename)
        # Sadece GENEL (OVERALL) istatistikleri alıyoruz
        df = df[df['LOCATION'] == 'OVERALL']
        print(f"CSV Yüklendi ve Filtrelendi: {len(df)} satır.")
    except FileNotFoundError:
        print(f"HATA: {filename} dosyası bulunamadı!")
        return

    with app.app_context():
        # Veritabanını temizle ve yeniden oluştur
        db.drop_all()
        db.create_all()
        print("Veritabanı tabloları sıfırlandı ve yeniden oluşturuldu.")

        # Kümeler (Sets) ile neyi eklediğimizi takip ediyoruz
        added_teams = set()
        added_players = set()
        added_reg_stats = set() # Regular Season istatistiği eklenen oyuncular
        added_playoff_stats = set() # Playoff istatistiği eklenen oyuncular

        for index, row in df.iterrows():
            
            # --- A. TAKIM EKLEME ---
            t_id = row['TEAM_ID']
            if t_id not in added_teams:
                # TEAM_NAME_x hatalı olabildiği için y sütununu kullanıyoruz
                team_name_correct = row['TEAM_NAME_y'] 
                
                new_team = Team(
                    teamID=t_id,
                    teamName=team_name_correct, 
                    teamAbbreviate=row['TEAM_ABBREVIATION'],
                    conference=row['Conference'],
                    logoUrl=row.get('Logo_URL', '')
                )
                db.session.add(new_team)
                added_teams.add(t_id)

            # --- B. OYUNCU EKLEME ---
            p_id = row['PLAYER_ID']
            if p_id not in added_players:
                new_player = Player(
                    playerID=p_id,
                    teamID=t_id,
                    playerName=row['PLAYER_NAME'],
                    position=row['POSITION'],
                    headshotUrl=row['HEADSHOT_URL']
                )
                db.session.add(new_player)
                added_players.add(p_id)

            # --- C. İSTATİSTİK EKLEME ---
            stats_data = {
                'playerID': p_id,
                'teamID': t_id,
                'GP_X': row.get('GP_y', 0),
                'MIN_X': row.get('MIN_x', 0),
                'PTS': row.get('PTS', 0),
                'REB': row.get('REB', 0),
                'AST': row.get('AST', 0),
                'STL': row.get('STL_x', 0),
                'BLK': row.get('BLK_x', 0),
                'efficiency': row.get('Efficiency', 0)
            }

            # Regular Season Kontrolü: Bu oyuncu daha önce eklendi mi?
            if row['Season Type'] == 'Regular Season':
                if p_id not in added_reg_stats:
                    new_stats = PlayerRegularSeason(**stats_data)
                    db.session.add(new_stats)
                    added_reg_stats.add(p_id) # Listeye tik atıyoruz
            
            # Playoff Kontrolü: Bu oyuncu daha önce eklendi mi?
            elif row['Season Type'] == 'Playoffs':
                 if p_id not in added_playoff_stats:
                    new_stats = PlayerPlayoffs(**stats_data)
                    db.session.add(new_stats)
                    added_playoff_stats.add(p_id) # Listeye tik atıyoruz

        # Değişiklikleri kaydet
        try:
            db.session.commit()
            print(f"🎉 BAŞARILI: Veritabanı doldu!")
            print(f"- {len(added_teams)} Takım")
            print(f"- {len(added_players)} Oyuncu")
            print(f"- {len(added_reg_stats)} Normal Sezon İstatistiği")
            print(f"- {len(added_playoff_stats)} Playoff İstatistiği")
        except Exception as e:
            db.session.rollback()
            print(f"❌ KAYIT HATASI: {e}")

if __name__ == '__main__':
    load_data()