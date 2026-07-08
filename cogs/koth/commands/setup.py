import discord
from discord import app_commands

import database
from ..utils import SetupView


def setup(group: app_commands.Group, bot):
    @group.command(name="setup", description="Configure a koth's settings")
    @app_commands.describe(id="The koth id")
    @app_commands.checks.has_permissions(administrator=True)
    async def koth_setup(interaction: discord.Interaction, id: str):
        koth = await database.get_koth(id)
        if not koth:
            await interaction.response.send_message(f"No koth found with id `{id}`.", ephemeral=True)
            return

        view = SetupView(id, interaction.user.id)
        embed = await view.build_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
