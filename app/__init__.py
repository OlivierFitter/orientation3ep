from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config

db      = SQLAlchemy()
login   = LoginManager()
mail    = Mail()
migrate = Migrate()

login.login_view        = 'auth.login'
login.login_message     = 'Veuillez vous connecter pour accéder à cette page.'
login.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init extensions
    db.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Blueprints
    from app.routes.public  import bp as public_bp
    from app.routes.auth    import bp as auth_bp
    from app.routes.membres import bp as membres_bp
    from app.routes.admin   import bp as admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp,    url_prefix='/auth')
    app.register_blueprint(membres_bp, url_prefix='/membres')
    app.register_blueprint(admin_bp)

    # Jinja globals utiles
    app.jinja_env.globals.update(enumerate=enumerate)

    # Création des tables si nécessaire
    with app.app_context():
        db.create_all()

    return app
