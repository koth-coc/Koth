import discord
from discord import app_commands

import database
from ..utils import ConfirmView


def setup(group: app_commands.Group, bot):
    @group.command(name="delete", description="Delete a koth")
    @app_commands.describe(id="The koth id")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete(interaction: discord.Interaction, id: str):
        koth = await database.get_koth(id)
        if not koth:
            await interaction.response.send_message(f"No koth found with id `{id}`.", ephemeral=True)
            return

        view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(
            f"Are you sure you want to delete koth `{id}`? This cannot be undone.", view=view, ephemeral=True
        )
        await view.wait()
        if view.value:
            await database.delete_koth(id)
