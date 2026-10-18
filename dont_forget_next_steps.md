# Astral Astrophotography Discord Bot — Plan

## Phase 4: Cog Refactor & Subscription Status Command

**Goal:** 
1. Refactor `cogs/bot.py` into a proper `discord.py` Cog (`cogs/apod.py`) and move bot instantiation and lifecycle management into `main.py`.
2. Implement the `/subscription` slash command to allow users (in DMs) and servers (in channels) to check their current delivery time, timezone, and next delivery timestamp.

---

### Current Architecture vs. Target Architecture

```
Current:
main.py ───────────────► cogs/bot.py (creates bot, registers commands globally)
                              ▲
cogs/scheduler.py ────────────┘ (imports send_apod, get_destination)

Target:
main.py (creates AstralBot, manages setup_hook & cogs)
   ├── loads ──► cogs/apod.py (ApodCog: /apod command, container builder, send_apod)
   └── loads ──► cogs/scheduler.py (SchedulerCog: /subscribe, /unsubscribe, /subscription, loop)
```

---

### Key Decisions

| Decision | Choice | Why |
|---|---|---|
| **Bot Instantiation** | Subclass `commands.Bot` inside `main.py` | Keeps `main.py` as the true entry point, handles `setup_hook` cleanly, and eliminates circular import risks. |
| **Cog Registration** | Standard `app_commands.command` inside `commands.Cog` | The idiomatic `discord.py` way to structure modular slash commands. |
| **Subscription Commands Grouping** | Group `/subscribe`, `/unsubscribe`, and `/subscription` in `cogs/scheduler.py` | Keeps all subscription logic and scheduling together in one place. |
| **Shared Helpers** | Keep `build_container_for_apod` and `send_apod` exported from `cogs/apod.py` | Both `/apod` and `cogs/scheduler.py` use the exact same sending logic. |
| **`/subscription` Output** | Ephemeral card with Discord dynamic timestamps (`<t:unix:F>` and `<t:unix:R>`) | Private to the caller, shows exact local time and relative countdown (e.g., *"in 18 hours"*). |

---

### 1. The New `/subscription` Command

**Behavior:**
- Runs as a slash command: `/subscription`
- Identifies the target via `get_target(interaction)`:
  - In DMs → `kind="dm"`, `target_id=interaction.user.id`
  - In a server → `kind="channel"`, `target_id=interaction.channel_id`
- Queries SQLite using existing `get_subscriptions(kind, target_id)`.

**Response when subscribed:**
```text
📅 APOD Subscription Details
• Destination: Direct Message (or #channel-name)
• Scheduled Time: 09:00 (Europe/London)
• Next Delivery: Monday, October 19, 2026 09:00 (in 18 hours)

Tip: Use /subscribe to change settings or /unsubscribe to cancel.
```

**Response when NOT subscribed:**
```text
You do not have an active APOD subscription for this DM / channel.
Use /subscribe time:<HH:MM> timezone:<timezone> to set one up!
```

---

### 2. Refactoring `cogs/bot.py` into a Proper Cog (`cogs/apod.py`)

#### Step A: `cogs/apod.py`
Transform the file into a class inheriting from `commands.Cog`:
```python
class ApodCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="apod", description="View the Astrophotography Picture of the Day")
    @app_commands.describe(date="Optional date as YYYY-MM-DD, YYYY/MM/DD or YYYY MM DD (e.g. 2024-01-01)")
    async def apod(self, interaction: discord.Interaction, date: str | None = None):
        ...

async def setup(bot: commands.Bot):
    await bot.add_cog(ApodCog(bot))
```
Also contains:
- `build_container_for_apod(apod)`
- `send_apod(destination, apod)`
- `get_destination(bot, kind, target_id)`
- `get_target(interaction)`

#### Step B: `cogs/scheduler.py`
Move `/subscribe`, `/unsubscribe`, and the new `/subscription` commands inside `Scheduler(commands.Cog)`:
```python
class Scheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash commands:
    # - /subscribe
    # - /unsubscribe
    # - /subscription
    
    # Task loop:
    # - deliver_due_apods
```

#### Step C: `main.py`
Instantiate the bot and configure `setup_hook`:
```python
import discord
from discord.ext import commands
from config import DISCORD_TOKEN
from database.database import innit_db

class AstralBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        innit_db()
        await self.load_extension("cogs.apod")
        await self.load_extension("cogs.scheduler")
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} slash commands")

if __name__ == "__main__":
    bot = AstralBot()
    bot.run(DISCORD_TOKEN)
```

---

### Task Checklist

- [ ] **Database Verification**: Ensure `get_subscriptions(kind, target_id)` in `database/database.py` returns all needed fields (`send_time`, `timezone`, `next_send_at`).
- [ ] **Convert `cogs/bot.py` to `cogs/apod.py`**:
  - [ ] Wrap `/apod` into `ApodCog(commands.Cog)` with `@app_commands.command`.
  - [ ] Add `setup(bot)` function at bottom.
  - [ ] Retain helper functions (`build_container_for_apod`, `send_apod`, `get_destination`, `get_target`).
- [ ] **Update `cogs/scheduler.py`**:
  - [ ] Move `/subscribe` and `/unsubscribe` from `bot.py` into `Scheduler`.
  - [ ] Add `/subscription` slash command to `Scheduler`.
  - [ ] Update imports to point to `cogs.apod` instead of `cogs.bot`.
- [ ] **Update `main.py`**:
  - [ ] Create `AstralBot` subclass with `setup_hook`.
  - [ ] Load `cogs.apod` and `cogs.scheduler`.
  - [ ] Clean up redundant code.
- [ ] **Delete / Deprecate `cogs/bot.py`**:
  - [ ] Verify nothing still imports from `cogs.bot`.
  - [ ] Remove `cogs/bot.py`.
- [ ] **Testing & Verification**:
  - [ ] Run bot and verify 4 commands synced: `/apod`, `/subscribe`, `/unsubscribe`, `/subscription`.
  - [ ] Test `/subscription` when not subscribed.
  - [ ] Test `/subscribe` followed by `/subscription` to verify details and countdown formatting.
  - [ ] Test `/apod` manual fetch.
