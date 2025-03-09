import json
import random
from typing import Final
import os

import discord
from dotenv import load_dotenv
from discord import Intents, Message
from discord.ext import commands

intents: Intents = Intents.default()
intents.message_content = True  # Enable message command handling
bot = commands.Bot(command_prefix="!", intents=intents)


import re
import asyncio
import datetime
import pytz


# ------------LOAD OUR TOKEN, ID AND FILES FROM SOMEWHERE ELSE------------
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
EXTINGUISH: Final[str] = os.getenv('EXTINGUISH')
FIRED_UP: Final[str] = os.getenv('FIRED_UP')

ALLOWED_CHANNEL_ID_DAILY = int(os.getenv('ALLOWED_CHANNEL_ID_DAILY'))
ALLOWED_CHANNEL_ID_WEEKLY = int(os.getenv('ALLOWED_CHANNEL_ID_WEEKLY'))
JSON_FILE = "streaks.json"

# ------------BOT SETUP------------
intents: Intents = Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ------------HANDLING THE STARTUP FOR OUR BOT AND CLIENT EVENT------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.loop.create_task(send_scheduled_message())



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


# ---------------SUMMARY MESSAGE---------------
def summary_message():
    message = load_json()
    # Extract daily streaks
    daily_streaks = message.get("dailyStreaks", {})
    daily_output = "\n".join(f"{info['count']} <-- {activity}" for activity, info in daily_streaks.items())
    return daily_output


# ------------------------------------EVENT FUNCTIONS-----------------------------------
async def send_scheduled_message():
    await bot.wait_until_ready()
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    est = pytz.timezone("America/New_York")  # EST time zone

    while not bot.is_closed():
        now = datetime.datetime.now(pytz.utc).astimezone(est)
        target_time = est.localize(datetime.datetime(now.year, now.month, now.day, 11, 6, 30))  # 6:00 PM EST

        if now >= target_time:  # If time is past, schedule for next day
            target_time += datetime.timedelta(days=1)

        wait_time = (target_time - now).total_seconds()
        print(f"Next message in {wait_time} seconds.")

        await asyncio.sleep(wait_time)

        if channel:
            await channel.purge(limit=100)
            owner = await bot.application_info()  # Get bot owner info
            await channel.send(f"Hello! <@{owner.owner.id}>")
            await channel.send(EXTINGUISH)
            print("Message sent!")


async def all_done_streaks():
    await bot.wait_until_ready()
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    owner = await bot.application_info()  # Get bot owner info
    streaks = load_json()
    count = 0
    _, master_count = streaks["parameter"]
    for activity, details in streaks["dailyStreaks"].items():
        if details["count"] == master_count:
            count += 1
    if channel:
        if count == master_count:
            await channel.send(f"<@{owner.owner.id}>")
            await channel.send("Your streak is still alive! 🌟 Keep pushing forward—you’re building something amazing!💪")
            await channel.send(FIRED_UP)


# ------------------------------------COMMAND FUNCTIONS-----------------------------------
# ------------CLEAR CHANNEL------------
# command: !clear_channel 50
@bot.command()
@commands.has_permissions(manage_messages=True, send_messages=True, read_message_history=True)
async def clear_channel(ctx, amount: int = 50):
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    if channel == ctx.channel:
        await channel.purge(limit=amount)
        await ctx.send(f"✅ Cleared `{amount}` messages in {channel.mention}!", delete_after=3)


# ---------------SUMMARY COMMAND---------------
# command: !summary
@bot.command()
@commands.has_permissions(send_messages=True)
async def summary(ctx):
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    if channel == ctx.channel:
        await ctx.send("**🔥🔥🔥🔥🔥🔥🔥🔥🔥**")
        await ctx.send(summary_message())
        await ctx.send("**🔥🔥🔥🔥🔥🔥🔥🔥🔥**")


# ---------------JUST SEND MESSAGE COMMAND---------------
# command: !hi
@bot.command()
@commands.has_permissions(send_messages=True)
async def hi(ctx):
    index = random.Random().random() * 100
    if index < 10:
        message = f"Hi {ctx.send.author.mention}"
    elif index < 30:
        message = f"Hello! I hope you are having a great day!"
    elif index < 50:
        message = f"Howdy! {ctx.author.mention}!"
    elif index < 70:
        message = f"Bonzour! {ctx.author.mention}!"
    elif index < 98:
        message = f"Bonjour! {ctx.author.mention}!"
    else:
        message = f"I wonder if you will achieve your dream"
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    if channel == ctx.channel:
        await ctx.send(f"{message}")


# ---------------UPDATE STREAKS---------------
# command: !done {streak-name}
@bot.command()
@commands.has_permissions(send_messages=True)
async def done(ctx, category: str = ""):
    streaks = load_json()
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    found = 0
    if channel == ctx.channel:
        for activity, details in streaks["dailyStreaks"].items():
            if activity == category:
                details['count'] = details['count'] + 1
                save_json(streaks)
                found = 1
        if found:
            await ctx.send(f"{category} streaks updated")


# ------------------------------------------------------------------------------------------


# ------------MAIN ENTRY POINT------------
def main() -> None:
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
