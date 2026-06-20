import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import logging
from typing import Optional
import asyncio

from config import Config
from modules.TicketManager import TicketManager
from modules.I18n import t

class TicketTypeSelect(discord.ui.Select):
    def __init__(self, cog: "TicketsCog"):
        self.cog = cog
        
        options = []
        for key, ticket_type in Config.TicketTypes.items():
            options.append(
                discord.SelectOption(
                    label=ticket_type["name"],
                    description=ticket_type["description"],
                    value=key
                )
            )
        
        super().__init__(
            placeholder=t("tickets.ui.select_placeholder", "Choisissez un type de ticket"),
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await self.cog.create_ticket_for_user(interaction, self.values[0])


class TicketTypeSelectView(discord.ui.View):
    def __init__(self, cog: "TicketsCog"):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect(cog))


class TicketActionView(discord.ui.View):
    def __init__(self, cog: "TicketsCog", ticket_channel_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.ticket_channel_id = ticket_channel_id

    @discord.ui.button(label=t("tickets.ui.button_claim", "Claim"), style=discord.ButtonStyle.primary, emoji="✋")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.claim_ticket_command(interaction, self.ticket_channel_id)

    @discord.ui.button(label=t("tickets.ui.button_close", "Fermer"), style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.close_ticket_command(interaction, "Fermé par staff")

    @discord.ui.button(label=t("tickets.ui.button_rename", "Renommer"), style=discord.ButtonStyle.secondary, emoji="✏️")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameTicketModal(self.cog, self.ticket_channel_id))

    @discord.ui.button(label=t("tickets.ui.button_transcript", "Transcrire"), style=discord.ButtonStyle.blurple, emoji="📄")
    async def transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            messages = []
            channel = self.cog.bot.get_channel(self.ticket_channel_id)
            if channel:
                async for message in channel.history(oldest_first=True):
                    messages.append(f"[{message.created_at}] {message.author}: {message.content}")
                
                transcript = "\n".join(messages)
                transcript_file = discord.File(
                    fp=__import__("io").BytesIO(transcript.encode()),
                    filename=f"transcript-{self.ticket_channel_id}.txt"
                )
                await interaction.followup.send(file=transcript_file, ephemeral=True)
                logging.info(f"Transcription générée pour le ticket {self.ticket_channel_id}")
            else:
                await interaction.followup.send(t("tickets.transcript.channel_not_found", "❌ Canal non trouvé"), ephemeral=True)
        except Exception as e:
            logging.error(f"Erreur transcription: {e}")
            await interaction.followup.send(t("tickets.transcript.generic_error", "❌ Erreur: {error}", error=str(e)), ephemeral=True)

    @discord.ui.button(label=t("tickets.ui.button_add_member", "Ajouter membre"), style=discord.ButtonStyle.green, emoji="➕")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddMemberModal(self.cog, self.ticket_channel_id))

    @discord.ui.button(label=t("tickets.ui.button_remove_member", "Retirer membre"), style=discord.ButtonStyle.danger, emoji="➖")
    async def remove_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveMemberModal(self.cog, self.ticket_channel_id))


