#!/usr/bin/env python3
# monitor_backup.py

import sqlite3
import time
import requests
import os
import sys

# ==== CONFIGURATION ====

# Chemin vers votre fichier SQLite (mode lecture seule)
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'card_tracker.db')

# Votre webhook Discord
WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1357383956106051714/fMm89TZX0pYpfX9-tQXDErUiRIp-YeyAMNyeUKLTg9PWBb7L1iLb3OfAtgqwDvzFqqhQ'

# Statut cible à détecter
TARGET_STATUS = 'TO BACKUP'

# Intervalle entre chaque scan (en secondes)
SCAN_INTERVAL = 10

# ==== FONCTIONS UTILES ====

def get_readonly_connection(db_path):
    """
    Ouvre la base en mode lecture seule pour éviter tout lock.
    """
    uri = f'file:{db_path}?mode=ro'
    return sqlite3.connect(uri, uri=True, check_same_thread=False)

def fetch_last_id(conn):
    """
    Récupère l'ID maximal des opérations déjà en TARGET_STATUS.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT MAX(id) FROM operation
        WHERE offload_status = ?
    """, (TARGET_STATUS,))
    row = cur.fetchone()
    return row[0] or 0

def fetch_new_backups(conn, last_id):
    """
    Récupère les opérations récentes passant en TARGET_STATUS et dont l'id > last_id.
    Inclut le statut géo.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT id, card_name, username, statut_geo
        FROM operation
        WHERE offload_status = ?
          AND id > ?
        ORDER BY id ASC
    """, (TARGET_STATUS, last_id))
    return cur.fetchall()  # liste de tuples (id, card_name, username, statut_geo)

def send_discord_notification(card_name, username, geo_status):
    """
    Envoie un message Discord mentionnant la carte, l'utilisateur et le statut géo.
    """
    content = (
        f":warning: **Carte en To Backup**\n"
        f"• Carte : `{card_name}`\n"
        f"• Par : `{username}`\n"
        f"• Statut Géographique : `{geo_status}`"
    )
    payload = { "content": content }
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Erreur Discord] {e}", file=sys.stderr)

def main():
    # Vérification du fichier
    if not os.path.isfile(DB_PATH):
        print(f"Fichier DB introuvable : {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    # Connexion initiale en lecture seule
    conn = get_readonly_connection(DB_PATH)
    last_id = fetch_last_id(conn)
    conn.close()

    print(f"[Init] Dernier ID notifié : {last_id}")

    # Boucle principale
    while True:
        try:
            conn = get_readonly_connection(DB_PATH)
            new_ops = fetch_new_backups(conn, last_id)
            conn.close()

            for op_id, card, user, geo in new_ops:
                send_discord_notification(card, user, geo)
                last_id = op_id

            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            print("\nArrêt par l'utilisateur.")
            break
        except Exception as e:
            print(f"[Erreur] {e}", file=sys.stderr)
            time.sleep(SCAN_INTERVAL)

if __name__ == '__main__':
    main()
