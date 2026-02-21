from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    nom           = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    confirme      = db.Column(db.Boolean, default=False)   # email confirmé
    actif         = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # RGPD
    rgpd_consent      = db.Column(db.Boolean, default=False)
    rgpd_consent_date = db.Column(db.DateTime, nullable=True)

    # Flags spéciaux
    parcoursup_2026   = db.Column(db.Boolean, default=False)  # inscrit via formulaire urgence

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # --- Tokens sécurisés ---
    def get_token(self, salt='email-confirm'):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt=salt)

    @staticmethod
    def verify_token(token, salt='email-confirm', max_age=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt=salt, max_age=max_age)
        except Exception:
            return None
        return User.query.filter_by(email=email).first()

    def __repr__(self):
        return f'<User {self.email}>'

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
