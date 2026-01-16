import mysql.connector
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "shadow_bot"),
                port=int(os.getenv("DB_PORT", "3306"))
            )
            logging.info("Connexion à la base de données établie")
        except mysql.connector.Error as e:
            logging.error(f"Erreur de connexion à la base de données : {str(e)}")
            raise
    
    def ensure_connection(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connect()
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la connexion : {str(e)}")
            self.connect()
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Connexion à la base de données fermée")
    
    def create_giveaway(self, giveaway_id: str, server_id: str, channel_id: str, title: str,
                       prizes: List[str], winner_count: int, end_date: datetime, organizer_id: str,
                       conditions: Optional[str] = None) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            query = """INSERT INTO giveaways (giveaway_id, server_id, giveaway_channel_id, giveaway_title,
                       giveaway_prizes, giveaway_winner_count, giveaway_end_date, giveaway_organizer_id,
                       giveaway_participants, giveaway_conditions, giveaway_is_finished)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (giveaway_id, server_id, channel_id, title, json.dumps(prizes, ensure_ascii=False),
                     winner_count, end_date, organizer_id, json.dumps([]), conditions, False)
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            logging.info(f"Giveaway {giveaway_id} créé")
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur création giveaway : {str(e)}")
            return False
    
    def update_giveaway_message_id(self, giveaway_id: str, message_id: int) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("UPDATE giveaways SET giveaway_message_id = %s WHERE giveaway_id = %s",
                         (str(message_id), giveaway_id))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur mise à jour message_id : {str(e)}")
            return False
    
    def add_participant(self, giveaway_id: str, user_id: int) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("SELECT giveaway_participants FROM giveaways WHERE giveaway_id = %s", (giveaway_id,))
            result = cursor.fetchone()
            if not result:
                cursor.close()
                return False
            participants = json.loads(result[0]) if result[0] else []
            if user_id in participants:
                cursor.close()
                return False
            participants.append(user_id)
            cursor.execute("UPDATE giveaways SET giveaway_participants = %s WHERE giveaway_id = %s",
                         (json.dumps(participants), giveaway_id))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur ajout participant : {str(e)}")
            return False
    
    def remove_participant(self, giveaway_id: str, user_id: int) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("SELECT giveaway_participants FROM giveaways WHERE giveaway_id = %s", (giveaway_id,))
            result = cursor.fetchone()
            if not result:
                cursor.close()
                return False
            participants = json.loads(result[0]) if result[0] else []
            if user_id not in participants:
                cursor.close()
                return False
            participants.remove(user_id)
            cursor.execute("UPDATE giveaways SET giveaway_participants = %s WHERE giveaway_id = %s",
                         (json.dumps(participants), giveaway_id))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur retrait participant : {str(e)}")
            return False
    
    def get_giveaway(self, giveaway_id: str) -> Optional[Dict]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM giveaways WHERE giveaway_id = %s", (giveaway_id,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                result['giveaway_prizes'] = json.loads(result['giveaway_prizes'])
                result['giveaway_participants'] = json.loads(result['giveaway_participants']) if result['giveaway_participants'] else []
            return result
        except mysql.connector.Error as e:
            logging.error(f"Erreur récupération giveaway : {str(e)}")
            return None
    
    def get_active_giveaways(self, server_id: Optional[str] = None) -> List[Dict]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            if server_id:
                cursor.execute("SELECT * FROM giveaways WHERE giveaway_is_finished = FALSE AND server_id = %s", (server_id,))
            else:
                cursor.execute("SELECT * FROM giveaways WHERE giveaway_is_finished = FALSE")
            results = cursor.fetchall()
            cursor.close()
            for result in results:
                result['giveaway_prizes'] = json.loads(result['giveaway_prizes'])
                result['giveaway_participants'] = json.loads(result['giveaway_participants']) if result['giveaway_participants'] else []
            return results
        except mysql.connector.Error as e:
            logging.error(f"Erreur récupération giveaways actifs : {str(e)}")
            return []
    
    def get_active_giveaway_by_channel(self, channel_id: str) -> Optional[Dict]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            query = """SELECT * FROM giveaways WHERE giveaway_channel_id = %s AND giveaway_is_finished = FALSE
                       ORDER BY created_at DESC LIMIT 1"""
            cursor.execute(query, (channel_id,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                result['giveaway_prizes'] = json.loads(result['giveaway_prizes'])
                result['giveaway_participants'] = json.loads(result['giveaway_participants']) if result['giveaway_participants'] else []
            return result
        except mysql.connector.Error as e:
            logging.error(f"Erreur récupération giveaway par canal : {str(e)}")
            return None
    
    def mark_giveaway_finished(self, giveaway_id: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("UPDATE giveaways SET giveaway_is_finished = TRUE WHERE giveaway_id = %s", (giveaway_id,))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur marquage giveaway terminé : {str(e)}")
            return False
    
    def delete_giveaway(self, giveaway_id: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM giveaways WHERE giveaway_id = %s", (giveaway_id,))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur suppression giveaway : {str(e)}")
            return False
    
    def get_giveaway_by_message_id(self, message_id: str) -> Optional[Dict]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM giveaways WHERE giveaway_message_id = %s", (message_id,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                result['giveaway_prizes'] = json.loads(result['giveaway_prizes'])
                result['giveaway_participants'] = json.loads(result['giveaway_participants']) if result['giveaway_participants'] else []
            return result
        except mysql.connector.Error as e:
            logging.error(f"Erreur récupération giveaway par message_id : {str(e)}")
            return None

db = Database()
