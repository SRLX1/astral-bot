from database.database import innit_db,add_or_update_subscription,remove_subscription
from discord import app_commands
from discord.ext import commands
from datetime import datetime, date as dt_date
from services.nasa import get_aopd, nasa_date
from zoneinfo import available_timezones
from cogs.scheduler_utils import compute_next_send

import discord, asyncio, re,zoneinfo

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# checks if a url points directly to a video file (can play inside a media gallery)
def is_direct_video(url):
    return bool(url) and url.lower().split("?")[0].endswith((".mp4", ".webm", ".mov"))

def get_target(interaction):
    if interaction.guild is None:
        return "dm", interaction.user.id
    return "channel", interaction.channel_id

# creates a container for the APOD data
def build_container_for_apod(apod):
    container = discord.ui.Container(accent_color=0x0B3D91) # NASA Blue
    container.add_item(discord.ui.TextDisplay(f"## {apod['title']}"))
    image_url = apod.get("image_url") or apod.get("hdurl") or apod.get("url")
    if apod["media_type"] == "image" and image_url:
        container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(image_url)))
    elif apod["media_type"] == "video":
        video_url = apod.get("video") or apod.get("url")
        if is_direct_video(video_url):
            container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(video_url)))
        elif video_url:
            thumb = (
                apod.get("thumbnail_url")
                or apod.get("image_url")
                or "https://apod.nasa.gov/apod/image/nasa_insignia_300.jpg"
            )
            container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(thumb)))

            if "youtu" in video_url.lower():
                label = "Watch on YouTube"
            elif "vimeo" in video_url.lower():
                label = "Watch on Vimeo"
            else:
                label = "Watch Video"

            container.add_item(discord.ui.ActionRow(discord.ui.Button(
                label=label,
                url=video_url,
                style=discord.ButtonStyle.link,
            )))
    container.add_item(discord.ui.TextDisplay(apod["explanation"]))
    if apod["credit"]: container.add_item(discord.ui.TextDisplay(f"**Credit**\n{apod['credit']}"))
    container.add_item(discord.ui.TextDisplay(f"-# NASA Astrophotography Picture of the Day • {apod['date']}"))
    view = discord.ui.LayoutView(timeout=None)
    view.add_item(container)
    return view

async def get_destination(bot,kind,target_id):
    if kind == "dm":
        return await bot.fetch_user(target_id)
    return bot.get_channel(target_id) or await bot.fetch_channel(target_id)

async def send_apod(destination, apod):
    return await destination.send(view=build_container_for_apod(apod))



@bot.event
async def setup_hook():
    innit_db()
    await bot.load_extension("cogs.scheduler")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error,app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ You are doing that too fast! Please try again in {error.retry_after:.1f}s.",
            ephemeral=True
        )
    else:
        cmd = interaction.command.name if interaction.command else "unknown"
        print(f"Command error in {cmd}: {error}")

@bot.tree.command(name="apod", description="View the Astrophotography Picture of the Day")
@app_commands.checks.cooldown(2, 4.0, key=lambda i: i.user.id)
@app_commands.describe(date="Optional date as YYYY-MM-DD, YYYY/MM/DD or YYYY MM DD (e.g. 2024-01-01)")
async def respod_apod(interaction: discord.Interaction, date: str | None = None):
    if date:
        # accept dashes, slashes, dots or spaces as separators by normalising them all to dashes
        normalised = re.sub(r"[-/.\s]+", "-", date.strip())
        try:
            parsed = datetime.strptime(normalised, "%Y-%m-%d").date()
        except ValueError:
            await interaction.response.send_message("Invalid date, use YYYY-MM-DD", ephemeral=True)
            return
        date = parsed.isoformat() # canonical YYYY-MM-DD (zero padded) for comparisons and the API
        if parsed < dt_date(1995, 6, 16) or date > nasa_date():
            await interaction.response.send_message("Date must be between 1995-06-16 and today", ephemeral=True)
            return
    await interaction.response.defer()
    apod = await asyncio.to_thread(get_aopd, date)
    if apod is None:
        await interaction.followup.send("NASA is not available right now, please try again later")
        return
    await interaction.followup.send(view=build_container_for_apod(apod))

@bot.tree.command(name="subscribe", description="get the APOD every day at a set time")
@app_commands.describe(time="Your local time as HH:MM", timezone="e.g. America/New_York")
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.cooldown(3, 5.0, key=lambda i: i.user.id)
async def subscribe(interaction: discord.Interaction, time: str, timezone: str):
    kind, target_id = get_target(interaction)
    try:
        hours,mins = map(int,time.split(":"))
        if hours not in range(0,24) or mins not in range(0,60):
            raise ValueError()
    except ValueError:
        await interaction.response.send_message("Invalid time format, use HH:MM", ephemeral=True)
        return
    try:
        zoneinfo.ZoneInfo(timezone)
    except (zoneinfo.ZoneInfoNotFoundError,ValueError):
        await interaction.response.send_message("Invalid timezone, use tz database format", ephemeral=True)
        return
    time = f"{hours:02d}:{mins:02d}" 
    next_send_at = compute_next_send(time,timezone)
    add_or_update_subscription(kind,target_id,time,timezone,next_send_at)
    await interaction.response.send_message(
        f"Subscribed! You'll get the APOD every day at {time} ({timezone}). "
        f"First one: <t:{next_send_at}:F>",
        ephemeral=True,
    )
@subscribe.autocomplete("timezone")
async def timezone_autocomplete(interaction: discord.Interaction, current: str):
    matches = [tz for tz in available_timezones() if current.lower() in tz.lower()]
    return([app_commands.Choice(name=tz,value=tz) for tz in matches[:25]])

@bot.tree.command(name="unsubscribe", description="Unsubscribe from the daily APOD")
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.cooldown(3, 5.0, key=lambda i: i.user.id)
async def unsubscribe(interaction: discord.Interaction):
    kind,target_id = get_target(interaction)
    remove_subscription(kind,target_id)
    await interaction.response.send_message("You have been unsubscribed from the daily APOD", ephemeral=True)