import logging
import os
from dotenv import load_dotenv
from config import Config

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
    await load_features()
    
    guild = discord.Object(id=Config.ServerID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    logging.info("Commandes sync pour la guild %s", Config.ServerID)
    logging.info("Connecté en tant que %s", bot.user)
    servercount = len(bot.guilds)
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.playing, name=f"Présent sur {servercount} serveurs"))

# LOAD FEATURES FUNCTION
async def load_features():
    features = ["features.Log", "features.JoinLeave", "features.Moderation", "features.Giveaway", "features.Tickets"]
    for feature in features:
        try:
            await bot.load_extension(feature)
            logging.info(f"Feature {feature.split('.')[-1]} chargée")
        except Exception as e:
            logging.error(f"Erreur lors du chargement de la Feature {feature.split('.')[-1]} : {str(e)}")

# RUN THE BOT
if __name__ == "__main__":
    if not os.getenv("DISCORD_TOKEN"):
        raise RuntimeError("DISCORD_TOKEN manquant dans les variables d'environnement")
    bot.run(os.getenv("DISCORD_TOKEN"))