from functools import wraps
from datetime import datetime, timedelta, date, timezone

from flask import (Blueprint, render_template, request, flash,
                   redirect, url_for, abort, current_app, jsonify)
from flask_login import login_required, current_user
from flask_mail import Message

from app import db, mail
from app.models.user import User
from app.models.contact import ContactRequest, QuestionMessage, Parcoursup2026Message
from app.models.event import Event, EventRegistrationPublic

bp = Blueprint('admin', __name__, url_prefix='/admin')


# ─── Décorateur admin_required ───────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard principal ─────────────────────────────────────────────

@bp.route('/')
@login_required
@admin_required
def dashboard():
    today = date.today()
    seven_days_ago = datetime.combine(today - timedelta(days=7), datetime.min.time())
    yesterday      = datetime.combine(today - timedelta(days=1), datetime.min.time())
    tomorrow       = datetime.combine(today + timedelta(days=1), datetime.min.time())

    stats = {
        'contacts_non_lus':    ContactRequest.query.filter_by(is_read=False).count(),
        'questions_non_lues':  QuestionMessage.query.filter_by(is_read=False).count(),
        'parcoursup_non_lus':  Parcoursup2026Message.query.filter_by(is_read=False).count(),
        'contacts_semaine':    ContactRequest.query.filter(
                                   ContactRequest.created_at >= seven_days_ago).count(),
        'events_a_venir':      Event.query.filter(
                                   Event.date_event >= datetime.utcnow(),
                                   Event.is_published == True).count(),
        'inscrits_semaine':    EventRegistrationPublic.query.filter(
                                   EventRegistrationPublic.created_at >= seven_days_ago).count(),
    }

    prochains_events = Event.query.filter(
        Event.date_event >= datetime.utcnow()
    ).order_by(Event.date_event).limit(5).all()

    derniers_contacts = ContactRequest.query.filter_by(
        is_read=False
    ).order_by(ContactRequest.created_at.desc()).limit(8).all()

    dernieres_questions = QuestionMessage.query.filter_by(
        is_read=False
    ).order_by(QuestionMessage.created_at.desc()).limit(8).all()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           prochains_events=prochains_events,
                           derniers_contacts=derniers_contacts,
                           dernieres_questions=dernieres_questions)


# ─── Contacts (recontact) ────────────────────────────────────────────

@bp.route('/contacts')
@login_required
@admin_required
def contacts():
    page = request.args.get('page', 1, type=int)
    filtre = request.args.get('filtre', 'non_lus')
    q = ContactRequest.query
    if filtre == 'non_lus':
        q = q.filter_by(is_read=False)
    elif filtre == 'lus':
        q = q.filter_by(is_read=True)
    items = q.order_by(ContactRequest.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/contacts.html', items=items, filtre=filtre)


@bp.route('/contacts/<int:id>/lire', methods=['POST'])
@login_required
@admin_required
def contact_lire(id):
    c = ContactRequest.query.get_or_404(id)
    c.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('admin.contacts'))


@bp.route('/contacts/tout-lire', methods=['POST'])
@login_required
@admin_required
def contacts_tout_lire():
    ContactRequest.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    flash('Tous les contacts marqués comme lus.', 'success')
    return redirect(url_for('admin.contacts'))


# ─── Messages (questions courtes) ────────────────────────────────────

@bp.route('/messages')
@login_required
@admin_required
def messages():
    page = request.args.get('page', 1, type=int)
    filtre = request.args.get('filtre', 'non_lus')
    q = QuestionMessage.query
    if filtre == 'non_lus':
        q = q.filter_by(is_read=False)
    elif filtre == 'lus':
        q = q.filter_by(is_read=True)
    items = q.order_by(QuestionMessage.created_at.desc()).paginate(page=page, per_page=20)

    # Parcoursup 2026
    qp = Parcoursup2026Message.query
    if filtre == 'non_lus':
        qp = qp.filter_by(is_read=False)
    elif filtre == 'lus':
        qp = qp.filter_by(is_read=True)
    items_pc = qp.order_by(Parcoursup2026Message.created_at.desc()).paginate(page=page, per_page=20)

    return render_template('admin/messages.html', items=items, items_pc=items_pc, filtre=filtre)


