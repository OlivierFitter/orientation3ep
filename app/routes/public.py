from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_mail import Message
from app import mail

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
        code    = request.form.get('code', '').strip()  # QC / AP / AA
        consent = request.form.get('rgpd_consent')

        if not all([nom, email, message]):
            flash('Merci de remplir tous les champs obligatoires.', 'danger')
            return render_template('contact.html', title='Contact')

        if not consent:
            flash('Vous devez accepter la politique de confidentialité.', 'danger')
            return render_template('contact.html', title='Contact')

        try:
            msg = Message(
                subject=f'[LeBonCap] Nouveau message - {code if code else "Contact"} - {nom}',
                recipients=[current_app.config['CONTACT_MAIL']],
                reply_to=email,
                body=f"""
Nouveau message depuis LeBonCap.net

Nom    : {nom}
Email  : {email}
Code   : {code if code else 'Non précisé'}

Message :
{message}
"""
            )
            mail.send(msg)
            flash('Votre message a bien été envoyé ! Je vous réponds rapidement.', 'success')
            return redirect(url_for('public.contact'))
        except Exception as e:
            flash('Erreur lors de l\'envoi. Veuillez réessayer.', 'danger')

    return render_template('contact.html', title='Contactez-moi')
