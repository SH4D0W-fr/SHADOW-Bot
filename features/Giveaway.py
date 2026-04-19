import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import logging
import random
from modules.Database import db
from config import Config
from modules.I18n import t

class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()
    
    async def send_giveaway_log(self, embed: discord.Embed):
        if "giveaway" in Config.Logs and Config.Logs["giveaway"]["enabled"]:
            try:
                channel = self.bot.get_channel(Config.Logs["giveaway"]["channel_id"])
                if channel:
                    await channel.send(embed=embed)
            except Exception as e:
                logging.error(f"Erreur log giveaway: {str(e)}")

    @app_commands.command(name="giveaway_create", description=t("giveaway.commands.create_description", "Crée un nouveau giveaway"))
    @app_commands.describe(
        titre="Titre du giveaway",
        date="Date de fin (format: JJ/MM/AAAA)",
        heure="Heure de fin (format: HH:MM)",
        nombre_gagnants="Nombre de gagnants",
        prix="Prix séparés par des virgules (ex: 100€, Nitro, Boost)",
        conditions="Conditions de participation (optionnel)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_create(
        self,
        interaction: discord.Interaction,
        titre: str,
        date: str,
        heure: str,
        nombre_gagnants: int,
        prix: str,
        conditions: str = None
    ):
        try:
            try:
                date_parts = date.split('/')
                heure_parts = heure.split(':')
                
                if len(date_parts) != 3 or len(heure_parts) != 2:
                    await interaction.response.send_message(
                        t("giveaway.create.invalid_date_time_format", "❌ Format de date ou heure invalide. Utilisez JJ/MM/AAAA pour la date et HH:MM pour l'heure."),
                        ephemeral=True
                    )
                    return
                
                jour = int(date_parts[0])
                mois = int(date_parts[1])
                annee = int(date_parts[2])
                heure_int = int(heure_parts[0])
                minute = int(heure_parts[1])
                
                fin_giveaway = datetime(annee, mois, jour, heure_int, minute)
                
                # Vérifier que la date est dans le futur
                if fin_giveaway <= datetime.now():
                    await interaction.response.send_message(
                        t("giveaway.create.end_date_must_be_future", "❌ La date de fin doit être dans le futur."),
                        ephemeral=True
                    )
                    return
                    
            except ValueError as e:
                await interaction.response.send_message(
                    t("giveaway.create.date_time_parse_error", "❌ Erreur de format de date/heure : {error}", error=str(e)),
                    ephemeral=True
                )
                return

            if nombre_gagnants <= 0:
                await interaction.response.send_message(t("giveaway.create.winner_count_must_be_positive", "❌ Le nombre de gagnants doit être positif."), ephemeral=True)
                return

            liste_prix = [p.strip() for p in prix.split(",")]
            giveaway_id = str(int(datetime.now().timestamp() * 1000))
            server_id = str(interaction.guild.id)
            
            success = db.create_giveaway(
                giveaway_id=giveaway_id,
                server_id=server_id,
                channel_id=str(interaction.channel.id),
                title=titre,
                prizes=liste_prix,
                winner_count=nombre_gagnants,
                end_date=fin_giveaway,
                organizer_id=str(interaction.user.id),
                conditions=conditions
            )
            
            if not success:
                await interaction.response.send_message(
                    t("giveaway.create.database_save_error", "❌ Erreur lors de la sauvegarde du giveaway en base de données."),
                    ephemeral=True
                )
                return
            
            giveaway_data = db.get_giveaway(giveaway_id)
            embed = self.create_giveaway_embed(giveaway_data, ongoing=True)
            message = await interaction.channel.send(embed=embed)
            db.update_giveaway_message_id(giveaway_id, message.id)
            view = GiveawayView(self, giveaway_id)
            await message.edit(view=view)
            
            temps_restant = fin_giveaway - datetime.now()
            heures = int(temps_restant.total_seconds() // 3600)
            minutes = int((temps_restant.total_seconds() % 3600) // 60)
            
            await interaction.response.send_message(
                t("giveaway.create.success", "✅ Giveaway créé ! Il se terminera le {date} à {heure} (dans {heures}h {minutes}m).", date=date, heure=heure, heures=heures, minutes=minutes),
                ephemeral=True
            )
            
            log_embed = discord.Embed(
                title="🎉 Giveaway créé",
                description=f"Un nouveau giveaway a été créé",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="📝 Titre", value=titre, inline=False)
            log_embed.add_field(name="🎁 Prix", value=", ".join(liste_prix), inline=False)
            if conditions:
                log_embed.add_field(name="📋 Conditions", value=conditions, inline=False)
            log_embed.add_field(name="👥 Gagnants", value=str(nombre_gagnants), inline=True)
            log_embed.add_field(name="📅 Date de fin", value=f"{date} à {heure}", inline=True)
            log_embed.add_field(name="📍 Canal", value=interaction.channel.mention, inline=True)
            log_embed.set_footer(text=f"Créé par {interaction.user.name} | ID: {giveaway_id}")
            
            await self.send_giveaway_log(log_embed)
            
            logging.info(f"Giveaway créé : {giveaway_id} - {titre} sur le serveur {server_id}")
            
        except Exception as e:
            logging.error(f"Erreur lors de la création du giveaway : {str(e)}")
            await interaction.response.send_message(
                t("giveaway.create.generic_error", "❌ Erreur lors de la création du giveaway : {error}", error=str(e)),
                ephemeral=True
            )

    def create_giveaway_embed(self, giveaway_data: dict, ongoing: bool = True) -> discord.Embed:
        couleur = discord.Color.gold() if ongoing else discord.Color.green()
        
        fin_datetime = giveaway_data["giveaway_end_date"]
        temps_restant = fin_datetime - datetime.now()
        
        if temps_restant.total_seconds() > 0:
            heures = int(temps_restant.total_seconds() // 3600)
            minutes = int((temps_restant.total_seconds() % 3600) // 60)
            temps_str = f"{heures}h {minutes}m" if heures > 0 else f"{minutes}m"
        else:
            temps_str = t("giveaway.embed.ended", "Terminé")
        
        embed = discord.Embed(
            title=f"🎉 {giveaway_data['giveaway_title']}",
            color=couleur
        )
        
        embed.add_field(
            name=t("giveaway.embed.price_field", "🎁 Prix"),
            value="\n".join([f"• {prix}" for prix in giveaway_data["giveaway_prizes"]]),
            inline=False
        )
        
        if giveaway_data.get("giveaway_conditions"):
            embed.add_field(
                name=t("giveaway.embed.conditions_field", "📋 Conditions"),
                value=giveaway_data["giveaway_conditions"],
                inline=False
            )
        
        embed.add_field(
            name=t("giveaway.embed.winners_field", "👥 Gagnants"),
            value=str(giveaway_data["giveaway_winner_count"]),
            inline=True
        )
        
        embed.add_field(
            name=t("giveaway.embed.remaining_time_field", "⏱️ Temps restant"),
            value=temps_str,
            inline=True
        )
        
        embed.add_field(
            name=t("giveaway.embed.participants_field", "📊 Participants"),
            value=str(len(giveaway_data["giveaway_participants"])),
            inline=True
        )
        
        date_fin_str = fin_datetime.strftime("%d/%m/%Y à %H:%M")
        embed.add_field(
            name=t("giveaway.embed.end_field", "📅 Fin"),
            value=date_fin_str,
            inline=False
        )
        
        if not ongoing:
            embed.set_footer(text=t("giveaway.embed.ended_footer", "Giveaway terminé"))
        else:
            embed.set_footer(text=t("giveaway.embed.join_footer", "Cliquez sur le bouton pour participer"))
        
        return embed

    @tasks.loop(minutes=1)
    async def check_giveaways(self):
        try:
            now = datetime.now()
            active_giveaways = db.get_active_giveaways()
            
            for giveaway_data in active_giveaways:
                fin_datetime = giveaway_data["giveaway_end_date"]
                
                if now >= fin_datetime:
                    await self.end_giveaway(giveaway_data["giveaway_id"], giveaway_data)
                    db.mark_giveaway_finished(giveaway_data["giveaway_id"])
                
        except Exception as e:
            logging.error(f"Erreur vérification giveaways : {str(e)}")

    async def end_giveaway(self, giveaway_id: str, giveaway_data: dict):
        try:
            canal = self.bot.get_channel(int(giveaway_data["giveaway_channel_id"]))
            if not canal:
                canal = await self.bot.fetch_channel(int(giveaway_data["giveaway_channel_id"]))
            
            if not canal:
                logging.error(f"Impossible de trouver le canal {giveaway_data['giveaway_channel_id']}")
                return
            
            participants = giveaway_data["giveaway_participants"]
            nombre_gagnants = min(giveaway_data["giveaway_winner_count"], len(participants))
            
            if nombre_gagnants == 0:
                embed_annule = discord.Embed(
                    title=f"❌ {giveaway_data['giveaway_title']} - Annulé",
                    description="Pas assez de participants pour désigner des gagnants.",
                    color=discord.Color.red()
                )
                
                if giveaway_data.get("giveaway_message_id"):
                    try:
                        message_original = await canal.fetch_message(int(giveaway_data["giveaway_message_id"]))
                        await message_original.edit(embed=embed_annule, view=None)
                    except Exception as e:
                        logging.warning(f"Impossible de modifier le message original : {str(e)}")
                
                await canal.send(embed=embed_annule)
                logging.info(f"Giveaway {giveaway_id} annulé : pas de participants")
                return
            
            gagnants = random.sample(participants, nombre_gagnants)
            
            embed_original = discord.Embed(
                title=f"🎉 {giveaway_data['giveaway_title']} - Terminé",
                color=discord.Color.green()
            )
            
            embed_original.add_field(
                name="🎁 Prix",
                value="\n".join([f"• {prix}" for prix in giveaway_data["giveaway_prizes"]]),
                inline=False
            )
            
            if giveaway_data.get("giveaway_conditions"):
                embed_original.add_field(
                    name="📋 Conditions",
                    value=giveaway_data["giveaway_conditions"],
                    inline=False
                )
            
            gagnants_mentions = ", ".join([f"<@{gagnant_id}>" for gagnant_id in gagnants])
            embed_original.add_field(
                name="🏆 Gagnants",
                value=gagnants_mentions,
                inline=False
            )
            
            embed_original.add_field(
                name="👥 Total participants",
                value=str(len(participants)),
                inline=True
            )
            
            date_fin_str = giveaway_data["giveaway_end_date"].strftime("%d/%m/%Y à %H:%M")
            embed_original.add_field(
                name="📅 Date de fin",
                value=date_fin_str,
                inline=True
            )
            
            embed_original.set_footer(text="Giveaway terminé")
            
            if giveaway_data.get("giveaway_message_id"):
                try:
                    message_original = await canal.fetch_message(int(giveaway_data["giveaway_message_id"]))
                    await message_original.edit(embed=embed_original, view=None)
                except Exception as e:
                    logging.warning(f"Impossible de modifier le message original : {str(e)}")
            
            embed_annonce = discord.Embed(
                title=f"🎉 Giveaway terminé !",
                description=f"Le giveaway **{giveaway_data['giveaway_title']}** est terminé !",
                color=discord.Color.gold()
            )
            
            embed_annonce.add_field(
                name="🏆 Gagnants",
                value=gagnants_mentions,
                inline=False
            )
            
            embed_annonce.add_field(
                name="🎁 Prix",
                value="\n".join([f"• {prix}" for prix in giveaway_data["giveaway_prizes"]]),
                inline=False
            )
            
            await canal.send(embed=embed_annonce)
            
            for gagnant_id in gagnants:
                try:
                    user = await self.bot.fetch_user(gagnant_id)
                    dm_embed = discord.Embed(
                        title="🎉 Vous avez gagné !",
                        description=f"Félicitations ! Vous avez gagné le giveaway **{giveaway_data['giveaway_title']}**",
                        color=discord.Color.gold()
                    )
                    dm_embed.add_field(
                        name="🎁 Prix",
                        value="\n".join([f"• {prix}" for prix in giveaway_data["giveaway_prizes"]]),
                        inline=False
                    )
                    await user.send(embed=dm_embed)
                except Exception as e:
                    logging.warning(f"Impossible d'envoyer un MP au gagnant {gagnant_id} : {str(e)}")
            
            log_embed = discord.Embed(
                title="🏆 Giveaway terminé",
                description=f"Le giveaway **{giveaway_data['giveaway_title']}** est terminé",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="🎁 Prix", value="\n".join([f"• {prix}" for prix in giveaway_data["giveaway_prizes"]]), inline=False)
            log_embed.add_field(name="🏆 Gagnants", value=gagnants_mentions, inline=False)
            log_embed.add_field(name="👥 Participants", value=str(len(participants)), inline=True)
            log_embed.add_field(name="📍 Canal", value=f"<#{giveaway_data['giveaway_channel_id']}>", inline=True)
            log_embed.set_footer(text=f"ID: {giveaway_id}")
            
            await self.send_giveaway_log(log_embed)
            
            logging.info(f"Giveaway {giveaway_id} terminé avec {nombre_gagnants} gagnants")
            
        except Exception as e:
            logging.error(f"Erreur terminaison giveaway {giveaway_id} : {str(e)}")

    @app_commands.command(name="giveaway_participants", description=t("giveaway.commands.participants_description", "Affiche les participants du giveaway"))
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_participants(self, interaction: discord.Interaction):
        try:
            giveaway_data = db.get_active_giveaway_by_channel(str(interaction.channel.id))
            
            if not giveaway_data:
                await interaction.response.send_message(
                    t("giveaway.participants.no_active", "❌ Aucun giveaway actif dans ce canal."),
                    ephemeral=True
                )
                return
            
            participants = giveaway_data["giveaway_participants"]
            
            if not participants:
                await interaction.response.send_message(
                    t("giveaway.participants.none_yet", "ℹ️ Aucun participant pour le moment."),
                    ephemeral=True
                )
                return
            
            participants_mentions = "\n".join([f"• <@{pid}>" for pid in participants])
            embed = discord.Embed(
                title=t("giveaway.participants.title", "📊 Participants du giveaway"),
                description=participants_mentions,
                color=discord.Color.blue()
            )
            embed.add_field(name=t("giveaway.participants.total_field", "Total"), value=str(len(participants)), inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.error(f"Erreur : {str(e)}")
            await interaction.response.send_message(
                t("giveaway.participants.generic_error", "❌ Erreur : {error}", error=str(e)),
                ephemeral=True
            )

    @app_commands.command(name="giveaway_delete", description=t("giveaway.commands.delete_description", "Supprime un giveaway actif"))
    @app_commands.describe(
        message_id="L'ID du message du giveaway à supprimer"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_delete(self, interaction: discord.Interaction, message_id: str):
        try:
            giveaway_data = db.get_giveaway_by_message_id(message_id)
            
            if not giveaway_data:
                await interaction.response.send_message(
                    t("giveaway.delete.not_found_by_message_id", "❌ Aucun giveaway trouvé avec cet ID de message."),
                    ephemeral=True
                )
                return
            
            if giveaway_data["server_id"] != str(interaction.guild.id):
                await interaction.response.send_message(
                    t("giveaway.delete.wrong_server", "❌ Ce giveaway n'appartient pas à ce serveur."),
                    ephemeral=True
                )
                return
            
            try:
                channel = self.bot.get_channel(int(giveaway_data["giveaway_channel_id"]))
                if channel:
                    message = await channel.fetch_message(int(message_id))
                    await message.delete()
            except Exception as e:
                logging.warning(f"Impossible de supprimer le message : {str(e)}")
            
            success = db.delete_giveaway(giveaway_data["giveaway_id"])
            
            if success:
                await interaction.response.send_message(
                    t("giveaway.delete.success", "✅ Giveaway **{title}** supprimé avec succès.", title=giveaway_data['giveaway_title']),
                    ephemeral=True
                )
                
                log_embed = discord.Embed(
                    title="🗑️ Giveaway supprimé",
                    description=f"Un giveaway a été supprimé",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                log_embed.add_field(name="📝 Titre", value=giveaway_data['giveaway_title'], inline=False)
                log_embed.add_field(name="🎁 Prix", value="\n".join([f"• {prix}" for prix in giveaway_data["giveaway_prizes"]]), inline=False)
                log_embed.add_field(name="👥 Participants", value=str(len(giveaway_data["giveaway_participants"])), inline=True)
                log_embed.add_field(name="📍 Canal", value=f"<#{giveaway_data['giveaway_channel_id']}>", inline=True)
                log_embed.set_footer(text=f"Supprimé par {interaction.user.name} | ID: {giveaway_data['giveaway_id']}")
                
                await self.send_giveaway_log(log_embed)
                
                logging.info(f"Giveaway {giveaway_data['giveaway_id']} supprimé par {interaction.user}")
            else:
                await interaction.response.send_message(
                    t("giveaway.delete.failure", "❌ Erreur lors de la suppression du giveaway."),
                    ephemeral=True
                )
                
        except Exception as e:
            logging.error(f"Erreur lors de la suppression : {str(e)}")
            await interaction.response.send_message(
                t("giveaway.delete.generic_error", "❌ Erreur : {error}", error=str(e)),
                ephemeral=True
            )

    @app_commands.command(name="giveaway_reroll", description=t("giveaway.commands.reroll_description", "Retirer un nouveau gagnant pour un giveaway terminé"))
    @app_commands.describe(
        message_id="L'ID du message du giveaway",
        nombre_gagnants="Nombre de nouveaux gagnants à tirer (optionnel, défaut: 1)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_reroll(
        self,
        interaction: discord.Interaction,
        message_id: str,
        nombre_gagnants: int = 1
    ):
        try:
            giveaway_data = db.get_giveaway_by_message_id(message_id)
            
            if not giveaway_data:
                await interaction.response.send_message(
                    t("giveaway.reroll.not_found_by_message_id", "❌ Aucun giveaway trouvé avec cet ID de message."),
                    ephemeral=True
                )
                return
            
            if giveaway_data["server_id"] != str(interaction.guild.id):
                await interaction.response.send_message(
                    t("giveaway.reroll.wrong_server", "❌ Ce giveaway n'appartient pas à ce serveur."),
                    ephemeral=True
                )
                return
            
            if not giveaway_data["giveaway_is_finished"]:
                await interaction.response.send_message(
                    t("giveaway.reroll.not_finished", "❌ Ce giveaway n'est pas encore terminé. Attendez la fin pour reroll."),
                    ephemeral=True
                )
                return
            
            participants = giveaway_data["giveaway_participants"]
            
            if len(participants) < nombre_gagnants:
                await interaction.response.send_message(
                    t("giveaway.reroll.not_enough_participants", "❌ Pas assez de participants pour tirer {winner_count} gagnant(s). Il y a seulement {participant_count} participant(s).", winner_count=nombre_gagnants, participant_count=len(participants)),
                    ephemeral=True
                )
                return
            
            if nombre_gagnants <= 0:
                await interaction.response.send_message(
                    t("giveaway.reroll.winner_count_must_be_positive", "❌ Le nombre de gagnants doit être positif."),
                    ephemeral=True
                )
                return
            
            await interaction.response.defer(ephemeral=True)
            nouveaux_gagnants = random.sample(participants, nombre_gagnants)
            
            embed = discord.Embed(
                title=t("giveaway.reroll.embed_title", "🔄 {title} - Reroll", title=giveaway_data['giveaway_title']),
                color=discord.Color.purple()
            )
            
            gagnants_mentions = ", ".join([f"<@{gagnant_id}>" for gagnant_id in nouveaux_gagnants])
            embed.add_field(
                name=t("giveaway.reroll.new_winner_label", "🏆 Nouveau gagnant") if nombre_gagnants == 1 else t("giveaway.reroll.new_winners_label", "🏆 Nouveaux gagnants"),
                value=gagnants_mentions,
                inline=False
            )
            
            embed.set_footer(text=t("giveaway.reroll.footer", "Reroll effectué par {user}", user=interaction.user.name))
            
            channel = self.bot.get_channel(int(giveaway_data["giveaway_channel_id"]))
            if channel:
                await channel.send(embed=embed)
            
            for gagnant_id in nouveaux_gagnants:
                try:
                    user = await self.bot.fetch_user(gagnant_id)
                    dm_embed = discord.Embed(
                        title=t("giveaway.reroll.dm_title", "🎉 Vous avez gagné (Reroll) !"),
                        description=t("giveaway.reroll.dm_description", "Félicitations ! Vous avez été sélectionné lors du reroll du giveaway **{title}**", title=giveaway_data['giveaway_title']),
                        color=discord.Color.purple()
                    )
                    dm_embed.add_field(
                        name="🎁 Prix",
                        value="\n".join([f"• {prix}" for prix in giveaway_data["giveaway_prizes"]]),
                        inline=False
                    )
                    await user.send(embed=dm_embed)
                except Exception as e:
                    logging.warning(f"Impossible d'envoyer un MP au gagnant {gagnant_id} : {str(e)}")
            
            await interaction.followup.send(
                t("giveaway.reroll.success_one", "✅ Reroll effectué ! {winner_count} nouveau gagnant tiré.", winner_count=nombre_gagnants) if nombre_gagnants == 1 else t("giveaway.reroll.success_many", "✅ Reroll effectué ! {winner_count} nouveaux gagnants tirés.", winner_count=nombre_gagnants),
                ephemeral=True
            )
            
            log_embed = discord.Embed(
                title="🔄 Giveaway Reroll",
                description=f"Un reroll a été effectué pour le giveaway **{giveaway_data['giveaway_title']}**",
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="🏆 Nouveaux gagnants", value=gagnants_mentions, inline=False)
            log_embed.add_field(name="🎁 Prix", value="\n".join([f"• {prix}" for prix in giveaway_data["giveaway_prizes"]]), inline=False)
            log_embed.add_field(name="👥 Nombre de gagnants", value=str(nombre_gagnants), inline=True)
            log_embed.add_field(name="📍 Canal", value=f"<#{giveaway_data['giveaway_channel_id']}>", inline=True)
            log_embed.set_footer(text=f"Reroll par {interaction.user.name} | ID: {giveaway_data['giveaway_id']}")
            
            await self.send_giveaway_log(log_embed)
            
            logging.info(f"Reroll du giveaway {giveaway_data['giveaway_id']} par {interaction.user}")
            
        except Exception as e:
            logging.error(f"Erreur reroll : {str(e)}")
            if interaction.response.is_done():
                await interaction.followup.send(
                    t("giveaway.reroll.generic_error", "❌ Erreur : {error}", error=str(e)),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    t("giveaway.reroll.generic_error", "❌ Erreur : {error}", error=str(e)),
                    ephemeral=True
                )


class GiveawayView(discord.ui.View):
    def __init__(self, cog: GiveawayCog, giveaway_id: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.giveaway_id = giveaway_id

    @discord.ui.button(label=t("giveaway.participation.button_label", "Participer 🎉"), style=discord.ButtonStyle.primary)
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            giveaway_data = db.get_giveaway(self.giveaway_id)
            
            if not giveaway_data:
                await interaction.response.send_message(
                    t("giveaway.participation.no_longer_exists", "❌ Ce giveaway n'existe plus."),
                    ephemeral=True
                )
                return
            
            if giveaway_data["giveaway_is_finished"]:
                await interaction.response.send_message(
                    t("giveaway.participation.already_finished", "❌ Ce giveaway est terminé."),
                    ephemeral=True
                )
                return
            
            user_id = interaction.user.id
            
            if user_id in giveaway_data["giveaway_participants"]:
                view = UnsubscribeView(self.giveaway_id)
                await interaction.response.send_message(
                    t("giveaway.participation.already_participating", "⚠️ Vous participez déjà à ce giveaway !\nVoulez-vous vous désinscrire ?"),
                    view=view,
                    ephemeral=True
                )
                return
            
            success = db.add_participant(self.giveaway_id, user_id)
            
            if not success:
                await interaction.response.send_message(
                    t("giveaway.participation.add_participation_error", "❌ Erreur lors de l'ajout de votre participation."),
                    ephemeral=True
                )
                return
            
            giveaway_data = db.get_giveaway(self.giveaway_id)
            
            await interaction.response.send_message(
                t("giveaway.participation.joined_success", "✅ Vous participez au giveaway ! ({participant_count} participant(s))", participant_count=len(giveaway_data['giveaway_participants'])),
                ephemeral=True
            )
            
            logging.info(f"Utilisateur {interaction.user} a participé au giveaway {self.giveaway_id}")
            
        except Exception as e:
            logging.error(f"Erreur lors de la participation : {str(e)}")
            await interaction.response.send_message(
                t("giveaway.reroll.generic_error", "❌ Erreur : {error}", error=str(e)),
                ephemeral=True
            )


class UnsubscribeView(discord.ui.View):
    def __init__(self, giveaway_id: str):
        super().__init__(timeout=60)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label=t("giveaway.unsubscribe.button_label", "Se désinscrire"), style=discord.ButtonStyle.danger)
    async def unsubscribe(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            giveaway_data = db.get_giveaway(self.giveaway_id)
            
            if not giveaway_data:
                await interaction.response.edit_message(
                    content=t("giveaway.participation.no_longer_exists", "❌ Ce giveaway n'existe plus."),
                    view=None
                )
                return
            
            if giveaway_data["giveaway_is_finished"]:
                await interaction.response.edit_message(
                    content=t("giveaway.participation.already_finished", "❌ Ce giveaway est terminé."),
                    view=None
                )
                return
            
            user_id = interaction.user.id
            
            success = db.remove_participant(self.giveaway_id, user_id)
            
            if not success:
                await interaction.response.edit_message(
                    content=t("giveaway.unsubscribe.not_participating_or_error", "❌ Erreur : Vous ne participez pas à ce giveaway ou une erreur s'est produite."),
                    view=None
                )
                return
            
            giveaway_data = db.get_giveaway(self.giveaway_id)
            
            await interaction.response.edit_message(
                content=t("giveaway.unsubscribe.left_success", "✅ Vous ne participez plus au giveaway. ({participant_count} participant(s))", participant_count=len(giveaway_data['giveaway_participants'])),
                view=None
            )
            
            logging.info(f"Utilisateur {interaction.user} s'est désinscrit du giveaway {self.giveaway_id}")
            
        except Exception as e:
            logging.error(f"Erreur lors de la désinscription : {str(e)}")
            await interaction.response.edit_message(
                content=t("giveaway.unsubscribe.generic_error", "❌ Erreur : {error}", error=str(e)),
                view=None
            )

    @discord.ui.button(label=t("giveaway.unsubscribe.cancel_button_label", "Annuler"), style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content=t("giveaway.unsubscribe.cancelled", "❌ Désinscription annulée. Vous participez toujours au giveaway."),
            view=None
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GiveawayCog(bot))
