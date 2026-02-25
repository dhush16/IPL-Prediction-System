import pandas as pd
import numpy as np
import logging
from src.data_cleaning import clean_matches_data, clean_deliveries_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def engineer_match_features(matches_df, deliveries_df):
    """
    Creates match-level features including toss impact, home advantage, venue factor.
    """
    logger.info("Engineering Match Level Features...")
    df = clean_matches_data(matches_df.copy())
    
    # Toss impact: Did toss winner win the match?
    df['toss_win_match_win'] = (df['toss_winner'] == df['winner']).astype(int)
    
    # Toss decision win rate by decision type
    toss_win_rate = df.groupby('toss_decision')['toss_win_match_win'].mean().to_dict()
    df['toss_decision_winrate'] = df['toss_decision'].map(toss_win_rate).fillna(0.5)
    
    # Venue/City factor
    if 'city' in df.columns:
        venue_win_rate = df.groupby('city')['winner'].count().reset_index()
        venue_win_rate.columns = ['city', 'matches_at_venue']
        df = df.merge(venue_win_rate, on='city', how='left')
        df['matches_at_venue'] = df['matches_at_venue'].fillna(0)
    
    # Team-based features at this stage
    df['team1_toss_wins'] = df['team1'].map(
        df[df['team1'] == df['toss_winner']].groupby('team1').size()
    ).fillna(0)
    
    df['team2_toss_wins'] = df['team2'].map(
        df[df['team2'] == df['toss_winner']].groupby('team2').size()
    ).fillna(0)
    
    logger.info(f"Created match-level features: {df.shape[1]} columns")
    return df

def calculate_team_performance(matches_df):
    """
    Calculate team-level statistics: win rate, avg runs, etc.
    """
    logger.info("Calculating team performance metrics...")
    df = clean_matches_data(matches_df.copy())
    
    team_stats = []
    
    # For each unique team
    teams = pd.concat([df['team1'], df['team2']]).unique()
    
    for team in teams:
        team_matches = df[(df['team1'] == team) | (df['team2'] == team)]
        
        wins = len(df[df['winner'] == team])
        total = len(team_matches)
        
        win_rate = wins / total if total > 0 else 0
        
        team_stats.append({
            'team': team,
            'total_matches': total,
            'wins': wins,
            'win_rate': win_rate,
            'losses': total - wins
        })
    
    team_perf_df = pd.DataFrame(team_stats)
    logger.info(f"Team performance stats for {len(team_perf_df)} teams")
    return team_perf_df

def calculate_player_stats(deliveries_df, matches_df):
    """
    Calculate player-level batting and bowling statistics.
    """
    logger.info("Calculating player statistics...")
    df = clean_deliveries_data(deliveries_df.copy())
    
    # === BATTING STATS ===
    # Get runs per batsman
    batsman_runs = df.groupby('batsman')['batsman_runs'].sum().reset_index()
    batsman_runs.columns = ['batsman', 'total_runs']
    
    # Get balls faced
    balls_faced = df.groupby('batsman').size().reset_index(name='balls_faced')
    
    # Get dismissals
    dismissals = df[df['player_dismissed'].notna() & (df['player_dismissed'] != 'None')]\
        .groupby('player_dismissed').size().reset_index(name='dismissals')
    dismissals.columns = ['batsman', 'dismissals']
    
    # Merge batting data
    batting_stats = batsman_runs.merge(balls_faced, on='batsman', how='outer')
    batting_stats = batting_stats.merge(dismissals, on='batsman', how='left')
    batting_stats['dismissals'] = batting_stats['dismissals'].fillna(0).astype(int)
    
    # Calculate strike rate and average
    batting_stats['strike_rate'] = (batting_stats['total_runs'] / batting_stats['balls_faced'] * 100).round(2)
    batting_stats['average'] = (batting_stats['total_runs'] / (batting_stats['dismissals'] + 1)).round(2)
    
    # === BOWLING STATS ===
    # Get runs conceded by bowler
    bowler_df = df.groupby('bowler').agg({
        'total_runs': 'sum',  # Runs conceded
        'match_id': 'count'   # Balls bowled
    }).reset_index()
    bowler_df.columns = ['bowler', 'runs_conceded', 'balls_bowled']
    
    # Get wickets
    wickets = df[df['player_dismissed'].notna() & (df['player_dismissed'] != 'None')]\
        .groupby('bowler').size().reset_index(name='wickets')
    
    bowling_stats = bowler_df.merge(wickets, on='bowler', how='left')
    bowling_stats['wickets'] = bowling_stats['wickets'].fillna(0).astype(int)
    
    # Calculate economy rate
    bowling_stats['economy_rate'] = (bowling_stats['runs_conceded'] / (bowling_stats['balls_bowled'] / 6)).round(2)
    
    logger.info(f"Calculated stats for {len(batting_stats)} batsmen and {len(bowling_stats)} bowlers")
    return batting_stats, bowling_stats

