import discord
from discord.ext import commands

import config
import database
from utils import CocClient
from tasks.koth_reminder import KothReminder

GUILD_ID = 1380802948497670195


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

        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        self.koth_reminder = KothReminder(self)
        print("Slash commands synced.")


bot = KothBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="TWO FOLD JULY FIESTA | Powered by GBS",
    )
    await bot.change_presence(activity=activity)
    print("Presence updated.")


if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)
