import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List
from modules.Database import db


class TicketData:
    def __init__(
        self,
        channel_id: int,
        owner_id: int,
        type_key: str,
        server_id: str,
        created_at: datetime = None,
        claimed_by_id: Optional[int] = None,
        last_owner_message: datetime = None,
        last_staff_message: Optional[datetime] = None,
        members: List[int] = None,
        is_closed: bool = False,
        autoclose_task: Optional[asyncio.Task] = None
    ):
        self.channel_id = channel_id
        self.owner_id = owner_id
        self.type_key = type_key
        self.server_id = server_id
        self.created_at = created_at or datetime.now()
        self.claimed_by_id = claimed_by_id
        self.last_owner_message = last_owner_message or datetime.now()
        self.last_staff_message = last_staff_message
        self.members: List[int] = members if members else [owner_id]
        self.is_closed = is_closed
        self.autoclose_task: Optional[asyncio.Task] = autoclose_task

    @classmethod
    def from_db(cls, data: dict) -> "TicketData":
        return cls(
            channel_id=int(data["channel_id"]),
            owner_id=int(data["owner_id"]),
            type_key=data["type_key"],
            server_id=data["server_id"],
            created_at=data.get("created_at"),
            claimed_by_id=int(data["claimed_by_id"]) if data.get("claimed_by_id") else None,
            last_owner_message=data.get("last_owner_message"),
            last_staff_message=data.get("last_staff_message"),
            members=data.get("members", [int(data["owner_id"])]),
            is_closed=data.get("is_closed", False)
        )


