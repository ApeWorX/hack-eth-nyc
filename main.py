import os
import time
from http import client
from typing import Any

import discord
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from logger import logger
from ape import accounts

load_dotenv()
TOKEN = os.getenv("TOKEN")
APE_GUILD = os.getenv("APE_GUILD")
ETH_GUILD = os.getenv("ETH_GUILD")
CAO_GUILD = os.getenv("CAO_GUILD")
TEST_ACCOUNT = accounts.test_accounts[0]
TEST_ACCOUNT_1 = accounts.test_accounts[1]

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
    discord_id = Column(Integer, index=True)
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
        return pd.read_sql(session.query(Faucet).statement, session.connection())


async def faucet(message):
    payload = message.content
    wallet_address = payload.split(" ")[1]
    discord_id = message.author.id
    date_time = time.time()
    db_obj = Faucet(
        wallet_address=wallet_address, discord_id=discord_id, time=date_time
    )
    with Session(engine) as db:
        wallet_obj = db.query(Faucet).filter(Faucet.wallet_address == wallet_address).first()
        if not wallet_obj:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
    # TODO: if they do not exist in the database, send to wallet anyway
    # TODO: send_to_wallet needs to be fixed here
    send_to_wallet(db_obj.wallet_address)
    return get_faucets()

def get_wallet_address(wallet_address):
    # TODO: refactor to same function
    with Session(engine) as db:
        query_wallet = db.query(Faucet).filter(Faucet.wallet_address == wallet_address).first()
        check_available = check_available_to_send(query_wallet)
    if check_available:
        return query_wallet.wallet_address
    return None


def get_user(discord_id):
    # TODO: refactor to same function
    with Session(engine) as db:
        query_user = db.query(Faucet).filter(Faucet.discord_id == discord_id).first()
        check_available = check_available_to_send(query_user)
    if check_available:
        return query_user.discord_id
    return None


def check_available_to_send(query):
    time_now = time.time()
    last_funded_time = query.time
    if time_now > last_funded_time + 86400:
        return True
    return False
   
async def send_to_wallet(wallet_address, discord_id):
    wallet_address = get_wallet_address(wallet_address)
    discord_id = get_user(discord_id)
    if not wallet_address or not discord_id:
        await message.channel.send("You need to wait 24 hours from your last request")
        #todo: tell user how much time they have to wait more
    elif not TEST_ACCOUNT.balance >= 100:
        await message.channel.send("Not enough ETH in faucet")
    elif wallet_address and discord_id:
        accounts.transfer(TEST_ACCOUNT, wallet_address, 100)
        with Session(engine) as db:
            query = db.query(Faucet).filter(Faucet.wallet_address == wallet_address).all()
            for q in query:
                q.time = time.time()
                db.add(q)
                db.commit()
    else:
        await message.channel.send("contact an ape representative, there has been an issue")
        

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
        # echos a bug to the targeted channel
        try:
            if message.content.startswith("$bug"):
                await echo(message, eth_guild, ape_guild)
                logger.info(message)
            # send testnet eth to user
            elif message.content.startswith("$faucet"):
                await faucet(message)
            # says hello to the user
            elif message.content.startswith("$hello"):
                await message.channel.send("Hello")
            elif message.guild.name == ETH_GUILD and not message.content.startswith(
                "$bug"
            ):
                await echo(message, eth_guild, ape_guild)
                logger.info(message)
        except Exception as err:
            logger.error(err)


def get_gas():
    pass


client.run(TOKEN)
