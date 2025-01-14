from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Operation, Card, StatusGeo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime

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
            return redirect(url_for('track'))
        else:
            flash("Nom d'utilisateur incorrect.")
    return render_template('login.html')

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

# Route principale pour le tracking des cartes
@app.route('/track', methods=['GET', 'POST'])
@login_required
def track():
    retour_cartes = Card.query.filter_by(quarantine=False).filter(Card.statut_geo != 'POST-PROD').all()
    sortie_cartes = Card.query.filter_by(statut_geo='POST-PROD', quarantine=False).all()
    status_geo = StatusGeo.query.filter(StatusGeo.status_name != 'POST-PROD').all()

    if request.method == 'POST':
        if 'retour' in request.form:
            card_name = request.form['retour_card']
            card = Card.query.filter_by(card_name=card_name).first()
            if card:
                new_operation = Operation(
                    username=current_user.username,
                    card_name=card_name,
                    statut_geo='POST-PROD',
                    timestamp=datetime.now().strftime('%Y%m%d-%H:%M:%S')
                )
                db.session.add(new_operation)
                card.statut_geo = 'POST-PROD'
                db.session.commit()
                flash(f"Carte {card_name} retournée à la post-prod.")
        elif 'sortie' in request.form:
            card_name = request.form['sortie_card']
            statut_geo = request.form['status_geo']
            card = Card.query.filter_by(card_name=card_name).first()
            if card:
                new_operation = Operation(
                    username=current_user.username,
                    card_name=card_name,
                    statut_geo=statut_geo,
                    timestamp=datetime.now().strftime('%Y%m%d-%H:%M:%S')
                )
                db.session.add(new_operation)
                card.statut_geo = statut_geo
                db.session.commit()
                flash(f"Carte {card_name} envoyée au statut {statut_geo}.")
        
        return redirect(url_for('track'))

    operations = Operation.query.filter_by(username=current_user.username).order_by(Operation.timestamp.desc()).limit(50).all()

    return render_template('track.html', retour_cartes=retour_cartes, sortie_cartes=sortie_cartes, status_geo=status_geo, operations=operations)


# Route pour annuler une opération
@app.route('/cancel_operation/<int:operation_id>', methods=['POST'])
@login_required
def cancel_operation(operation_id):
    operation = Operation.query.get(operation_id)
    if operation:
        # Récupérer la carte associée à l'opération
        card = Card.query.filter_by(card_name=operation.card_name).first()

        # Supprimer l'opération actuelle
        db.session.delete(operation)
        db.session.commit()

        # Trouver la dernière opération pour cette carte
        last_operation = Operation.query.filter_by(card_name=card.card_name).order_by(Operation.timestamp.desc()).first()

        # Mettre à jour le statut géo de la carte avec la dernière opération
        if last_operation:
            card.statut_geo = last_operation.statut_geo
        else:
            card.statut_geo = 'INCONNU'  # Statut par défaut si aucune opération précédente n'existe

        db.session.commit()
        flash(f"L'opération a été annulée et la carte {card.card_name} a été mise à jour avec le statut géo {card.statut_geo}.")
    else:
        flash("Opération introuvable.")

    return redirect(url_for('track'))

# Route pour afficher les opérations de "Spot"
from datetime import datetime

@app.route('/spot', methods=['GET', 'POST'])
@login_required
def spot():
    # Récupérer toutes les cartes de la table CARDS
    cards = Card.query.all()

    selected_card = None
    card_info = None
    timeline_data = None

    if request.method == 'POST':
        selected_card = request.form.get('selected_card')

        # Si une carte est sélectionnée, récupérer ses informations
        if selected_card:
            card_info = Card.query.filter_by(card_name=selected_card).first()
            operations = Operation.query.filter_by(card_name=selected_card).all()

            # Formater les données pour TimelineJS
            timeline_data = []
            for op in operations:
                try:
                    timestamp = datetime.strptime(op.timestamp, '%Y%m%d-%H:%M:%S')

                    # Ajouter les données de timeline
                    timeline_data.append({
                        "start_date": {
                            "year": timestamp.year,
                            "month": timestamp.month,
                            "day": timestamp.day,
                            "hour": timestamp.hour,
                            "minute": timestamp.minute
                        },
                        "text": {
                            "headline": f"Position : {op.statut_geo}",
                            "text": f"Carte: {op.card_name} | User: {op.username} | Statut géo: {op.statut_geo}"
                        }
                    })
                except ValueError:
                    print(f"Erreur de conversion de la date pour l'opération {op.id}: {op.timestamp}")

    return render_template('spot.html', cards=cards, selected_card=selected_card, card_info=card_info, timeline_data=timeline_data)

@app.route('/offload')
@login_required
def offload():
    return render_template('offload.html')


@app.route('/card-focus', methods=['GET', 'POST'])
def card_focus():
    # Logique pour gérer l'affichage des détails de la carte
    selected_card = request.form.get('selected_card', None)
    card_details = None
    if selected_card:
        card_details = Card.query.filter_by(card_name=selected_card).first()
    
    return render_template('spot.html', card_details=card_details)


# Route pour les utilisateurs administrateurs
@app.route('/manage')
@login_required
def manage():
    if current_user.level >= 47:
        return render_template('manage.html')
    return redirect(url_for('track'))

# Lancement de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
