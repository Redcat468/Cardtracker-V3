from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Operation, Card, StatusGeo, CanceledOperation, OffloadStatus
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

    # Récupérer les statuts offload
    offload_statuses = OffloadStatus.query.all()

    # Initialiser les opérations pour l'historique (limitées aux 50 dernières)
    operations = Operation.query.order_by(Operation.timestamp.desc()).limit(50).all()

    # Précharger les valeurs "Source" et "Carte" si présentes dans la requête GET
    preloaded_source = request.args.get('source', '')
    preloaded_card = request.args.get('card', '')

    # Vérifier que la carte préchargée existe et est valide
    if preloaded_card:
        valid_card = Card.query.filter_by(card_name=preloaded_card).first()
        if not valid_card:
            preloaded_card = ''  # Réinitialiser si la carte n'existe pas

    # Logique pour déplacer les cartes (si nécessaire)
    if request.method == 'POST':
        source = request.form.get('source')
        target = request.form.get('target')
        card_name = request.form.get('card')
        offload_status = request.form.get('offload_status')

        if card_name:
            card = Card.query.filter_by(card_name=card_name).first()
            if card:
                # Créer une nouvelle opération
                new_operation = Operation(
                    username=current_user.username,
                    card_name=card_name,
                    statut_geo=target,
                    timestamp=datetime.now().strftime('%Y%m%d-%H:%M:%S'),
                    offload_status=offload_status
                )
                db.session.add(new_operation)

                # Mettre à jour la carte
                card.statut_geo = target
                card.offload_status = offload_status
                card.last_operation = datetime.now()
                card.usage += 1
                db.session.commit()

                flash(f"Carte {card_name} déplacée avec succès et statut offload mis à jour.")
            else:
                flash("Carte introuvable.")
        else:
            flash("Veuillez sélectionner une carte.")

    return render_template(
        'track.html',
        status_geo=status_geo,
        offload_statuses=offload_statuses,
        operations=operations,
        preloaded_source=preloaded_source,
        preloaded_card=preloaded_card
    )



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
            "offload_status": operation.offload_status,  # Inclure le statut offload
            "timestamp": operation.timestamp,
            "username": operation.username
        }
        for operation in operations
    ])

@app.route('/get_offload_status/<card_name>', methods=['GET'])
@login_required
def get_offload_status(card_name):
    card = Card.query.filter_by(card_name=card_name).first()
    if card:
        return jsonify({"offload_status": card.offload_status})
    return jsonify({"offload_status": "Non défini"}), 404

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
                username=current_user.username,
                offload_status=operation.offload_status  # Sauvegarder le statut offload dans canceled_operations
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
                card.offload_status = last_operation.offload_status  # Rétablir le dernier statut offload
                if isinstance(last_operation.timestamp, str):
                    card.last_operation = datetime.strptime(last_operation.timestamp, '%Y%m%d-%H:%M:%S')
                else:
                    card.last_operation = last_operation.timestamp
            else:
                card.statut_geo = 'INCONNU'
                card.offload_status = None  # Réinitialiser le statut offload
                card.last_operation = None

            db.session.commit()
            print("Carte mise à jour avec le dernier statut géographique et offload")
        else:
            print("Carte introuvable.")
            flash("Carte introuvable.")
    else:
        print("Opération introuvable.")
        flash("Opération introuvable.")

    return redirect(url_for('track'))



# Route pour afficher les opérations de "Spot"
from datetime import datetime

@app.route('/spot', methods=['GET', 'POST'])
@login_required
def spot():
    # Charger tous les statuts géographiques, utilisateurs et cartes
    status_geo = StatusGeo.query.all()
    users = User.query.all()
    cards = Card.query.all()
    offload_statuses = OffloadStatus.query.all()  # Ajout du chargement des statuts offload

    # Variables pour différencier les onglets
    current_tab = "card_focus"  # Par défaut, afficher Card Focus
    selected_card = None
    card_info = None
    timeline_data = None
    selected_status = None
    cards_by_status = []
    selected_user = None
    user_operations = []
    selected_offload = None
    cards_by_offload = []

    if request.method == 'POST':
        action = request.form.get('action')  # Identifier l'origine du formulaire
        current_tab = request.form.get('current_tab', current_tab)

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
                    .as_scalar(),
                    db.session.query(Operation.username)
                    .filter(Operation.card_name == Card.card_name)
                    .order_by(Operation.timestamp.desc())
                    .limit(1)
                    .as_scalar()
                ).filter(Card.statut_geo == selected_status).all()




        elif action == "user_focus":
            current_tab = "user_focus"
            selected_user = request.form.get('selected_user')
            if selected_user:
                # Récupérer les 100 dernières opérations de l'utilisateur sélectionné
                user_operations = Operation.query.filter_by(username=selected_user)\
                    .order_by(Operation.timestamp.desc())\
                    .limit(100).all()

        elif action == "offload_focus":
            current_tab = "offload_focus"
            selected_offload = request.form.get('selected_offload')
            if selected_offload:
                # Récupérer les cartes associées au statut offload avec leur dernière opération et utilisateur
                cards_by_offload = db.session.query(
                    Card,
                    db.session.query(Operation.timestamp)
                    .filter(Operation.card_name == Card.card_name)
                    .order_by(Operation.timestamp.desc())
                    .limit(1)
                    .as_scalar().label('last_timestamp'),
                    db.session.query(Operation.username)
                    .filter(Operation.card_name == Card.card_name)
                    .order_by(Operation.timestamp.desc())
                    .limit(1)
                    .as_scalar().label('last_user')
                ).filter(Card.offload_status == selected_offload).all()

        elif action == "card_focus":
            current_tab = "card_focus"
            selected_card = request.form.get('selected_card')
            if selected_card:
                # Charger les informations de la carte et les opérations associées
                card_info = Card.query.filter_by(card_name=selected_card).first()
                operations = Operation.query.filter_by(card_name=selected_card).all()

                # Formater les données pour TimelineJS
                timeline_data = {
                    "events": [],
                    "default_position": len(operations) - 1  # Index du dernier événement
                }
                for op in operations:
                    try:
                        timestamp = datetime.strptime(op.timestamp, '%Y%m%d-%H:%M:%S')
                        timeline_data["events"].append({
                            "start_date": {
                                "year": timestamp.year,
                                "month": timestamp.month,
                                "day": timestamp.day,
                                "hour": timestamp.hour,
                                "minute": timestamp.minute
                            },
                            "text": {
                                "headline": f"Position : {op.statut_geo} / {op.offload_status} ",
                                "text": f"Carte: {op.card_name} | User: {op.username} | Statut géo: {op.statut_geo} | Statut Offload: {op.offload_status}"
                            }
                        })
                    except ValueError:
                        print(f"Erreur de conversion de la date pour l'opération {op.id}: {op.timestamp}")

    return render_template(
        'spot.html',
        cards=cards,
        status_geo=status_geo,
        users=users,
        selected_card=selected_card,
        card_info=card_info,
        timeline_data=timeline_data,
        selected_status=selected_status,
        cards_by_status=cards_by_status,
        selected_user=selected_user,
        user_operations=user_operations,
        current_tab=current_tab,
        offload_statuses=offload_statuses,  # Ajout des statuts offload
        selected_offload=selected_offload,  # Ajout du statut offload sélectionné
        cards_by_offload=cards_by_offload  # Ajout des cartes filtrées par statut offload
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
