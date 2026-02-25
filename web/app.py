from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from web.config import DevelopmentConfig

db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    
    # Register Blueprints
    from web.routes.home import home_bp
    from web.routes.prediction import pred_bp
    from web.routes.dashboard import dash_bp
    from web.routes.api import api_bp
    
    app.register_blueprint(home_bp)
    app.register_blueprint(pred_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Global Error Handling
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
        
    return app
