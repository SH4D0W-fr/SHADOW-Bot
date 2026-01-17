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

    def create_ticket(self, server_id: str, channel_id: str, owner_id: str, type_key: str, members: List[int] = None) -> Optional[int]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            members_json = json.dumps(members if members else [int(owner_id)])
            query = """INSERT INTO tickets (server_id, channel_id, owner_id, type_key, members)
                       VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query, (server_id, channel_id, owner_id, type_key, members_json))
            self.connection.commit()
            ticket_id = cursor.lastrowid
            cursor.close()
            logging.info(f"Ticket {ticket_id} créé pour le serveur {server_id}, canal {channel_id}")
            return ticket_id
        except mysql.connector.Error as e:
            logging.error(f"Erreur création ticket : {str(e)}")
            return None
    
    def get_ticket_by_channel(self, channel_id: str) -> Optional[Dict]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tickets WHERE channel_id = %s", (channel_id,))
            result = cursor.fetchone()
            cursor.close()
            if result and result.get('members'):
                result['members'] = json.loads(result['members'])
            return result
        except mysql.connector.Error as e:
            logging.error(f"Erreur récupération ticket : {str(e)}")
            return None
    
    def get_user_tickets(self, server_id: str, owner_id: str, is_closed: bool = False) -> List[Dict]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            query = """SELECT * FROM tickets WHERE server_id = %s AND owner_id = %s AND is_closed = %s"""
            cursor.execute(query, (server_id, owner_id, is_closed))
            results = cursor.fetchall()
            cursor.close()
            for result in results:
                if result.get('members'):
                    result['members'] = json.loads(result['members'])
            return results
        except mysql.connector.Error as e:
            logging.error(f"Erreur récupération tickets utilisateur : {str(e)}")
            return []
    
    def update_ticket_owner_message(self, channel_id: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("UPDATE tickets SET last_owner_message = NOW() WHERE channel_id = %s", (channel_id,))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur mise à jour message propriétaire : {str(e)}")
            return False
    
    def update_ticket_staff_message(self, channel_id: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("UPDATE tickets SET last_staff_message = NOW() WHERE channel_id = %s", (channel_id,))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur mise à jour message staff : {str(e)}")
            return False
    
    def claim_ticket(self, channel_id: str, staff_id: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("UPDATE tickets SET claimed_by_id = %s WHERE channel_id = %s", (staff_id, channel_id))
            self.connection.commit()
            cursor.close()
            logging.info(f"Ticket {channel_id} réclamé par {staff_id}")
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur claim ticket : {str(e)}")
            return False
    
    def unclaim_ticket(self, channel_id: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("UPDATE tickets SET claimed_by_id = NULL WHERE channel_id = %s", (channel_id,))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur unclaim ticket : {str(e)}")
            return False
    
    def add_ticket_member(self, channel_id: str, member_id: int) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("SELECT members FROM tickets WHERE channel_id = %s", (channel_id,))
            result = cursor.fetchone()
            if not result:
                cursor.close()
                return False
            members = json.loads(result[0]) if result[0] else []
            if member_id not in members:
                members.append(member_id)
                cursor.execute("UPDATE tickets SET members = %s WHERE channel_id = %s",
                             (json.dumps(members), channel_id))
                self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur ajout membre ticket : {str(e)}")
            return False
    
    def remove_ticket_member(self, channel_id: str, member_id: int) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("SELECT members FROM tickets WHERE channel_id = %s", (channel_id,))
            result = cursor.fetchone()
            if not result:
                cursor.close()
                return False
            members = json.loads(result[0]) if result[0] else []
            if member_id in members:
                members.remove(member_id)
                cursor.execute("UPDATE tickets SET members = %s WHERE channel_id = %s",
                             (json.dumps(members), channel_id))
                self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur retrait membre ticket : {str(e)}")
            return False
    
    def close_ticket(self, channel_id: str, closed_by_id: str, reason: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            query = """UPDATE tickets SET is_closed = TRUE, closed_at = NOW(), 
                       closed_by_id = %s, close_reason = %s WHERE channel_id = %s"""
            cursor.execute(query, (closed_by_id, reason, channel_id))
            self.connection.commit()
            cursor.close()
            logging.info(f"Ticket {channel_id} fermé par {closed_by_id}")
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur fermeture ticket : {str(e)}")
            return False
    
    def delete_ticket(self, channel_id: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM tickets WHERE channel_id = %s", (channel_id,))
            self.connection.commit()
            cursor.close()
            logging.info(f"Ticket {channel_id} supprimé de la BDD")
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur suppression ticket : {str(e)}")
            return False
    
    def get_all_tickets(self, server_id: str, is_closed: bool = False) -> List[Dict]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM tickets WHERE server_id = %s AND is_closed = %s"
            cursor.execute(query, (server_id, is_closed))
            results = cursor.fetchall()
            cursor.close()
            for result in results:
                if result.get('members'):
                    result['members'] = json.loads(result['members'])
            return results
        except mysql.connector.Error as e:
            logging.error(f"Erreur récupération tous tickets : {str(e)}")
            return []
    
    def set_config(self, server_id: str, config_key: str, config_value: str) -> bool:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            query = """INSERT INTO configurations (server_id, config_key, config_value)
                       VALUES (%s, %s, %s)
                       ON DUPLICATE KEY UPDATE config_value = %s, updated_at = CURRENT_TIMESTAMP"""
            cursor.execute(query, (server_id, config_key, config_value, config_value))
            self.connection.commit()
            cursor.close()
            logging.info(f"Configuration {config_key} définie pour le serveur {server_id}")
            return True
        except mysql.connector.Error as e:
            logging.error(f"Erreur définition configuration : {str(e)}")
            return False
    
    def get_config(self, server_id: str, config_key: str) -> Optional[str]:
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            cursor.execute("SELECT config_value FROM configurations WHERE server_id = %s AND config_key = %s",
                         (server_id, config_key))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except mysql.connector.Error as e:
            logging.error(f"Erreur récupération configuration : {str(e)}")
            return None

db = Database()
