import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
import logging

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Expulse un utilisateur du serveur")
    @app_commands.describe(
        member="Le membre à expulser",
        reason="Raison de l'expulsion (optionnel)"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            if member.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "❌ Vous ne pouvez pas expulser cette personne (rôle trop élevé).",
                    ephemeral=True
                )
                return

            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    "❌ Je ne peux pas expulser cette personne (rôle trop élevé).",
                    ephemeral=True
                )
                return

            dm_embed = discord.Embed(
                title="Vous avez été expulsé",
                description=f"Vous avez été expulsé de {interaction.guild.name}",
                color=discord.Color.red()
            )
            if reason:
                dm_embed.add_field(name="Raison", value=reason, inline=False)
            
            try:
                await member.send(embed=dm_embed)
            except:
                pass

            await member.kick(reason=reason)

            embed = discord.Embed(
                title="Membre expulsé",
                description=f"{member.mention} a été expulsé du serveur.",
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name="Raison", value=reason, inline=False)
            embed.set_footer(text=f"Expulsé par {interaction.user.name}")

            await interaction.response.send_message(embed=embed)
            logging.info(f"{member} kicked by {interaction.user} - Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {str(e)}", ephemeral=True)
            logging.error(f"Erreur lors du kick : {str(e)}")

    @app_commands.command(name="ban", description="Bannit un utilisateur du serveur")
    @app_commands.describe(
        member="Le membre à bannir",
        reason="Raison du bannissement (optionnel)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            if member.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "❌ Vous ne pouvez pas bannir cette personne (rôle trop élevé).",
                    ephemeral=True
                )
                return

            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    "❌ Je ne peux pas bannir cette personne (rôle trop élevé).",
                    ephemeral=True
                )
                return

            dm_embed = discord.Embed(
                title="Vous avez été banni",
                description=f"Vous avez été banni de {interaction.guild.name}",
                color=discord.Color.red()
            )
            if reason:
                dm_embed.add_field(name="Raison", value=reason, inline=False)
            
            try:
                await member.send(embed=dm_embed)
            except:
                pass

            await member.ban(reason=reason)

            embed = discord.Embed(
                title="Membre banni",
                description=f"{member.mention} a été banni du serveur.",
                color=discord.Color.red()
            )
            if reason:
                embed.add_field(name="Raison", value=reason, inline=False)
            embed.set_footer(text=f"Banni par {interaction.user.name}")

            await interaction.response.send_message(embed=embed)
            logging.info(f"{member} banned by {interaction.user} - Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {str(e)}", ephemeral=True)
            logging.error(f"Erreur lors du ban : {str(e)}")

    @app_commands.command(name="unban", description="Débannit un utilisateur du serveur")
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
                title="Utilisateur débanni",
                description=f"{user.mention} ({user.name}) a été débanni du serveur.",
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name="Raison", value=reason, inline=False)
            embed.set_footer(text=f"Débanni par {interaction.user.name}")

            await interaction.response.send_message(embed=embed)
            logging.info(f"{user} unbanned by {interaction.user} - Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {str(e)}", ephemeral=True)
            logging.error(f"Erreur lors du unban : {str(e)}")

    @app_commands.command(name="mute", description="Applique un timeout à un utilisateur")
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
                    "❌ La durée maximale du timeout est de 40320 minutes (28 jours).",
                    ephemeral=True
                )
                return

            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    "❌ Je ne peux pas timeout cette personne (rôle trop élevé).",
                    ephemeral=True
                )
                return

            timeout_duration = timedelta(minutes=duration)
            await member.timeout(timeout_duration, reason=reason)

            embed = discord.Embed(
                title="Timeout appliqué",
                description=f"{member.mention} a reçu un timeout.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Durée", value=f"{duration} minutes", inline=False)
            if reason:
                embed.add_field(name="Raison", value=reason, inline=False)
            embed.set_footer(text=f"Timeout par {interaction.user.name}")

            await interaction.response.send_message(embed=embed)
            logging.info(f"{member} timed out by {interaction.user} for {duration} minutes - Reason: {reason}")

        except discord.Forbidden:
            await interaction.response.send_message("❌ Je n'ai pas les permissions nécessaires pour timeout ce membre.", ephemeral=True)
            logging.error("Permission manquante pour timeout")
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {str(e)}", ephemeral=True)
            logging.error(f"Erreur lors du timeout : {str(e)}")

    @app_commands.command(name="unmute", description="Retire le timeout d'un utilisateur")
    @app_commands.describe(
        member="Le membre dont retirer le timeout",
        reason="Raison du retrait du timeout (optionnel)"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        try:
            await member.timeout(None, reason=reason)

            embed = discord.Embed(
                title="Timeout retiré",
                description=f"{member.mention} a maintenant la parole.",
                color=discord.Color.green()
            )
            if reason:
                embed.add_field(name="Raison", value=reason, inline=False)
            embed.set_footer(text=f"Timeout retiré par {interaction.user.name}")

            await interaction.response.send_message(embed=embed)
            logging.info(f"{member} timeout removed by {interaction.user} - Reason: {reason}")

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {str(e)}", ephemeral=True)
            logging.error(f"Erreur lors du retrait du timeout : {str(e)}")

    @app_commands.command(name="purge", description="Supprime un nombre de messages")
    @app_commands.describe(
        amount="Le nombre de messages à supprimer (max 100)",
        user="Filtrer par utilisateur (optionnel)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int, user: discord.Member = None):
        try:
            if amount > 100:
                await interaction.response.send_message(
                    "❌ Vous ne pouvez pas supprimer plus de 100 messages.",
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
                title="Messages supprimés",
                description=f"{len(deleted)} message(s) supprimé(s).",
                color=discord.Color.green()
            )
            if user:
                embed.add_field(name="Utilisateur", value=user.mention, inline=False)
            embed.set_footer(text=f"Purgé par {interaction.user.name}")

            await interaction.followup.send(embed=embed, ephemeral=True)
            logging.info(f"{len(deleted)} messages purged by {interaction.user} - User filter: {user}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Je n'ai pas les permissions nécessaires.", ephemeral=True)
            logging.error("Permission manquante pour purge")
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Erreur : {str(e)}", ephemeral=True)
            except:
                pass
            logging.error(f"Erreur lors de la purge : {str(e)}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModerationCog(bot))
