import logging
import os
from dotenv import load_dotenv
from config import Config

import discord
from discord.ext import commands
from modules.I18n import load_locale, t

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
    active_locale = load_locale(Config.Language)
    await load_features()
    
    guild = discord.Object(id=Config.ServerID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    logging.info("Commandes sync pour la guild %s", Config.ServerID)
    logging.info("Connecté en tant que %s", bot.user)
    logging.info("Locale chargée: %s", active_locale)
    servercount = len(bot.guilds)

    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd,
        "invisible": discord.Status.invisible,
    }
    activity_type_map = {
        "playing": discord.ActivityType.playing,
        "streaming": discord.ActivityType.streaming,
        "listening": discord.ActivityType.listening,
        "watching": discord.ActivityType.watching,
    }

    configured_status = str(getattr(Config, "StatusType", "online")).lower()
    configured_activity_type = str(getattr(Config, "StatusActivityType", "playing")).lower()
    configured_activity_text = getattr(Config, "StatusActivityText", "")

    if configured_status not in status_map:
        logging.warning("StatusType invalide (%s), fallback sur online", configured_status)
    if configured_activity_type not in activity_type_map:
        logging.warning("StatusActivityType invalide (%s), fallback sur playing", configured_activity_type)

    status = status_map.get(configured_status, discord.Status.online)
    activity_type = activity_type_map.get(configured_activity_type, discord.ActivityType.playing)

    default_text = t("app.presence_playing", "Présent sur {servercount} serveurs", servercount=servercount)
    raw_text = configured_activity_text or default_text
    try:
        activity_text = str(raw_text).format(servercount=servercount)
    except Exception:
        activity_text = str(raw_text)

    await bot.change_presence(
        status=status,
        activity=discord.Activity(type=activity_type, name=activity_text),
    )

# LOAD FEATURES FUNCTION
async def load_features():
    features = ["features.Log", "features.JoinLeave", "features.Moderation", "features.Giveaway", "features.Tickets", "features.Patchnote"]
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