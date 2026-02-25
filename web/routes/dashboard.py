from flask import Blueprint, render_template, request, jsonify
from web.models import (MatchPrediction, PlayerPrediction, TeamStats, 
                        Match, PlayerStats, VenueStats)
from web.app import db, cache
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

dash_bp = Blueprint('dashboard', __name__)

# ==================== DASHBOARD MAIN ====================

@dash_bp.route('/dashboard', methods=['GET'])
@cache.cached(timeout=300)
def dashboard():
    """Main dashboard page."""
    try:
        # Overall statistics
        total_predictions = MatchPrediction.query.count()
        accurate_predictions = MatchPrediction.query.filter_by(
            prediction_accuracy=True
        ).count()
        
        accuracy = (accurate_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        # Recent predictions
        recent_predictions = MatchPrediction.query.order_by(
            MatchPrediction.prediction_time.desc()
        ).limit(5).all()
        
        # Get team stats
        teams_data = TeamStats.query.all()
        
        # Top performers
        top_players = PlayerStats.query.order_by(
            PlayerStats.batting_average.desc()
        ).limit(10).all()
        
        # Win probability distribution
        predictions_data = MatchPrediction.query.all()
        win_prob_data = {
            'high': len([p for p in predictions_data if p.win_probability >= 70]),
            'medium': len([p for p in predictions_data if 50 <= p.win_probability < 70]),
            'low': len([p for p in predictions_data if p.win_probability < 50])
        }
        
        return render_template(
            'dashboard.html',
            total_predictions=total_predictions,
            accuracy=round(accuracy, 2),
            recent_predictions=recent_predictions,
            teams=teams_data,
            top_players=top_players,
            win_prob_data=win_prob_data
        )
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', error="Error loading dashboard")

# ==================== ANALYTICS ====================

@dash_bp.route('/analytics/models', methods=['GET'])
@cache.cached(timeout=600)
def model_analytics():
    """Model performance analytics."""
    try:
        models = db.session.query(
            MatchPrediction.model_used,
            func.count(MatchPrediction.id).label('total'),
            func.sum(func.cast(MatchPrediction.prediction_accuracy, db.Integer)).label('correct')
        ).group_by(MatchPrediction.model_used).all()
        
        model_data = []
        for model, total, correct in models:
            accuracy = (correct / total * 100) if total > 0 else 0
            model_data.append({
                'model': model,
                'total': total,
                'correct': correct or 0,
                'accuracy': round(accuracy, 2)
            })
        
        return render_template('model_analytics.html', models=model_data)
    
    except Exception as e:
        logger.error(f"Model analytics error: {e}")
        return render_template('model_analytics.html', error="Error loading analytics")

@dash_bp.route('/analytics/teams', methods=['GET'])
@cache.cached(timeout=600)
def team_analytics():
    """Team performance analytics."""
    try:
        teams = TeamStats.query.all()
        
        team_data = []
        for team in teams:
            team_data.append({
                'name': team.team_name,
                'matches': team.total_matches,
                'wins': team.wins,
                'losses': team.losses,
                'win_rate': team.win_percentage,
                'home_win_rate': (team.home_wins / team.home_matches * 100) if team.home_matches > 0 else 0
            })
        
        return render_template('team_analytics.html', teams=team_data)
    
    except Exception as e:
        logger.error(f"Team analytics error: {e}")
        return render_template('team_analytics.html', error="Error loading analytics")

@dash_bp.route('/analytics/venues', methods=['GET'])
@cache.cached(timeout=600)
def venue_analytics():
    """Venue-based analytics."""
    try:
        venues = VenueStats.query.all()
        
        venue_data = []
        for venue in venues:
            venue_data.append({
                'name': venue.venue_name,
                'city': venue.city,
                'matches': venue.total_matches,
                'avg_runs': round(venue.avg_runs, 2),
                'home_win_rate': venue.home_win_percentage
            })
        
        return render_template('venue_analytics.html', venues=venue_data)
    
    except Exception as e:
        logger.error(f"Venue analytics error: {e}")
        return render_template('venue_analytics.html', error="Error loading analytics")

# ==================== API DATA ====================

@dash_bp.route('/api/chart/win-probability', methods=['GET'])
def chart_win_probability():
    """Get win probability data for chart."""
    try:
        predictions = MatchPrediction.query.all()
        
        data = {
            'labels': [],
            'data': []
        }
        
        # Create bins
        bins = [0, 50, 60, 70, 80, 90, 100]
        bin_names = ['<50%', '50-60%', '60-70%', '70-80%', '80-90%', '90%+']
        
        for i, bin_name in enumerate(bin_names):
            if i == 0:
                count = len([p for p in predictions if p.win_probability < 50])
            elif i == len(bin_names) - 1:
                count = len([p for p in predictions if p.win_probability >= 90])
            else:
                count = len([p for p in predictions if bins[i] <= p.win_probability < bins[i+1]])
            
            data['labels'].append(bin_name)
            data['data'].append(count)
        
        return jsonify(data), 200
    
    except Exception as e:
        logger.error(f"Chart error: {e}")
        return jsonify({'error': 'Error loading chart'}), 500

@dash_bp.route('/api/chart/team-performance', methods=['GET'])
def chart_team_performance():
    """Get team performance data for chart."""
    try:
        teams = TeamStats.query.limit(8).all()
        
        data = {
            'labels': [t.team_name for t in teams],
            'wins': [t.wins for t in teams],
            'losses': [t.losses for t in teams]
        }
        
        return jsonify(data), 200
    
    except Exception as e:
        logger.error(f"Chart error: {e}")
        return jsonify({'error': 'Error loading chart'}), 500

@dash_bp.route('/api/chart/prediction-accuracy', methods=['GET'])
def chart_prediction_accuracy():
    """Get prediction accuracy trend."""
    try:
        predictions = MatchPrediction.query.order_by(
            MatchPrediction.prediction_time
        ).all()
        
        # Calculate rolling accuracy
        labels = []
        accuracies = []
        window_size = 10
        
        for i in range(window_size, len(predictions)):
            window = predictions[i-window_size:i]
            correct = sum(1 for p in window if p.prediction_accuracy)
            accuracy = (correct / window_size * 100)
            
            labels.append(predictions[i].prediction_time.strftime('%Y-%m-%d'))
            accuracies.append(round(accuracy, 2))
        
        return jsonify({
            'labels': labels[-20:],  # Last 20 points
            'data': accuracies[-20:]
        }), 200
    
    except Exception as e:
        logger.error(f"Chart error: {e}")
        return jsonify({'error': 'Error loading chart'}), 500

@dash_bp.route('/api/chart/player-performance', methods=['GET'])
def chart_player_performance():
    """Get top player performance data."""
    try:
        players = PlayerStats.query.order_by(
            PlayerStats.batting_average.desc()
        ).limit(10).all()
        
        data = {
            'labels': [p.player_name for p in players],
            'average': [round(p.batting_average, 2) for p in players],
            'strike_rate': [round(p.strike_rate, 2) for p in players]
        }
        
        return jsonify(data), 200
    
    except Exception as e:
        logger.error(f"Chart error: {e}")
        return jsonify({'error': 'Error loading chart'}), 500

# ==================== COMPARISON ====================

@dash_bp.route('/comparison/teams', methods=['GET', 'POST'])
def team_comparison():
    """Compare teams."""
    try:
        teams = TeamStats.query.all()
        comparison_data = None
        
        if request.method == 'POST':
            team1 = request.form.get('team1')
            team2 = request.form.get('team2')
            
            t1 = TeamStats.query.filter_by(team_name=team1).first()
            t2 = TeamStats.query.filter_by(team_name=team2).first()
            
            if t1 and t2:
                comparison_data = {
                    'team1': {
                        'name': t1.team_name,
                        'matches': t1.total_matches,
                        'wins': t1.wins,
                        'win_rate': t1.win_percentage,
                        'home_wins': t1.home_wins,
                        'away_wins': t1.away_wins
                    },
                    'team2': {
                        'name': t2.team_name,
                        'matches': t2.total_matches,
                        'wins': t2.wins,
                        'win_rate': t2.win_percentage,
                        'home_wins': t2.home_wins,
                        'away_wins': t2.away_wins
                    }
                }
        
        return render_template(
            'team_comparison.html',
            teams=[t.team_name for t in teams],
            comparison=comparison_data
        )
    
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return render_template('team_comparison.html', error="Error loading comparison")
