from discord.ext import tasks

import database


class KothReminder:
    """Background loop: once a koth's start_time arrives, ping its log channel."""

    def __init__(self, bot):
        self.bot = bot
        self.check_koths.start()

    def stop(self):
        self.check_koths.cancel()

    @tasks.loop(seconds=60)
    async def check_koths(self):
        due = await database.get_koths_due_for_reminder()
        for koth in due:
            channel = self.bot.get_channel(koth["log_channel_id"]) if koth["log_channel_id"] else None
            if channel:
                await channel.send(f"⏰ KOTH `{koth['id']}` start time has arrived!")
            await database.mark_reminder_sent(koth["id"])

    @check_koths.before_loop
    async def before_check_koths(self):
        await self.bot.wait_until_ready()
from discord.ext import tasks

import database


class KothReminder:
    """Background loop: once a koth's start_time arrives, ping its log channel."""

    def __init__(self, bot):
        self.bot = bot
        self.check_koths.start()

    def stop(self):
        self.check_koths.cancel()

    @tasks.loop(seconds=60)
    async def check_koths(self):
        due = await database.get_koths_due_for_reminder()
        for koth in due:
            channel = self.bot.get_channel(koth["log_channel_id"]) if koth["log_channel_id"] else None
            if channel:
                await channel.send(f"⏰ KOTH `{koth['id']}` start time has arrived!")
            await database.mark_reminder_sent(koth["id"])

    @check_koths.before_loop
    async def before_check_koths(self):
        await self.bot.wait_until_ready()
