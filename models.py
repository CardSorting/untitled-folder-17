from flask import current_app
from flask_sqlalchemy import SQLAlchemy

def get_db():
    return current_app.extensions['sqlalchemy'].db

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
