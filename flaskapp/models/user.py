from .. import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'firebase_uid': self.firebase_uid,
            'email': self.email
        }

    @staticmethod
    def get_by_firebase_uid(firebase_uid):
        return User.query.filter_by(firebase_uid=firebase_uid).first()

    @staticmethod
    def create_user(firebase_uid, email):
        user = User(firebase_uid=firebase_uid, email=email)
        db.session.add(user)
        db.session.commit()
        return user
