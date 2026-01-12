from discord import *
import asyncio

async def SendMessage(message=str):
    await message.channel.send(message)
    return

async def DeleteMessage(message=Message):
    await message.delete()
    return

async def EditMessage(message=Message, new_content=str):
    await message.edit(content=new_content)
    return

async def ReactToMessage(message=Message, emoji=str):
    await message.add_reaction(emoji)
    return

async def ClearReactions(message=Message):
    await message.clear_reactions()
    return

async def PinMessage(message=Message):
    await message.pin()
    return

async def UnpinMessage(message=Message):
    await message.unpin()
    return

async def FetchMessage(channel=TextChannel, message_id=int):
    message = await channel.fetch_message(message_id)
    return message

async def BulkDeleteMessages(channel=TextChannel, limit=int):
    deleted = await channel.purge(limit=limit)
    return deleted

async def SendEmbedMessage(channel=TextChannel, title=str, description=str, color=int):
    embed = Embed(title=title, description=description, color=color)
    await channel.send(embed=embed)
    return

async def SendDM(user=User, content=str):
    dm_channel = await user.create_dm()
    await dm_channel.send(content)
    return