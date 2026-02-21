import os
from datetime import timedelta

class Config:
    # --- Sécurité ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'changez-moi-en-production-clé-très-longue')

    # --- Base de données ---
    # Render fournit parfois "postgres://" au lieu de "postgresql://" (SQLAlchemy 1.4+)
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///leboncap.db')
    SQLALCHEMY_DATABASE_URI = _db_url.replace('postgres://', 'postgresql://', 1) if _db_url else _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Mail (Brevo SMTP) ---
    MAIL_SERVER   = 'smtp-relay.brevo.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('BREVO_LOGIN', '')       # votre login Brevo
    MAIL_PASSWORD = os.environ.get('BREVO_SMTP_KEY', '')    # clé SMTP Brevo
    MAIL_DEFAULT_SENDER = ('LeBonCap', 'contact@leboncap.org')

    # --- Sessions ---
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # --- Tokens (confirmation mail, reset mdp) ---
    TOKEN_EXPIRATION_SECONDS = 3600   # 1 heure

    # --- Site ---
    SITE_NAME    = 'LeBonCap'
    SITE_URL     = os.environ.get('SITE_URL', 'http://localhost:5000')
    CONTACT_MAIL = 'contact@leboncap.org'

    # --- Admin cron webhook token ---
    CRON_SECRET_TOKEN = os.environ.get('CRON_SECRET_TOKEN', '')

