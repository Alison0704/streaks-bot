import json
from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
from discord.ext import commands
from responses import get_response
import re

# ------------LOAD OUR TOKEN, ID AND FILES FROM SOMEWHERE ELSE------------
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1343002143312973926
COUNT_FILE = "count.json"

# -------------Array streaks------------


# ------------BOT SETUP------------
intents: Intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  #NOQA

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------HANDLING THE STARTUP FOR OUR BOT------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ------------MESSAGE FUNCIONALITY------------
async def send_message(message: Message, user_message: str) -> None:
    if message.channel.id == ALLOWED_CHANNEL_ID:
        if not user_message:
            print('(Message empty no intents)')
            return

        if is_private := user_message[0] == '?':
            user_message = user_message[1:]
        try:
            response: str = get_response(user_message)
            await message.author.send(response) if is_private else message.channel.send(response)
        except Exception as e:
            print(e)


# ------------COUNT FUNCTIONS------------
def load_count():
    """Loads the 'done' count from count.json."""
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, "r") as f:
            return json.load(f).get("done_count", 0)
    return 0


def save_count(count):
    """Saves the 'done' count to count.json."""
    with open(COUNT_FILE, "w") as f:
        json.dump({"done_count": count}, f)


# ------------HANDLING INCOMING MESSAGE------------
@bot.event
async def on_message(message: Message) -> None:
    done_count = load_count()

    if message.author == bot.user:
        return  # Ignore messages from itself

    if message.channel.id == ALLOWED_CHANNEL_ID:
        if re.search(r'\bdone\b', message.content, re.IGNORECASE):  # Match exact word "done"
            done_count += 1
            save_count(done_count)  # Save updated count to JSON

        user_message: str = message.content
        await send_message(message, user_message)

        await bot.process_commands(message)  # Ensure other commands still work

# ------------MAIN ENTRY POINT------------
def main() -> None:
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
