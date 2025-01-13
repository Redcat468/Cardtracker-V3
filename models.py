from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):  # Hérite de UserMixin
    __tablename__ = 'USERS'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    level = db.Column(db.Integer, nullable=False)

from datetime import datetime

class Operation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.String(20), nullable=False)  # Ceci est un texte à convertir
    card_name = db.Column(db.String(50), nullable=False)
    statut_geo = db.Column(db.String(50), nullable=False)


class Card(db.Model):
    __tablename__ = 'CARDS'
    id = db.Column(db.Integer, primary_key=True)  # Clé primaire auto-incrémentée
    card_name = db.Column(db.String(50), nullable=False)
    card_birth = db.Column(db.String(50))
    quarantine = db.Column(db.Boolean, default=False)
    statut_geo = db.Column(db.String(50))
    capacity = db.Column(db.Integer)
    brand = db.Column(db.String(50))
    card_type = db.Column(db.String(50))


class StatusGeo(db.Model):
    __tablename__ = 'STATUS_GEO'
    
    status_name = db.Column(db.String(50), primary_key=True)
