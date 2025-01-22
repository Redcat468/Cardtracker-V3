from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db  # Modification cruciale ici
from models import User, Operation, Card, StatusGeo, CanceledOperation, OffloadStatus
from datetime import datetime



# Route de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')  # Utiliser get() au lieu de []
        
        if not username or not password:
            flash("Veuillez remplir tous les champs", "danger")
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash("Connexion réussie.", "success")
            return redirect(request.args.get('next') or url_for('track'))
        else:
            flash("Identifiants incorrects.", "danger")
    
    return render_template('login.html')

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
    status_geo = StatusGeo.query.all()
    offload_statuses = OffloadStatus.query.all()
    operations = Operation.query.order_by(Operation.timestamp.desc()).limit(50).all()

    # Préchargement des valeurs
    preloaded_source = request.args.get('source', '')
    preloaded_card = request.args.get('card', '')

    # Variables pour la persistance des champs
    selected_source = preloaded_source
    selected_target = ''
    selected_card = preloaded_card
    offload_only = False

    available_cards = []  # Cartes à afficher dans le datalist

    if request.method == 'POST':
        selected_source = request.form.get('source', preloaded_source)
        selected_target = request.form.get('target', selected_source)
        selected_card = request.form.get('card', preloaded_card)
        offload_only = request.form.get('no_move') == 'on'
        offload_status = request.form.get('offload_status')

        if selected_card:
            card = Card.query.filter_by(card_name=selected_card).first()
            if card:
                if card.quarantine:
                    flash("Cette carte est en quarantaine et ne peut pas être déplacée", "danger")
                    return redirect(url_for('track', source=selected_source, card=selected_card))

                if offload_only:
                    selected_target = selected_source

                new_operation = Operation(
                    username=current_user.username,
                    card_name=selected_card,
                    statut_geo=selected_target,
                    timestamp=datetime.now().strftime('%Y%m%d-%H:%M:%S'),
                    offload_status=offload_status
                )
                db.session.add(new_operation)
                card.statut_geo = selected_target
                card.offload_status = offload_status
                card.last_operation = datetime.now()
                card.usage += 1
                db.session.commit()
                flash(f"Carte {selected_card} déplacée avec succès et statut offload mis à jour.")
            else:
                flash("Carte introuvable.")
        else:
            flash("Veuillez sélectionner une carte.")

    # Récupérer les cartes disponibles pour la source sélectionnée
    if selected_source:
        available_cards = Card.query.filter_by(statut_geo=selected_source).all()

    return render_template(
        'track.html',
        status_geo=status_geo,
        offload_statuses=offload_statuses,
        operations=operations,
        preloaded_source=preloaded_source,
        preloaded_card=preloaded_card,
        selected_source=selected_source,
        selected_target=selected_target,
        offload_only=offload_only,
        available_cards=available_cards
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

@app.route('/refresh_cards', methods=['GET'])
@login_required
def refresh_cards():
    cards = Card.query.filter_by(quarantine=False).all()
    return jsonify([{
        "card_name": card.card_name,
        "statut_geo": card.statut_geo
    } for card in cards])

@app.route('/get_cards_by_status/<status>', methods=['GET'])
@login_required
def get_cards_by_status(status):
    # Récupération actualisée depuis la base
    cards = Card.query.filter(
        Card.statut_geo == status,
        Card.quarantine == False
    ).all()
    
    return jsonify([{
        "card_name": card.card_name,
        "quarantine": card.quarantine,
        "statut_geo": card.statut_geo
    } for card in cards])



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
        return jsonify({
            "offload_status": card.offload_status,
            "quarantine": card.quarantine  # Ajout de l'état de quarantaine
        })
    return jsonify({"offload_status": "Non défini", "quarantine": False}), 404

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

    # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))

    current_tab = request.form.get('current_tab') or request.args.get('current_tab', 'card_manager')
    print(f"Current tab: {current_tab}")
    cards = Card.query.all()
    users = User.query.all()
    status_geo = StatusGeo.query.all()
    offload_statuses = OffloadStatus.query.all()

    selected_card = None
    selected_user = None
    selected_status_geo = None
    selected_offload_status = None  # Initialiser la variable par défaut

    if request.method == 'POST':
        action = request.form.get('action')
        
        if current_tab == "card_manager":
            selected_card_name = request.form.get('selected_card')
            if selected_card_name:
                selected_card = Card.query.filter_by(card_name=selected_card_name).first()

        elif current_tab == "user_manager":
            if action == 'edit_user':
                selected_user_id = request.form.get('selected_user')
                if selected_user_id:
                    selected_user = User.query.get(selected_user_id)

        elif request.method == 'POST' and current_tab == "geo_manager":
            action = request.form.get('action')
            print(f"Action: {action}")
            
            if action == 'edit_status_geo':
                selected_status_geo_id = request.form.get('selected_status_geo')
                print(f"Selected status ID: {selected_status_geo_id}")                
                if selected_status_geo_id:
                    selected_status_geo = StatusGeo.query.get(int(selected_status_geo_id))
                    print(f"Found status: {selected_status_geo.status_name if selected_status_geo else None}")

        elif current_tab == "offload_manager":
            action = request.form.get('action')
            if action == 'edit_offload_status':
                selected_offload_status_id = request.form.get('selected_offload_status')
                if selected_offload_status_id:
                    selected_offload_status = OffloadStatus.query.get(int(selected_offload_status_id))


    return render_template(
        'manage.html',
        current_tab=current_tab,
        cards=cards,
        users=users,
        status_geo=status_geo,
        offload_statuses=offload_statuses,
        selected_card_info=selected_card,
        selected_user=selected_user,
        selected_status_geo=selected_status_geo,
        selected_offload_status=selected_offload_status  # Assurez-vous que cette variable est bien transmise
    )


@app.route('/create_card', methods=['GET', 'POST'])
@login_required
def create_card():
    # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
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
    # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
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
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        level = request.form.get('level')

        if username and level.isdigit():
            new_user = User(username=username, level=int(level))
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(f"L'utilisateur {username} a été créé avec succès.", "success")
            return redirect(url_for('manage', current_tab='user_manager'))
        else:
            flash("Veuillez remplir tous les champs correctement.", "danger")

    return render_template('add_user.html')


@app.route('/create_user', methods=['POST'])
@login_required
def create_user():
    # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
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
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
    
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    password = request.form.get('password')
    level = request.form.get('level')

    user = User.query.get(user_id)
    if user:
        user.username = username
        if password:  # Si un nouveau mot de passe est fourni
            user.set_password(password)
        user.level = level
        db.session.commit()
        flash(f"Utilisateur '{username}' mis à jour avec succès.", "success")
    else:
        flash("Utilisateur introuvable.", "danger")

    return redirect(url_for('manage', current_tab='user_manager'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
        # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
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
        # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
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
        # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
    status_geo_id = request.form.get('status_geo_id')
    status_name = request.form.get('status_name')
    
    status = StatusGeo.query.get(status_geo_id)
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
        # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
    status = StatusGeo.query.get(status_id)
    if status:
        print(f"Tentative de suppression : {status.status_name} (ID: {status.id})")  # Debug
        db.session.delete(status)
        db.session.commit()
        flash(f"Statut géographique '{status.status_name}' supprimé avec succès.", "success")
    else:
        flash("Statut géographique introuvable.", "danger")

    return redirect(url_for('manage', current_tab='geo_manager'))

@app.route('/add_offload_status', methods=['GET', 'POST'])
@login_required
def add_offload_status():
        # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
    if request.method == 'POST':
        status_name = request.form.get('status_name')
        if status_name:
            new_status = OffloadStatus(status_name=status_name)
            db.session.add(new_status)
            db.session.commit()
            flash(f"Statut d'offload '{status_name}' ajouté avec succès.", "success")
            return redirect(url_for('manage', current_tab='offload_manager'))
        else:
            flash("Le nom du statut est requis.", "danger")

    return render_template('add_offload_status.html')

@app.route('/update_offload_status', methods=['POST'])
@login_required
def update_offload_status():
        # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
    status_id = request.form.get('offload_status_id')
    status_name = request.form.get('status_name')

    status = OffloadStatus.query.get(status_id)
    if status and status_name:
        status.status_name = status_name
        db.session.commit()
        flash(f"Statut d'offload '{status_name}' mis à jour avec succès.", "success")
    else:
        flash("Erreur lors de la mise à jour du statut d'offload.", "danger")

    return redirect(url_for('manage', current_tab='offload_manager'))


@app.route('/delete_offload_status/<int:status_id>', methods=['POST'])
@login_required
def delete_offload_status(status_id):
        # Ajoutez ce code au début de chaque route de gestion
    if current_user.level < 48:
        flash("Accès refusé. Niveau d'autorisation insuffisant.", "danger")
        return redirect(url_for('track'))
    status = OffloadStatus.query.get(status_id)
    if status:
        db.session.delete(status)
        db.session.commit()
        flash(f"Statut d'offload '{status.status_name}' supprimé avec succès.", "success")
    else:
        flash("Statut d'offload introuvable.", "danger")

    return redirect(url_for('manage', current_tab='offload_manager'))