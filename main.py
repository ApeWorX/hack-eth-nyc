import os
import time
from http import client
from typing import Any

import ape
import discord
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from logger import logger

load_dotenv()
TOKEN = os.getenv("TOKEN")
APE_GUILD = os.getenv("APE_GUILD")
ETH_GUILD = os.getenv("ETH_GUILD")
CAO_GUILD = os.getenv("CAO_GUILD")

SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
client = discord.Client()
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)


@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class Faucet(Base):
    __tablename__ = "faucet_table"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String, index=True)
    discord_name = Column(String, index=True)
    time = Column(Integer, index=True)


Base.metadata.create_all(bind=engine)


@client.event
async def on_ready():
    logger.info("We have logged in as {0.user}".format(client))

    guild = discord.utils.get(client.guilds, name=APE_GUILD)
    logger.info(
        f"{client.user} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})"
    )


def list_gen(guild):
    name_list = []
    for channel in guild:
        name_list.append(channel.name)
    return name_list


def get_faucets():
    with Session(engine) as session:
        breakpoint()
        return pd.read_sql(session.query(Faucet).statement, session.connection())


async def faucet(message):
    payload = message.content
    wallet_address = payload.split(" ")[1]
    discord_name = message.author.name
    date_time = time.time()
    db_obj = Faucet(
        wallet_address=wallet_address, discord_name=discord_name, time=date_time
    )
    with Session(engine) as session:
        session.add(db_obj)
        session.commit()
    return get_faucets()


async def echo(message, eth_guild, ape_guild):
    # send msg to APE from origin
    if message.guild.name == CAO_GUILD:
        name_list = list_gen(ape_guild.text_channels)
        new_message = (
            f"**Server** {message.guild} **Channel** {message.channel.name} "
            f"**Author** {message.author.display_name}\n " + message.content
        )
        index_of_name_list = name_list.index("testing")

        try:
            await ape_guild.text_channels[index_of_name_list].send(new_message)
            await message.channel.send("Your bug has been sent to ApeWorx/Bug Channel")
        except Exception as err:
            logger.error(err)

    # send msg from ape to origin
    if message.guild.name == APE_GUILD:
        new_message = (
            f"**Server** {message.guild} **Channel** {message.channel.name} "
            f"**Author** {message.author.display_name}\n " + message.content
        )
        name_list = list_gen(ape_guild.text_channels)

        index_of_name_list = name_list.index("general")
        try:
            await ape_guild.text_channels[index_of_name_list].send(new_message)
            await message.channel.send("Your bug has been sent to ApeWorx/Bug Channel")
            logger.info(new_message)
        except Exception as err:
            logger.error(err)

    if message.guild.name == ETH_GUILD:
        new_message = (
            f"**Server** {message.guild} **Channel** {message.channel.name} "
            f"**Author** {message.author.display_name}\n " + message.content
        )
        name_list = list_gen(ape_guild.text_channels)
        if message.content.startswith("$bug"):
            index_of_name_list = name_list.index("🐞-bugs")
            try:
                await ape_guild.text_channels[index_of_name_list].send(new_message)
                await message.channel.send(
                    "Your message has been echoed to Apeworx/🐞-bugs"
                )
                logger.info(new_message)
            except Exception as err:
                logger.error(err)
        else:
            index_of_name_list = name_list.index("🗣-general")
            try:
                await ape_guild.text_channels[index_of_name_list].send(new_message)
                await message.channel.send(
                    "Your message has been echoed to Apeworx/🗣-general"
                )
                logger.info(new_message)
            except Exception as err:
                logger.error(err)


@client.event
async def on_message(message):
    eth_guild = discord.utils.get(client.guilds, name=ETH_GUILD)
    ape_guild = discord.utils.get(client.guilds, name=APE_GUILD)
    if message.author == client.user:
        return

    try:
        # echos a bug to the targeted channel
        if message.content.startswith("$bug"):
            await echo(message, eth_guild, ape_guild)
            logger.info(message)
        # send testnet eth to user
        elif message.content.startswith("$faucet"):
            await faucet(message)
        # says hello to the user
        elif message.content.startswith("$hello"):
            await message.channel.send("Hello")
        elif message.guild.name == ETH_GUILD and not message.content.startswith("$bug"):
            await echo(message, eth_guild, ape_guild)
            logger.info(message)
    except Exception as err:
        logger.error(err)


client.run(TOKEN)
