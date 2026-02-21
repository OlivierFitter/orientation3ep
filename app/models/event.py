from app import db
from datetime import datetime
import secrets


class Event(db.Model):
    """Rencontre (visio ou présentiel) organisée par l'admin"""
    __tablename__ = 'events'

    id           = db.Column(db.Integer, primary_key=True)
    titre        = db.Column(db.String(200), nullable=False)
    thematique   = db.Column(db.String(200), nullable=False)
    precisions   = db.Column(db.Text, nullable=True)
    date_event   = db.Column(db.DateTime, nullable=False)
    mode         = db.Column(db.String(20), nullable=False)   # 'presentiel' | 'visio'
    lieu         = db.Column(db.String(300), nullable=True)   # adresse ou lien visio
    places_max   = db.Column(db.Integer, nullable=False, default=30)
    is_published = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    created_by   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    registrations = db.relationship(
        'Registration', back_populates='event',
        lazy='dynamic', cascade='all, delete-orphan'
    )

    @property
    def places_confirmees(self):
        return self.registrations.filter_by(status='confirmed').count()

    @property
    def places_restantes(self):
        return max(0, self.places_max - self.places_confirmees)

    @property
    def est_complet(self):
        return self.places_restantes == 0

    @property
    def est_passe(self):
        return self.date_event < datetime.utcnow()

    @property
    def mode_label(self):
        return '🖥️ Visioconférence' if self.mode == 'visio' else '📍 Présentiel'

    def __repr__(self):
        return f'<Event {self.titre} le {self.date_event}>'


class Registration(db.Model):
    """Inscription d'un utilisateur à un événement"""
    __tablename__ = 'registrations'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id     = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    # Inscription depuis un formulaire public (sans compte)
    nom_public   = db.Column(db.String(100), nullable=True)  # si sans compte
    email_public = db.Column(db.String(150), nullable=True)  # si sans compte
    status       = db.Column(db.String(20), default='confirmed')
    # 'confirmed' | 'waitlist' | 'cancelled'
    token        = db.Column(db.String(64), unique=True, nullable=False,
                             default=lambda: secrets.token_urlsafe(32))
    confirmed_at = db.Column(db.DateTime, nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', name='uq_user_event'),
    )

    user  = db.relationship('User', backref=db.backref('registrations', lazy='dynamic'))
    event = db.relationship('Event', back_populates='registrations')

    @property
    def nom(self):
        return self.user.nom if self.user else self.nom_public

    @property
    def email(self):
        return self.user.email if self.user else self.email_public

    def __repr__(self):
        return f'<Registration user={self.user_id} event={self.event_id} status={self.status}>'


class EventRegistrationPublic(db.Model):
    """Inscription publique (sans compte) à un événement"""
    __tablename__ = 'event_registrations_public'

    id           = db.Column(db.Integer, primary_key=True)
    event_id     = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    nom          = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(150), nullable=False)
    telephone    = db.Column(db.String(30), nullable=True)
    status       = db.Column(db.String(20), default='confirmed')  # 'confirmed' | 'waitlist' | 'cancelled'
    token        = db.Column(db.String(64), unique=True, nullable=False,
                             default=lambda: secrets.token_urlsafe(32))
    rgpd_consent = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    event = db.relationship('Event', backref=db.backref('public_registrations', lazy='dynamic'))

    def __repr__(self):
        return f'<EventRegistrationPublic {self.nom} event={self.event_id}>'
