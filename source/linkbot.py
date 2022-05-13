"""Main entry point for the Interlock-bouncer."""

import requests
import configparser
import logging
import discord
import re
import os

# Set the logging up
logging.basicConfig(level=logging.INFO)

# Parse the configuration.ini file in the repository root
configuration = configparser.ConfigParser()
configuration.read('configuration.ini')

# Get needed values from the configuration.ini file
token_from_config = configuration.get('discord', 'token')
# Get the needed values from the environment variables
token_from_environment = os.getenv('DISCORD_TOKEN')

# Set the token either by config or environment variable
token = token_from_config or token_from_environment

if (token_from_config and token_from_environment and
   token_from_config != token_from_environment):
    logging.warning("Different Discord token set via configuration.ini file \
AND environment variable! Prioritizing token from configuration.ini.")

# Create a discord client
client = discord.Client()


@client.event
async def on_ready():
    """Invoke when the bot has connected to Discord."""
    print(f'{client.user} has connected to Discord!')
    # Set the bot profile picture
    with open('profile.png', 'rb') as image:
        await client.user.edit(avatar=image.read())


def urls_from_str(str):
    """Find and return all URLs in a string."""
    urlRegex = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|\
    [!*, ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str)
    return urlRegex


def str_contains_url_p(str):
    """Return True or False depending on whether a string contains a URL."""
    if (len(urls_from_str(str)) > 0):
        return True
    else:
        return False


def url_malicious_p(url):
    """Return True or False depending on whether a URL is malicious or not."""
    r = requests.get("https://perceptual.apozy.com/host/{0}".format(url))
    rjson = r.json()

    # If there was an error with the API, we cannot guarantee anything
    try:
        rjson['error']
        logging.warning("API error for URL %s", url)
        return True
    except KeyError:
        pass

    # If there is a corresponding traffic rank entry, the URL is well rated
    try:
        rjson['trafficRank']
        return False
    except KeyError:
        logging.info("Traffic rank not available for URL %s", url)
        return True


@client.event
async def on_message(message):
    """Invoke when a message is received on the Guild/server."""
    if message.author.bot:
        return
    for url in urls_from_str(message.content):
        if (url_malicious_p(url)):
            await message.reply(
                content="Message contains dangerous links! **{0}:** `{1}`"
                .format(message.author.name, message.content))
            await message.delete()
            break

if __name__ == '__main__':
    client.run(token)
