from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app import db, mail
from app.models.user import User
from datetime import datetime

bp = Blueprint('auth', __name__)

# ─── Inscription ────────────────────────────────────────────────────

@bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if current_user.is_authenticated:
        return redirect(url_for('membres.tableau_bord'))

    if request.method == 'POST':
        nom      = request.form.get('nom', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        consent  = request.form.get('rgpd_consent')

        # Validations
        if not all([nom, email, password, confirm]):
            flash('Tous les champs sont obligatoires.', 'danger')
            return render_template('auth/inscription.html', title='Inscription')

        if password != confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('auth/inscription.html', title='Inscription')

        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
            return render_template('auth/inscription.html', title='Inscription')

        if not consent:
            flash('Vous devez accepter la politique de confidentialité (RGPD).', 'danger')
            return render_template('auth/inscription.html', title='Inscription')

        if User.query.filter_by(email=email).first():
            flash('Cette adresse email est déjà utilisée.', 'danger')
            return render_template('auth/inscription.html', title='Inscription')

        # Création du compte
        user = User(
            nom=nom,
            email=email,
            rgpd_consent=True,
            rgpd_consent_date=datetime.utcnow()
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Envoi email de confirmation
        token = user.get_token(salt='email-confirm')
        confirm_url = url_for('auth.confirmer_email', token=token, _external=True)

        try:
            msg = Message(
                subject='[LeBonCap] Confirmez votre adresse email',
                recipients=[email],
                html=render_template('emails/confirmation.html',
                                     nom=nom, confirm_url=confirm_url)
            )
            mail.send(msg)
            flash('Inscription réussie ! Vérifiez votre email pour activer votre compte.', 'success')
        except Exception:
            flash('Compte créé mais email de confirmation non envoyé. Contactez-nous.', 'warning')

        return redirect(url_for('auth.login'))

    return render_template('auth/inscription.html', title='Inscription')


# ─── Confirmation email ─────────────────────────────────────────────

@bp.route('/confirmer/<token>')
def confirmer_email(token):
    user = User.verify_token(token, salt='email-confirm', max_age=86400)
    if not user:
        flash('Lien de confirmation invalide ou expiré.', 'danger')
        return redirect(url_for('auth.inscription'))

    if user.confirme:
        flash('Votre compte est déjà confirmé.', 'info')
    else:
        user.confirme = True
        db.session.commit()
        flash('Email confirmé ! Vous pouvez maintenant vous connecter.', 'success')

    return redirect(url_for('auth.login'))


# ─── Connexion ──────────────────────────────────────────────────────

@bp.route('/connexion', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('membres.tableau_bord'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Email ou mot de passe incorrect.', 'danger')
            return render_template('auth/login.html', title='Connexion')

        if not user.confirme:
            flash('Veuillez confirmer votre email avant de vous connecter.', 'warning')
            return render_template('auth/login.html', title='Connexion')

        login_user(user, remember=bool(remember))
        next_page = request.args.get('next')
        flash(f'Bienvenue {user.nom} !', 'success')
        return redirect(next_page or url_for('membres.tableau_bord'))

    return render_template('auth/login.html', title='Connexion')


# ─── Déconnexion ────────────────────────────────────────────────────

@bp.route('/deconnexion')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('public.accueil'))


# ─── Mot de passe oublié ────────────────────────────────────────────

@bp.route('/mot-de-passe-oublie', methods=['GET', 'POST'])
def mot_de_passe_oublie():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()

        if user:
            token = user.get_token(salt='reset-password')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                msg = Message(
                    subject='[LeBonCap] Réinitialisation de votre mot de passe',
                    recipients=[email],
                    html=render_template('emails/reset_mdp.html',
                                         nom=user.nom, reset_url=reset_url)
                )
                mail.send(msg)
            except Exception:
                pass

        # Toujours afficher ce message (sécurité : ne pas révéler si l'email existe)
        flash('Si cet email existe, un lien de réinitialisation vous a été envoyé.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/mot_de_passe_oublie.html', title='Mot de passe oublié')


# ─── Reset mot de passe ─────────────────────────────────────────────

@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_token(token, salt='reset-password', max_age=3600)
    if not user:
        flash('Lien invalide ou expiré.', 'danger')
        return redirect(url_for('auth.mot_de_passe_oublie'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
            return render_template('auth/reset_password.html', title='Nouveau mot de passe')

        if password != confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('auth/reset_password.html', title='Nouveau mot de passe')

        user.set_password(password)
        db.session.commit()
        flash('Mot de passe modifié avec succès !', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', title='Nouveau mot de passe')


# ─── Suppression compte (RGPD) ──────────────────────────────────────

@bp.route('/supprimer-mon-compte', methods=['POST'])
@login_required
def supprimer_compte():
    user = current_user
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('Votre compte a été supprimé définitivement.', 'info')
    return redirect(url_for('public.accueil'))
