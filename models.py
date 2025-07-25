from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from database import db

# Table d'association pour lier Team et StatusGeo
team_status_geo = db.Table(
    'TEAM_STATUS_GEO',
    db.Column('team_id', db.Integer, db.ForeignKey('TEAM.id'), primary_key=True),
    db.Column('status_geo_id', db.Integer, db.ForeignKey('STATUS_GEO.id'), primary_key=True)
)

class Team(db.Model):
    __tablename__ = 'TEAM'
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(50), unique=True, nullable=False)
    # Relation many-to-many vers StatusGeo
    status_geo = db.relationship(
        'StatusGeo',
        secondary=team_status_geo,
        backref=db.backref('teams', lazy='dynamic'),
        lazy='dynamic'
    )

class User(UserMixin, db.Model):
    __tablename__ = 'USERS'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('TEAM.id'), nullable=True)
    team = db.relationship('Team', backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class StatusGeo(db.Model):
    __tablename__ = 'STATUS_GEO'
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), unique=True, nullable=False)

    # Note : la backref 'teams' est déjà défini sur Team.status_geo

class Operation(db.Model):
    __tablename__ = 'OPERATION'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.String(20), nullable=False)  # YYYYMMDD-HH:MM:SS
    card_name = db.Column(db.String(50), nullable=False)
    statut_geo = db.Column(db.String(50), nullable=False)
    offload_status = db.Column(db.String(50), default="Not Started")

    @property
    def datetime(self):
        return datetime.strptime(self.timestamp, "%Y%m%d-%H:%M:%S")

    @datetime.setter
    def datetime(self, value):
        self.timestamp = value.strftime("%Y%m%d-%H:%M:%S")

class CanceledOperation(db.Model):
    __tablename__ = 'CANCELED_OPERATION'
    id = db.Column(db.Integer, primary_key=True)
    card_name = db.Column(db.String(50), nullable=False)
    statut_geo = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    offload_status = db.Column(db.String(50), default="Not Started")

    @property
    def datetime(self):
        return datetime.strptime(self.timestamp, "%Y%m%d-%H:%M:%S")

    @datetime.setter
    def datetime(self, value):
        self.timestamp = value.strftime("%Y%m%d-%H:%M:%S")

class Card(db.Model):
    __tablename__ = 'CARDS'
    id = db.Column(db.Integer, primary_key=True)
    card_name = db.Column(db.String(50), unique=True, nullable=False)
    card_birth = db.Column(db.DateTime, nullable=False)
    quarantine = db.Column(db.Boolean, default=False)
    statut_geo = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer)
    brand = db.Column(db.String(50))
    card_type = db.Column(db.String(50))
    usage = db.Column(db.Integer, default=0)
    last_operation = db.Column(db.DateTime, nullable=True)
    offload_status = db.Column(db.String(50), default="Not Started")

class OffloadStatus(db.Model):
    __tablename__ = 'OFFLOAD_STATUS'
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), unique=True, nullable=False)
