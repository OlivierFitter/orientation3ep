from datetime import datetime, timezone
import secrets

from flask import (Blueprint, render_template, request, flash,
                   redirect, url_for, current_app)
from flask_mail import Message
from werkzeug.security import generate_password_hash

from app import mail, db
from app.models.user import User
from app.models.contact import ContactRequest, QuestionMessage, Parcoursup2026Message
from app.models.event import Event, EventRegistrationPublic

bp = Blueprint('public', __name__)


# ─── Setup admin one-shot (à supprimer après usage) ─────────────────

@bp.route('/setup-admin-olivierfitter-2025')
def setup_admin():
    """Route temporaire pour initialiser le compte admin sans Shell Render."""
    user = User.query.filter_by(email='olivierfitter@gmail.com').first()
    created = False
    if not user:
        user = User(
            nom='Olivier Fitter',
            email='olivierfitter@gmail.com',
            password_hash=generate_password_hash('LeBonCap2025!'),
            confirme=True,
            actif=True,
            role='admin',
            rgpd_consent=True,
            rgpd_consent_date=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(user)
        created = True
    else:
        user.password_hash = generate_password_hash('LeBonCap2025!')
        user.confirme = True
        user.actif    = True
        user.role     = 'admin'
    db.session.commit()
    action = "Compte créé et configuré" if created else "Compte mis à jour"
    return f'''
    <h2>✅ {action} !</h2>
    <p>Email : olivierfitter@gmail.com</p>
    <p>Mot de passe : <strong>LeBonCap2025!</strong></p>
    <p><a href="/auth/connexion">→ Se connecter maintenant</a></p>
    <p><em>⚠️ Pensez à changer votre mot de passe après connexion.</em></p>
    '''


# ─── Health check (diagnostic Render) ───────────────────────────────

@bp.route('/health')
def health():
    """Route de diagnostic — vérifie la connexion DB et les tables."""
    import sqlalchemy as sa
    from flask import jsonify
    status = {}
    try:
        result = db.session.execute(sa.text("SELECT 1")).scalar()
        status['db_ping'] = 'ok'
    except Exception as e:
        status['db_ping'] = f'ERROR: {e}'

    try:
        inspector = sa.inspect(db.engine)
        status['tables'] = sorted(inspector.get_table_names())
    except Exception as e:
        status['tables'] = f'ERROR: {e}'

    try:
        rev = db.session.execute(
            sa.text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar()
        status['alembic_version'] = rev or 'empty'
    except Exception as e:
        status['alembic_version'] = f'no table or error: {e}'

    try:
        user_count = db.session.execute(sa.text("SELECT COUNT(*) FROM users")).scalar()
        status['user_count'] = user_count
    except Exception as e:
        status['user_count'] = f'ERROR: {e}'

    return jsonify(status)


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


# ─── Rencontres publiques ────────────────────────────────────────────

@bp.route('/rencontres')
def rencontres():
    events = Event.query.filter_by(is_published=True).order_by(Event.date_event).all()
    return render_template('rencontres.html', title='Rencontres', events=events)


@bp.route('/rencontres/<int:id>')
def rencontre_detail(id):
    event = Event.query.filter_by(id=id, is_published=True).first_or_404()
    return render_template('rencontre_detail.html', title=event.titre, event=event)


@bp.route('/rencontres/<int:id>/inscrire', methods=['GET', 'POST'])
def rencontre_inscrire(id):
    event = Event.query.filter_by(id=id, is_published=True).first_or_404()

    if event.est_passe:
        flash('Cet événement est déjà passé.', 'warning')
        return redirect(url_for('public.rencontres'))

    if request.method == 'POST':
        nom       = request.form.get('nom', '').strip()
        email     = request.form.get('email', '').strip()
        telephone = request.form.get('telephone', '').strip()
        consent   = request.form.get('rgpd_consent')

        if not all([nom, email]):
            flash('Nom et email sont obligatoires.', 'danger')
            return render_template('rencontre_inscription.html', event=event)

        if not consent:
            flash('Vous devez accepter la politique de confidentialité.', 'danger')
            return render_template('rencontre_inscription.html', event=event)

        # Vérifier si déjà inscrit
        deja = EventRegistrationPublic.query.filter_by(
            event_id=id, email=email
        ).first()
        if deja and deja.status != 'cancelled':
            flash('Vous êtes déjà inscrit(e) à cette rencontre.', 'warning')
            return redirect(url_for('public.rencontres'))

        # Calcul du statut (confirmé ou liste d'attente)
        places = event.places_restantes
        statut = 'confirmed' if places > 0 else 'waitlist'

        reg = EventRegistrationPublic(
            event_id=id,
            nom=nom, email=email,
            telephone=telephone or None,
            status=statut,
            rgpd_consent=True
        )
        db.session.add(reg)
        db.session.commit()

        # Email de confirmation
        try:
            if statut == 'confirmed':
                sujet = f'✅ Inscription confirmée — {event.titre}'
                corps = f"""Bonjour {nom},

Votre inscription à la rencontre "{event.titre}" est confirmée !

📅 Date : {event.date_event.strftime('%A %d %B %Y à %Hh%M')}
{'🖥️ Mode : Visioconférence' if event.mode == 'visio' else f'📍 Lieu : {event.lieu or "à préciser"}'}
{'🔗 Lien de connexion : ' + (event.lieu or 'sera envoyé prochainement') if event.mode == 'visio' else ''}

Pour annuler votre inscription :
{url_for('public.rencontre_annuler', token=reg.token, _external=True)}

À bientôt !
Olivier Fitter — LeBonCap"""
            else:
                sujet = f'⏳ Liste d\'attente — {event.titre}'
                corps = f"""Bonjour {nom},

L'événement "{event.titre}" est complet, mais vous êtes inscrit(e) sur la liste d'attente.
Vous serez prévenu(e) par email si une place se libère.

Pour annuler votre demande :
{url_for('public.rencontre_annuler', token=reg.token, _external=True)}

Olivier Fitter — LeBonCap"""

            msg = Message(
                subject=sujet,
                recipients=[email],
                body=corps
            )
            mail.send(msg)
        except Exception:
            pass  # L'inscription est prioritaire, l'email est secondaire

        # Notification admin
        try:
            msg_admin = Message(
                subject=f'[LeBonCap] Nouvelle inscription — {event.titre}',
                recipients=[current_app.config['CONTACT_MAIL']],
                body=f"""Nouvelle inscription à "{event.titre}"
Nom    : {nom}
Email  : {email}
Tel    : {telephone or '-'}
Statut : {statut}
Places restantes : {event.places_restantes}"""
            )
            mail.send(msg_admin)
        except Exception:
            pass

        if statut == 'confirmed':
            flash(f'✅ Inscription confirmée ! Un email de confirmation vous a été envoyé.', 'success')
        else:
            flash('⏳ L\'événement est complet. Vous avez été ajouté(e) sur la liste d\'attente.', 'warning')
        return redirect(url_for('public.rencontres'))

    return render_template('rencontre_inscription.html', title=f'Inscription — {event.titre}', event=event)


@bp.route('/rencontres/annuler/<token>')
def rencontre_annuler(token):
    reg = EventRegistrationPublic.query.filter_by(token=token).first_or_404()
    if reg.status == 'cancelled':
        flash('Cette inscription est déjà annulée.', 'info')
        return redirect(url_for('public.rencontres'))

    reg.status = 'cancelled'
    db.session.commit()

    # Promouvoir le premier de la liste d'attente
    if reg.event.places_restantes > 0:
        premier_attente = EventRegistrationPublic.query.filter_by(
            event_id=reg.event_id, status='waitlist'
        ).order_by(EventRegistrationPublic.created_at).first()
        if premier_attente:
            premier_attente.status = 'confirmed'
            db.session.commit()
            try:
                msg = Message(
                    subject=f'✅ Place disponible — {reg.event.titre}',
                    recipients=[premier_attente.email],
                    body=f"""Bonne nouvelle {premier_attente.nom} !

Une place s'est libérée pour "{reg.event.titre}" — votre inscription est maintenant confirmée !

📅 Date : {reg.event.date_event.strftime('%A %d %B %Y à %Hh%M')}

Pour annuler :
{url_for('public.rencontre_annuler', token=premier_attente.token, _external=True)}

Olivier Fitter — LeBonCap"""
                )
                mail.send(msg)
            except Exception:
                pass

    flash('Votre inscription a bien été annulée.', 'success')
    return redirect(url_for('public.rencontres'))


# ─── Formulaire de recontact ─────────────────────────────────────────

@bp.route('/recontact', methods=['GET', 'POST'])
def recontact():
    if request.method == 'POST':
        nom       = request.form.get('nom', '').strip()
        email     = request.form.get('email', '').strip()
        telephone = request.form.get('telephone', '').strip()
        consent   = request.form.get('rgpd_consent')

        if not all([nom, email]):
            flash('Nom et email sont obligatoires.', 'danger')
            return render_template('recontact.html', title='Être recontacté.e')

        if not consent:
            flash('Vous devez accepter la politique de confidentialité.', 'danger')
            return render_template('recontact.html', title='Être recontacté.e')

        # Enregistrement en BDD
        cr = ContactRequest(
            nom=nom, email=email,
            telephone=telephone or None,
            rgpd_consent=True
        )
        db.session.add(cr)
        db.session.commit()

        # Email de notification admin
        try:
            msg = Message(
                subject=f'[LeBonCap] 📬 Demande de recontact — {nom}',
                recipients=[current_app.config['CONTACT_MAIL']],
                reply_to=email,
                body=f"""Nouvelle demande de recontact depuis LeBonCap

Nom       : {nom}
Email     : {email}
Téléphone : {telephone or '-'}
Date      : {datetime.now().strftime('%d/%m/%Y %H:%M')}

→ Répondre : {url_for('admin.contacts', _external=True)}"""
            )
            mail.send(msg)
        except Exception:
            pass

        flash('✅ Votre demande a bien été reçue ! Je vous recontacte très prochainement.', 'success')
        return redirect(url_for('public.recontact'))

    return render_template('recontact.html', title='Être recontacté.e')


# ─── Formulaire de contact (question courte) ─────────────────────────

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

        # Enregistrement en BDD
        qm = QuestionMessage(nom=nom, email=email, message=message)
        db.session.add(qm)
        db.session.commit()

        # Email de notification
        try:
            msg = Message(
                subject=f'[LeBonCap] Question courte — {nom}',
                recipients=[current_app.config['CONTACT_MAIL']],
                reply_to=email,
                body=f"""Nouvelle question courte depuis LeBonCap.net

Nom   : {nom}
Email : {email}

Question :
{message}"""
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

        # Enregistrement message en BDD
        pm = Parcoursup2026Message(nom=nom, email=email, message=question)
        db.session.add(pm)

        # Inscription automatique si l'email n'existe pas encore
        user = User.query.filter_by(email=email).first()
        inscrit = False
        if not user:
            tmp_pwd = secrets.token_hex(16)
            user = User(
                nom=nom, email=email,
                password_hash=generate_password_hash(tmp_pwd),
                confirme=False, actif=True,
                rgpd_consent=True,
                rgpd_consent_date=datetime.now(timezone.utc),
                parcoursup_2026=True
            )
            db.session.add(user)
            inscrit = True

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Email de notification
        try:
            msg = Message(
                subject=f'[LeBonCap] 🚨 Parcoursup 2026 — {nom}',
                recipients=[current_app.config['CONTACT_MAIL']],
                reply_to=email,
                body=f"""🚨 Nouvelle question PARCOURSUP 2026
{'✅ Nouvel inscrit !' if inscrit else '(utilisateur existant)'}

Nom   : {nom}
Email : {email}

Question :
{question}"""
            )
            mail.send(msg)
        except Exception:
            pass

        flash(
            '✅ Votre question a bien été reçue ! '
            + ('Vous êtes également inscrit(e) sur LeBonCap — vous recevrez nos conseils gratuits. '
               if inscrit else '')
            + 'Je vous réponds au plus vite.',
            'success'
        )
        return redirect(url_for('public.parcoursup_2026'))

    return render_template('parcoursup_2026.html', title='Urgence Parcoursup 2026')
