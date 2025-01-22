import os
import sys
from flask import Flask
from flask_login import LoginManager
from models import db, User
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy.ext.declarative  # Force l'inclusion du module

# Configuration de l'application
def create_app():
    app = Flask(__name__)
    
    # Configuration des chemins
    if getattr(sys, 'frozen', False):
        app.template_folder = os.path.join(sys._MEIPASS, 'templates')
        app.static_folder = os.path.join(sys._MEIPASS, 'static')
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        app.template_folder = os.path.join(base_dir, 'templates')
        app.static_folder = os.path.join(base_dir, 'static')

    # Configuration de la base de données
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "instance", "card_tracker.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.urandom(24)

    # Initialisation des extensions
    db.init_app(app)
    
    # Configuration de Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import flash, redirect, url_for  # Import local pour éviter les conflits
        flash("Vous devez être connecté pour accéder à cette page.", "warning")
        return redirect(url_for('login'))

    return app

# Création de l'application
app = create_app()

# Initialisation de la base de données
with app.app_context():
    db.create_all()
    # Création de l'utilisateur admin si inexistant
    if not User.query.filter_by(username='fabt').first():
        admin = User(username='fabt', level=48)
        admin.set_password('motdepasse')  # À changer en production
        db.session.add(admin)
        db.session.commit()

# Import des routes APRÈS la création de l'app
from routes import *

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)