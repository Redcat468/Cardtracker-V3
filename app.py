from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Operation, Card, StatusGeo, CanceledOperation
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime
from flask import jsonify


app = Flask(__name__)

# Configuration de la base de données
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'card_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de la base de données et Flask-Login
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Configurer la redirection pour les utilisateurs non authentifiés
login_manager.login_view = 'login'
login_manager.login_message = "Vous devez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"

# Initialiser les tables dans la base de données
with app.app_context():
    db.create_all()

# Vérifier si un utilisateur existe déjà, sinon en créer un
with app.app_context():
    existing_user = User.query.filter_by(username='fabt').first()
    if not existing_user:
        new_user = User(username='fabt', level=48)
        db.session.add(new_user)
        db.session.commit()
    else:
        print("L'utilisateur 'fabt' existe déjà")

# Gestion des sessions utilisateurs avec Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            login_user(user)
            flash("Connexion réussie.", "success")
            return redirect(request.args.get('next') or url_for('track'))
        else:
            flash("Nom d'utilisateur incorrect.", "danger")
    return render_template('login.html')

# Gestion des accès non autorisés
@login_manager.unauthorized_handler
def unauthorized():
    flash("Vous devez être connecté pour accéder à cette page.", "warning")
    return redirect(url_for('login'))

@app.errorhandler(401)
def unauthorized_error(error):
    flash("Vous devez être connecté pour accéder à cette page.", "warning")
    return redirect(url_for('login'))

# Route pour se déconnecter
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/search_cards')
@login_required
def search_cards():
    query = request.args.get('query', '')

    if query:
        # Rechercher les cartes correspondant au texte saisi
        matching_cards = Card.query.filter(Card.card_name.like(f'{query}%')).all()
        card_list = [{'card_name': card.card_name} for card in matching_cards]
        return jsonify(card_list)

    return jsonify([])

@app.route('/track', methods=['GET', 'POST'])
@login_required
def track():
    # Récupérer tous les statuts géographiques
    status_geo = StatusGeo.query.all()

    # Initialiser les opérations pour l'historique (limitées aux 50 dernières)
    operations = Operation.query.order_by(Operation.timestamp.desc()).limit(50).all()

    # Logique pour déplacer les cartes (si nécessaire)
    if request.method == 'POST':
        source = request.form.get('source')
        target = request.form.get('target')
        card_name = request.form.get('card')

        if card_name:
            card = Card.query.filter_by(card_name=card_name).first()
            if card:
                # Créer une nouvelle opération
                new_operation = Operation(
                    username=current_user.username,
                    card_name=card_name,
                    statut_geo=target,
                    timestamp=datetime.now().strftime('%Y%m%d-%H:%M:%S')
                )
                db.session.add(new_operation)

                # Mettre à jour la carte
                card.statut_geo = target
                card.last_operation = datetime.now()
                card.usage += 1  # Incrémenter l'usage
                db.session.commit()

                flash(f"Carte {card_name} déplacée avec succès.")
            else:
                flash("Carte introuvable.")
        else:
            flash("Veuillez sélectionner une carte.")

    return render_template('track.html', status_geo=status_geo, operations=operations)


@app.route('/get_cards_by_status/<status>', methods=['GET'])
@login_required
def get_cards_by_status(status):
    cards = Card.query.filter_by(statut_geo=status).all()
    return jsonify([{"card_name": card.card_name} for card in cards])



@app.route('/get_status_geo', methods=['GET'])
@login_required
def get_status_geo():
    statuses = StatusGeo.query.all()
    return jsonify([{"status_name": status.status_name} for status in statuses])


@app.route('/get_operations', methods=['GET'])
@login_required
def get_operations():
    # Récupérer les opérations
    operations = Operation.query.order_by(Operation.timestamp.desc()).limit(50).all()
    return jsonify([
        {
            "id": operation.id,
            "card_name": operation.card_name,
            "statut_geo": operation.statut_geo,
            "timestamp": operation.timestamp,
            "username": operation.username
        }
        for operation in operations
    ])

