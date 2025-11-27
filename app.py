from flask import Flask, jsonify, request
from flask_cors import CORS
from models import db, Team, Player, PlayerRegularSeason

app = Flask(__name__)
CORS(app) # Frontend ile iletişimi açar

# Veritabanı Ayarı
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nba_stats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# İlk çalıştırmada tabloları oluştur
with app.app_context():
    db.create_all()

# --- API ENDPOINTLERİ ---

@app.route('/')
def home():
    return "NBA Backend Calisiyor!"

# 1. Tüm Oyuncuları Listele (Frontend: Players Page)
@app.route('/api/players', methods=['GET'])
def get_players():
    # Sayfalama mantığı (Pagination) eklenebilir
    players = Player.query.limit(100).all() # Şimdilik ilk 50'yi getir
    return jsonify([p.to_dict() for p in players])

# 2. Tek Oyuncu Detayı (Frontend: Player Profile)
@app.route('/api/players/<int:id>', methods=['GET'])
def get_player_detail(id):
    player = Player.query.get_or_404(id)
    data = player.to_dict()
    
    # İstatistikleri "stats" objesi altında topluyoruz
    data['stats'] = {
        'regular': None,
        'playoffs': None
    }

    # 1. Normal Sezon Verisi Varsa Ekle
    if player.reg_season_stats:
        rs = player.reg_season_stats
        data['stats']['regular'] = {
            'GP': rs.GP_X,
            'MIN': rs.MIN_X,
            'PTS': rs.PTS,
            'AST': rs.AST,
            'REB': rs.REB,
            'STL': rs.steal,
            'BLK': rs.BLK,
            'EFF': rs.efficiency,
            'FG_PCT': rs.FG_PCT
        }

    # 2. Playoff Verisi Varsa Ekle (YENİ EKLENEN KISIM)
    if player.playoff_stats:
        ps = player.playoff_stats
        data['stats']['playoffs'] = {
            'GP': ps.GP_X,
            'MIN': ps.MIN_X,
            'PTS': ps.PTS,
            'AST': ps.AST,
            'REB': ps.REB,
            'STL': ps.steal,
            'BLK': ps.BLK,
            'EFF': ps.efficiency,
            'FG_PCT': ps.FG_PCT
        }

    return jsonify(data)

# 3. Tüm Takımları Listele (Frontend: Teams Page)
@app.route('/api/teams', methods=['GET'])
def get_teams():
    teams = Team.query.all()
    return jsonify([t.to_dict() for t in teams])

# ----------------------------------------------------------------
# CRUD İŞLEMLERİ (CREATE, UPDATE, DELETE)
# ----------------------------------------------------------------

