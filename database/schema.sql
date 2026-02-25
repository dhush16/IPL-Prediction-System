-- IPL Prediction System Database Schema
-- For MySQL 5.7+

CREATE DATABASE IF NOT EXISTS ipl_prediction_db;
USE ipl_prediction_db;

-- ==================== USERS TABLE ====================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== MATCH PREDICTIONS TABLE ====================
CREATE TABLE IF NOT EXISTS match_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL,
    team1 VARCHAR(100) NOT NULL,
    team2 VARCHAR(100) NOT NULL,
    venue VARCHAR(150),
    city VARCHAR(100),
    match_date DATETIME,
    toss_winner VARCHAR(100),
    toss_decision VARCHAR(10),
    predicted_winner VARCHAR(100) NOT NULL,
    actual_winner VARCHAR(100),
    win_probability FLOAT NOT NULL,
    team1_probability FLOAT,
    team2_probability FLOAT,
    model_used VARCHAR(50) NOT NULL,
    prediction_accuracy BOOLEAN,
    confidence_score FLOAT,
    feature_data JSON,
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_match_id (match_id),
    INDEX idx_team1 (team1),
    INDEX idx_team2 (team2),
    INDEX idx_prediction_time (prediction_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== PLAYER PREDICTIONS TABLE ====================
CREATE TABLE IF NOT EXISTS player_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL,
    player_id VARCHAR(100) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    player_team VARCHAR(100) NOT NULL,
    opposition_team VARCHAR(100),
    venue VARCHAR(150),
    predicted_category VARCHAR(20) NOT NULL,
    predicted_runs FLOAT,
    predicted_wickets FLOAT,
    predicted_strike_rate FLOAT,
    actual_category VARCHAR(20),
    actual_runs INT,
    actual_wickets INT,
    actual_strike_rate FLOAT,
    prediction_accuracy BOOLEAN,
    confidence_score FLOAT,
    model_used VARCHAR(50) NOT NULL,
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_player_id (player_id),
    INDEX idx_player_name (player_name),
    INDEX idx_opposition_team (opposition_team)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== MATCHES TABLE ====================
CREATE TABLE IF NOT EXISTS matches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL UNIQUE,
    team1 VARCHAR(100) NOT NULL,
    team2 VARCHAR(100) NOT NULL,
    winner VARCHAR(100),
    venue VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    season INT NOT NULL,
    toss_winner VARCHAR(100),
    toss_decision VARCHAR(10),
    result VARCHAR(20),
    margin INT,
    date DATETIME,
    player_of_match VARCHAR(100),
    team1_runs INT,
    team2_runs INT,
    team1_wickets INT,
    team2_wickets INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_match_id (match_id),
    INDEX idx_team1 (team1),
    INDEX idx_team2 (team2),
    INDEX idx_season (season)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== PLAYER STATS TABLE ====================
CREATE TABLE IF NOT EXISTS player_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id VARCHAR(100) NOT NULL UNIQUE,
    player_name VARCHAR(100) NOT NULL,
    team VARCHAR(100) NOT NULL,
    player_type VARCHAR(20) NOT NULL,
    matches_played INT DEFAULT 0,
    innings INT DEFAULT 0,
    runs_scored INT DEFAULT 0,
    batting_average FLOAT DEFAULT 0.0,
    strike_rate FLOAT DEFAULT 0.0,
    centuries INT DEFAULT 0,
    fifties INT DEFAULT 0,
    wickets INT DEFAULT 0,
    runs_conceded INT DEFAULT 0,
    economy_rate FLOAT DEFAULT 0.0,
    bowling_average FLOAT DEFAULT 0.0,
    recent_form FLOAT DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_player_id (player_id),
    INDEX idx_player_name (player_name),
    INDEX idx_team (team)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== TEAM STATS TABLE ====================
CREATE TABLE IF NOT EXISTS team_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    season INT NOT NULL,
    total_matches INT DEFAULT 0,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    win_percentage FLOAT DEFAULT 0.0,
    home_matches INT DEFAULT 0,
    home_wins INT DEFAULT 0,
    away_matches INT DEFAULT 0,
    away_wins INT DEFAULT 0,
    toss_wins INT DEFAULT 0,
    toss_win_match_win INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_team_name (team_name),
    INDEX idx_season (season)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== VENUE STATS TABLE ====================
CREATE TABLE IF NOT EXISTS venue_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venue_name VARCHAR(150) NOT NULL UNIQUE,
    city VARCHAR(100) NOT NULL,
    total_matches INT DEFAULT 0,
    avg_runs FLOAT DEFAULT 0.0,
    avg_wickets FLOAT DEFAULT 0.0,
    home_team_wins INT DEFAULT 0,
    away_team_wins INT DEFAULT 0,
    home_win_percentage FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_venue_name (venue_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== INDEXES FOR PERFORMANCE ====================
CREATE INDEX idx_team1_team2 ON match_predictions(team1, team2);
CREATE INDEX idx_model_used ON match_predictions(model_used);
CREATE INDEX idx_player_team_opposition ON player_predictions(player_team, opposition_team);

-- ==================== SAMPLE DATA ====================
INSERT IGNORE INTO team_stats (team_name, season, total_matches, wins, losses, win_percentage)
VALUES 
    ('Mumbai Indians', 2023, 17, 10, 7, 58.82),
    ('Chennai Super Kings', 2023, 17, 8, 9, 47.06),
    ('Royal Challengers Bangalore', 2023, 17, 8, 9, 47.06),
    ('Kolkata Knight Riders', 2023, 17, 9, 8, 52.94),
    ('Delhi Capitals', 2023, 17, 9, 8, 52.94),
    ('Rajasthan Royals', 2023, 17, 10, 7, 58.82),
    ('Punjab Kings', 2023, 17, 5, 12, 29.41),
    ('Gujarat Titans', 2023, 17, 7, 10, 41.18),
    ('Sunrisers Hyderabad', 2023, 17, 6, 11, 35.29),
    ('Lucknow Super Giants', 2023, 17, 8, 9, 47.06);
