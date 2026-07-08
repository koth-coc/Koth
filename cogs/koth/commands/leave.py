import discord
from discord import app_commands

import database
from utils import normalize_tag


def setup(group: app_commands.Group, bot):
    @group.command(name="leave", description="Leave a koth you registered for")
    @app_commands.describe(tag="Your in-game player tag")
    async def leave(interaction: discord.Interaction, tag: str):
        normalized = normalize_tag(tag)
        reg = await database.find_registration_by_tag(normalized, interaction.user.id)
        if not reg:
            await interaction.response.send_message("You're not registered with that tag.", ephemeral=True)
            return
        await database.remove_registration(reg["id"])
        await interaction.response.send_message("You've been removed from that koth.", ephemeral=True)
