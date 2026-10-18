import os
from dotenv import load_dotenv

load_dotenv()

NASA_API_KEY = os.getenv("NASA_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing! Make sure your .env file is passed to Docker.")

if not NASA_API_KEY:
    raise ValueError("NASA_API_KEY is missing! Make sure your .env file is passed to Docker.")