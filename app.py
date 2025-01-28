import os
import sys
from flask import Flask
from flask_login import LoginManager
from pathlib import Path
from database import db

def create_app():
    app = Flask(__name__)
    
    # Configuration des chemins
    if getattr(sys, 'frozen', False):
        # Mode exécutable : DB à côté du .exe
        base_dir = Path(sys.executable).parent
        app.template_folder = Path(sys._MEIPASS) / "templates"
        app.static_folder = Path(sys._MEIPASS) / "static"
    else:
        # Mode développement : DB dans instance/
        base_dir = Path(__file__).parent
        app.template_folder = "templates"
        app.static_folder = "static"

    # Chemin de la base de données
    instance_path = base_dir / "instance"
    instance_path.mkdir(exist_ok=True)
    db_path = instance_path / "card_tracker.db"

    # Configuration SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.urandom(24)

    # Initialisation des extensions
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    # Création des tables ET import des modèles
    with app.app_context():
        from models import User, Operation, Card, StatusGeo, CanceledOperation, OffloadStatus  # Import explicite
        db.create_all()  # Doit être APRÈS l'import des modèles
        
        # Création de l'admin
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
    
    # Import des routes
    from routes import init_routes
    init_routes(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=10000)