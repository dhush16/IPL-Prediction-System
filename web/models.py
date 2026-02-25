from web.app import db
from datetime import datetime
from sqlalchemy import JSON

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class MatchPrediction(db.Model):
    __tablename__ = 'match_predictions'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, nullable=True)
    team1 = db.Column(db.String(100), nullable=False, index=True)
    team2 = db.Column(db.String(100), nullable=False, index=True)
    venue = db.Column(db.String(150), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    match_date = db.Column(db.DateTime, nullable=True)
    toss_winner = db.Column(db.String(100), nullable=True)
    toss_decision = db.Column(db.String(10), nullable=True)  # 'bat' or 'field'
    predicted_winner = db.Column(db.String(100), nullable=False)
    actual_winner = db.Column(db.String(100), nullable=True)
    win_probability = db.Column(db.Float, nullable=False)  # 0-100
    team1_probability = db.Column(db.Float, nullable=True)
    team2_probability = db.Column(db.Float, nullable=True)
    model_used = db.Column(db.String(50), nullable=False)  # 'Random Forest', 'XGBoost', etc.
    prediction_accuracy = db.Column(db.Boolean, nullable=True)  # True/False after match
    confidence_score = db.Column(db.Float, nullable=True)
    feature_data = db.Column(JSON, nullable=True)  # Store input features for debugging
    prediction_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MatchPrediction {self.team1} vs {self.team2}>'

class PlayerPrediction(db.Model):
    __tablename__ = 'player_predictions'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, nullable=True)
    player_id = db.Column(db.String(100), nullable=True, index=True)
    player_name = db.Column(db.String(100), nullable=False)
    player_team = db.Column(db.String(100), nullable=False)
    opposition_team = db.Column(db.String(100), nullable=True, index=True)
    venue = db.Column(db.String(150), nullable=True)
    
    # Performance prediction
    predicted_category = db.Column(db.String(20), nullable=False)  # 'High', 'Medium', 'Low'
    predicted_runs = db.Column(db.Float, nullable=True)
    predicted_wickets = db.Column(db.Float, nullable=True)
    predicted_strike_rate = db.Column(db.Float, nullable=True)
    
    # Actual performance (after match)
    actual_category = db.Column(db.String(20), nullable=True)
    actual_runs = db.Column(db.Integer, nullable=True)
    actual_wickets = db.Column(db.Integer, nullable=True)
    actual_strike_rate = db.Column(db.Float, nullable=True)
    
    prediction_accuracy = db.Column(db.Boolean, nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    model_used = db.Column(db.String(50), nullable=False)
    prediction_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PlayerPrediction {self.player_name}>'

class Match(db.Model):
    __tablename__ = 'matches'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    team1 = db.Column(db.String(100), nullable=False)
    team2 = db.Column(db.String(100), nullable=False)
    winner = db.Column(db.String(100), nullable=True)
    venue = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    toss_winner = db.Column(db.String(100), nullable=True)
    toss_decision = db.Column(db.String(10), nullable=True)
    result = db.Column(db.String(20), nullable=True)
    margin = db.Column(db.Integer, nullable=True)
    date = db.Column(db.DateTime, nullable=True)
    player_of_match = db.Column(db.String(100), nullable=True)
    
    # Match statistics
    team1_runs = db.Column(db.Integer, nullable=True)
    team2_runs = db.Column(db.Integer, nullable=True)
    team1_wickets = db.Column(db.Integer, nullable=True)
    team2_wickets = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Match {self.team1} vs {self.team2}>'

class PlayerStats(db.Model):
    __tablename__ = 'player_stats'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    player_name = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(100), nullable=False, index=True)
    player_type = db.Column(db.String(20), nullable=False)  # 'batsman', 'bowler', 'all-rounder'
    
    # Batting stats
    matches_played = db.Column(db.Integer, default=0)
    innings = db.Column(db.Integer, default=0)
    runs_scored = db.Column(db.Integer, default=0)
    batting_average = db.Column(db.Float, default=0.0)
    strike_rate = db.Column(db.Float, default=0.0)
    centuries = db.Column(db.Integer, default=0)
    fifties = db.Column(db.Integer, default=0)
    
    # Bowling stats
    wickets = db.Column(db.Integer, default=0)
    runs_conceded = db.Column(db.Integer, default=0)
    economy_rate = db.Column(db.Float, default=0.0)
    bowling_average = db.Column(db.Float, default=0.0)
    
    # Recent form (last 5 matches)
    recent_form = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PlayerStats {self.player_name}>'

class TeamStats(db.Model):
    __tablename__ = 'team_stats'
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    season = db.Column(db.Integer, nullable=False)
    
    # Win/Loss Record
    total_matches = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    win_percentage = db.Column(db.Float, default=0.0)
    
    # Venue-specific stats
    home_matches = db.Column(db.Integer, default=0)
    home_wins = db.Column(db.Integer, default=0)
    away_matches = db.Column(db.Integer, default=0)
    away_wins = db.Column(db.Integer, default=0)
    
    # Toss stats
    toss_wins = db.Column(db.Integer, default=0)
    toss_win_match_win = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TeamStats {self.team_name}>'

class VenueStats(db.Model):
    __tablename__ = 'venue_stats'
    id = db.Column(db.Integer, primary_key=True)
    venue_name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    city = db.Column(db.String(100), nullable=False)
    
    total_matches = db.Column(db.Integer, default=0)
    avg_runs = db.Column(db.Float, default=0.0)
    avg_wickets = db.Column(db.Float, default=0.0)
    
    # Home team advantage
    home_team_wins = db.Column(db.Integer, default=0)
    away_team_wins = db.Column(db.Integer, default=0)
    home_win_percentage = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VenueStats {self.venue_name}>'
