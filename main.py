import discord
from discord.ext import commands

import config
import database
from utils import CocClient
from tasks.koth_reminder import KothReminder


class KothBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.coc_client = CocClient()
        self.koth_reminder = None

    async def setup_hook(self):
        await database.init_db()
        await self.coc_client.login(config.COC_EMAIL, config.COC_PASSWORD)
        await self.load_extension("cogs.koth")
        await self.tree.sync()
        self.koth_reminder = KothReminder(self)
        print("Slash commands synced.")


bot = KothBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")


if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
