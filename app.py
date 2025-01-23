import os
import sys
from flask import Flask
from flask_login import LoginManager
from database import db  # Importer db depuis le nouveau fichier

def create_app():
    app = Flask(__name__)
    
    # Configuration des chemins
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
        app.template_folder = os.path.join(base_dir, 'templates')
        app.static_folder = os.path.join(base_dir, 'static')
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Création du dossier instance
    instance_path = os.path.join(base_dir, 'instance')
    os.makedirs(instance_path, exist_ok=True)

    # Configuration de la DB
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "card_tracker.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.urandom(24)

    # Initialiser les extensions
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    # Création des tables
    with app.app_context():
        db.create_all()
        from models import User  # Import local pour éviter la circularité
        if not User.query.filter_by(username='fabt').first():
            admin = User(username='fabt', level=48)
            admin.set_password('motdepasse')
            db.session.add(admin)
            db.session.commit()

    # Configuration Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User  # Import local
        return User.query.get(int(user_id))

    # Importer les routes
    from routes import init_routes
    init_routes(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)