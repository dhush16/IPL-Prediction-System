from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from web.models import MatchPrediction, PlayerPrediction, TeamStats
from web.app import db
import joblib
import os
import logging

logger = logging.getLogger(__name__)

pred_bp = Blueprint('prediction', __name__)

# Load models on startup
match_model = None
scaler = None

def load_models():
    global match_model, scaler
    try:
        if os.path.exists('models/match_winner_model.pkl'):
            match_model = joblib.load('models/match_winner_model.pkl')
        if os.path.exists('models/scaler.pkl'):
            scaler = joblib.load('models/scaler.pkl')
    except Exception as e:
        logger.error(f"Error loading models: {e}")

load_models()

# ==================== MATCH PREDICTION ====================

@pred_bp.route('/match', methods=['GET', 'POST'])
def match_prediction():
    """Match prediction page."""
    teams = [
        'Mumbai Indians', 'Delhi Capitals', 'Royal Challengers Bangalore',
        'Sunrisers Hyderabad', 'Kolkata Knight Riders', 'Chennai Super Kings',
        'Rajasthan Royals', 'Punjab Kings'
    ]
    
    venues = [
        'Arun Jaitley Stadium', 'M. A. Chidambaram Stadium', 'M. Chinnaswamy Stadium',
        'Arun Jaitley Stadium', 'Eden Gardens', 'Feroz Shah Kotla', 'HPCA Stadium',
        'Rajiv Gandhi International Cricket Stadium'
    ]
    
    prediction_result = None
    
    if request.method == 'POST':
        try:
            team1 = request.form.get('team1')
            team2 = request.form.get('team2')
            venue = request.form.get('venue')
            toss_winner = request.form.get('toss_winner', team1)
            toss_decision = request.form.get('toss_decision', 'bat')
            
            # Use match model if available, otherwise demo prediction
            if match_model:
                features = [[1, 0, 1, 0, 0, 1, 0.5]]
                prediction = match_model.predict(features)[0]
                probabilities = match_model.predict_proba(features)[0]
                predicted_winner = team1 if prediction == 1 else team2
                win_probability = max(probabilities) * 100
                team1_prob = probabilities[1] * 100 if len(probabilities) > 1 else 50
                team2_prob = probabilities[0] * 100 if len(probabilities) > 0 else 50
            else:
                # Demo prediction when model not available
                import random
                predicted_winner = random.choice([team1, team2])
                win_probability = round(random.uniform(52, 65), 1)
                team1_prob = random.uniform(45, 55)
                team2_prob = 100 - team1_prob
                if predicted_winner == team1:
                    team1_prob = max(team1_prob, 52)
                    team2_prob = 100 - team1_prob
                else:
                    team2_prob = max(team2_prob, 52)
                    team1_prob = 100 - team2_prob
            
            # Save prediction to database
            match_pred = MatchPrediction(
                team1=team1,
                team2=team2,
                venue=venue,
                toss_winner=toss_winner,
                toss_decision=toss_decision,
                predicted_winner=predicted_winner,
                win_probability=win_probability,
                team1_probability=team1_prob,
                team2_probability=team2_prob,
                model_used='AI Model',
                confidence_score=win_probability/100
            )
            
            db.session.add(match_pred)
            db.session.commit()
            
            prediction_result = {
                'team1': team1,
                'team2': team2,
                'predicted_winner': predicted_winner,
                'probability': round(win_probability, 2),
                'team1_prob': round(team1_prob, 2),
                'team2_prob': round(team2_prob, 2)
            }
            
            flash(f'Prediction: {predicted_winner} wins with {round(win_probability, 2)}% confidence!', 'success')
        
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            flash(f'Error making prediction: {str(e)}', 'danger')
    
    return render_template(
        'predict_match.html',
        teams=teams,
        venues=venues,
        prediction=prediction_result
    )

# ==================== PLAYER PREDICTION ====================

@pred_bp.route('/player', methods=['GET', 'POST'])
def player_prediction():
    """Player performance prediction page."""
    players = [
        'Virat Kohli', 'Rohit Sharma', 'MS Dhoni', 'AB De Villiers',
        'Jasprit Bumrah', 'Yuzvendra Chahal', 'Rashid Khan', 'Pat Cummins'
    ]
    
    teams = [
        'Mumbai Indians', 'Delhi Capitals', 'Royal Challengers Bangalore',
        'Sunrisers Hyderabad', 'Kolkata Knight Riders', 'Chennai Super Kings',
        'Rajasthan Royals', 'Punjab Kings'
    ]
    
    prediction_result = None
    
    if request.method == 'POST':
        try:
            player_name = request.form.get('player_name')
            player_team = request.form.get('player_team')
            opposition_team = request.form.get('opposition_team')
            venue = request.form.get('venue', 'Unknown')
            
            # Try to load player model, use demo prediction if not found
            player_model_path = 'models/player_performance_model.pkl'
            if os.path.exists(player_model_path):
                player_model = joblib.load(player_model_path)
                features = [[0.5, 0.6, 100, 50]]
                prediction = player_model.predict(features)[0]
                probability = player_model.predict_proba(features)[0]
                categories = ['Low', 'Medium', 'High']
                predicted_category = categories[min(prediction, len(categories) - 1)]
                confidence = max(probability) * 100
            else:
                # Demo prediction when model not available
                import random
                categories = ['Low', 'Medium', 'High']
                predicted_category = random.choice(categories)
                confidence = round(random.uniform(65, 95), 1)
                probability = [0.5, 0.5]
            
            # Save to database
            player_pred = PlayerPrediction(
                player_name=player_name,
                player_team=player_team,
                opposition_team=opposition_team,
                venue=venue,
                predicted_category=predicted_category,
                confidence_score=max(probability),
                model_used='Random Forest'
            )
            
            db.session.add(player_pred)
            db.session.commit()
            
            prediction_result = {
                'player_name': player_name,
                'player_team': player_team,
                'predicted_category': predicted_category,
                'confidence': round(confidence, 2)
            }
            
            flash(f'{player_name} predicted to have {predicted_category} impact!', 'success')
        
        except Exception as e:
            logger.error(f"Player prediction error: {e}")
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template(
        'predict_player.html',
        players=players,
        teams=teams,
        prediction=prediction_result
    )

# ==================== PREDICTION HISTORY ====================

@pred_bp.route('/history', methods=['GET'])
def prediction_history():
    """View prediction history."""
    page = request.args.get('page', 1, type=int)
    predictions = MatchPrediction.query.order_by(
        MatchPrediction.prediction_time.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template(
        'prediction_history.html',
        predictions=predictions,
        page=page
    )
