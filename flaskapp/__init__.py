from flask import Flask
from flask_login import LoginManager
from .config import Config
import os

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
        return dict(now=Config.now)

    # Create temp directory for audio files
    temp_dir = os.path.join(app.static_folder, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    return app
