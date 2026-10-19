# Astral

Astral is a Discord bot that delivers NASA's Astronomy Picture of the Day (APOD) to your discord server or directly too you.

Users can view today's featured astronomy media, browse historical entries dating back to 1995, or set up automated daily deliveries for their channels or DMs.

## Features

- **On-Demand APOD**: Look up the current picture of the day or browse entries from any date back to June 16, 1995.
- **Scheduled Deliveries**: Set up automatic daily postings in a server channel or DM at a specific time and timezone.
- **Rich Media**: Displays high-resolution photos, direct videos, or YouTube links alongside full explanations and image credits.
- **Flexible Destinations**: Works in server text channels and private direct messages.

## Commands

| Command | Parameters | Permissions | Description |
| :--- | :--- | :--- | :--- |
| `/apod` | `date` *(optional)* | Everyone | Displays today's APOD or an entry from a specific date (`YYYY-MM-DD`). |
| `/subscribe` | `time`, `timezone` | Manage Channels / DMs | Schedules daily delivery for the current channel or DM (24-hour `HH:MM` and timezone). |
| `/unsubscribe` | *None* | Manage Channels / DMs | Removes the daily delivery schedule for the current channel or DM. |

## Setup

### Prerequisites

- A **Discord Bot Token** from the [Discord Developer Portal](https://discord.com/developers/applications)
- A **NASA API Key** from [api.nasa.gov](https://api.nasa.gov/)
- **Docker** (recommended) or **Python 3.12+** (run locally)

### Configuration

Create a `.env` file from the provided template:

```bash
cp .env.example .env
```

Add your credentials to `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token
NASA_API_KEY=your_nasa_api_key
```

---

### Running with Docker

Run the container using Docker Compose:

```bash
docker compose up -d --build
```

Manage the service:

```bash
# View logs
docker compose logs -f

# Stop the bot
docker compose down
```

---

### Running Locally

1. **Set up a virtual environment:**

   **Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS / Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the bot:**

   ```bash
   python main.py
   ```
## Limitations
- **Direct Messages & Mutual Server**: Due to Discord's privacy settings, the bot can only send daily DMs to users who share at least one mutual server with the bot and have **Direct Messages** enabled. If a user leaves all mutual servers or closes their DMs, the dead subscription is automatically removed.
- **Channel Permissions**: In servers, the bot requires **View Channel**, **Send Messages**, and **Embed Links** permissions in the target channel. If the channel is deleted or permissions are revoked, the subscription is automatically cleaned up.
- **Daily Release Timing**: NASA publishes each day's APOD around **midnight US Eastern Time** (`America/New_York`). If a subscription is scheduled for an early morning hour in timezones ahead of New York (e.g. Europe, Asia, or Australia), it will deliver the current APOD until NASA updates their daily feed.
- **Archive Date Range**: The APOD archive began on **June 16, 1995**. Date lookups before `1995-06-16` or in the future cannot be queried.
- **Video Playback**: Discord's layout components cannot play external web players (like YouTube or Vimeo) inline. For video entries, the bot displays the highest-resolution thumbnail available along with an interactive link button to watch the video externally.
- **NASA API Uptime**: While Astral caches the current APOD in memory to minimize requests, historical lookups query the NASA APOD API directly and are subject to NASA's server availability and rate limits.