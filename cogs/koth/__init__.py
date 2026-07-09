from discord import app_commands
from discord.ext import commands as discord_commands

from .commands import create, register, start, setup as setup_cmd, delete, leave, list as list_cmd, embed_builder, participants

koth_group = app_commands.Group(name="koth", description="KOTH commands")
embed_group = app_commands.Group(name="embed", description="Embed tools")


async def setup(bot: discord_commands.Bot):
    """Called automatically by bot.load_extension('cogs.koth')."""
    create.setup(koth_group, bot)
    register.setup(koth_group, bot)
    start.setup(koth_group, bot)
    setup_cmd.setup(koth_group, bot)
    delete.setup(koth_group, bot)
    leave.setup(koth_group, bot)
    list_cmd.setup(koth_group, bot)
    embed_builder.setup(embed_group, bot)
    participants.setup(koth_group, bot)

    bot.tree.add_command(koth_group)
    bot.tree.add_command(embed_group)