class ClosedTicketView(discord.ui.View):
    def __init__(self, cog: "TicketsCog", ticket_channel_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.ticket_channel_id = ticket_channel_id

    @discord.ui.button(label=t("tickets.ui.button_reopen", "Réouvrir"), style=discord.ButtonStyle.green, emoji="🔓")
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.reopen_ticket_command(interaction, self.ticket_channel_id)

    @discord.ui.button(label=t("tickets.ui.button_delete", "Supprimer"), style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.delete_ticket_command(interaction, self.ticket_channel_id)


class RenameTicketModal(discord.ui.Modal):
    def __init__(self, cog: "TicketsCog", ticket_channel_id: int):
        super().__init__(title=t("tickets.ui.modal_rename_title", "Renommer le ticket"))
        self.cog = cog
        self.ticket_channel_id = ticket_channel_id
        self.name_input = discord.ui.TextInput(
            label=t("tickets.ui.modal_rename_field", "Nouveau nom"),
            placeholder=t("tickets.ui.modal_rename_placeholder", "nouveau-nom-ticket"),
            min_length=2,
            max_length=100
        )
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.rename_ticket_command(interaction, self.ticket_channel_id, self.name_input.value)


class AddMemberModal(discord.ui.Modal):
    def __init__(self, cog: "TicketsCog", ticket_channel_id: int):
        super().__init__(title=t("tickets.ui.modal_add_member_title", "Ajouter un membre"))
        self.cog = cog
        self.ticket_channel_id = ticket_channel_id
        self.member_input = discord.ui.TextInput(
            label=t("tickets.ui.modal_member_field", "Mention ou ID du membre"),
            placeholder=t("tickets.ui.modal_member_placeholder", "@user ou user_id")
        )
        self.add_item(self.member_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.add_member_to_ticket(interaction, self.ticket_channel_id, self.member_input.value)


class RemoveMemberModal(discord.ui.Modal):
    def __init__(self, cog: "TicketsCog", ticket_channel_id: int):
        super().__init__(title=t("tickets.ui.modal_remove_member_title", "Retirer un membre"))
        self.cog = cog
        self.ticket_channel_id = ticket_channel_id
        self.member_input = discord.ui.TextInput(
            label=t("tickets.ui.modal_member_field", "Mention ou ID du membre"),
            placeholder=t("tickets.ui.modal_member_placeholder", "@user ou user_id")
        )
        self.add_item(self.member_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.remove_member_from_ticket(interaction, self.ticket_channel_id, self.member_input.value)


class TicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ticket_manager = TicketManager(bot)
        self.logger = logging.getLogger("TicketsCog")
        self.user_ping_cooldown = {}
    
    async def send_ticket_log(self, log_type: str, embed: discord.Embed):
        if log_type in Config.Logs and Config.Logs[log_type]["enabled"]:
            channel_id = Config.Logs[log_type]["channel_id"]
            try:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    try:
                        channel = await self.bot.fetch_channel(channel_id)
                    except Exception:
                        self.logger.warning(f"Canal de log {channel_id} non trouvé")
                        return
                
                if channel:
                    await channel.send(embed=embed)
            except discord.Forbidden:
                self.logger.warning(f"Permissions insuffisantes pour envoyer un log dans {channel_id}")
            except discord.NotFound:
                self.logger.warning(f"Canal de log {channel_id} introuvable")
            except Exception as e:
                self.logger.error(f"Erreur lors de l'envoi du log {log_type}: {str(e)}")
        
    async def cog_load(self):
        for guild in self.bot.guilds:
            await self.ticket_manager.load_from_db(str(guild.id))
        
        await self.restore_ticket_views()
        await self.restore_ticket_panel()
        self.logger.info("Système de tickets initialisé")
    
    async def restore_ticket_views(self):
        try:
            for channel_id, ticket in self.ticket_manager.tickets.items():
                try:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue
                    
                    async for message in channel.history(limit=10):
                        if message.embeds:
                            embed = message.embeds[0]
                            if "Ticket:" in embed.title or "🎫" in embed.title:
                                if ticket.is_closed:
                                    await message.edit(view=ClosedTicketView(self, channel_id))
                                else:
                                    await message.edit(view=TicketActionView(self, channel_id))
                                break
                except discord.NotFound:
                    # Le message ou le canal n'existe plus
                    pass
                except Exception as e:
                    self.logger.error(f"Erreur restauration vue pour ticket {channel_id}: {e}")
        except Exception as e:
            self.logger.error(f"Erreur restauration vues: {e}")
    
    async def restore_ticket_panel(self):
        try:
            from modules.Database import db
            
            for guild in self.bot.guilds:
                server_id = str(guild.id)
                panel_message_id = db.get_config(server_id, "ticket_panel_message_id")
                
                if panel_message_id:
                    try:
                        channel = self.bot.get_channel(Config.TicketChannel)
                        if not channel:
                            try:
                                channel = await self.bot.fetch_channel(Config.TicketChannel)
                            except discord.NotFound:
                                self.logger.warning(f"Canal de ticket {Config.TicketChannel} non trouvé")
                                continue
                        
                        if channel:
                            message = await channel.fetch_message(int(panel_message_id))
                            await message.edit(view=TicketTypeSelectView(self))
                            self.logger.info(f"Vue du panel de tickets restaurée pour {guild.id}")
                    except discord.NotFound:
                        db.set_config(server_id, "ticket_panel_message_id", "")
                    except Exception as e:
                        self.logger.error(f"Erreur restauration panel pour {guild.id}: {e}")
        except Exception as e:
            self.logger.error(f"Erreur restauration panel: {e}")

    async def cog_unload(self):
        for task in self.ticket_manager.autoclose_delays.values():
            task.cancel()

    @app_commands.command(name="ticket_panel", description=t("tickets.commands.panel_description", "Envoie le panel d'ouverture de tickets"))
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        try:
            from modules.Database import db
            
            channel = self.bot.get_channel(Config.TicketChannel) or await self.bot.fetch_channel(Config.TicketChannel)
            if not channel:
                await interaction.response.send_message(t("tickets.panel.channel_not_found", "❌ TicketChannel non trouvé"), ephemeral=True)
                return

            embed = discord.Embed(
                title=t("tickets.panel.embed_title", "🎫 Tickets"),
                description=t("tickets.panel.embed_description", "Choississez le type de ticket que vous souhaitez ouvrir en utilisant le menu ci-dessous. Merci de fournir autant de détails que possible afin que notre équipe puisse vous aider efficacement."),
                color=discord.Color.blurple()
            )
            embed.set_footer(text=t("tickets.panel.embed_footer", "Cliquez sur le menu ci-dessous pour choisir la catégorie de votre ticket."))

            message = await channel.send(embed=embed, view=TicketTypeSelectView(self))
            
            server_id = str(interaction.guild.id)
            db.set_config(server_id, "ticket_panel_message_id", str(message.id))
            
            await interaction.response.send_message(t("tickets.panel.sent", "✅ Panel envoyé"), ephemeral=True)
            self.logger.info(f"Panel de tickets envoyé dans {Config.TicketChannel} - Message ID: {message.id}")
        except Exception as e:
            self.logger.error(f"Erreur envoi panel: {e}")
            await interaction.response.send_message(t("tickets.panel.generic_error", "❌ Erreur: {error}", error=str(e)), ephemeral=True)

    async def create_ticket_for_user(self, interaction: discord.Interaction, ticket_type_key: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            if ticket_type_key not in Config.TicketTypes:
                await interaction.followup.send(t("tickets.create.invalid_type", "❌ Type de ticket invalide"), ephemeral=True)
                return

            ticket_type = Config.TicketTypes[ticket_type_key]
            guild = interaction.guild
            category_id = ticket_type.get("category_id")

            category = guild.get_channel(category_id) or await guild.fetch_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                self.logger.error(f"Catégorie {category_id} invalide pour type {ticket_type_key}")
                await interaction.followup.send(t("tickets.create.category_not_found", "❌ Catégorie de ticket non trouvée"), ephemeral=True)
                return

            user_tickets = self.ticket_manager.get_user_open_tickets(str(guild.id), interaction.user.id)
            ticket_number = len(user_tickets) + 1
            
            channel_name = f"ticket-{interaction.user.name}".lower()[:100]

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )
            }

            for staff_role_id in ticket_type.get("staff_roles_id", []):
                staff_role = guild.get_role(staff_role_id)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True
                    )

            ticket_channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites
            )

            self.ticket_manager.create_ticket(
                server_id=str(guild.id),
                channel_id=ticket_channel.id,
                owner_id=interaction.user.id,
                type_key=ticket_type_key
            )

            embed = discord.Embed(
                title=t("tickets.create.embed_title", "🎫 Ticket: {type}", type=ticket_type['name']),
                description=t("tickets.create.embed_description", "Merci d'avoir ouvert un ticket. Le staff vous répondra bientôt."),
                color=discord.Color.green()
            )
            embed.add_field(name=t("tickets.create.type_field", "Type"), value=ticket_type["name"], inline=True)
            embed.add_field(name=t("tickets.create.author_field", "Auteur"), value=interaction.user.mention, inline=True)
            embed.add_field(name=t("tickets.create.created_at_field", "Créé à"), value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)
            embed.add_field(
                name=t("tickets.create.instructions_field", "Instructions"),
                value=t("tickets.create.instructions_value", "• Merci de décrire votre problème en détail, et de fournir autant d'information que nécessaire\n• Veuillez attendre la réponse du staff, ces derniers répondront à votre demande sous les plus brefs délais"),
                inline=False
            )
            embed.set_footer(text=t("tickets.create.footer", "Ticket ID: {ticket_id}", ticket_id=ticket_channel.id))

            ping_text = ""
            if ticket_type.get("roles_to_ping"):
                roles_mentions = []
                for role_id in ticket_type["roles_to_ping"]:
                    role = guild.get_role(role_id)
                    if role:
                        roles_mentions.append(role.mention)
                if roles_mentions:
                    ping_text = " ".join(roles_mentions)

            message_content = f"{ping_text}\n" if ping_text else ""
            message = await ticket_channel.send(content=message_content, embed=embed, view=TicketActionView(self, ticket_channel.id))

            await interaction.followup.send(
                t("tickets.create.success", "✅ Ticket créé: {channel}", channel=ticket_channel.mention),
                ephemeral=True
            )
            self.logger.info(f"Ticket créé pour {interaction.user} ({interaction.user.id}) - Type: {ticket_type_key} - Canal: {ticket_channel.id}")
            
            log_embed = discord.Embed(
                title="🎫 Ticket Créé",
                description=f"**Canal:** {ticket_channel.mention}\n**Auteur:** {interaction.user.mention}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="Type", value=ticket_type['name'], inline=True)
            log_embed.add_field(name="ID Canal", value=ticket_channel.id, inline=True)
            log_embed.add_field(name="ID Utilisateur", value=interaction.user.id, inline=True)
            log_embed.set_footer(text=f"Ticket ID: {ticket_channel.id}")
            await self.send_ticket_log("ticket_create", log_embed)

        except discord.Forbidden:
            self.logger.error("Permissions insuffisantes pour créer le canal")
            await interaction.followup.send(t("tickets.create.missing_permissions", "❌ Permissions insuffisantes"), ephemeral=True)
        except Exception as e:
            self.logger.error(f"Erreur création ticket: {e}")
            await interaction.followup.send(t("tickets.create.generic_error", "❌ Erreur: {error}", error=str(e)), ephemeral=True)

    async def claim_ticket_command(self, interaction: discord.Interaction, channel_id: int):
        await interaction.response.defer(ephemeral=True)
        
        try:
            ticket = self.ticket_manager.get_ticket(channel_id)
            if not ticket:
                await interaction.followup.send("❌ Ce n'est pas un canal de ticket", ephemeral=True)
                return

            if not self.can_manage_ticket(interaction, ticket):
                await interaction.followup.send("❌ Vous n'avez pas la permission", ephemeral=True)
                return

            if ticket.claimed_by_id:
                claimer = interaction.guild.get_member(ticket.claimed_by_id)
                claimer_name = claimer.mention if claimer else f"<@{ticket.claimed_by_id}>"
                await interaction.followup.send(
                    f"❌ Ce ticket est déjà réclamé par {claimer_name}",
                    ephemeral=True
                )
                return

            self.ticket_manager.claim_ticket(channel_id, interaction.user.id)

            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="✋ Ticket Réclamé",
                    description=f"{interaction.user.mention} prend en charge ce ticket.",
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed)

            await interaction.followup.send("✅ Ticket réclamé avec succès", ephemeral=True)
            self.logger.info(f"Ticket {channel_id} réclamé par {interaction.user}")
            
            log_embed = discord.Embed(
                title="✋ Ticket Réclamé",
                description=f"**Canal:** {channel.mention if channel else 'Inconnu'}\n**Réclamé par:** {interaction.user.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="ID Canal", value=channel_id, inline=True)
            log_embed.add_field(name="ID Staff", value=interaction.user.id, inline=True)
            log_embed.set_footer(text=f"Ticket ID: {channel_id}")
            await self.send_ticket_log("ticket_claim", log_embed)

        except Exception as e:
            self.logger.error(f"Erreur claim ticket: {e}")
            await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    async def rename_ticket_command(self, interaction: discord.Interaction, channel_id: int, new_name: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            ticket = self.ticket_manager.get_ticket(channel_id)
            if not ticket:
                await interaction.followup.send("❌ Ce n'est pas un canal de ticket", ephemeral=True)
                return

            # Vérifier permissions
            if not self.can_manage_ticket(interaction, ticket):
                await interaction.followup.send("❌ Vous n'avez pas la permission", ephemeral=True)
                return

            if len(new_name) < 2 or len(new_name) > 100:
                await interaction.followup.send("❌ Le nom doit faire entre 2 et 100 caractères", ephemeral=True)
                return

            channel = self.bot.get_channel(channel_id)
            if channel:
                old_name = channel.name
                await channel.edit(name=new_name)
                await interaction.followup.send(f"✅ Ticket renommé en `{new_name}`", ephemeral=True)
                self.logger.info(f"Ticket {channel_id} renommé en {new_name}")
                
                log_embed = discord.Embed(
                    title="✏️ Ticket Renommé",
                    description=f"**Canal:** {channel.mention}\n**Renommé par:** {interaction.user.mention}",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                log_embed.add_field(name="Ancien nom", value=old_name, inline=True)
                log_embed.add_field(name="Nouveau nom", value=new_name, inline=True)
                log_embed.add_field(name="ID Canal", value=channel_id, inline=True)
                log_embed.set_footer(text=f"Ticket ID: {channel_id}")
                await self.send_ticket_log("ticket_rename", log_embed)
            else:
                await interaction.followup.send("❌ Canal non trouvé", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("❌ Permissions insuffisantes", ephemeral=True)
        except Exception as e:
            self.logger.error(f"Erreur renommage ticket: {e}")
            await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    async def delete_ticket_command(self, interaction: discord.Interaction, channel_id: int):
        await interaction.response.defer(ephemeral=True)
        
        try:
            ticket = self.ticket_manager.get_ticket(channel_id)
            if not ticket:
                from modules.Database import db
                ticket_data = db.get_ticket_by_channel(str(channel_id))
                if not ticket_data or not ticket_data.get("is_closed"):
                    await interaction.followup.send("❌ Ticket non trouvé ou non fermé", ephemeral=True)
                    return
            else:
                if not ticket.is_closed:
                    await interaction.followup.send("❌ Le ticket doit être fermé avant d'être supprimé", ephemeral=True)
                    return

            # Vérifier permissions
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.followup.send("❌ Vous n'avez pas la permission", ephemeral=True)
                return

            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.delete()
            
            self.ticket_manager.delete_ticket(channel_id)
            
            log_embed = discord.Embed(
                title="🗑️ Ticket Supprimé",
                description=f"**Supprimé par:** {interaction.user.mention}",
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="ID Canal", value=channel_id, inline=True)
            log_embed.add_field(name="ID Utilisateur", value=interaction.user.id, inline=True)
            log_embed.set_footer(text=f"Ticket ID: {channel_id}")
            await self.send_ticket_log("ticket_delete", log_embed)

        except discord.Forbidden:
            await interaction.followup.send("❌ Permissions insuffisantes", ephemeral=True)
        except Exception as e:
            self.logger.error(f"Erreur suppression ticket: {e}")
            await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    @app_commands.command(name="ticket_reopen", description=t("tickets.commands.reopen_description", "Réouvre un ticket fermé"))
    async def ticket_reopen(self, interaction: discord.Interaction):
        await self.reopen_ticket_command(interaction, interaction.channel.id)

    @app_commands.command(name="ticket_close", description=t("tickets.commands.close_description", "Ferme le ticket"))
    @app_commands.describe(reason="Raison de la fermeture")
    async def ticket_close(self, interaction: discord.Interaction, reason: str = "Aucune raison fournie"):
        await self.close_ticket_command(interaction, reason)

    async def close_ticket_command(self, interaction: discord.Interaction, reason: str = "Aucune raison fournie"):
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = interaction.channel
            ticket = self.ticket_manager.get_ticket(channel.id)

            if not ticket:
                await interaction.followup.send("❌ Ce n'est pas un canal de ticket", ephemeral=True)
                return

            # Vérifier permissions
            if not self.can_manage_ticket(interaction, ticket):
                await interaction.followup.send("❌ Vous n'avez pas la permission", ephemeral=True)
                return

            self.ticket_manager.cancel_autoclose_task(channel.id)

            self.ticket_manager.close_ticket(channel.id, interaction.user.id, reason)

            embed = discord.Embed(
                title="🔒 Ticket Fermé",
                description=f"Raison: {reason}",
                color=discord.Color.red()
            )
            embed.add_field(name="Fermé par", value=interaction.user.mention, inline=True)
            embed.add_field(name="Fermé à", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)
            embed.add_field(
                name="Information",
                value="Ce ticket est maintenant en lecture seule. Utilisez les boutons ci-dessous pour le réouvrir ou le supprimer définitivement.",
                inline=False
            )

            await channel.send(embed=embed, view=ClosedTicketView(self, channel.id))

            overwrites = channel.overwrites
            for target, overwrite in overwrites.items():
                if target != channel.guild.default_role:
                    overwrite.send_messages = False
                    await channel.set_permissions(target, overwrite=overwrite)

            if not channel.name.startswith("fermé-"):
                await channel.edit(name=f"fermé-{channel.name}")

            await interaction.followup.send("✅ Ticket fermé", ephemeral=True)
            self.logger.info(f"Ticket {channel.id} fermé par {interaction.user} - Raison: {reason}")
            
            log_embed = discord.Embed(
                title="🔒 Ticket Fermé",
                description=f"**Canal:** {channel.mention}\n**Fermé par:** {interaction.user.mention}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="Raison", value=reason, inline=False)
            log_embed.add_field(name="ID Canal", value=channel.id, inline=True)
            log_embed.set_footer(text=f"Ticket ID: {channel.id}")
            await self.send_ticket_log("ticket_close", log_embed)

        except Exception as e:
            self.logger.error(f"Erreur fermeture ticket: {e}")
            await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    @app_commands.command(name="ticket_add", description=t("tickets.commands.add_description", "Ajoute un membre au ticket"))
    @app_commands.describe(member="Membre à ajouter")
    async def ticket_add_member(self, interaction: discord.Interaction, member: discord.Member):
        await self.add_member_to_ticket(interaction, interaction.channel.id, member.mention)

    async def add_member_to_ticket(self, interaction: discord.Interaction, channel_id: int, member_input: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await interaction.followup.send("❌ Canal non trouvé", ephemeral=True)
                return

            ticket = self.ticket_manager.get_ticket(channel_id)
            if not ticket:
                await interaction.followup.send("❌ Ce n'est pas un canal de ticket", ephemeral=True)
                return

            # Vérifier permissions
            if not self.can_manage_ticket(interaction, ticket):
                await interaction.followup.send("❌ Vous n'avez pas la permission", ephemeral=True)
                return

            # Récupérer le membre
            member = await self.parse_member(interaction.guild, member_input)
            if not member:
                await interaction.followup.send("❌ Membre non trouvé", ephemeral=True)
                return

            try:
                await channel.set_permissions(
                    member,
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )
                self.ticket_manager.add_ticket_member(channel_id, member.id)
                await interaction.followup.send(f"✅ {member.mention} ajouté au ticket", ephemeral=True)
                self.logger.info(f"Membre {member} ajouté au ticket {channel_id}")
                
                log_embed = discord.Embed(
                    title="➕ Membre Ajouté au Ticket",
                    description=f"**Canal:** {channel.mention}\n**Membre ajouté:** {member.mention}\n**Ajouté par:** {interaction.user.mention}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                log_embed.add_field(name="ID Membre", value=member.id, inline=True)
                log_embed.add_field(name="ID Canal", value=channel_id, inline=True)
                log_embed.set_footer(text=f"Ticket ID: {channel_id}")
                await self.send_ticket_log("ticket_member_add", log_embed)
            except discord.Forbidden:
                await interaction.followup.send("❌ Permissions insuffisantes", ephemeral=True)

        except Exception as e:
            self.logger.error(f"Erreur ajout membre: {e}")
            await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    @app_commands.command(name="ticket_remove", description=t("tickets.commands.remove_description", "Retire un membre du ticket"))
    @app_commands.describe(member="Membre à retirer")
    async def ticket_remove_member(self, interaction: discord.Interaction, member: discord.Member):
        await self.remove_member_from_ticket(interaction, interaction.channel.id, member.mention)

    async def remove_member_from_ticket(self, interaction: discord.Interaction, channel_id: int, member_input: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await interaction.followup.send("❌ Canal non trouvé", ephemeral=True)
                return

            ticket = self.ticket_manager.get_ticket(channel_id)
            if not ticket:
                await interaction.followup.send("❌ Ce n'est pas un canal de ticket", ephemeral=True)
                return

            if not self.can_manage_ticket(interaction, ticket):
                await interaction.followup.send("❌ Vous n'avez pas la permission", ephemeral=True)
                return

            member = await self.parse_member(interaction.guild, member_input)
            if not member:
                await interaction.followup.send("❌ Membre non trouvé", ephemeral=True)
                return

            if member.id == ticket.owner_id:
                await interaction.followup.send("❌ Impossible de retirer le propriétaire du ticket", ephemeral=True)
                return

            try:
                await channel.set_permissions(member, overwrite=None)
                self.ticket_manager.remove_ticket_member(channel_id, member.id)
                await interaction.followup.send(f"✅ {member.mention} retiré du ticket", ephemeral=True)
                self.logger.info(f"Membre {member} retiré du ticket {channel_id}")
                
                log_embed = discord.Embed(
                    title="➖ Membre Retiré du Ticket",
                    description=f"**Canal:** {channel.mention}\n**Membre retiré:** {member.mention}\n**Retiré par:** {interaction.user.mention}",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                log_embed.add_field(name="ID Membre", value=member.id, inline=True)
                log_embed.add_field(name="ID Canal", value=channel_id, inline=True)
                log_embed.set_footer(text=f"Ticket ID: {channel_id}")
                await self.send_ticket_log("ticket_member_remove", log_embed)
            except discord.Forbidden:
                await interaction.followup.send("❌ Permissions insuffisantes", ephemeral=True)

        except Exception as e:
            self.logger.error(f"Erreur retrait membre: {e}")
            await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    @app_commands.command(name="ticket_rename", description=t("tickets.commands.rename_description", "Renomme le ticket"))
    @app_commands.describe(name="Nouveau nom")
    async def ticket_rename(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = interaction.channel
            ticket = self.ticket_manager.get_ticket(channel.id)

            if not ticket:
                await interaction.followup.send("❌ Ce n'est pas un canal de ticket", ephemeral=True)
                return

            # Vérifier permissions
            if not self.can_manage_ticket(interaction, ticket):
                await interaction.followup.send("❌ Vous n'avez pas la permission", ephemeral=True)
                return

            # Valider le nom
            if len(name) < 2 or len(name) > 100:
                await interaction.followup.send("❌ Le nom doit faire entre 2 et 100 caractères", ephemeral=True)
                return

            # Renommer
            await channel.edit(name=name)
            await interaction.followup.send(f"✅ Ticket renommé en `{name}`", ephemeral=True)
            self.logger.info(f"Ticket {channel.id} renommé en {name}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Permissions insuffisantes", ephemeral=True)
        except Exception as e:
            self.logger.error(f"Erreur renommage ticket: {e}")
            await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or message.guild.id != Config.ServerID:
            return

        ticket = self.ticket_manager.get_ticket(message.channel.id)
        if not ticket:
            return

        if Config.TicketAutoPingRole:
            auto_ping_role = message.guild.get_role(Config.TicketAutoPingRole)
            if auto_ping_role and auto_ping_role in message.author.roles:
                # Ping une seule fois par message (anti-spam)
                if message.author.id != ticket.owner_id:  # Ne pas ping si c'est le proprio
                    owner = message.guild.get_member(ticket.owner_id)
                    if owner:
                        try:
                            ping_message = await message.reply(f"{owner.mention}", allowed_mentions=discord.AllowedMentions(users=True))
                            await ping_message.delete()
                            self.logger.info(f"Auto-ping: {message.author} a pingé {owner} dans ticket {message.channel.id}")
                        except Exception as e:
                            self.logger.error(f"Erreur auto-ping: {e}")

        try:
            ticket_type = Config.TicketTypes.get(ticket.type_key, {})
            staff_roles = ticket_type.get("staff_roles_id", [])
            is_staff = any(role.id in staff_roles for role in message.author.roles)

            if is_staff:
                self.ticket_manager.update_staff_message_time(message.channel.id)
                
                if not self.ticket_manager.get_autoclose_task(message.channel.id):
                    task = asyncio.create_task(
                        self.autoclose_ticket_task(
                            message.channel.id,
                            Config.TicketAutoCloseDelay
                        )
                    )
                    self.ticket_manager.set_autoclose_task(message.channel.id, task)
                    self.logger.info(f"Timer auto-close démarré pour ticket {message.channel.id}")

            elif message.author.id == ticket.owner_id:
                self.ticket_manager.update_owner_message_time(message.channel.id)
                self.ticket_manager.cancel_autoclose_task(message.channel.id)
                self.logger.info(f"Timer auto-close annulé (propriétaire a répondu) pour ticket {message.channel.id}")

        except Exception as e:
            self.logger.error(f"Erreur gestion auto-close: {e}")

    async def autoclose_ticket_task(self, channel_id: int, delay_hours: int):
        try:
            await asyncio.sleep(delay_hours * 3600)

            ticket = self.ticket_manager.get_ticket(channel_id)
            if not ticket:
                return

            if ticket.last_owner_message > ticket.last_staff_message:
                return

            channel = self.bot.get_channel(channel_id)
            if channel:
                self.ticket_manager.close_ticket(channel_id, self.bot.user.id, f"Inactivité ({delay_hours}h sans réponse)")

                embed = discord.Embed(
                    title="🔒 Ticket Fermé Automatiquement",
                    description=f"Ce ticket a été fermé pour inactivité ({delay_hours}h sans réponse).",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Pourquoi?",
                    value="Aucune réponse du créateur du ticket après que le staff ait répondu.",
                    inline=False
                )
                embed.add_field(
                    name="Information",
                    value="Ce ticket est maintenant en lecture seule. Utilisez les boutons ci-dessous pour le réouvrir ou le supprimer définitivement.",
                    inline=False
                )

                try:
                    await channel.send(embed=embed, view=ClosedTicketView(self, channel_id))
                    
                    overwrites = channel.overwrites
                    for target, overwrite in overwrites.items():
                        if target != channel.guild.default_role:
                            overwrite.send_messages = False
                            await channel.set_permissions(target, overwrite=overwrite)
                    
                    if not channel.name.startswith("fermé-"):
                        await channel.edit(name=f"fermé-{channel.name}")
                    
                    self.logger.info(f"Ticket {channel_id} fermé automatiquement pour inactivité")
                    
                    log_embed = discord.Embed(
                        title="⏰ Ticket Fermé Automatiquement",
                        description=f"**Canal:** {channel.mention}",
                        color=discord.Color.dark_orange(),
                        timestamp=datetime.now()
                    )
                    log_embed.add_field(name="Raison", value=f"Inactivité ({delay_hours}h sans réponse)", inline=False)
                    log_embed.add_field(name="ID Canal", value=channel_id, inline=True)
                    log_embed.set_footer(text=f"Ticket ID: {channel_id}")
                    await self.send_ticket_log("ticket_autoclose", log_embed)
                except Exception as e:
                    self.logger.error(f"Erreur fermeture auto ticket: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Erreur tâche auto-close: {e}")

    async def reopen_ticket_command(self, interaction: discord.Interaction, channel_id: int):
        await interaction.response.defer(ephemeral=True)

        try:
            from modules.Database import db
            from modules.TicketManager import TicketData

            ticket = self.ticket_manager.tickets.get(channel_id)
            if not ticket:
                ticket_data_db = db.get_ticket_by_channel(str(channel_id))
                if not ticket_data_db:
                    await interaction.followup.send("❌ Ticket non trouvé", ephemeral=True)
                    return
                ticket = TicketData.from_db(ticket_data_db)

            if not ticket.is_closed:
                await interaction.followup.send("❌ Ce ticket n'est pas fermé", ephemeral=True)
                return

            if not self.can_manage_ticket(interaction, ticket):
                await interaction.followup.send("❌ Vous n'avez pas la permission", ephemeral=True)
                return

            self.ticket_manager.reopen_ticket(channel_id)

            channel = self.bot.get_channel(channel_id)
            if channel:
                overwrites = channel.overwrites
                for target, overwrite in overwrites.items():
                    if target != channel.guild.default_role:
                        overwrite.send_messages = True
                        await channel.set_permissions(target, overwrite=overwrite)

                if channel.name.startswith("fermé-"):
                    await channel.edit(name=channel.name[len("fermé-"):])

                embed = discord.Embed(
                    title="🔓 Ticket Réouvert",
                    description=f"Ce ticket a été réouvert par {interaction.user.mention}.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Réouvert par", value=interaction.user.mention, inline=True)
                embed.add_field(name="Réouvert à", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)
                await channel.send(embed=embed, view=TicketActionView(self, channel_id))

            await interaction.followup.send("✅ Ticket réouvert", ephemeral=True)
            self.logger.info(f"Ticket {channel_id} réouvert par {interaction.user}")

            log_embed = discord.Embed(
                title="🔓 Ticket Réouvert",
                description=f"**Canal:** {channel.mention if channel else 'Inconnu'}\n**Réouvert par:** {interaction.user.mention}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="ID Canal", value=channel_id, inline=True)
            log_embed.add_field(name="ID Utilisateur", value=interaction.user.id, inline=True)
            log_embed.set_footer(text=f"Ticket ID: {channel_id}")
            await self.send_ticket_log("ticket_reopen", log_embed)

        except Exception as e:
            self.logger.error(f"Erreur réouverture ticket: {e}")
            await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    def can_manage_ticket(self, interaction: discord.Interaction, ticket) -> bool:
        if interaction.user.guild_permissions.manage_channels:
            return True

        if interaction.user.id == ticket.owner_id:
            return True

        ticket_type = Config.TicketTypes.get(ticket.type_key, {})
        staff_roles = ticket_type.get("staff_roles_id", [])
        if any(role.id in staff_roles for role in interaction.user.roles):
            return True

        return False

    async def parse_member(self, guild: discord.Guild, input_str: str) -> Optional[discord.Member]:
        try:
            if input_str.startswith("<@"):
                member_id = int(input_str.strip("<@!>"))
                return await guild.fetch_member(member_id)
            
            # Essayer ID simple
            try:
                member_id = int(input_str)
                return await guild.fetch_member(member_id)
            except ValueError:
                return None
        except Exception:
            return None


async def setup(bot: commands.Bot):
    cog = TicketsCog(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
