import os
from datetime import timedelta

class Config:
    # --- Sécurité ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'changez-moi-en-production-clé-très-longue')

    # --- Base de données ---
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///leboncap.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Mail (Brevo SMTP) ---
    MAIL_SERVER   = 'smtp-relay.brevo.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('BREVO_LOGIN', '')       # votre login Brevo
    MAIL_PASSWORD = os.environ.get('BREVO_SMTP_KEY', '')    # clé SMTP Brevo
    MAIL_DEFAULT_SENDER = ('LeBonCap', 'noreply@leboncap.net')

    # --- Sessions ---
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # --- Tokens (confirmation mail, reset mdp) ---
    TOKEN_EXPIRATION_SECONDS = 3600   # 1 heure

    # --- Site ---
    SITE_NAME    = 'LeBonCap'
    SITE_URL     = os.environ.get('SITE_URL', 'http://localhost:5000')
    CONTACT_MAIL = 'olivierfitter@gmail.com'

    # --- Admin cron webhook token ---
    CRON_SECRET_TOKEN = os.environ.get('CRON_SECRET_TOKEN', '')

    # --- Correctif URL PostgreSQL (Render retourne parfois "postgres://") ---
    @classmethod
    def fix_database_url(cls):
        url = cls.SQLALCHEMY_DATABASE_URI
        if url and url.startswith('postgres://'):
            cls.SQLALCHEMY_DATABASE_URI = url.replace('postgres://', 'postgresql://', 1)
