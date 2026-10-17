import time,asyncio
from discord.ext import commands,tasks
from database.database import get_due_subscriptions,set_next_send_times
from services.nasa import get_aopd
from cogs.bot import get_destination,send_apod
from cogs.scheduler_utils import compute_next_send

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.deliver_due_apods.start()

    async def cog_unload(self):
        self.deliver_due_apods.cancel()

    @tasks.loop(minutes=1)
    async def deliver_due_apods(self):
        now_utc = int(time.time())
        due = get_due_subscriptions(now_utc)
        if not due:
            return
        apod = await asyncio.to_thread(get_aopd)
        if not apod:
            return
        updates = []
        for row in due:
            try:
                destination = await get_destination(self.bot, row["kind"], row["target_id"])
                ok = await send_apod(destination,apod)
                if ok:
                    updates.append((compute_next_send(row["send_time"],row["timezone"]),row["kind"],row["target_id"]))
            except Exception as e:
                # one bad row (deleted channel, unknown user, bad timezone) shouldn't stop the others
                print(f"Failed to deliver APOD to {row['kind']} {row['target_id']}: {e}")
        if updates:
            set_next_send_times(updates)

        
    @deliver_due_apods.before_loop
    async def before_deliver(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Scheduler(bot))