# Route pour annuler une opération
@app.route('/cancel_operation/<int:operation_id>', methods=['POST'])
@login_required
def cancel_operation(operation_id):
    operation = Operation.query.get(operation_id)
    if operation:
        print(f"Opération trouvée : {operation.card_name}, {operation.statut_geo}, {operation.timestamp}")

        # Récupérer la carte associée à l'opération
        card = Card.query.filter_by(card_name=operation.card_name).first()
        if card:
            print(f"Carte trouvée : {card.card_name}")

            # Désincrémenter le compteur d'usage
            card.usage = max(card.usage - 1, 0)  # Ne pas aller en dessous de 0
            print(f"Usage désincrémenté : {card.usage}")

            # Créer une nouvelle entrée dans la table CanceledOperation
            canceled_operation = CanceledOperation(
                card_name=operation.card_name,
                statut_geo=operation.statut_geo,
                timestamp=operation.timestamp,
                username=current_user.username
            )
            db.session.add(canceled_operation)
            print(f"Opération annulée ajoutée à CanceledOperation : {canceled_operation}")

            # Supprimer l'opération actuelle
            db.session.delete(operation)
            db.session.commit()
            print("Opération supprimée de la table Operation")

            # Trouver la dernière opération pour cette carte
            last_operation = Operation.query.filter_by(card_name=card.card_name).order_by(Operation.timestamp.desc()).first()
            if last_operation:
                card.statut_geo = last_operation.statut_geo
                if isinstance(last_operation.timestamp, str):
                    card.last_operation = datetime.strptime(last_operation.timestamp, '%Y%m%d-%H:%M:%S')
                else:
                    card.last_operation = last_operation.timestamp
            else:
                card.statut_geo = 'INCONNU'
                card.last_operation = None

            db.session.commit()
            print("Carte mise à jour avec le dernier statut géographique")
        else:
            print("Carte introuvable.")
            flash("Carte introuvable.")
    else:
        print("Opération introuvable.")
        flash("Opération introuvable.")

    return redirect(url_for('track'))


# Route pour afficher les opérations de "Spot"
from datetime import datetime

from datetime import datetime

@app.route('/spot', methods=['GET', 'POST'])
@login_required
def spot():
    # Charger tous les statuts géographiques et toutes les cartes
    status_geo = StatusGeo.query.all()
    cards = Card.query.all()

    # Variables pour différencier les onglets
    current_tab = "card_focus"  # Par défaut, afficher Card Focus
    selected_card = None
    card_info = None
    timeline_data = None
    selected_status = None
    cards_by_status = []

    if request.method == 'POST':
        action = request.form.get('action')  # Identifier l'origine du formulaire

        if action == "status_geo":
            current_tab = "status_geo"
            selected_status = request.form.get('selected_status')
            if selected_status:
                # Récupérer les cartes associées au statut sélectionné avec leur dernière opération
                cards_by_status = db.session.query(
                    Card,
                    db.session.query(Operation.timestamp)
                    .filter(Operation.card_name == Card.card_name)
                    .order_by(Operation.timestamp.desc())
                    .limit(1)
                    .as_scalar()
                ).filter(Card.statut_geo == selected_status).all()

    return render_template(
        'spot.html',
        cards=cards,
        status_geo=status_geo,
        selected_card=selected_card,
        card_info=card_info,
        timeline_data=timeline_data,
        selected_status=selected_status,
        cards_by_status=cards_by_status,
        current_tab=current_tab
    )


@app.route('/card-focus', methods=['GET', 'POST'])
def card_focus():
    # Logique pour gérer l'affichage des détails de la carte
    selected_card = request.form.get('selected_card', None)
    card_details = None
    if selected_card:
        card_details = Card.query.filter_by(card_name=selected_card).first()
    
    return render_template('spot.html', card_details=card_details)

@app.route('/')
def home():
    return redirect(url_for('track'))


# Route pour les utilisateurs administrateurs
@app.route('/manage')
@login_required
def manage():
    if current_user.level >= 47:
        return render_template('manage.html')
    return redirect(url_for('track'))

# Lancement de l'application Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
