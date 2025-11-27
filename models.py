from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ----------------------
# TABLO 1: TEAMS (Takımlar)
# ----------------------
class Team(db.Model):
    __tablename__ = 'teams'
    teamID = db.Column(db.Integer, primary_key=True)
    teamName = db.Column(db.String(100), nullable=False, unique=True)
    logoUrl = db.Column(db.String(255))
    teamAbbreviate = db.Column(db.String(10))
    conference = db.Column(db.String(50))

    # İlişkiler
    players = db.relationship('Player', backref='team', lazy=True)
    reg_season_stats = db.relationship('TeamRegularSeason', backref='team', uselist=False)
    playoff_stats = db.relationship('TeamPlayoffs', backref='team', uselist=False)

    def to_dict(self):
        return {
            'teamID': self.teamID,
            'teamName': self.teamName,
            'logoUrl': self.logoUrl,
            'teamAbbreviate': self.teamAbbreviate,
            'conference': self.conference
        }

# ----------------------
# TABLO 2: PLAYERS (Oyuncular)
# ----------------------
class Player(db.Model):
    __tablename__ = 'players'
    playerID = db.Column(db.Integer, primary_key=True)
    teamID = db.Column(db.Integer, db.ForeignKey('teams.teamID'), nullable=False)
    playerName = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50))
    headshotUrl = db.Column(db.String(255))
    
    # İlişkiler
    reg_season_stats = db.relationship('PlayerRegularSeason', backref='player', uselist=False)
    playoff_stats = db.relationship('PlayerPlayoffs', backref='player', uselist=False)

    def to_dict(self):
        return {
            'playerID': self.playerID,
            'playerName': self.playerName,
            'teamID': self.teamID,
            'teamName': self.team.teamName if self.team else "N/A",
            'position': self.position,
            'headshotUrl': self.headshotUrl
        }

# ----------------------
# PERFORMANS TABLOLARI İÇİN ORTAK YAPI
# ----------------------
class StatsMixin(object):
    GP_X = db.Column(db.Integer)
    MIN_X = db.Column(db.Float)
    PTS = db.Column(db.Float)
    REB = db.Column(db.Float)
    AST = db.Column(db.Float)
    STL = db.Column(db.Float)
    BLK = db.Column(db.Float)
    efficiency = db.Column(db.Float)

# TABLO 3: TEAM REGULAR SEASON
class TeamRegularSeason(db.Model):
    __tablename__ = 'team_regular_season'
    teamID = db.Column(db.Integer, db.ForeignKey('teams.teamID'), primary_key=True)
    winRank = db.Column(db.Integer)
    # Diğer rank sütunları eklenebilir

# TABLO 4: TEAM PLAYOFFS
class TeamPlayoffs(db.Model):
    __tablename__ = 'team_playoffs'
    teamID = db.Column(db.Integer, db.ForeignKey('teams.teamID'), primary_key=True)
    winRank = db.Column(db.Integer)

# TABLO 5: PLAYER REGULAR SEASON
class PlayerRegularSeason(db.Model, StatsMixin):
    __tablename__ = 'player_regular_season'
    playerID = db.Column(db.Integer, db.ForeignKey('players.playerID'), primary_key=True)
    teamID = db.Column(db.Integer, db.ForeignKey('teams.teamID'))

# TABLO 6: PLAYER PLAYOFFS
class PlayerPlayoffs(db.Model, StatsMixin):
    __tablename__ = 'player_playoffs'
    playerID = db.Column(db.Integer, db.ForeignKey('players.playerID'), primary_key=True)
    teamID = db.Column(db.Integer, db.ForeignKey('teams.teamID'))