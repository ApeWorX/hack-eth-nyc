from http import client

import discord
import os
from logger import logger

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
APE_GUILD = os.getenv('APE_GUILD')
ETH_GUILD = os.getenv('ETH_GUILD')
CAO_GUILD = os.getenv('CAO_GUILD')

client = discord.Client()

@client.event
async def on_ready():
    logger.info('We have logged in as {0.user}'
    .format(client))

    guild = discord.utils.get(client.guilds, name=APE_GUILD)
    logger.info(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

def list_gen(guild):
    name_list = []
    for channel in guild:
        name_list.append(channel.name)
    return name_list


async def echo(message, ape_guild, listening_guild):
    # send msg to APE from origin
    if message.guild.name == CAO_GUILD:
        name_list = list_gen(ape_guild.text_channels)
        new_message = f"**Server** {message.guild} **Channel** {message.channel.name} " \
                      f"**Author** {message.author.display_name}\n " + message.content
        index_of_name_list = name_list.index('testing')

        try:
            await ape_guild.text_channels[index_of_name_list].send(new_message)
            await message.channel.send('Your bug has been sent to ApeWorx/Bug Channel')
        except Exception as err:
            logger.error(err)

    # send msg from ape to origin
    if message.guild.name == APE_GUILD:
        new_message = f"**Server** {message.guild} **Channel** {message.channel.name} " \
                      f"**Author** {message.author.display_name}\n " + message.content
        name_list = list_gen(listening_guild.text_channels)
        index_of_name_list = name_list.index('general')
        try:
            await listening_guild.text_channels[index_of_name_list].send(new_message)
            await message.channel.send('Your bug has been sent to ApeWorx/Bug Channel')
            logger.info(new_message)
        except Exception as err:
            logger.error(err)

@client.event
async def on_message(message):
    ape_guild = discord.utils.get(client.guilds, name=APE_GUILD)
    listening_guild = discord.utils.get(client.guilds, name=CAO_GUILD)
    if message.author == client.user:
        return
    # echos a bug to the targeted channel
    if message.content.startswith('$bug'):
        try:
            await echo(message, ape_guild, listening_guild)
            logger.info(message)
        except Exception as err:
            logger.error(err)

    # says hello to the user
    if message.content.startswith('$hello'):
        try:
            await message.channel.send('Hello')
        except Exception as err:
            logger.error(err)


client.run(TOKEN)