def calculate_recent_form(matches_df, window=5):
    """
    Calculate recent form (last N matches performance).
    """
    logger.info(f"Calculating recent form (last {window} matches)...")
    df = clean_matches_data(matches_df.copy())
    df = df.sort_values('date')
    
    form_stats = []
    teams = pd.concat([df['team1'], df['team2']]).unique()
    
    for team in teams:
        team_matches = df[(df['team1'] == team) | (df['team2'] == team)].tail(window)
        
        recent_wins = len(team_matches[team_matches['winner'] == team])
        recent_matches = len(team_matches)
        
        form_stats.append({
            'team': team,
            f'recent_{window}_wins': recent_wins,
            f'recent_{window}_form': recent_wins / recent_matches if recent_matches > 0 else 0
        })
    
    form_df = pd.DataFrame(form_stats)
    return form_df

def calculate_head_to_head(matches_df):
    """
    Calculate head-to-head statistics between teams.
    """
    logger.info("Calculating head-to-head statistics...")
    df = clean_matches_data(matches_df.copy())
    
    h2h_dict = {}
    
    for idx, row in df.iterrows():
        team1, team2 = row['team1'], row['team2']
        winner = row['winner']
        
        key = tuple(sorted([team1, team2]))
        
        if key not in h2h_dict:
            h2h_dict[key] = {'team1': team1, 'team2': team2, 'team1_wins': 0, 'team2_wins': 0, 'total': 0}
        
        h2h_dict[key]['total'] += 1
        
        if winner == team1:
            h2h_dict[key]['team1_wins'] += 1
        elif winner == team2:
            h2h_dict[key]['team2_wins'] += 1
    
    h2h_list = list(h2h_dict.values())
    h2h_df = pd.DataFrame(h2h_list)
    logger.info(f"Calculated H2H for {len(h2h_df)} unique matchups")
    return h2h_df

def calculate_powerplay_death_stats(deliveries_df):
    """
    Calculate powerplay (overs 1-6) and death overs (overs 16-20) performance.
    """
    logger.info("Calculating powerplay and death overs statistics...")
    df = clean_deliveries_data(deliveries_df.copy())
    
    # Extract over numbers
    df['over_number'] = df['over'].astype(int)
    
    # Define phases
    df['phase'] = 'middle'
    df.loc[df['over_number'] < 6, 'phase'] = 'powerplay'
    df.loc[df['over_number'] >= 16, 'phase'] = 'death'
    
    # Batting stats by phase
    phase_stats = df.groupby(['batting_team', 'phase']).agg({
        'batsman_runs': 'sum',
        'match_id': 'count'
    }).reset_index()
    phase_stats.columns = ['team', 'phase', 'runs', 'balls']
    
    # Calculate strike rate by phase
    phase_stats['strike_rate'] = (phase_stats['runs'] / phase_stats['balls'] * 100).round(2)
    
    logger.info(f"Calculated phase statistics for {phase_stats['team'].nunique()} teams")
    return phase_stats

def build_training_dataset(matches_df, deliveries_df):
    """
    Build comprehensive training dataset combining all features.
    """
    logger.info("Building training dataset...")
    
    matches_clean = clean_matches_data(matches_df.copy())
    deliveries_clean = clean_deliveries_data(deliveries_df.copy())
    
    # Get team performance
    team_perf = calculate_team_performance(matches_df)
    team_perf.rename(columns={'team': 'team1'}, inplace=True)
    
    # Merge team1 stats
    dataset = matches_clean.merge(
        team_perf[['team1', 'win_rate', 'wins', 'losses']],
        on='team1',
        how='left'
    )
    dataset.rename(columns={
        'win_rate': 'team1_win_rate',
        'wins': 'team1_wins',
        'losses': 'team1_losses'
    }, inplace=True)
    
    # Merge team2 stats
    team_perf.rename(columns={'team1': 'team2'}, inplace=True)
    dataset = dataset.merge(
        team_perf[['team2', 'win_rate', 'wins', 'losses']],
        on='team2',
        how='left'
    )
    dataset.rename(columns={
        'win_rate': 'team2_win_rate',
        'wins': 'team2_wins',
        'losses': 'team2_losses'
    }, inplace=True)
    
    # Add recent form
    form_df = calculate_recent_form(matches_df, window=5)
    form_df.rename(columns={'team': 'team1'}, inplace=True)
    dataset = dataset.merge(form_df, on='team1', how='left')
    
    form_df.rename(columns={'team1': 'team2'}, inplace=True)
    dataset = dataset.merge(form_df, on='team2', how='left')
    
    # Encode target variable (winner as binary)
    dataset['target'] = (dataset['winner'] == dataset['team1']).astype(int)
    
    # Fill remaining NaN values
    dataset = dataset.fillna(0)
    
    logger.info(f"Training dataset shape: {dataset.shape}")
    return dataset
    """
    Combine datasets to generate the final feature matrix for match winner prediction.
    """
    match_features = engineer_match_features(matches_df)
    
    # For Match Winner Prediction, select target and features
    # Features: team1, team2, venue, toss_winner, toss_decision, etc.
    final_df = match_features[['team1', 'team2', 'venue', 'toss_winner', 'toss_decision', 'winner']]
    final_df = final_df.dropna()
    
    return final_df
