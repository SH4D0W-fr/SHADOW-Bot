import logging
import os
from dotenv import load_dotenv
from config import Config
from features.JoinLeave import send_card


import discord
from discord.ext import commands

# LOAD ENV VARIABLES
load_dotenv()

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# BOT SETUP
intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# STARTUP EVENT
@bot.event
async def on_ready():
    guild = discord.Object(id=Config.ServerID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    logging.info("Commandes sync pour la guild %s", Config.ServerID)
    logging.info("Connecté en tant que %s", bot.user)

# JOIN/LEAVE EVENTS
@bot.event
async def on_member_join(member: discord.Member):
    await send_card(bot, member, Config.WelcomeChannelID, "Bienvenue", join=True)

@bot.event
async def on_member_remove(member: discord.Member):
    await send_card(bot, member, Config.GoodbyeChannelID, "À bientôt", join=False)

# RUN THE BOT
if __name__ == "__main__":
    if not os.getenv("DISCORD_TOKEN"):
        raise RuntimeError("DISCORD_TOKEN manquant dans les variables d'environnement")
    bot.run(os.getenv("DISCORD_TOKEN"))