from flask import Flask, request
from flask_login import LoginManager
from .config import Config
import os
from redis import Redis

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.get_by_firebase_uid(user_id)

def create_app(config_class=Config):
    app = Flask(__name__, 
                static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
    app.config.from_object(config_class)

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Add CSP nonce to each request
    @app.before_request
    def add_csp_nonce():
        request.csp_nonce = os.urandom(16).hex()

    # Add Content Security Policy headers
    @app.after_request
    def add_security_headers(response):
        nonce = getattr(request, 'csp_nonce', '')
        
        csp = {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                f"'nonce-{nonce}'",
                "'unsafe-eval'",
                "https://cdn.tailwindcss.com",
                "https://www.gstatic.com",
                "https://*.googleapis.com",
                "https://apis.google.com"
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",
                "https://fonts.googleapis.com",
                "https://cdn.tailwindcss.com"
            ],
            'font-src': [
                "'self'",
                "data:",
                "https://fonts.gstatic.com"
            ],
            'img-src': ["'self'", "data:", "https:"],
            'connect-src': [
                "'self'", 
                "https://*.googleapis.com",
                "https://www.googleapis.com",
                "https://apis.google.com",
                "https://*.firebaseapp.com",
                "https://*.firebase.com"
            ],
            'frame-src': [
                "'self'",
                "https://apis.google.com",
                "https://*.firebaseapp.com",
                "https://*.firebase.com"
            ],
            'worker-src': ["'self'", "blob:"],
            'child-src': ["'self'", "blob:"],
            'form-action': ["'self'"],
            'base-uri': ["'self'"],
            'object-src': ["'none'"]
        }
        
        # Build the CSP header string
        csp_string = '; '.join(f"{key} {' '.join(values)}" for key, values in csp.items())
        response.headers['Content-Security-Policy'] = csp_string
        
        # Add SameSite cookie policy
        if 'Set-Cookie' in response.headers:
            response.headers['Set-Cookie'] += '; SameSite=Lax'
        
        return response

    # Initialize Redis
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.chat_redis = Redis.from_url(app.config['CHAT_REDIS_URL'])

    # Initialize Firebase
    from .utils.firebase import initialize_firebase
    initialize_firebase(app.config)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.companion import companion_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(companion_bp)

    @app.context_processor
    def utility_processor():
        def get_csp_nonce():
            return getattr(request, 'csp_nonce', '')
        return dict(now=Config.now, get_csp_nonce=get_csp_nonce)

    # Create temp directory for audio files
    temp_dir = os.path.join(app.static_folder, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    return app