class TicketManager:
    def __init__(self, bot):
        self.bot = bot
        self.tickets: Dict[int, TicketData] = {}
        self.logger = logging.getLogger("TicketManager")
        self.autoclose_delays: Dict[int, asyncio.Task] = {}
        
    async def load_from_db(self, server_id: str):
        try:
            tickets_data = db.get_all_tickets(server_id, is_closed=False)
            for ticket_data in tickets_data:
                ticket = TicketData.from_db(ticket_data)
                self.tickets[ticket.channel_id] = ticket
            self.logger.info(f"Chargé {len(tickets_data)} tickets depuis la BDD pour le serveur {server_id}")
        except Exception as e:
            self.logger.error(f"Erreur chargement tickets: {e}")

    def create_ticket(
        self,
        server_id: str,
        channel_id: int,
        owner_id: int,
        type_key: str
    ) -> Optional[TicketData]:
        try:
            ticket_id = db.create_ticket(
                server_id=server_id,
                channel_id=str(channel_id),
                owner_id=str(owner_id),
                type_key=type_key,
                members=[owner_id]
            )
            
            if not ticket_id:
                return None
            
            ticket = TicketData(
                channel_id=channel_id,
                owner_id=owner_id,
                type_key=type_key,
                server_id=server_id,
                created_at=datetime.now()
            )
            self.tickets[channel_id] = ticket
            self.logger.info(f"Ticket créé: canal {channel_id}, propriétaire {owner_id}, type {type_key}")
            return ticket
        except Exception as e:
            self.logger.error(f"Erreur création ticket: {e}")
            return None

    def get_ticket(self, channel_id: int) -> Optional[TicketData]:
        if channel_id in self.tickets:
            return self.tickets[channel_id]
        
        try:
            ticket_data = db.get_ticket_by_channel(str(channel_id))
            if ticket_data and not ticket_data.get("is_closed"):
                ticket = TicketData.from_db(ticket_data)
                self.tickets[channel_id] = ticket
                return ticket
        except Exception as e:
            self.logger.error(f"Erreur récupération ticket: {e}")
        
        return None

    def delete_ticket(self, channel_id: int):
        try:
            if channel_id in self.autoclose_delays:
                self.autoclose_delays[channel_id].cancel()
                del self.autoclose_delays[channel_id]
            
            db.delete_ticket(str(channel_id))
            
            if channel_id in self.tickets:
                del self.tickets[channel_id]
            
            self.logger.info(f"Ticket supprimé: canal {channel_id}")
        except Exception as e:
            self.logger.error(f"Erreur suppression ticket: {e}")

    def close_ticket(self, channel_id: int, closed_by_id: int, reason: str = "Aucune raison"):
        try:
            db.close_ticket(str(channel_id), str(closed_by_id), reason)
            
            if channel_id in self.tickets:
                self.tickets[channel_id].is_closed = True
            
            self.logger.info(f"Ticket fermé: canal {channel_id}")
        except Exception as e:
            self.logger.error(f"Erreur fermeture ticket: {e}")

    def is_ticket_channel(self, channel_id: int) -> bool:
        return self.get_ticket(channel_id) is not None

    def update_owner_message_time(self, channel_id: int):
        try:
            db.update_ticket_owner_message(str(channel_id))
            if channel_id in self.tickets:
                self.tickets[channel_id].last_owner_message = datetime.now()
        except Exception as e:
            self.logger.error(f"Erreur mise à jour message propriétaire: {e}")

    def update_staff_message_time(self, channel_id: int):
        try:
            db.update_ticket_staff_message(str(channel_id))
            if channel_id in self.tickets:
                self.tickets[channel_id].last_staff_message = datetime.now()
        except Exception as e:
            self.logger.error(f"Erreur mise à jour message staff: {e}")

    def claim_ticket(self, channel_id: int, staff_id: int):
        try:
            db.claim_ticket(str(channel_id), str(staff_id))
            if channel_id in self.tickets:
                self.tickets[channel_id].claimed_by_id = staff_id
            self.logger.info(f"Ticket {channel_id} réclamé par {staff_id}")
        except Exception as e:
            self.logger.error(f"Erreur claim ticket: {e}")

    def unclaim_ticket(self, channel_id: int):
        try:
            db.unclaim_ticket(str(channel_id))
            if channel_id in self.tickets:
                self.tickets[channel_id].claimed_by_id = None
            self.logger.info(f"Ticket {channel_id} non réclamé")
        except Exception as e:
            self.logger.error(f"Erreur unclaim ticket: {e}")

    def add_ticket_member(self, channel_id: int, member_id: int):
        try:
            db.add_ticket_member(str(channel_id), member_id)
            if channel_id in self.tickets and member_id not in self.tickets[channel_id].members:
                self.tickets[channel_id].members.append(member_id)
            self.logger.info(f"Membre {member_id} ajouté au ticket {channel_id}")
        except Exception as e:
            self.logger.error(f"Erreur ajout membre: {e}")

    def remove_ticket_member(self, channel_id: int, member_id: int):
        try:
            db.remove_ticket_member(str(channel_id), member_id)
            if channel_id in self.tickets and member_id in self.tickets[channel_id].members:
                self.tickets[channel_id].members.remove(member_id)
            self.logger.info(f"Membre {member_id} retiré du ticket {channel_id}")
        except Exception as e:
            self.logger.error(f"Erreur retrait membre: {e}")

    def get_user_open_tickets(self, server_id: str, user_id: int) -> List[TicketData]:
        try:
            tickets_data = db.get_user_tickets(server_id, str(user_id), is_closed=False)
            return [TicketData.from_db(t) for t in tickets_data]
        except Exception as e:
            self.logger.error(f"Erreur récupération tickets utilisateur: {e}")
            return []

    def set_autoclose_task(self, channel_id: int, task: asyncio.Task):
        if channel_id in self.autoclose_delays:
            self.autoclose_delays[channel_id].cancel()
        self.autoclose_delays[channel_id] = task

    def get_autoclose_task(self, channel_id: int) -> Optional[asyncio.Task]:
        return self.autoclose_delays.get(channel_id)

    def cancel_autoclose_task(self, channel_id: int):
        if channel_id in self.autoclose_delays:
            self.autoclose_delays[channel_id].cancel()
            del self.autoclose_delays[channel_id]
            self.logger.info(f"Tâche auto-close annulée pour {channel_id}")
