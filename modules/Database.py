import mysql.connector
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    """Classe pour gérer la connexion et les opérations sur la base de données"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Établit la connexion à la base de données"""
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
        """Vérifie et rétablit la connexion si nécessaire"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connect()
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la connexion : {str(e)}")
            self.connect()
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Connexion à la base de données fermée")
    
    # ==================== GIVEAWAYS ====================
    
    def create_giveaway(
        self,
        giveaway_id: str,
        server_id: str,
        channel_id: str,
        title: str,
        prizes: List[str],
        winner_count: int,
        end_date: datetime,
        organizer_id: str,
        conditions: Optional[str] = None
    ) -> bool:
        """Crée un nouveau giveaway dans la base de données"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            
            # Convertir la liste des prix en JSON
            prizes_json = json.dumps(prizes, ensure_ascii=False)
            
            query = """
                INSERT INTO giveaways (
                    giveaway_id, server_id, giveaway_channel_id, giveaway_title,
                    giveaway_prizes, giveaway_winner_count, giveaway_end_date,
                    giveaway_organizer_id, giveaway_participants, giveaway_conditions, giveaway_is_finished
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                giveaway_id, server_id, channel_id, title, prizes_json,
                winner_count, end_date, organizer_id, json.dumps([]), conditions, False
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            
            logging.info(f"Giveaway {giveaway_id} créé dans la base de données")
            return True
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors de la création du giveaway : {str(e)}")
            return False
    
    def update_giveaway_message_id(self, giveaway_id: str, message_id: int) -> bool:
        """Met à jour l'ID du message d'un giveaway"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            
            query = "UPDATE giveaways SET giveaway_message_id = %s WHERE giveaway_id = %s"
            cursor.execute(query, (str(message_id), giveaway_id))
            
            self.connection.commit()
            cursor.close()
            
            return True
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors de la mise à jour du message_id : {str(e)}")
            return False
    
    def add_participant(self, giveaway_id: str, user_id: int) -> bool:
        """Ajoute un participant à un giveaway"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            
            # Récupérer les participants actuels
            query = "SELECT giveaway_participants FROM giveaways WHERE giveaway_id = %s"
            cursor.execute(query, (giveaway_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                return False
            
            participants = json.loads(result[0]) if result[0] else []
            
            # Vérifier si l'utilisateur participe déjà
            if user_id in participants:
                cursor.close()
                return False
            
            # Ajouter le participant
            participants.append(user_id)
            
            # Mettre à jour la base de données
            update_query = "UPDATE giveaways SET giveaway_participants = %s WHERE giveaway_id = %s"
            cursor.execute(update_query, (json.dumps(participants), giveaway_id))
            
            self.connection.commit()
            cursor.close()
            
            return True
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors de l'ajout du participant : {str(e)}")
            return False
    
    def remove_participant(self, giveaway_id: str, user_id: int) -> bool:
        """Retire un participant d'un giveaway"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            
            # Récupérer les participants actuels
            query = "SELECT giveaway_participants FROM giveaways WHERE giveaway_id = %s"
            cursor.execute(query, (giveaway_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                return False
            
            participants = json.loads(result[0]) if result[0] else []
            
            # Vérifier si l'utilisateur participe
            if user_id not in participants:
                cursor.close()
                return False
            
            # Retirer le participant
            participants.remove(user_id)
            
            # Mettre à jour la base de données
            update_query = "UPDATE giveaways SET giveaway_participants = %s WHERE giveaway_id = %s"
            cursor.execute(update_query, (json.dumps(participants), giveaway_id))
            
            self.connection.commit()
            cursor.close()
            
            return True
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors du retrait du participant : {str(e)}")
            return False
    
    def get_giveaway(self, giveaway_id: str) -> Optional[Dict]:
        """Récupère un giveaway par son ID"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = "SELECT * FROM giveaways WHERE giveaway_id = %s"
            cursor.execute(query, (giveaway_id,))
            result = cursor.fetchone()
            
            cursor.close()
            
            if result:
                # Convertir les champs JSON
                result['giveaway_prizes'] = json.loads(result['giveaway_prizes'])
                result['giveaway_participants'] = json.loads(result['giveaway_participants']) if result['giveaway_participants'] else []
                
            return result
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors de la récupération du giveaway : {str(e)}")
            return None
    
    def get_active_giveaways(self, server_id: Optional[str] = None) -> List[Dict]:
        """Récupère tous les giveaways actifs (non terminés)"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            if server_id:
                query = "SELECT * FROM giveaways WHERE giveaway_is_finished = FALSE AND server_id = %s"
                cursor.execute(query, (server_id,))
            else:
                query = "SELECT * FROM giveaways WHERE giveaway_is_finished = FALSE"
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            
            # Convertir les champs JSON
            for result in results:
                result['giveaway_prizes'] = json.loads(result['giveaway_prizes'])
                result['giveaway_participants'] = json.loads(result['giveaway_participants']) if result['giveaway_participants'] else []
            
            return results
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors de la récupération des giveaways actifs : {str(e)}")
            return []
    
    def get_active_giveaway_by_channel(self, channel_id: str) -> Optional[Dict]:
        """Récupère le giveaway actif d'un canal spécifique"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT * FROM giveaways 
                WHERE giveaway_channel_id = %s AND giveaway_is_finished = FALSE
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor.execute(query, (channel_id,))
            result = cursor.fetchone()
            
            cursor.close()
            
            if result:
                # Convertir les champs JSON
                result['giveaway_prizes'] = json.loads(result['giveaway_prizes'])
                result['giveaway_participants'] = json.loads(result['giveaway_participants']) if result['giveaway_participants'] else []
            
            return result
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors de la récupération du giveaway par canal : {str(e)}")
            return None
    
    def mark_giveaway_finished(self, giveaway_id: str) -> bool:
        """Marque un giveaway comme terminé"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            
            query = "UPDATE giveaways SET giveaway_is_finished = TRUE WHERE giveaway_id = %s"
            cursor.execute(query, (giveaway_id,))
            
            self.connection.commit()
            cursor.close()
            
            return True
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors du marquage du giveaway comme terminé : {str(e)}")
            return False
    
    def delete_giveaway(self, giveaway_id: str) -> bool:
        """Supprime un giveaway de la base de données"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            
            query = "DELETE FROM giveaways WHERE giveaway_id = %s"
            cursor.execute(query, (giveaway_id,))
            
            self.connection.commit()
            cursor.close()
            
            return True
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors de la suppression du giveaway : {str(e)}")
            return False
    
    def get_giveaway_by_message_id(self, message_id: str) -> Optional[Dict]:
        """Récupère un giveaway par son ID de message"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = "SELECT * FROM giveaways WHERE giveaway_message_id = %s"
            cursor.execute(query, (message_id,))
            result = cursor.fetchone()
            
            cursor.close()
            
            if result:
                # Convertir les champs JSON
                result['giveaway_prizes'] = json.loads(result['giveaway_prizes'])
                result['giveaway_participants'] = json.loads(result['giveaway_participants']) if result['giveaway_participants'] else []
                
            return result
            
        except mysql.connector.Error as e:
            logging.error(f"Erreur lors de la récupération du giveaway par message_id : {str(e)}")
            return None


# Instance globale de la base de données
db = Database()
