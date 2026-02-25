from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token
from web.app import db, cache
from web.models import MatchPrediction, PlayerPrediction, User, TeamStats
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import os
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# ==================== AUTHENTICATION ====================

@api_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password') or not data.get('email'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password'])
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.id
        }), 201
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """User login."""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user_id': user.id,
            'username': user.username
        }), 200
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

# ==================== MATCH PREDICTIONS ====================

@api_bp.route('/predictions/match', methods=['POST'])
def predict_match():
    """Predict match winner."""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['team1', 'team2', 'venue']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        team1 = data.get('team1')
        team2 = data.get('team2')
        venue = data.get('venue')
        toss_winner = data.get('toss_winner', team1)
        toss_decision = data.get('toss_decision', 'bat')
        
        # Load model
        model_path = 'models/match_winner_model.pkl'
        if not os.path.exists(model_path):
            return jsonify({'error': 'Model not found. Please train the model first.'}), 500
        
        model = joblib.load(model_path)
        
        # Create feature vector (simplified - use actual features from your model)
        features = [[1, 0, 1, 0, 0, 1, 0.5]]
        
        # Predict
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        
        predicted_winner = team1 if prediction == 1 else team2
        win_probability = max(probabilities) * 100
        
        # Save prediction to DB
        match_pred = MatchPrediction(
            team1=team1,
            team2=team2,
            venue=venue,
            toss_winner=toss_winner,
            toss_decision=toss_decision,
            predicted_winner=predicted_winner,
            win_probability=win_probability,
            team1_probability=probabilities[1] * 100 if len(probabilities) > 1 else 50,
            team2_probability=probabilities[0] * 100 if len(probabilities) > 0 else 50,
            model_used='Random Forest',
            confidence_score=max(probabilities)
        )
        
        db.session.add(match_pred)
        db.session.commit()
        
        return jsonify({
            'prediction_id': match_pred.id,
            'team1': team1,
            'team2': team2,
            'predicted_winner': predicted_winner,
            'win_probability': round(win_probability, 2),
            'team1_probability': round(probabilities[1] * 100 if len(probabilities) > 1 else 50, 2),
            'team2_probability': round(probabilities[0] * 100 if len(probabilities) > 0 else 50, 2),
            'confidence': round(max(probabilities), 4)
        }), 200
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': 'Prediction failed', 'details': str(e)}), 500

@api_bp.route('/predictions/match/<int:prediction_id>', methods=['GET'])
def get_match_prediction(prediction_id):
    """Get specific match prediction."""
    try:
        prediction = MatchPrediction.query.get(prediction_id)
        
        if not prediction:
            return jsonify({'error': 'Prediction not found'}), 404
        
        return jsonify({
            'id': prediction.id,
            'team1': prediction.team1,
            'team2': prediction.team2,
            'venue': prediction.venue,
            'predicted_winner': prediction.predicted_winner,
            'win_probability': prediction.win_probability,
            'model_used': prediction.model_used,
            'prediction_time': prediction.prediction_time.isoformat(),
            'actual_winner': prediction.actual_winner,
            'accuracy': prediction.prediction_accuracy
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching prediction: {e}")
        return jsonify({'error': 'Failed to fetch prediction'}), 500

@api_bp.route('/predictions/match/history', methods=['GET'])
def get_match_predictions_history():
    """Get match predictions history."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        predictions = MatchPrediction.query.order_by(
            MatchPrediction.prediction_time.desc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'total': predictions.total,
            'pages': predictions.pages,
            'current_page': page,
            'predictions': [{
                'id': p.id,
                'team1': p.team1,
                'team2': p.team2,
                'predicted_winner': p.predicted_winner,
                'win_probability': p.win_probability,
                'prediction_time': p.prediction_time.isoformat()
            } for p in predictions.items]
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({'error': 'Failed to fetch predictions'}), 500

# ==================== PLAYER PREDICTIONS ====================

@api_bp.route('/predictions/player', methods=['POST'])
def predict_player_performance():
    """Predict player performance."""
    try:
        data = request.get_json()
        
        required_fields = ['player_name', 'player_team', 'opposition_team']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Load model
        model_path = 'models/player_performance_model.pkl'
        if not os.path.exists(model_path):
            return jsonify({'error': 'Player model not found'}), 500
        
        model = joblib.load(model_path)
        
        # Create feature vector (simplified)
        features = [[0.5, 0.6, 100, 50]]
        
        # Predict
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0]
        
        categories = ['Low', 'Medium', 'High']
        predicted_category = categories[prediction] if prediction < len(categories) else 'Medium'
        confidence = max(probability)
        
        # Save to DB
        player_pred = PlayerPrediction(
            player_name=data['player_name'],
            player_team=data['player_team'],
            opposition_team=data['opposition_team'],
            venue=data.get('venue', 'Unknown'),
            predicted_category=predicted_category,
            model_used='Random Forest',
            confidence_score=confidence
        )
        
        db.session.add(player_pred)
        db.session.commit()
        
        return jsonify({
            'prediction_id': player_pred.id,
            'player_name': data['player_name'],
            'predicted_category': predicted_category,
            'confidence': round(confidence, 4)
        }), 200
    
    except Exception as e:
        logger.error(f"Player prediction error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

# ==================== STATS & ANALYTICS ====================

@api_bp.route('/stats/teams', methods=['GET'])
def get_team_stats():
    """Get all team statistics."""
    try:
        teams = TeamStats.query.all()
        
        return jsonify({
            'total_teams': len(teams),
            'teams': [{
                'team_name': t.team_name,
                'total_matches': t.total_matches,
                'wins': t.wins,
                'losses': t.losses,
                'win_percentage': round(t.win_percentage, 2),
                'home_win_percentage': round(t.home_wins / t.home_matches if t.home_matches > 0 else 0, 2)
            } for t in teams]
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching team stats: {e}")
        return jsonify({'error': 'Failed to fetch stats'}), 500

@api_bp.route('/stats/model-performance', methods=['GET'])
def model_performance():
    """Get model performance metrics."""
    try:
        total_predictions = MatchPrediction.query.count()
        accurate_predictions = MatchPrediction.query.filter_by(prediction_accuracy=True).count()
        
        accuracy = (accurate_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        return jsonify({
            'total_predictions': total_predictions,
            'accurate_predictions': accurate_predictions,
            'accuracy_percentage': round(accuracy, 2)
        }), 200
    
    except Exception as e:
        logger.error(f"Error calculating model performance: {e}")
        return jsonify({'error': 'Failed to calculate performance'}), 500

# ==================== HEALTH CHECK ====================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check."""
    return jsonify({
        'status': 'healthy',
        'message': 'IPL Prediction API is running'
    }), 200
