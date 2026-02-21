from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint('membres', __name__)

# Décorateur @login_required protège automatiquement toutes ces routes

@bp.route('/tableau-de-bord')
@login_required
def tableau_bord():
    return render_template('membres/tableau_bord.html', title='Mon espace')

@bp.route('/essentiel')
@login_required
def essentiel():
    return render_template('membres/essentiel.html', title='L\'essentiel pour bien démarrer')

@bp.route('/conseil/<int:num>')
@login_required
def conseil(num):
    if num < 1 or num > 8:
        return render_template('membres/tableau_bord.html', title='Mon espace')
    return render_template(f'membres/conseil_{num}.html',
                           title=f'Conseil n°{num}',
                           num=num)

@bp.route('/mon-compte')
@login_required
def mon_compte():
    return render_template('membres/mon_compte.html', title='Mon compte')
