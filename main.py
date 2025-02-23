import json
from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Message
from discord.ext import commands
import re

# ------------LOAD OUR TOKEN, ID AND FILES FROM SOMEWHERE ELSE------------
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
EXTINGUISH: Final[str] = os.getenv('EXTINGUISH')
FIRED_UP: Final[str] = os.getenv('FIRED_UP')

ALLOWED_CHANNEL_ID_DAILY = 1343002143312973926
ALLOWED_CHANNEL_ID_WEEKLY = 1343060263854804993
JSON_FILE = "streaks.json"

# ------------BOT SETUP------------
intents: Intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  #NOQA

bot = commands.Bot(command_prefix="!", intents=intents)


# ------------CLEAR CHANNEL------------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear_channel(ctx, amount: int = 50):
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    await channel.purge(limit=amount)
    await ctx.send(f"✅ Cleared `{amount}` messages in {channel.mention}!", delete_after=3)


# command: !clear_channel 50


# ------------HANDLING THE STARTUP FOR OUR BOT------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ------------JSON FILE FUNCTIONS------------
def load_json():
    with open(JSON_FILE, "r") as file:
        return json.load(file)


def save_json(jsonfile):
    with open(JSON_FILE, "w") as file:
        json.dump(jsonfile, file, indent=4)


# Function to update multiple entries
def update_json(data, category):
    # if a streak
    if category in data["dailyStreaks"]:
        data["dailyStreaks"][category]["count"] += 1
        save_json(data)
        print("✅ JSON updated successfully!")
    else:
        print(f"❌Streak name {category} does not exist!")


# ------------TEXT PATTERN TRACKING------------
def parse_input(text):
    pattern = r"!([^-\s]+)-([^-\s]+)"  # Matches `!word-word`
    match = re.match(pattern, text, re.IGNORECASE)

    if match:
        command, category = match.groups()
        return command, category
    return None, None  # Return None if the pattern doesn't match


# ------------HANDLING INCOMING MESSAGE------------
@bot.event
async def on_message(message: Message) -> None:
    done_streaks = load_json()

    if message.author == bot.user:
        return  # Ignore messages from itself

    if message.channel.id == ALLOWED_CHANNEL_ID_DAILY:
        command, category = parse_input(message.content)
        if command == "done" and category is not None:
            update_json(done_streaks, category)

        await bot.process_commands(message)  # Ensure other commands still work


# ------------MAIN ENTRY POINT------------
def main() -> None:
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
