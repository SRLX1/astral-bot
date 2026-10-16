import discord, asyncio
from discord.ext import commands
from config import DISCORD_TOKEN
from nasa import get_aopd

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
channel_id = 1559180502035075144

# checks if a url points directly to a video file (can play inside a media gallery)
def is_direct_video(url):
    return bool(url) and url.lower().split("?")[0].endswith((".mp4", ".webm", ".mov"))

# creates a container for the APOD data
def build_container_for_apod(apod):
    container = discord.ui.Container(accent_color=0x0B3D91) # NASA Blue
    container.add_item(discord.ui.TextDisplay(f"## {apod['title']}"))
    if apod["media_type"] == "image" and apod["image_url"]:
        container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(apod["image_url"])))
    elif apod["media_type"] == "video" and is_direct_video(apod["video"]):
        container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(apod["video"])))
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

@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")
    destination = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
    await destination.send("Hello World!")

async def send_apod(destination,apod):
    try:
        await destination.send(view = build_container_for_apod(apod))
        # YouTube/Vimeo etc. can't go in the gallery, send the link separately so Discord shows its player
        if apod["media_type"] == "video" and apod["video"] and not is_direct_video(apod["video"]):
            await destination.send(apod["video"])
        return True
    except discord.Forbidden:
        print(f"Can't send to {destination}: DMs closed or missing permissions")
    except discord.NotFound:
        print(f"Destination {destination} no longer exists")
    except discord.HTTPException as e:
        print(f"Failed to send message: {e}")
    return False

@bot.tree.command(name="apod", description="Veiw the Astrophotgraphy of the day")
async def respod_apod(interaction: discord.Interaction):
    await interaction.response.defer()
    apod = await asyncio.to_thread(get_aopd)
    if apod is None:
        await interaction.followup.send("Nasa is not available right now, please try again later")
        return
    await interaction.followup.send(view = build_container_for_apod(apod))
    # YouTube/Vimeo etc. can't go in the gallery, send the link separately so Discord shows its player
    if apod["media_type"] == "video" and apod["video"] and not is_direct_video(apod["video"]):
        await interaction.followup.send(apod["video"])