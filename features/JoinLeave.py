import logging
import discord
from discord.ext import commands
from config import Config
from modules.Image import render_card


class JoinLeaveCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def build_embed(self, member: discord.Member, title: str, join: bool):
        image = await render_card(member, title, join)
        filename = "welcome.png" if join else "goodbye.png"
        file = discord.File(fp=image, filename=filename)

        description = (
            Config.WelcomeMessage.format(member=member.mention)
            if join
            else Config.GoodbyeMessage.format(member=member.mention)
        )

        color = discord.Color.green() if join else discord.Color.red()
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_image(url=f"attachment://{filename}")
        embed.set_footer(text=f"Total membres : {member.guild.member_count}")
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
        await self.send_card(member, Config.WelcomeChannelID, "Bienvenue", join=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.send_card(member, Config.GoodbyeChannelID, "À bientôt", join=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinLeaveCog(bot))