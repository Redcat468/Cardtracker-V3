from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
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
    offload_status = db.Column(db.String(50), default="Not Started")  # Nouveau champ


class CanceledOperation(db.Model):
    __tablename__ = 'canceled_operations'

    id = db.Column(db.Integer, primary_key=True)
    card_name = db.Column(db.String(50), nullable=False)
    statut_geo = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(50), nullable=False)  # Utilisateur qui a annulé l’opération
    offload_status = db.Column(db.String(50), default="Not Started")  # Nouveau champ


class Card(db.Model):
    __tablename__ = 'CARDS'
    id = db.Column(db.Integer, primary_key=True)
    card_name = db.Column(db.String(50), unique=True, nullable=False)
    card_birth = db.Column(db.DateTime, nullable=False)
    quarantine = db.Column(db.Boolean, default=False)
    statut_geo = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer)  # Capacité en Go
    brand = db.Column(db.String(50))  # Marque de la carte
    card_type = db.Column(db.String(50))  # Type de la carte (CFAST, SD, etc.)
    usage = db.Column(db.Integer, default=0)  # Nombre d'opérations effectuées sur la carte
    last_operation = Column(DateTime, nullable=True)  # Dernière opération
    offload_status = db.Column(db.String(50), default="Not Started")  # Nouveau champ: statut de l'offload

class OffloadStatus(db.Model):
    __tablename__ = 'OFFLOAD_STATUS'
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), unique=True, nullable=False)


class StatusGeo(db.Model):
    __tablename__ = 'STATUS_GEO'
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), unique=True, nullable=False)
