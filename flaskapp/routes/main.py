from flask import Blueprint, render_template
from flask_login import current_user
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Render the home page."""
    return render_template('main/home.html', 
                         current_user=current_user,
                         now=datetime.utcnow())

@main_bp.route('/providers')
def providers():
    """Render the providers page."""
    return render_template('main/providers.html',
                           current_user=current_user,
                           now=datetime.utcnow())
