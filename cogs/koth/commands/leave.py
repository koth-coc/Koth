import discord
from discord import app_commands

import database
from utils import normalize_tag


def setup(group: app_commands.Group, bot):
    @group.command(name="leave", description="Leave a koth you registered for")
    @app_commands.describe(id="The koth id", tag="Your in-game player tag")
    async def leave(interaction: discord.Interaction, id: str, tag: str):
        koth = await database.get_koth(id)
        if not koth:
            embed = discord.Embed(description=f"No koth found with id `{id}`.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        normalized = normalize_tag(tag)
        reg = await database.find_registration(id, interaction.user.id, normalized)
        if not reg:
            embed = discord.Embed(
                description="You're not registered for that koth with that tag.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
            return

        await database.remove_registration(reg["id"])
        embed = discord.Embed(description=f"You've been removed from koth `{id}`.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