# 4. YENİ OYUNCU EKLE (CREATE)
@app.route('/api/players', methods=['POST'])
def add_player():
    data = request.json # Frontend'den gelen veriyi al
    
    # Basit Validasyon: İsim ve Takım ID zorunlu olsun
    if not data.get('playerName') or not data.get('teamID'):
        return jsonify({'error': 'Eksik veri: playerName ve teamID zorunludur.'}), 400
    
    # Yeni ID oluştur (En son ID'nin bir fazlası veya rastgele)
    # Gerçek projede veritabanı bunu otomatik yapar (Auto Increment), 
    # ama biz manuel ID verdiğimiz için en büyük ID'yi bulup 1 ekleyelim.
    max_id = db.session.query(db.func.max(Player.playerID)).scalar() or 1000000
    new_id = int(max_id) + 1
    
    try:
        new_player = Player(
            playerID=new_id,
            teamID=data['teamID'],
            playerName=data['playerName'],
            position=data.get('position', 'Unknown'), # Verilmezse varsayılan
            headshotUrl=data.get('headshotUrl', '')
        )
        db.session.add(new_player)
        db.session.commit()
        return jsonify({'message': 'Oyuncu başarıyla eklendi!', 'player': new_player.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 5. OYUNCU GÜNCELLE (UPDATE)
@app.route('/api/players/<int:id>', methods=['PUT'])
def update_player(id):
    player = Player.query.get_or_404(id)
    data = request.json

    # Gelen veriye göre alanları güncelle
    if 'playerName' in data:
        player.playerName = data['playerName']
    if 'teamID' in data:
        player.teamID = data['teamID']
    if 'position' in data:
        player.position = data['position']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Oyuncu güncellendi!', 'player': player.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 6. OYUNCU SİL (DELETE)
@app.route('/api/players/<int:id>', methods=['DELETE'])
def delete_player(id):
    player = Player.query.get_or_404(id)
    
    try:
        # Önce istatistikleri silmeliyiz (Cascade ayarı models.py'da yoksa elle sileriz)
        # Ama models.py'da cascade tanımlamadıysak hata alabiliriz. 
        # Şimdilik direkt oyuncuyu siliyoruz.
        db.session.delete(player)
        db.session.commit()
        return jsonify({'message': f'{player.playerName} veritabanından silindi.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# 7. OYUNCU ARAMA (SEARCH)
@app.route('/api/players/search', methods=['GET'])
def search_players():
    query = request.args.get('q', '') # URL'den ?q=LeBron parametresini al
    if not query:
        return jsonify({'error': 'Arama terimi girilmedi.'}), 400
    
    # İsim içinde arama yap (Büyük/küçük harf duyarsız - ilike veya func.lower)
    results = Player.query.filter(Player.playerName.ilike(f'%{query}%')).all()
    
    return jsonify([p.to_dict() for p in results])

# 8. TAKIM DETAYI VE KADROSU (ROSTER)
@app.route('/api/teams/<int:id>', methods=['GET'])
def get_team_detail(id):
    team = Team.query.get_or_404(id)
    team_data = team.to_dict()
    
    # Takım Performans İstatistikleri
    team_data['stats'] = {
        'regular': None,
        'playoffs': None
    }

    # Normal Sezon Sıralamaları
    if team.reg_season_stats:
        team_data['stats']['regular'] = {
            'winRank': team.reg_season_stats.winRank,
            'defRatingRank': team.reg_season_stats.defRatingRank,
            'stealRank': team.reg_season_stats.stealRank,
            'blockRank': team.reg_season_stats.blockRank
        }
    
    # Playoff Sıralamaları (YENİ EKLENEN KISIM)
    if team.playoff_stats:
        team_data['stats']['playoffs'] = {
            'winRank': team.playoff_stats.winRank,
            'defRatingRank': team.playoff_stats.defRatingRank,
            'stealRank': team.playoff_stats.stealRank,
            'blockRank': team.playoff_stats.blockRank
        }

    # Kadroyu (Roster) Ekle
    roster = []
    for player in team.players:
        p_data = player.to_dict()
        # Kadro listesinde sadece ortalama sayıyı (PTS) göstermek yeterli olabilir
        if player.reg_season_stats:
             p_data['PTS'] = player.reg_season_stats.PTS
        roster.append(p_data)
        
    team_data['roster'] = roster
        
    return jsonify(team_data)

# 9. EN İYİLER (TOP PERFORMERS)
# Örnek: /api/stats/top?category=PTS (Sayı kralları)
@app.route('/api/stats/top', methods=['GET'])
def get_top_performers():
    category = request.args.get('category', 'PTS') # Varsayılan: Sayı (PTS)
    limit = int(request.args.get('limit', 5)) # İlk 5 kişi
    
    # İstatistik tablosundan sıralama yapıyoruz
    # desc() = Büyükten küçüğe sırala
    if category == 'PTS':
        stats = PlayerRegularSeason.query.order_by(PlayerRegularSeason.PTS.desc()).limit(limit).all()
    elif category == 'AST':
        stats = PlayerRegularSeason.query.order_by(PlayerRegularSeason.AST.desc()).limit(limit).all()
    elif category == 'REB':
        stats = PlayerRegularSeason.query.order_by(PlayerRegularSeason.REB.desc()).limit(limit).all()
    elif category == 'EFF': # Verimlilik
        stats = PlayerRegularSeason.query.order_by(PlayerRegularSeason.efficiency.desc()).limit(limit).all()
    else:
        return jsonify({'error': 'Geçersiz kategori. PTS, AST, REB, EFF kullanın.'}), 400

    results = []
    for stat in stats:
        # İstatistiğin sahibi olan oyuncu bilgilerini de getir
        player_info = stat.player.to_dict()
        player_info['value'] = getattr(stat, category) # İstenen değeri ekle (Örn: 30.1)
        results.append(player_info)
        
    return jsonify(results)    

if __name__ == '__main__':
    app.run(debug=True, port=5000)