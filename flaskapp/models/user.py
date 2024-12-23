from firebase_admin import firestore
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, firebase_uid, email, data=None):
        self.firebase_uid = firebase_uid
        self.email = email
        self.data = data or {}
        self._id = firebase_uid  # For Flask-Login

    def get_id(self):
        """Required by Flask-Login"""
        return self.firebase_uid

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'firebase_uid': self.firebase_uid,
            'email': self.email,
            **self.data
        }

    @staticmethod
    def get_by_firebase_uid(firebase_uid):
        """Get user by Firebase UID"""
        db = firestore.client()
        doc_ref = db.collection('users').document(firebase_uid)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return User(firebase_uid, data.get('email'), data)
        return None

    @staticmethod
    def create_user(firebase_uid, email):
        """Create a new user in Firestore"""
        db = firestore.client()
        user_ref = db.collection('users').document(firebase_uid)
        user_data = {
            'firebase_uid': firebase_uid,
            'email': email,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        user_ref.set(user_data)
        return User(firebase_uid, email, user_data)

    def save_message(self, message, ai_response, request_id, thread_id=None, audio_url=None):
        """Save chat messages to the conversation thread"""
        db = firestore.client()
        messages_ref = db.collection('users').document(self.firebase_uid).collection('messages')
        
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())

        # Save user message
        user_message = {
            'content': message,
            'type': 'user',
            'request_id': request_id,
            'timestamp': datetime.utcnow(),
            'user_id': self.firebase_uid,
            'thread_id': thread_id,
            'audio_url': audio_url
        }
        messages_ref.add(user_message)
        
        # Save AI response
        ai_message = {
            'content': ai_response,
            'type': 'ai',
            'request_id': request_id,
            'timestamp': datetime.utcnow(),
            'user_id': self.firebase_uid,
            'thread_id': thread_id
        }
        messages_ref.add(ai_message)

    def get_chat_history(self, limit=50, thread_id=None):
        """Get user's chat history"""
        db = firestore.client()
        messages_ref = (db.collection('users')
                       .document(self.firebase_uid)
                       .collection('messages')
                       .order_by('timestamp', direction=firestore.Query.DESCENDING))
        
        if thread_id:
            messages_ref = messages_ref.where('thread_id', '==', thread_id)

        messages_ref = messages_ref.limit(limit)
        
        messages = []
        for doc in messages_ref.stream():
            message_data = doc.to_dict()
            message_data['id'] = doc.id
            messages.append(message_data)
        
        return messages

    def update_profile(self, data):
        """Update user profile data"""
        db = firestore.client()
        user_ref = db.collection('users').document(self.firebase_uid)
        
        update_data = {
            **data,
            'updated_at': datetime.utcnow()
        }
        
        user_ref.update(update_data)
        self.data.update(update_data)
