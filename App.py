import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from modules import Functions, Queries as fn, db

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

async def on_ready():
    await tree.sync()
    print(f'Logged in as {client.user}')

client.run()