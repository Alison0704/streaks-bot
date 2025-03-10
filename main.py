import json
import random
from typing import Final
import os

import discord
from dotenv import load_dotenv
from discord.ext import commands

import re
import asyncio
import datetime
import pytz

# Define bot command prefix
intents = discord.Intents.default()
intents.messages = True  # Enable message events
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------LOAD OUR TOKEN, ID AND FILES FROM SOMEWHERE ELSE------------
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
EXTINGUISH: Final[str] = os.getenv('EXTINGUISH')
FIRED_UP: Final[str] = os.getenv('FIRED_UP')
STILL_ALIVE: Final[str] = os.getenv('STILL_ALIVE')

ALLOWED_CHANNEL_ID_DAILY = int(os.getenv('ALLOWED_CHANNEL_ID_DAILY'))
ALLOWED_CHANNEL_ID_WEEKLY = int(os.getenv('ALLOWED_CHANNEL_ID_WEEKLY'))
JSON_FILE = "streaks.json"


# ------------HANDLING THE STARTUP FOR OUR BOT AND CLIENT EVENT------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.loop.create_task(send_scheduled_message())
    

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"An error occurred: {event}")


# ------------JSON FILE FUNCTIONS------------
def load_json():
    with open(JSON_FILE, "r") as file:
        return json.load(file)


def save_json(jsonfile):
    with open(JSON_FILE, "w") as file:
        json.dump(jsonfile, file, indent=4)


# Function to update multiple entries
def update_json(data, category):
    if category in data["daily-streaks"]:
        data["daily-streaks"][category]["count"] += 1
        save_json(data)
        print("✅ JSON updated successfully!")
    else:
        print(f"❌Streak name {category} does not exist!")


# ---------------MESSAGE---------------
def summary_message():
    message = load_json()
    summary_output = "```"
    summary_streaks = message.get("daily-streaks", {})
    for activity, info in summary_streaks.items():
        summary_output += f"\nStreaks:{info['daily']} - - - - Completed: {info['daily']==info['aim']} - - - - {str(activity).upper()} "
    summary_output += "```"
    return summary_output


def left_message():
    message = load_json()
    left_output = "```"
    left_streaks = message.get("daily-streaks", {})
    for activity, info in left_streaks.items():
        if int(info['daily']) != int(info['aim']):
            left_output += f"\n>>{activity}"
    left_output += "```"
    return left_output


# ------------------------------------EVENT FUNCTIONS-----------------------------------
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Debug print to check if messages are being received
    print(f"Message received: {message.content}")

    if message.content.lower() == "hello":
        await message.channel.send("Hello there!")

    await bot.process_commands(message)


async def send_scheduled_message():
    await bot.wait_until_ready()
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    est = pytz.timezone("America/New_York")  # EST time zone
    streaks = load_json()
    count = 0

    while not bot.is_closed():
        now = datetime.datetime.now(pytz.utc).astimezone(est)
        target_time = est.localize(datetime.datetime(now.year, now.month, now.day, 6, 15, 0))  # 6:00 AM EST

        if now >= target_time:
            target_time += datetime.timedelta(days=1)

        wait_time = (target_time - now).total_seconds()
        print(f"Next message in {wait_time} seconds.")

        await asyncio.sleep(wait_time)

        if channel:
            await channel.purge(limit=100)
            owner = await bot.application_info()
            await channel.send(f"Hello! <@{owner.owner.id}>")
            await channel.send("Hope you slept well!")
            await channel.send("====================================================================")
            await channel.send("Here is your current streaks:")
            await channel.send("**🔥🔥🔥🔥🔥🔥🔥🔥🔥**")
            await channel.send(summary_message())
            await channel.send("**🔥🔥🔥🔥🔥🔥🔥🔥🔥**")
            await channel.send("====================================================================")

            # pick out the details
            if "master-count" in streaks:
                master_count = streaks["master-count"]
            else:
                print("❌ 'master-count' key not found in streaks JSON.")
                return

            # Iterate through dailyStreaks
            for activity, details in streaks["daily-streaks"].items():
                if details["daily"] == details["aim"]:
                    count += 1

            # Debug
            print("Count:", count)
            print("Master Count:", master_count)

            if count != master_count:
                await channel.send(
                    f"**Oh no! {master_count - count} extinguished streaks!**")
                # Iterate through dailyStreaks
                for activity, details in streaks["daily-streaks"].items():
                    if details["daily"] != details["aim"]:
                        details["daily"] = 0
                        details["aim"] = 0
                        await channel.send(f"```{activity} has been reset to zero```")
                await channel.send(EXTINGUISH)
            else:
                await channel.send("WE ARE STILL ALIVE!!")
                await channel.send(STILL_ALIVE)
            for activity, details in streaks["daily-streaks"].items():
                details["aim"] += 1
            save_json(streaks)
            await channel.send("====================================================================")
            await channel.send("Have a wonderful day!")
            await channel.send("====================================================================")
            print("Message sent!")


# ------------------------------------COMMAND FUNCTIONS-----------------------------------
@bot.command()
@commands.has_permissions(manage_messages=True, send_messages=True, read_message_history=True)
async def clear_channel(ctx, amount: int = 50):
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    if channel == ctx.channel:
        await channel.purge(limit=amount)
        await ctx.send(f"✅ Cleared `{amount}` messages in {channel.mention}!", delete_after=3)


@bot.command()
@commands.has_permissions(send_messages=True)
async def summary(ctx):
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    if channel == ctx.channel:
        await ctx.send("**🔥🔥🔥🔥🔥🔥🔥🔥🔥**")
        await ctx.send(summary_message())
        await ctx.send("**🔥🔥🔥🔥🔥🔥🔥🔥🔥**")

@bot.command()
@commands.has_permissions(send_messages=True)
async def left(ctx):
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    await ctx.send("For today, you need to complete:")
    if channel == ctx.channel:
        if left_message() != "``````":
            await ctx.send(left_message())
        else:
            await ctx.send("Ah you completed everything!!")
            await ctx.send(FIRED_UP)

@bot.command()
@commands.has_permissions(send_messages=True)
async def hi(ctx):
    index = random.Random().random() * 100
    if index < 10:
        message = f"Hi {ctx.author.mention}"
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


@bot.command()
@commands.has_permissions(send_messages=True)
async def done(ctx, category: str = ""):
    if not category:
        await ctx.send("Please provide a streak name!")
        return

    streaks = load_json()
    channel = bot.get_channel(ALLOWED_CHANNEL_ID_DAILY)
    found = False
    if channel == ctx.channel:
        for activity, details in streaks["daily-streaks"].items():
            if activity == category:
                if details["daily"] < details["aim"]:
                    details["daily"] += 1
                    save_json(streaks)
                    await ctx.send(f"{category} streaks updated")
                else:
                    await ctx.send(f"{category} streaks already updated")
                found = True
                break
        if not found:
            await ctx.send(f"Streak {category} not found.")


# ------------MAIN ENTRY POINT------------
def main() -> None:
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
