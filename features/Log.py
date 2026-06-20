import discord
from discord import app_commands
from discord.ext import commands
import logging
from config import Config
from datetime import datetime

class LogCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_main_guild(self, guild: discord.Guild | None) -> bool:
        return guild is not None and guild.id == Config.ServerID

    def get_log_channel(self, log_type: str) -> int | None:
        if Config.LogsEnabled:
            return Config.LogsChannel
        return None

    async def send_log(self, log_type: str, embed: discord.Embed):
        channel_id = self.get_log_channel(log_type)
        if channel_id:
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi du log {log_type}: {str(e)}")

    # MESSAGES LOGS

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not self._is_main_guild(message.guild):
            return

        if message.author.bot:
            return

        embed = discord.Embed(
            title="📛 Message supprimé",
            description=f"**Auteur:** {message.author.mention}\n**Canal:** {message.channel.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Contenu", value=message.content[:1024] if message.content else "*(aucun contenu)*", inline=False)
        embed.add_field(name="ID du message", value=message.id, inline=True)
        embed.set_footer(text=f"ID utilisateur: {message.author.id}")

        await self.send_log("message_delete", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not self._is_main_guild(after.guild):
            return

        if after.author.bot:
            return

        if before.content == after.content:
            return

        embed = discord.Embed(
            title="✏️ Message édité",
            description=f"**Auteur:** {after.author.mention}\n**Canal:** {after.channel.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Avant", value=before.content[:1024] if before.content else "*(aucun contenu)*", inline=False)
        embed.add_field(name="Après", value=after.content[:1024] if after.content else "*(aucun contenu)*", inline=False)
        embed.add_field(name="ID du message", value=before.id, inline=True)
        embed.set_footer(text=f"ID utilisateur: {after.author.id}")

        await self.send_log("message_edit", embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        if not messages or not self._is_main_guild(messages[0].guild):
            return

        embed = discord.Embed(
            title="🗑️ Messages supprimés en masse",
            description=f"**Canal:** {messages[0].channel.mention if messages else 'Inconnu'}",
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Nombre de messages", value=len(messages), inline=True)
        
        await self.send_log("message_bulk_delete", embed)

    # VOICE LOGS

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if not self._is_main_guild(member.guild):
            return

        if member.bot:
            return

        # Rejoindre un canal vocal
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🎤 Utilisateur connecté au vocal",
                description=f"**Utilisateur:** {member.mention}\n**Canal:** {after.channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"ID utilisateur: {member.id}")
            await self.send_log("voice_join", embed)

        # Quitter un canal vocal
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="🎤 Utilisateur déconnecté du vocal",
                description=f"**Utilisateur:** {member.mention}\n**Canal:** {before.channel.mention}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"ID utilisateur: {member.id}")
            await self.send_log("voice_leave", embed)

        # Se déplacer entre canaux
        elif before.channel != after.channel:
            embed = discord.Embed(
                title="🎤 Utilisateur déplacé",
                description=f"**Utilisateur:** {member.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="De", value=before.channel.mention, inline=True)
            embed.add_field(name="Vers", value=after.channel.mention, inline=True)
            embed.set_footer(text=f"ID utilisateur: {member.id}")
            await self.send_log("voice_move", embed)

        # Mute/Unmute
        if before.self_mute != after.self_mute:
            action = "🔇 Utilisateur mute" if after.self_mute else "🔊 Utilisateur unmute"
            embed = discord.Embed(
                title=action,
                description=f"**Utilisateur:** {member.mention}\n**Canal:** {after.channel.mention if after.channel else 'N/A'}",
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"ID utilisateur: {member.id}")
            await self.send_log("voice_mute", embed)

        # Deafen/Undeafen
        if before.self_deaf != after.self_deaf:
            action = "🔇 Utilisateur sourdine" if after.self_deaf else "🔊 Utilisateur entendu"
            embed = discord.Embed(
                title=action,
                description=f"**Utilisateur:** {member.mention}\n**Canal:** {after.channel.mention if after.channel else 'N/A'}",
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"ID utilisateur: {member.id}")
            await self.send_log("voice_deafen", embed)

    # CHANNEL LOGS

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if not self._is_main_guild(channel.guild):
            return

        embed = discord.Embed(
            title="➕ Canal créé",
            description=f"**Canal:** {channel.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Type", value=channel.type.name, inline=True)
        embed.add_field(name="ID", value=channel.id, inline=True)
        embed.set_footer(text=f"ID canal: {channel.id}")
        
        await self.send_log("channel_create", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if not self._is_main_guild(channel.guild):
            return

        embed = discord.Embed(
            title="➖ Canal supprimé",
            description=f"**Canal:** {channel.name}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Type", value=channel.type.name, inline=True)
        embed.add_field(name="ID", value=channel.id, inline=True)
        embed.set_footer(text=f"ID canal: {channel.id}")
        
        await self.send_log("channel_delete", embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        if not self._is_main_guild(after.guild):
            return

        changes = []

        if before.name != after.name:
            changes.append(f"**Nom:** {before.name} → {after.name}")
        
        if isinstance(before, (discord.TextChannel, discord.VoiceChannel)):
            if before.topic != after.topic:
                changes.append(f"**Sujet:** {before.topic or 'aucun'} → {after.topic or 'aucun'}")
            if before.nsfw != after.nsfw:
                changes.append(f"**NSFW:** {before.nsfw} → {after.nsfw}")

        if not changes:
            return

        embed = discord.Embed(
            title="✏️ Canal modifié",
            description=f"**Canal:** {after.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        for change in changes:
            embed.add_field(name="Changement", value=change, inline=False)
        embed.set_footer(text=f"ID canal: {after.id}")
        
        await self.send_log("channel_update", embed)

    # ROLES LOGS

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        if not self._is_main_guild(role.guild):
            return

        embed = discord.Embed(
            title="➕ Rôle créé",
            description=f"**Rôle:** {role.mention}",
            color=role.color,
            timestamp=datetime.now()
        )
        embed.add_field(name="Couleur", value=str(role.color), inline=True)
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.set_footer(text=f"ID rôle: {role.id}")
        
        await self.send_log("role_create", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        if not self._is_main_guild(role.guild):
            return

        embed = discord.Embed(
            title="➖ Rôle supprimé",
            description=f"**Rôle:** {role.name}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Couleur", value=str(role.color), inline=True)
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.set_footer(text=f"ID rôle: {role.id}")
        
        await self.send_log("role_delete", embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        if not self._is_main_guild(after.guild):
            return

        changes = []

        if before.name != after.name:
            changes.append(f"**Nom:** {before.name} → {after.name}")
        if before.color != after.color:
            changes.append(f"**Couleur:** {before.color} → {after.color}")
        if before.permissions != after.permissions:
            changes.append(f"**Permissions:** Modifiées")
        if before.mentionable != after.mentionable:
            changes.append(f"**Mentionnable:** {before.mentionable} → {after.mentionable}")

        if not changes:
            return

        embed = discord.Embed(
            title="✏️ Rôle modifié",
            description=f"**Rôle:** {after.mention}",
            color=after.color,
            timestamp=datetime.now()
        )
        for change in changes:
            embed.add_field(name="Changement", value=change, inline=False)
        embed.set_footer(text=f"ID rôle: {after.id}")
        
        await self.send_log("role_update", embed)

    # MEMBERS LOGS

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if not self._is_main_guild(after.guild):
            return

        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Surnom modifié",
                description=f"**Utilisateur:** {after.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Avant", value=before.nick or "Aucun", inline=True)
            embed.add_field(name="Après", value=after.nick or "Aucun", inline=True)
            embed.set_footer(text=f"ID utilisateur: {after.id}")
            await self.send_log("member_nickname_change", embed)

        if before.roles != after.roles:
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)
            
            description = f"**Utilisateur:** {after.mention}\n"
            
            if added_roles:
                description += f"**Rôles ajoutés:** {', '.join([r.mention for r in added_roles])}\n"
            if removed_roles:
                description += f"**Rôles supprimés:** {', '.join([r.mention for r in removed_roles])}"
            
            embed = discord.Embed(
                title="👥 Rôles modifiés",
                description=description,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"ID utilisateur: {after.id}")
            await self.send_log("member_role_update", embed)

    # MODERATION LOGS

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        if not self._is_main_guild(guild):
            return

        embed = discord.Embed(
            title="🔨 Utilisateur banni",
            description=f"**Utilisateur:** {user.mention}",
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Nom", value=str(user), inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.set_footer(text=f"ID utilisateur: {user.id}")
        
        await self.send_log("member_ban", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        if not self._is_main_guild(guild):
            return

        embed = discord.Embed(
            title="🔓 Utilisateur débanni",
            description=f"**Utilisateur:** {user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Nom", value=str(user), inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.set_footer(text=f"ID utilisateur: {user.id}")
        
        await self.send_log("member_unban", embed)

    # INVITATIONS LOGS

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if not self._is_main_guild(invite.guild):
            return

        embed = discord.Embed(
            title="🔗 Invitation créée",
            description=f"**Canal:** {invite.channel.mention if invite.channel else 'Inconnu'}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Code", value=invite.code, inline=True)
        embed.add_field(name="Créateur", value=invite.inviter.mention if invite.inviter else "Inconnu", inline=True)
        embed.add_field(name="Utilisations", value=f"{invite.uses}/{invite.max_uses if invite.max_uses else '∞'}", inline=True)
        embed.set_footer(text=f"Code: {invite.code}")
        
        await self.send_log("invite_create", embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if not self._is_main_guild(invite.guild):
            return

        embed = discord.Embed(
            title="🔗 Invitation supprimée",
            description=f"**Canal:** {invite.channel.mention if invite.channel else 'Inconnu'}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Code", value=invite.code, inline=True)
        embed.add_field(name="Créateur", value=invite.inviter.mention if invite.inviter else "Inconnu", inline=True)
        embed.set_footer(text=f"Code: {invite.code}")
        
        await self.send_log("invite_delete", embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(LogCog(bot))

    