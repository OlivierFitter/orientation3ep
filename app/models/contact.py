from app import db
from datetime import datetime


class ContactRequest(db.Model):
    """Demande de recontact ('Je souhaite être recontacté.e')"""
    __tablename__ = 'contact_requests'

    id           = db.Column(db.Integer, primary_key=True)
    nom          = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(150), nullable=False)
    telephone    = db.Column(db.String(30), nullable=True)
    rgpd_consent = db.Column(db.Boolean, nullable=False, default=False)
    is_read      = db.Column(db.Boolean, default=False)   # marqué lu par l'admin
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContactRequest {self.nom} ({self.email})>'


class QuestionMessage(db.Model):
    """Question courte envoyée via le formulaire contact standard"""
    __tablename__ = 'question_messages'

    id           = db.Column(db.Integer, primary_key=True)
    nom          = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(150), nullable=False)
    message      = db.Column(db.Text, nullable=False)
    is_read      = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuestionMessage {self.nom} ({self.email})>'


class Parcoursup2026Message(db.Model):
    """Question envoyée via le formulaire Parcoursup 2026"""
    __tablename__ = 'parcoursup2026_messages'

    id           = db.Column(db.Integer, primary_key=True)
    nom          = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(150), nullable=False)
    message      = db.Column(db.Text, nullable=False)
    is_read      = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Parcoursup2026Message {self.nom}>'
