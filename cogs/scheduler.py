from database.database import remove_subscription
import time,asyncio,discord
from discord.ext import commands,tasks
from database.database import get_due_subscriptions, update_subscription_next_send
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

        for row in due:
            kind = row["kind"]
            target_id = row["target_id"]
            old_next_send = row["next_send_at"]
            new_next_send = compute_next_send(row["send_time"], row["timezone"])

            try:
                destination = await get_destination(self.bot, kind, target_id)
                await send_apod(destination, apod)
                update_subscription_next_send(kind, target_id, old_next_send, new_next_send)
            except (discord.Forbidden, discord.NotFound):
                print(f"Removing dead subscription for {kind} {target_id} (Forbidden or NotFound)")
                remove_subscription(kind, target_id)
            except Exception as e:
                print(f"Temporary failure delivering APOD to {kind} {target_id}: {e}")
                update_subscription_next_send(kind, target_id, old_next_send, new_next_send)


        
    @deliver_due_apods.before_loop
    async def before_deliver(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Scheduler(bot))