import logging
import discord
from discord.ext import commands
from config import Config
from modules.Image import render_card
from modules.I18n import t


class JoinLeaveCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_main_guild(self, guild: discord.Guild | None) -> bool:
        return guild is not None and guild.id == Config.ServerID

    async def assign_join_roles(self, member: discord.Member):
        role_ids = getattr(Config, "JoinRoles", []) or []
        if not role_ids:
            return

        roles_to_add = []
        for role_id in role_ids:
            role = member.guild.get_role(role_id)
            if role is None:
                logging.warning("Rôle d'arrivée introuvable: %s", role_id)
                continue

            if role >= member.guild.me.top_role:
                logging.warning("Rôle d'arrivée %s ignoré: au-dessus du rôle du bot", role.name)
                continue

            roles_to_add.append(role)

        if not roles_to_add:
            return

        try:
            await member.add_roles(*roles_to_add, reason="Attribution automatique des rôles à l'arrivée")
            logging.info("Rôles d'arrivée attribués à %s: %s", member, ", ".join(role.name for role in roles_to_add))
        except discord.Forbidden:
            logging.warning("Permissions insuffisantes pour attribuer les rôles d'arrivée à %s", member)
        except Exception as e:
            logging.error("Erreur attribution rôles d'arrivée à %s: %s", member, str(e))

    async def build_embed(self, member: discord.Member, title: str, join: bool):
        image = await render_card(member, title, join)
        filename = "welcome.png" if join else "goodbye.png"
        file = discord.File(fp=image, filename=filename)

        description = (
            t("config.welcome_message", Config.WelcomeMessage, member=member.mention)
            if join
            else t("config.goodbye_message", Config.GoodbyeMessage, member=member.mention)
        )

        color = discord.Color.green() if join else discord.Color.red()
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_image(url=f"attachment://{filename}")
        embed.set_footer(
            text=t(
                "join_leave.total_members_footer",
                "Total membres : {member_count}",
                member_count=member.guild.member_count,
            )
        )
        return file, embed

    async def send_card(self, member: discord.Member, channel_id: int, title: str, join: bool):
        if channel_id <= 0:
            logging.warning("Le channel ID pour %s n'est pas défini.", title)
            return

        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
        if channel is None:
            logging.error("Impossible de trouver le salon %s", channel_id)
            return

        file, embed = await self.build_embed(member, title, join)
        await channel.send(file=file, embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self._is_main_guild(member.guild):
            return
        await self.assign_join_roles(member)
        await self.send_card(
            member,
            Config.WelcomeChannelID,
            t("join_leave.welcome_title", "Bienvenue"),
            join=True,
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not self._is_main_guild(member.guild):
            return
        await self.send_card(
            member,
            Config.GoodbyeChannelID,
            t("join_leave.goodbye_title", "À bientôt"),
            join=False,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinLeaveCog(bot))