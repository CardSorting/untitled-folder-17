from functools import wraps
from flask import make_response, current_app

def set_security_headers():
    """Set security headers for the application."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            
            # Get Firebase domain from config
            firebase_domain = current_app.config.get('FIREBASE_AUTH_DOMAIN', 'irlmbm.firebaseapp.com')
            
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://apis.google.com https://*.firebaseio.com "
                f"https://{firebase_domain} https://www.gstatic.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                f"frame-src 'self' https://{firebase_domain} https://accounts.google.com; "
                "img-src 'self' data: https: blob:; "
                "connect-src 'self' https://*.googleapis.com "
                f"https://{firebase_domain} "
                "https://identitytoolkit.googleapis.com "
                "https://*.firebaseio.com "
                "wss://*.firebaseio.com "
                "https://securetoken.googleapis.com; "
                "media-src 'self' blob:; "
                "object-src 'none';"
            )
            
            # Set security headers
            resp.headers['Content-Security-Policy'] = csp
            resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
            resp.headers['X-Content-Type-Options'] = 'nosniff'
            resp.headers['X-XSS-Protection'] = '1; mode=block'
            
            # CORS headers
            resp.headers['Access-Control-Allow-Origin'] = f'https://{firebase_domain}'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            resp.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
            
            return resp
        return decorated_function
    return decorator
