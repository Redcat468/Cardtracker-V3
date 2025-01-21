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

@app.route('/update_card', methods=['POST'])
@login_required
def update_card():
    card_id = request.form.get('card_id')
    offload_status = request.form.get('offload_status')
    statut_geo = request.form.get('statut_geo')
    quarantine = request.form.get('quarantine') == 'on'
    capacity = request.form.get('capacity')
    brand = request.form.get('brand')
    card_type = request.form.get('card_type')

    card = Card.query.get(card_id)
    if card:
        # Conserver les anciens statuts pour l'opération
        old_geo_status = card.statut_geo
        old_offload_status = card.offload_status

        # Mise à jour de la carte
        card.offload_status = offload_status
        card.statut_geo = statut_geo
        card.quarantine = quarantine
        card.capacity = capacity
        card.brand = brand
        card.card_type = card_type
        card.last_operation = datetime.now()

        # Ajouter une ligne dans la table Operation
        new_operation = Operation(
            username=current_user.username,
            card_name=card.card_name,
            statut_geo=statut_geo,
            offload_status=offload_status,
            timestamp=datetime.now().strftime('%Y%m%d-%H:%M:%S')
        )
        db.session.add(new_operation)

        # Sauvegarder les modifications dans la base de données
        db.session.commit()
        flash(f"Carte {card.card_name} mise à jour avec succès.", "success")
    else:
        flash("Carte introuvable.", "danger")

    return redirect(url_for('manage', current_tab='card_manager'))



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
                card_info = Card.query.filter_by(card_name=selected_card).first()
                operations = Operation.query.filter_by(card_name=selected_card).all()

                timeline_data = {
                    "events": [],
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
                                "headline": f"Position : {op.statut_geo} / {op.offload_status}",
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


@app.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    # Déterminer l'onglet actif
    current_tab = request.form.get('current_tab') or request.args.get('current_tab', 'card_manager')

    # Charger les données nécessaires pour les onglets
    cards = Card.query.all()
    users = User.query.all()
    status_geo = StatusGeo.query.all()
    offload_statuses = OffloadStatus.query.all()

    # Variables spécifiques pour chaque onglet
    selected_card = None
    selected_user = None
    selected_status_geo = None

    # Gestion des actions selon l'onglet actif
    if current_tab == "card_manager":
        selected_card_name = request.form.get('selected_card')
        if selected_card_name:
            selected_card = Card.query.filter_by(card_name=selected_card_name).first()

    elif current_tab == "user_manager":
        selected_user_id = request.form.get('selected_user')
        if selected_user_id:
            selected_user = User.query.get(selected_user_id)

    elif current_tab == "geo_manager":
        print(f"DEBUG: Statut en selection")
        selected_status_geo_id = request.form.get('selected_status_geo')
        if selected_status_geo_id:
            selected_status_geo = StatusGeo.query.get(int(selected_status_geo_id))
            print(f"DEBUG: Statut sélectionné - {selected_status_geo}")

    return render_template(
        'manage.html',
        current_tab=current_tab,
        cards=cards,
        users=users,
        status_geo=status_geo,
        offload_statuses=offload_statuses,
        selected_card_info=selected_card,
        selected_user=selected_user,
        selected_status_geo=selected_status_geo  # Transmettre le statut sélectionné
    )



@app.route('/create_card', methods=['GET', 'POST'])
@login_required
def create_card():
    # Récupérer les statuts géographiques et offload pour les menus déroulants
    status_geo = StatusGeo.query.all()
    offload_statuses = OffloadStatus.query.all()

    if request.method == 'POST':
        # Logique pour créer une carte
        card_name = request.form.get('card_name')
        card_birth = request.form.get('card_birth')
        quarantine = bool(request.form.get('quarantine'))
        statut_geo = request.form.get('statut_geo')
        offload_status = request.form.get('offload_status')
        capacity = request.form.get('capacity')
        brand = request.form.get('brand')
        card_type = request.form.get('card_type')

        # Vérifier que le nom de la carte est unique
        existing_card = Card.query.filter_by(card_name=card_name).first()
        if existing_card:
            flash(f"Une carte avec le nom '{card_name}' existe déjà.", "danger")
        else:
            new_card = Card(
                card_name=card_name,
                card_birth=datetime.strptime(card_birth, '%Y-%m-%dT%H:%M:%S'),
                quarantine=quarantine,
                statut_geo=statut_geo,
                offload_status=offload_status,
                capacity=int(capacity),
                brand=brand,
                card_type=card_type,
            )
            db.session.add(new_card)
            db.session.commit()
            flash(f"Carte '{card_name}' créée avec succès.", "success")
            return redirect(url_for('manage'))

    return render_template(
        'create_card.html', 
        status_geo=status_geo, 
        offload_statuses=offload_statuses, 
        datetime=datetime  # Passer datetime au contexte
    )


@app.route('/delete_card/<int:card_id>', methods=['POST'])
@login_required
def delete_card(card_id):
    card = Card.query.get(card_id)
    if card:
        db.session.delete(card)
        db.session.commit()
        flash(f"La carte {card.card_name} a été supprimée avec succès.", "success")
    else:
        flash("Carte introuvable.", "danger")
    return redirect(url_for('manage', current_tab='card_manager'))


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        level = request.form.get('level')

        if username and level.isdigit():
            new_user = User(username=username, level=int(level))
            db.session.add(new_user)
            db.session.commit()
            flash(f"L'utilisateur {username} a été créé avec succès.", "success")
        else:
            flash("Veuillez entrer un nom d'utilisateur valide et un niveau valide.", "danger")

        # Rediriger vers User Manager après ajout
        return redirect(url_for('manage', current_tab='user_manager'))

    return render_template('add_user.html')


@app.route('/create_user', methods=['POST'])
@login_required
def create_user():
    # Logique pour créer un utilisateur
    username = request.form.get('username')
    level = request.form.get('level')

    if username and level:
        # Créer et ajouter l'utilisateur à la base de données
        new_user = User(username=username, level=level)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Utilisateur '{username}' créé avec succès.", "success")
    else:
        flash("Veuillez remplir tous les champs.", "danger")

    return redirect(url_for('manage'))

@app.route('/update_user', methods=['POST'])
@login_required
def update_user():
    # Logique pour mettre à jour un utilisateur
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    level = request.form.get('level')

    user = User.query.get(user_id)
    if user:
        user.username = username
        user.level = level
        db.session.commit()
        flash(f"Utilisateur '{username}' mis à jour avec succès.", "success")
    else:
        flash("Utilisateur introuvable.", "danger")

    return redirect(url_for('manage', current_tab='user_manager'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    print(f"Route delete_user appelée pour user_id : {user_id}")
    # Vérifier que l'utilisateur existe
    user = User.query.get(user_id)
    if user:
        try:
            db.session.delete(user)
            db.session.commit()
            flash(f"Utilisateur '{user.username}' supprimé avec succès.", "success")
            print(f"Utilisateur trouvé : {user.username}")  # Pour debug
        except Exception as e:
            db.session.rollback()  # Annuler les modifications en cas d'erreur
            flash(f"Erreur lors de la suppression de l'utilisateur : {str(e)}", "danger")
    else:
        flash("Utilisateur introuvable.", "danger")

    # Rester dans l'onglet User Manager après la suppression
    return redirect(url_for('manage', current_tab='user_manager'))


@app.route('/add_geo_status', methods=['GET', 'POST'])
@login_required
def add_geo_status():
    if request.method == 'POST':
        status_name = request.form.get('status_name')
        if status_name:
            new_status = StatusGeo(status_name=status_name)
            db.session.add(new_status)
            db.session.commit()
            flash(f"Statut géographique '{status_name}' ajouté avec succès.", "success")
            return redirect(url_for('manage', current_tab='geo_manager'))
        else:
            flash("Le nom du statut est requis.", "danger")

    return render_template('add_geo_status.html')


@app.route('/update_geo_status', methods=['POST'])
@login_required
def update_geo_status():
    status_id = request.form.get('status_id')
    status_name = request.form.get('status_name')
    status = StatusGeo.query.get(status_id)
    if status and status_name:
        status.status_name = status_name
        db.session.commit()
        flash(f"Statut géographique '{status_name}' mis à jour avec succès.", "success")
    else:
        flash("Erreur lors de la mise à jour du statut géographique.", "danger")

    return redirect(url_for('manage', current_tab='geo_manager'))

@app.route('/delete_status_geo/<int:status_id>', methods=['POST'])
@login_required
def delete_status_geo(status_id):
    status = StatusGeo.query.get(status_id)
    if status:
        db.session.delete(status)
        db.session.commit()
        flash(f"Statut géographique '{status.status_name}' supprimé avec succès.", "success")
    else:
        flash("Statut géographique introuvable.", "danger")

    return redirect(url_for('manage', current_tab='geo_manager'))



# Lancement de l'application Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
