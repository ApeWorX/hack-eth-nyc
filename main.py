import os
import time
from http import client
from typing import Any

import discord
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session
from sqlalchemy import or_

from logger import logger
from ape import accounts, networks

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


class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(
        String,
        ForeignKey(
            "faucet_table.wallet_address",
            ondelete="CASCADE"
        ),
        index=True)
    discord_id = Column(
        Integer,
        ForeignKey(
            "faucet_table.discord_id",
            ondelete="CASCADE"
        ),
        index=True
    )
    time = Column(Integer, index=True)
    amount = Column(Integer, index=True)
    faucet_balance = Column(Integer, index=True)
    receiver_balance = Column(Integer, index=True)
    eth_network = Column(Integer, index=True)


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
    db_obj = Faucet(
        wallet_address=wallet_address, 
        discord_id=discord_id, 
        time=0
    )
    with Session(engine) as db:
        wallet_obj = db.query(
            Faucet).filter(
            or_(
                Faucet.wallet_address == wallet_address,
                Faucet.discord_id == discord_id
            )).first()
        if not wallet_obj:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
    msg = send_to_wallet(db_obj.wallet_address, int(db_obj.discord_id))
    await(send_message(message, msg))
    return get_faucets()


def get_wallet_address(wallet_identifier):
    with Session(engine) as db:
        if isinstance(wallet_identifier, str):
            query_wallet = db.query(
                Faucet).filter(
                Faucet.wallet_address == wallet_identifier).first()
        elif isinstance(wallet_identifier, int):
            query_wallet = db.query(
                Faucet).filter(
                Faucet.discord_id == wallet_identifier).first()
    check_available = check_available_to_send(query_wallet)
    if check_available and isinstance(wallet_identifier, str):
        return query_wallet.wallet_address
    elif check_available and isinstance(wallet_identifier, int):
        return query_wallet.discord_id
    return None


def check_available_to_send(query):
    time_now = time.time()
    last_funded_time = query.time
    if time_now > last_funded_time + 86400:
        return True
    return False


def send_to_wallet(_wallet_address, _discord_id):
    wallet_address = get_wallet_address(_wallet_address)
    discord_id = get_wallet_address(_discord_id)
    with networks.get_ecosystem("ethereum").local.use_default_provider() as provider:
        TEST_ACCOUNT.transfer(wallet_address, TEST_ACCOUNT.balance - 10**15)
        if not wallet_address or not discord_id:
            message = "You need to wait 24 hours from your last request"
        elif not TEST_ACCOUNT.balance >= 100:
            message = "Not enough ETH in faucet"
        elif wallet_address and discord_id:
            amount = 100
            txn = TEST_ACCOUNT.transfer(wallet_address, amount)
            logger.info(f"{TEST_ACCOUNT.balance}: moved 100 wei to {wallet_address}")
            update_db_obj(wallet_address, discord_id)
            update_transactions_table(txn)
            message = "eth sent"
        else:
            message = "contact an ape representative, there has been an issue"
    return message


@client.event
async def send_message(message, msg):
    await message.channel.send(msg)


def update_db_obj(wallet_address, discord_id):
    with Session(engine) as db:
        query = db.query(Faucet).filter(Faucet.wallet_address == wallet_address).all()
        for q in query:
            q.time = time.time()
            db.add(q)
            db.commit()
        query2 = db.query(Faucet).filter(Faucet.discord_id == discord_id).all()
        for q in query2:
            q.time = time.time()
            db.add(q)
            db.commit()


def update_transactions_table(txn):
    with Session(engine) as db:
        pass


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
