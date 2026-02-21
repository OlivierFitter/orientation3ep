from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_mail import Message
from app import mail, db
from app.models.user import User

bp = Blueprint('public', __name__)

# ─── Pages publiques ────────────────────────────────────────────────

@bp.route('/')
def accueil():
    return render_template('accueil.html', title='Accueil')

@bp.route('/comment-orienter')
def comment_orienter():
    return render_template('comment_orienter.html', title='Comment orienter ?')

@bp.route('/prestations')
def prestations():
    return render_template('prestations.html', title='Les Prestations')

@bp.route('/rencontres')
def rencontres():
    return render_template('rencontres.html', title='Rencontres')

@bp.route('/blog')
def blog():
    return render_template('blog.html', title='Le Blog')

@bp.route('/faq')
def faq():
    return render_template('faq.html', title='FAQ')

@bp.route('/qui-suis-je')
def qui_suis_je():
    return render_template('qui_suis_je.html', title="Qui suis-je ?")

@bp.route('/fil-actualite')
def fil_actualite():
    return render_template('fil_actualite.html', title="Fil d'actualité")

@bp.route('/mentions-legales')
def mentions_legales():
    return render_template('mentions_legales.html', title='Mentions légales')

@bp.route('/politique-confidentialite')
def politique_confidentialite():
    return render_template('politique_confidentialite.html', title='Politique de confidentialité')

# ─── Formulaire de contact ──────────────────────────────────────────

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        nom     = request.form.get('nom', '').strip()
        email   = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        consent = request.form.get('rgpd_consent')

        if not all([nom, email, message]):
            flash('Merci de remplir tous les champs obligatoires.', 'danger')
            return render_template('contact.html', title='Question courte')

        if len(message) > 1000:
            flash('Votre question dépasse 1000 caractères.', 'danger')
            return render_template('contact.html', title='Question courte')

        if not consent:
            flash('Vous devez accepter la politique de confidentialité.', 'danger')
            return render_template('contact.html', title='Question courte')

        try:
            msg = Message(
                subject=f'[LeBonCap] Question courte — {nom}',
                recipients=[current_app.config['CONTACT_MAIL']],
                reply_to=email,
                body=f"""
Nouvelle question courte depuis LeBonCap.net

Nom   : {nom}
Email : {email}

Question :
{message}
"""
            )
            mail.send(msg)
            flash('Votre question a bien été envoyée ! Je vous réponds rapidement.', 'success')
            return redirect(url_for('public.contact'))
        except Exception:
            flash('Erreur lors de l\'envoi. Veuillez réessayer ou utiliser WhatsApp.', 'danger')

    return render_template('contact.html', title='Question courte')


# ─── Formulaire Parcoursup 2026 ─────────────────────────────────────

@bp.route('/parcoursup-2026', methods=['GET', 'POST'])
def parcoursup_2026():
    from datetime import datetime, timezone

    if request.method == 'POST':
        nom      = request.form.get('nom', '').strip()
        email    = request.form.get('email', '').strip()
        question = request.form.get('question', '').strip()
        consent  = request.form.get('rgpd_consent')

        if not all([nom, email, question]):
            flash('Merci de remplir tous les champs obligatoires.', 'danger')
            return render_template('parcoursup_2026.html', title='Urgence Parcoursup 2026')

        if len(question) > 1000:
            flash('Votre question dépasse 1000 caractères.', 'danger')
            return render_template('parcoursup_2026.html', title='Urgence Parcoursup 2026')

        if not consent:
            flash('Vous devez accepter la politique de confidentialité.', 'danger')
            return render_template('parcoursup_2026.html', title='Urgence Parcoursup 2026')

        # Inscription automatique si l'email n'existe pas encore
        user = User.query.filter_by(email=email).first()
        inscrit = False
        if not user:
            import secrets
            from werkzeug.security import generate_password_hash
            tmp_pwd = secrets.token_hex(16)
            user = User(
                nom=nom,
                email=email,
                password_hash=generate_password_hash(tmp_pwd),
                confirme=False,
                actif=True,
                rgpd_consent=True,
                rgpd_consent_date=datetime.now(timezone.utc),
                parcoursup_2026=True
            )
            db.session.add(user)
            try:
                db.session.commit()
                inscrit = True
            except Exception:
                db.session.rollback()

        # Envoi du mail de notification
        try:
            msg = Message(
                subject=f'[LeBonCap] 🚨 Parcoursup 2026 — {nom}',
                recipients=[current_app.config['CONTACT_MAIL']],
                reply_to=email,
                body=f"""
🚨 Nouvelle question PARCOURSUP 2026 depuis LeBonCap.net
{'✅ Nouvel inscrit !' if inscrit else '(utilisateur déjà inscrit)'}

Nom   : {nom}
Email : {email}

Question :
{question}
"""
            )
            mail.send(msg)
        except Exception:
            pass  # Le mail est secondaire, l'inscription est prioritaire

        flash(
            '✅ Votre question a bien été reçue ! '
            + ('Vous êtes également inscrit(e) sur LeBonCap — vous recevrez nos conseils gratuits. ' if inscrit else '')
            + 'Je vous réponds au plus vite.',
            'success'
        )
        return redirect(url_for('public.parcoursup_2026'))

    return render_template('parcoursup_2026.html', title='Urgence Parcoursup 2026')