@bp.route('/messages/<int:id>/lire', methods=['POST'])
@login_required
@admin_required
def message_lire(id):
    m = QuestionMessage.query.get_or_404(id)
    m.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('admin.messages'))


@bp.route('/messages/parcoursup/<int:id>/lire', methods=['POST'])
@login_required
@admin_required
def parcoursup_lire(id):
    m = Parcoursup2026Message.query.get_or_404(id)
    m.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('admin.messages'))


# ─── Résumé quotidien ─────────────────────────────────────────────────

@bp.route('/resume')
@login_required
@admin_required
def resume():
    """Prévisualisation du résumé avant envoi."""
    today = date.today()
    depuis = request.args.get('depuis', str(today - timedelta(days=1)))
    try:
        depuis_dt = datetime.strptime(depuis, '%Y-%m-%d')
    except ValueError:
        depuis_dt = datetime.utcnow() - timedelta(days=1)

    contacts  = ContactRequest.query.filter(ContactRequest.created_at >= depuis_dt).all()
    questions = QuestionMessage.query.filter(QuestionMessage.created_at >= depuis_dt).all()
    parcoursup = Parcoursup2026Message.query.filter(Parcoursup2026Message.created_at >= depuis_dt).all()
    inscrits  = EventRegistrationPublic.query.filter(
        EventRegistrationPublic.created_at >= depuis_dt).all()

    return render_template('admin/resume.html',
                           contacts=contacts, questions=questions,
                           parcoursup=parcoursup, inscrits=inscrits,
                           depuis=depuis)


@bp.route('/resume/envoyer', methods=['POST'])
@login_required
@admin_required
def resume_envoyer():
    """Envoi du résumé par email."""
    depuis = request.form.get('depuis', str(date.today() - timedelta(days=1)))
    try:
        depuis_dt = datetime.strptime(depuis, '%Y-%m-%d')
    except ValueError:
        depuis_dt = datetime.utcnow() - timedelta(days=1)

    contacts   = ContactRequest.query.filter(ContactRequest.created_at >= depuis_dt).all()
    questions  = QuestionMessage.query.filter(QuestionMessage.created_at >= depuis_dt).all()
    parcoursup = Parcoursup2026Message.query.filter(Parcoursup2026Message.created_at >= depuis_dt).all()
    inscrits   = EventRegistrationPublic.query.filter(
        EventRegistrationPublic.created_at >= depuis_dt).all()

    if not any([contacts, questions, parcoursup, inscrits]):
        flash('Rien à signaler pour cette période.', 'info')
        return redirect(url_for('admin.resume'))

    try:
        html = render_template('admin/emails/resume_quotidien.html',
                               contacts=contacts, questions=questions,
                               parcoursup=parcoursup, inscrits=inscrits,
                               depuis=depuis_dt)
        msg = Message(
            subject=f'[LeBonCap] Résumé du {depuis_dt.strftime("%d/%m/%Y")}',
            recipients=[current_app.config['CONTACT_MAIL']],
            html=html
        )
        mail.send(msg)
        flash(f'Résumé envoyé à {current_app.config["CONTACT_MAIL"]} ✅', 'success')
    except Exception as e:
        flash(f'Erreur lors de l\'envoi : {e}', 'danger')

    return redirect(url_for('admin.resume'))


@bp.route('/api/trigger-resume', methods=['POST'])
def api_trigger_resume():
    """Webhook appelé par cron-job.org pour le résumé automatique."""
    token = request.headers.get('X-Cron-Token', '')
    expected = current_app.config.get('CRON_SECRET_TOKEN', '')
    if not expected or token != expected:
        abort(403)

    yesterday = datetime.utcnow() - timedelta(days=1)
    contacts   = ContactRequest.query.filter(ContactRequest.created_at >= yesterday).all()
    questions  = QuestionMessage.query.filter(QuestionMessage.created_at >= yesterday).all()
    parcoursup = Parcoursup2026Message.query.filter(Parcoursup2026Message.created_at >= yesterday).all()
    inscrits   = EventRegistrationPublic.query.filter(
        EventRegistrationPublic.created_at >= yesterday).all()

    if any([contacts, questions, parcoursup, inscrits]):
        try:
            html = render_template('admin/emails/resume_quotidien.html',
                                   contacts=contacts, questions=questions,
                                   parcoursup=parcoursup, inscrits=inscrits,
                                   depuis=yesterday)
            msg = Message(
                subject=f'[LeBonCap] Résumé automatique {datetime.utcnow().strftime("%d/%m/%Y")}',
                recipients=[current_app.config['CONTACT_MAIL']],
                html=html
            )
            mail.send(msg)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({'status': 'ok', 'sent': bool(any([contacts, questions, parcoursup, inscrits]))}), 200


