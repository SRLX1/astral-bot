import discord
from discord.ext import commands
from config import DISCORD_TOKEN

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
channel_id = 1559180502035075144

# creates an embed for the APOD data
def build_embed_for_apod(apod):
    embed = discord.Embed(
        title = apod["title"],
#        url = apod["hdurl"],
        description = apod["explanation"],
        colour = 0x0B3D91,    #Official NASA blue
    )
    if apod["media_type"] ==  "image" and apod["image_url"]:
        embed.set_image(url = apod["image_url"])
    if apod["media_type"] == "video" and apod["video"]:
        embed.add_field(name="Video", value=apod["video"], inline=False)
    if apod["credit"]:
        embed.add_field(name="Credit", value=apod["credit"][:1024], inline=False)
    embed.set_footer(text=f"NASA Astrophotography Picture of the Day • {apod['date']}")
    return embed

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
        await destination.send(
            content = apod["video"] if apod["media_type"] == "video" else None,
            embed = build_embed_for_apod(apod)
        )
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
    pass
