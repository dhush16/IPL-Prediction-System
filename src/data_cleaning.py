import pandas as pd
import numpy as np
import logging
import os

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEAM_MAPPING = {
    'Rising Pune Supergiant': 'Rising Pune Supergiants',
    'Pune Warriors': 'Rising Pune Supergiants',
    'Delhi Daredevils': 'Delhi Capitals',
    'Deccan Chargers': 'Sunrisers Hyderabad',
    'Gujarat Lions': 'Gujarat Titans',
    'Kings XI Punjab': 'Punjab Kings'
}

def standardize_team_names(df, team_columns):
    """Standardize inconsistent team names across the dataset."""
    logger.info(f"Standardizing team names in columns: {team_columns}")
    for col in team_columns:
        if col in df.columns:
            df[col] = df[col].replace(TEAM_MAPPING)
    return df

def clean_matches_data(matches_df):
    """Clean matches dataset: remove null results, handle missing values."""
    logger.info("Cleaning matches data...")
    matches_df = matches_df.copy()
    
    # Filter out no result matches
    initial_rows = len(matches_df)
    matches_df = matches_df[matches_df['result'].notna()]
    matches_df = matches_df[matches_df['result'].str.lower() != 'no result']
    logger.info(f"Removed {initial_rows - len(matches_df)} no-result matches")
    
    # Handle missing cities/venues
    if 'city' in matches_df.columns and 'venue' in matches_df.columns:
        matches_df['city'] = matches_df['city'].fillna(
            matches_df['venue'].apply(lambda x: x.split(',')[0] if pd.notna(x) else 'Unknown')
        )
    
    # Fill missing toss values
    if 'toss_decision' in matches_df.columns:
        matches_df['toss_decision'] = matches_df['toss_decision'].fillna('bat')
    
    # Standardize teams
    matches_df = standardize_team_names(
        matches_df, 
        ['team1', 'team2', 'toss_winner', 'winner']
    )
    
    logger.info(f"Cleaned matches: {len(matches_df)} records")
    return matches_df

def clean_deliveries_data(deliveries_df):
    """Clean deliveries dataset: standardize teams, handle dismissals."""
    logger.info("Cleaning deliveries data...")
    deliveries_df = deliveries_df.copy()
    
    # Fill missing values in dismissal columns
    deliveries_df['dismissal_kind'] = deliveries_df['dismissal_kind'].fillna('Not Out')
    deliveries_df['player_dismissed'] = deliveries_df['player_dismissed'].fillna('None')
    deliveries_df['fielder'] = deliveries_df['fielder'].fillna('Unknown')
    
    # Standardize teams
    deliveries_df = standardize_team_names(
        deliveries_df,
        ['batting_team', 'bowling_team']
    )
    
    # Ensure numeric columns
    deliveries_df['runs'] = pd.to_numeric(deliveries_df['runs'], errors='coerce').fillna(0)
    deliveries_df['extra_runs'] = pd.to_numeric(deliveries_df['extra_runs'], errors='coerce').fillna(0)
    
    logger.info(f"Cleaned deliveries: {len(deliveries_df)} records")
    return deliveries_df

def load_and_clean_data(matches_path, deliveries_path):
    """Load and clean both datasets."""
    logger.info("Loading IPL datasets...")
    
    try:
        matches_df = pd.read_csv(matches_path)
        deliveries_df = pd.read_csv(deliveries_path)
        
        logger.info(f"Loaded {len(matches_df)} matches and {len(deliveries_df)} deliveries")
        
        matches_df = clean_matches_data(matches_df)
        deliveries_df = clean_deliveries_data(deliveries_df)
        
        return matches_df, deliveries_df
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise
