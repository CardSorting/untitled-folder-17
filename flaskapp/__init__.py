from flask import Flask, request
from flask_login import LoginManager
from .config import Config
import os
from redis import Redis
from .firebase import init_firebase
from datetime import datetime

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.get_by_firebase_uid(user_id)

def create_app(config_class=Config):
    app = Flask(__name__, 
                static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
    app.config['SERVER_NAME'] = None
    app.config.from_object(config_class)

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Initialize Firebase Admin SDK
    init_firebase(app)

    # Add CSP nonce to each request
    @app.before_request
    def add_csp_nonce():
        request.csp_nonce = os.urandom(16).hex()

    # Add template helper for CSP nonce
    @app.context_processor
    def utility_processor():
        return dict(get_csp_nonce=lambda: getattr(request, 'csp_nonce', ''))

    # Add template context processor for current datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        nonce = getattr(request, 'csp_nonce', '')
        firebase_domain = app.config.get('FIREBASE_AUTH_DOMAIN', 'irlmbm.firebaseapp.com')
        
        csp = '; '.join([
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' 'unsafe-inline' 'unsafe-eval' https://apis.google.com https://*.firebaseio.com https://{firebase_domain} https://www.gstatic.com https://cdn.tailwindcss.com https://*.googleapis.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            f"frame-src 'self' https://{firebase_domain} https://accounts.google.com",
            "img-src 'self' data: https: blob:",
            f"connect-src 'self' https://*.googleapis.com https://{firebase_domain} https://identitytoolkit.googleapis.com https://*.firebaseio.com wss://*.firebaseio.com https://securetoken.googleapis.com",
            "media-src 'self' blob:",
            "object-src 'none'"
        ])
        
        response.headers['Content-Security-Policy'] = csp
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        
        # CORS headers for Firebase
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Allow-Origin'] = f'https://{firebase_domain}'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

    # Initialize Redis
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.chat_redis = Redis.from_url(app.config['CHAT_REDIS_URL'])

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.companion import companion_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(companion_bp)

    # Create temp directory for audio files
    temp_dir = os.path.join(app.static_folder, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    return app