# ─── Rencontres — CRUD ────────────────────────────────────────────────

@bp.route('/rencontres')
@login_required
@admin_required
def rencontres():
    events = Event.query.order_by(Event.date_event.desc()).all()
    return render_template('admin/rencontres.html', events=events)


@bp.route('/rencontres/new', methods=['GET', 'POST'])
@login_required
@admin_required
def rencontre_new():
    if request.method == 'POST':
        titre      = request.form.get('titre', '').strip()
        thematique = request.form.get('thematique', '').strip()
        precisions = request.form.get('precisions', '').strip()
        date_str   = request.form.get('date_event', '').strip()
        mode       = request.form.get('mode', 'visio')
        lieu       = request.form.get('lieu', '').strip()
        places_max = request.form.get('places_max', 30, type=int)
        publier    = request.form.get('publier') == '1'

        if not all([titre, thematique, date_str]):
            flash('Titre, thématique et date sont obligatoires.', 'danger')
            return render_template('admin/rencontre_form.html', event=None)

        try:
            date_event = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Format de date invalide.', 'danger')
            return render_template('admin/rencontre_form.html', event=None)

        event = Event(
            titre=titre, thematique=thematique, precisions=precisions or None,
            date_event=date_event, mode=mode,
            lieu=lieu or None, places_max=places_max,
            is_published=publier, created_by=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash(f'Rencontre "{titre}" créée {"et publiée" if publier else "(brouillon)"}. ✅', 'success')
        return redirect(url_for('admin.rencontres'))

    return render_template('admin/rencontre_form.html', event=None)


@bp.route('/rencontres/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def rencontre_edit(id):
    event = Event.query.get_or_404(id)

    if request.method == 'POST':
        event.titre      = request.form.get('titre', '').strip()
        event.thematique = request.form.get('thematique', '').strip()
        event.precisions = request.form.get('precisions', '').strip() or None
        date_str         = request.form.get('date_event', '').strip()
        event.mode       = request.form.get('mode', 'visio')
        event.lieu       = request.form.get('lieu', '').strip() or None
        event.places_max = request.form.get('places_max', 30, type=int)
        event.is_published = request.form.get('publier') == '1'

        if not all([event.titre, event.thematique, date_str]):
            flash('Titre, thématique et date sont obligatoires.', 'danger')
            return render_template('admin/rencontre_form.html', event=event)

        try:
            event.date_event = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Format de date invalide.', 'danger')
            return render_template('admin/rencontre_form.html', event=event)

        db.session.commit()
        flash('Rencontre mise à jour. ✅', 'success')
        return redirect(url_for('admin.rencontres'))

    return render_template('admin/rencontre_form.html', event=event)


@bp.route('/rencontres/<int:id>/toggle-publish', methods=['POST'])
@login_required
@admin_required
def rencontre_toggle_publish(id):
    event = Event.query.get_or_404(id)
    event.is_published = not event.is_published
    db.session.commit()
    etat = 'publiée' if event.is_published else 'dépubliée'
    flash(f'Rencontre {etat}. ✅', 'success')
    return redirect(url_for('admin.rencontres'))


@bp.route('/rencontres/<int:id>/inscrits')
@login_required
@admin_required
def rencontre_inscrits(id):
    event = Event.query.get_or_404(id)
    confirmes = event.public_registrations.filter_by(status='confirmed').all()
    attente   = event.public_registrations.filter_by(status='waitlist').all()
    annules   = event.public_registrations.filter_by(status='cancelled').all()
    return render_template('admin/rencontre_inscrits.html',
                           event=event,
                           confirmes=confirmes,
                           attente=attente,
                           annules=annules)
