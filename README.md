# Discord Faucet Bot feat Gas Price

Made by Christopher Cao, Blake Johnson, Matt Nakamatami, Dalena Dang 

## Goal

In this project we decided to make a bot that can help on board a user to get testnet eth to interact with Ethereum Networks. 

**Intermediate users** will find the bot useful to be efficent with gas fees

**Contributing users** will find it helpful to create github issues with automation

**General Degenerates** will be able to talk across multiple servers with the echo method.



# Roadmap

**We decided to attack this project in 4 phases:**
1. Discord Keyword Recognition
2. Payload injection to a sql db
3. Transfer funds to user input wallet
4. Extra features:
  * Gas Price
  * Low and High Score tracking based on time
  * Automate deployment based on Low score and time
  * Automate calls based on Low score and time


We decided to break the project down into 4 parts because we have 4 developers and we wanted let everyone shine in their strengths and bring a collaboration of minds together. 


### Discord Keyword Recognition

Discord bots recognize and listen to keywords based on parameters that are provided
Guild name
Channel Name
Message content

Ape Bot listens to general chat and looks for:
$bug
$faucet
$hello (test if it is alive)

#### echo internal method
Echo will listen to other server and with specfication of channels. It will echo the message to and from different servers can see messages. 
* Feature improvement: allow direct replies to the messages from another channel
* use case: allow moderators to reply to messages faster to other less popular servers.

#### $bug
$bug will echo a message from the general chat to bugs channel so you can keep track of issues
* Feature improvement: add github actions to automate issue creation of issue
* Feature Improvement: add email tracking to approve issues to create in github

#### $faucet
$faucet will prompt the user for a wallet address to send testnet eth so they interact with Ethereum. The bot is connected to a sql db so it can keep track of the discord user id, time they asked for eth, and wallet address. So we can control the amount of testnet eth provided. 
* Feature improvement: verify address
* Feature improvement: specify testnet
* Feature improvement: check for balance and decline balances over X amount

#### $gas
$gas will check the prices of the gas and relay the information to the user. More importantly it will allow users to automate deployment of contracts, calls, transfers anything that requires eth at the LOWEST gas. 


* Prints gas price
* Feature improvement: Parameters can be set to find the lowest score and maxim score you will allow for calls. 
* Weekly resets can help the user deploy contracts at the lowest possible gas fee
* It can be ran with ape scripts



