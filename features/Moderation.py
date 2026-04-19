import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import logging
from config import Config
from modules.I18n import t

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_moderation_log(self, log_type: str, embed: discord.Embed, guild: discord.Guild):
        if log_type in Config.Logs and Config.Logs[log_type]["enabled"]:
            channel_id = Config.Logs[log_type]["channel_id"]
            try:
                channel = guild.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi du log {log_type}: {str(e)}")

    @app_commands.command(name="kick", description=t("moderation.commands.kick_description", "Expulse un utilisateur du serveur"))
    @app_commands.describe(
        member="Le membre à expulser",
        reason="Raison de l'expulsion (optionnel)"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            if member.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    t("moderation.kick.cannot_kick_higher_user", "❌ Vous ne pouvez pas expulser cette personne (rôle trop élevé)."),
                    ephemeral=True
                )
                return

            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    t("moderation.kick.cannot_kick_higher_bot", "❌ Je ne peux pas expulser cette personne (rôle trop élevé)."),
                    ephemeral=True
                )
                return

            dm_embed = discord.Embed(
                title=t("moderation.kick.dm_title", "Vous avez été expulsé"),
                description=t("moderation.kick.dm_description", "Vous avez été expulsé de {guild}", guild=interaction.guild.name),
                color=discord.Color.red()
            )
            if reason:
                dm_embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            
            try:
                await member.send(embed=dm_embed)
            except:
                pass

            await member.kick(reason=reason)

            embed = discord.Embed(
                title=t("moderation.kick.success_title", "Membre expulsé"),
                description=t("moderation.kick.success_description", "{member} a été expulsé du serveur.", member=member.mention),
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            embed.set_footer(text=t("moderation.kick.success_footer", "Expulsé par {moderator}", moderator=interaction.user.name))

            await interaction.response.send_message(embed=embed)
            
            # Log de modération
            log_embed = discord.Embed(
                title=t("moderation.kick.log_title", "🚪 Utilisateur expulsé (KICK)"),
                description=t("moderation.kick.log_description", "**Utilisateur:** {member}\n**Modérateur:** {moderator}", member=member.mention, moderator=interaction.user.mention),
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            if reason:
                log_embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            log_embed.add_field(name=t("moderation.common.user_id_field", "ID utilisateur"), value=member.id, inline=True)
            log_embed.set_footer(text=t("moderation.common.moderator_id_footer", "ID modérateur: {moderator_id}", moderator_id=interaction.user.id))
            
            await self.send_moderation_log("member_kick", log_embed, interaction.guild)
            logging.info(f"{member} kicked by {interaction.user} - Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(t("moderation.common.generic_error", "❌ Erreur : {error}", error=str(e)), ephemeral=True)
            logging.error(f"Erreur lors du kick : {str(e)}")

    @app_commands.command(name="ban", description=t("moderation.commands.ban_description", "Bannit un utilisateur du serveur"))
    @app_commands.describe(
        member="Le membre à bannir",
        reason="Raison du bannissement (optionnel)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            if member.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    t("moderation.ban.cannot_ban_higher_user", "❌ Vous ne pouvez pas bannir cette personne (rôle trop élevé)."),
                    ephemeral=True
                )
                return

            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    t("moderation.ban.cannot_ban_higher_bot", "❌ Je ne peux pas bannir cette personne (rôle trop élevé)."),
                    ephemeral=True
                )
                return

            dm_embed = discord.Embed(
                title=t("moderation.ban.dm_title", "Vous avez été banni"),
                description=t("moderation.ban.dm_description", "Vous avez été banni de {guild}", guild=interaction.guild.name),
                color=discord.Color.red()
            )
            if reason:
                dm_embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            
            try:
                await member.send(embed=dm_embed)
            except:
                pass

            await member.ban(reason=reason)

            embed = discord.Embed(
                title=t("moderation.ban.success_title", "Membre banni"),
                description=t("moderation.ban.success_description", "{member} a été banni du serveur.", member=member.mention),
                color=discord.Color.red()
            )
            if reason:
                embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            embed.set_footer(text=t("moderation.ban.success_footer", "Banni par {moderator}", moderator=interaction.user.name))

            await interaction.response.send_message(embed=embed)
            
            # Log de modération
            log_embed = discord.Embed(
                title=t("moderation.ban.log_title", "🔨 Utilisateur banni (BAN)"),
                description=t("moderation.ban.log_description", "**Utilisateur:** {member}\n**Modérateur:** {moderator}", member=member.mention, moderator=interaction.user.mention),
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            if reason:
                log_embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            log_embed.add_field(name=t("moderation.common.user_id_field", "ID utilisateur"), value=member.id, inline=True)
            log_embed.set_footer(text=t("moderation.common.moderator_id_footer", "ID modérateur: {moderator_id}", moderator_id=interaction.user.id))
            
            await self.send_moderation_log("member_ban", log_embed, interaction.guild)
            logging.info(f"{member} banned by {interaction.user} - Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(t("moderation.common.generic_error", "❌ Erreur : {error}", error=str(e)), ephemeral=True)
            logging.error(f"Erreur lors du ban : {str(e)}")

    @app_commands.command(name="unban", description=t("moderation.commands.unban_description", "Débannit un utilisateur du serveur"))
    @app_commands.describe(
        user_id="L'ID de l'utilisateur à débannir",
        reason="Raison du débannissement (optionnel)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = None):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=reason)

            embed = discord.Embed(
                title=t("moderation.unban.success_title", "Utilisateur débanni"),
                description=t("moderation.unban.success_description", "{user} ({username}) a été débanni du serveur.", user=user.mention, username=user.name),
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            embed.set_footer(text=t("moderation.unban.success_footer", "Débanni par {moderator}", moderator=interaction.user.name))

            await interaction.response.send_message(embed=embed)
            
            # Log de modération
            log_embed = discord.Embed(
                title=t("moderation.unban.log_title", "🔓 Utilisateur débanni (UNBAN)"),
                description=t("moderation.unban.log_description", "**Utilisateur:** {user}\n**Modérateur:** {moderator}", user=user.mention, moderator=interaction.user.mention),
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            if reason:
                log_embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            log_embed.add_field(name=t("moderation.common.user_id_field", "ID utilisateur"), value=user.id, inline=True)
            log_embed.set_footer(text=t("moderation.common.moderator_id_footer", "ID modérateur: {moderator_id}", moderator_id=interaction.user.id))
            
            await self.send_moderation_log("member_unban", log_embed, interaction.guild)
            logging.info(f"{user} unbanned by {interaction.user} - Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(t("moderation.common.generic_error", "❌ Erreur : {error}", error=str(e)), ephemeral=True)
            logging.error(f"Erreur lors du unban : {str(e)}")

    @app_commands.command(name="mute", description=t("moderation.commands.mute_description", "Applique un timeout à un utilisateur"))
    @app_commands.describe(
        member="Le membre à timeout",
        duration="Durée du timeout en minutes (par défaut 10, max 40320)",
        reason="Raison du timeout (optionnel)"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int = 10, reason: str = None):
        try:
            if duration > 40320:
                await interaction.response.send_message(
                    t("moderation.mute.max_duration", "❌ La durée maximale du timeout est de 40320 minutes (28 jours)."),
                    ephemeral=True
                )
                return

            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    t("moderation.mute.cannot_timeout_higher", "❌ Je ne peux pas timeout cette personne (rôle trop élevé)."),
                    ephemeral=True
                )
                return

            timeout_duration = timedelta(minutes=duration)
            await member.timeout(timeout_duration, reason=reason)

            embed = discord.Embed(
                title=t("moderation.mute.success_title", "Timeout appliqué"),
                description=t("moderation.mute.success_description", "{member} a reçu un timeout.", member=member.mention),
                color=discord.Color.orange()
            )
            embed.add_field(name=t("moderation.mute.duration_field", "Durée"), value=t("moderation.mute.duration_value", "{duration} minutes", duration=duration), inline=False)
            if reason:
                embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            embed.set_footer(text=t("moderation.mute.success_footer", "Timeout par {moderator}", moderator=interaction.user.name))

            await interaction.response.send_message(embed=embed)
            
            # Log de modération
            log_embed = discord.Embed(
                title=t("moderation.mute.log_title", "🔇 Timeout appliqué (MUTE)"),
                description=t("moderation.mute.log_description", "**Utilisateur:** {member}\n**Modérateur:** {moderator}", member=member.mention, moderator=interaction.user.mention),
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name=t("moderation.mute.duration_field", "Durée"), value=t("moderation.mute.duration_value", "{duration} minutes", duration=duration), inline=True)
            if reason:
                log_embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            log_embed.add_field(name=t("moderation.common.user_id_field", "ID utilisateur"), value=member.id, inline=True)
            log_embed.set_footer(text=t("moderation.common.moderator_id_footer", "ID modérateur: {moderator_id}", moderator_id=interaction.user.id))
            
            await self.send_moderation_log("member_timeout", log_embed, interaction.guild)
            logging.info(f"{member} timed out by {interaction.user} for {duration} minutes - Reason: {reason}")

        except discord.Forbidden:
            await interaction.response.send_message(t("moderation.mute.missing_permissions", "❌ Je n'ai pas les permissions nécessaires pour timeout ce membre."), ephemeral=True)
            logging.error("Permission manquante pour timeout")
        except Exception as e:
            await interaction.response.send_message(t("moderation.common.generic_error", "❌ Erreur : {error}", error=str(e)), ephemeral=True)
            logging.error(f"Erreur lors du timeout : {str(e)}")

    @app_commands.command(name="unmute", description=t("moderation.commands.unmute_description", "Retire le timeout d'un utilisateur"))
    @app_commands.describe(
        member="Le membre dont retirer le timeout",
        reason="Raison du retrait du timeout (optionnel)"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            await member.timeout(None, reason=reason)

            embed = discord.Embed(
                title=t("moderation.unmute.success_title", "Timeout retiré"),
                description=t("moderation.unmute.success_description", "{member} a maintenant la parole.", member=member.mention),
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            embed.set_footer(text=t("moderation.unmute.success_footer", "Timeout retiré par {moderator}", moderator=interaction.user.name))

            await interaction.response.send_message(embed=embed)
            
            # Log de modération
            log_embed = discord.Embed(
                title=t("moderation.unmute.log_title", "🔊 Timeout retiré (UNMUTE)"),
                description=t("moderation.unmute.log_description", "**Utilisateur:** {member}\n**Modérateur:** {moderator}", member=member.mention, moderator=interaction.user.mention),
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            if reason:
                log_embed.add_field(name=t("moderation.common.reason_field", "Raison"), value=reason, inline=False)
            log_embed.add_field(name=t("moderation.common.user_id_field", "ID utilisateur"), value=member.id, inline=True)
            log_embed.set_footer(text=t("moderation.common.moderator_id_footer", "ID modérateur: {moderator_id}", moderator_id=interaction.user.id))
            
            await self.send_moderation_log("member_timeout", log_embed, interaction.guild)
            logging.info(f"{member} timeout removed by {interaction.user} - Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(t("moderation.common.generic_error", "❌ Erreur : {error}", error=str(e)), ephemeral=True)
            logging.error(f"Erreur lors du retrait du timeout : {str(e)}")

    @app_commands.command(name="purge", description=t("moderation.commands.purge_description", "Supprime un nombre de messages"))
    @app_commands.describe(
        amount="Le nombre de messages à supprimer (max 100)",
        user="Filtrer par utilisateur (optionnel)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int, user: discord.Member = None):
        try:
            if amount > 100:
                await interaction.response.send_message(
                    t("moderation.purge.max_100", "❌ Vous ne pouvez pas supprimer plus de 100 messages."),
                    ephemeral=True
                )
                return

            await interaction.response.defer(ephemeral=True)

            def filter_messages(msg):
                if user:
                    return msg.author == user
                return True

            deleted = await interaction.channel.purge(limit=amount, check=filter_messages)

            embed = discord.Embed(
                title=t("moderation.purge.success_title", "Messages supprimés"),
                description=t("moderation.purge.success_description", "{count} message(s) supprimé(s).", count=len(deleted)),
                color=discord.Color.green()
            )
            if user:
                embed.add_field(name=t("moderation.purge.user_field", "Utilisateur"), value=user.mention, inline=False)
            embed.set_footer(text=t("moderation.purge.success_footer", "Purgé par {moderator}", moderator=interaction.user.name))

            await interaction.followup.send(embed=embed, ephemeral=True)
            logging.info(f"{len(deleted)} messages purged by {interaction.user} - User filter: {user}")

        except discord.Forbidden:
            await interaction.followup.send(t("moderation.purge.missing_permissions", "❌ Je n'ai pas les permissions nécessaires."), ephemeral=True)
            logging.error("Permission manquante pour purge")
        except Exception as e:
            try:
                await interaction.followup.send(t("moderation.common.generic_error", "❌ Erreur : {error}", error=str(e)), ephemeral=True)
            except:
                pass
            logging.error(f"Erreur lors de la purge : {str(e)}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModerationCog(bot))
