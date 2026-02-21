import click
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

    # ─── Commandes CLI ──────────────────────────────────────────
    @app.cli.command('make-admin')
    @click.argument('email')
    def make_admin(email):
        """Passe un utilisateur en rôle ADMIN. Usage : flask make-admin email@example.com"""
        from app.models.user import User
        user = User.query.filter_by(email=email).first()
        if not user:
            click.echo(f'❌  Aucun utilisateur trouvé avec l\'email : {email}')
            return
        user.role = 'admin'
        db.session.commit()
        click.echo(f'✅  {user.nom} ({email}) est maintenant ADMIN.')

    @app.cli.command('remove-admin')
    @click.argument('email')
    def remove_admin(email):
        """Retire le rôle ADMIN d'un utilisateur. Usage : flask remove-admin email@example.com"""
        from app.models.user import User
        user = User.query.filter_by(email=email).first()
        if not user:
            click.echo(f'❌  Aucun utilisateur trouvé avec l\'email : {email}')
            return
        user.role = 'user'
        db.session.commit()
        click.echo(f'✅  {user.nom} ({email}) n\'est plus admin.')

    @app.cli.command('list-users')
    def list_users():
        """Liste tous les utilisateurs. Usage : flask list-users"""
        from app.models.user import User
        users = User.query.order_by(User.created_at.desc()).all()
        if not users:
            click.echo('Aucun utilisateur.')
            return
        click.echo(f'\n{"ID":<5} {"Nom":<25} {"Email":<35} {"Rôle":<8} {"Confirmé":<10} {"Date"}')
        click.echo('─' * 95)
        for u in users:
            click.echo(
                f'{u.id:<5} {u.nom[:24]:<25} {u.email[:34]:<35} '
                f'{u.role:<8} {"✅" if u.confirme else "❌":<10} '
                f'{u.created_at.strftime("%d/%m/%Y %H:%M")}'
            )
        click.echo(f'\nTotal : {len(users)} utilisateur(s)\n')

    return app
