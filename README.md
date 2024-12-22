# Flask Application with Firebase Authentication

A Flask application structured using industry-standard conventions, featuring Firebase authentication, SQLAlchemy for database management, and Jinja2 templates.

## Project Structure

```
flaskapp/
├── __init__.py          # Application factory
├── config.py            # Configuration management
├── models/              # Database models
│   ├── __init__.py
│   └── user.py
├── routes/              # Blueprint routes
│   ├── auth.py
│   └── main.py
├── templates/           # Jinja2 templates
│   ├── base.html
│   └── main/
│       └── home.html
├── static/              # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── utils/              # Utility functions
    └── firebase.py
```

## Features

- Modular application structure using Flask Blueprints
- Firebase Authentication integration
- SQLAlchemy database integration
- Jinja2 templating
- Separation of concerns (models, views, templates)
- Environment-based configuration
- Static asset management

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Firebase:
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
   - Download your Firebase Admin SDK service account key and save it in the `cred/` directory
   - Copy `.env.example` to `.env` and fill in your Firebase configuration:
     ```bash
     cp .env.example .env
     ```

5. Configure environment variables:
   - Edit `.env` with your Firebase Web SDK configuration
   - Add your Firebase Admin SDK credentials path
   - Set a secure SECRET_KEY

6. Initialize the database:
   ```bash
   flask db upgrade
   ```

7. Run the application:
   ```bash
   python run.py
   ```

## Development

- Models are defined in `flaskapp/models/`
- Routes are organized in blueprints in `flaskapp/routes/`
- Templates use Jinja2 inheritance from `base.html`
- Static files (CSS, JS) are in `flaskapp/static/`

## Authentication Flow

1. User clicks login button
2. Firebase Authentication popup appears
3. User authenticates with Google
4. Frontend receives Firebase ID token
5. Token is sent to backend `/auth` endpoint
6. Backend verifies token and creates/retrieves user
7. User session is established

## Environment Variables

Required environment variables (see `.env.example`):
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: Database connection URL
- `FIREBASE_CREDENTIALS_PATH`: Path to Firebase Admin SDK credentials
- `FIREBASE_API_KEY`: Firebase Web SDK API key
- `FIREBASE_AUTH_DOMAIN`: Firebase Auth domain
- `FIREBASE_PROJECT_ID`: Firebase project ID
- `FIREBASE_STORAGE_BUCKET`: Firebase storage bucket
- `FIREBASE_MESSAGING_SENDER_ID`: Firebase messaging sender ID
- `FIREBASE_APP_ID`: Firebase application ID
