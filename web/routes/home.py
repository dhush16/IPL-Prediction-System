from flask import Blueprint, render_template, jsonify
from web.models import MatchPrediction, TeamStats
from web.app import cache
import logging

logger = logging.getLogger(__name__)

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    """Home page with statistics overview."""
    try:
        # Get statistics
        total_predictions = MatchPrediction.query.count()
        accurate_predictions = MatchPrediction.query.filter_by(
            prediction_accuracy=True
        ).count()
        
        accuracy = (accurate_predictions / total_predictions * 100) if total_predictions > 0 else 0
        total_teams = TeamStats.query.count()
        
        # Recent predictions
        recent_predictions = MatchPrediction.query.order_by(
            MatchPrediction.prediction_time.desc()
        ).limit(5).all()
        
        stats = {
            'total_predictions': total_predictions,
            'accuracy': round(accuracy, 2),
            'total_teams': total_teams
        }
        
        return render_template(
            'index.html',
            stats=stats,
            recent_predictions=recent_predictions
        )
    
    except Exception as e:
        logger.error(f"Home page error: {e}")
        return render_template('index.html', error="Error loading page")

@home_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@home_bp.route('/api/stats', methods=['GET'])
@cache.cached(timeout=300)
def get_stats():
    """API endpoint for statistics."""
    try:
        total_predictions = MatchPrediction.query.count()
        accurate = MatchPrediction.query.filter_by(prediction_accuracy=True).count()
        
        return jsonify({
            'total_predictions': total_predictions,
            'accurate_predictions': accurate,
            'accuracy': round((accurate / total_predictions * 100), 2) if total_predictions > 0 else 0
        }), 200
    
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({'error': 'Error fetching stats'}), 500
