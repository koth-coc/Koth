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
            embed = discord.Embed(description=f"No koth found with id `{id}`.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        view = SetupView(id, interaction.user.id)
        embed = await view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @koth_setup.error
    async def koth_setup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                description="You don't have permission to use this command.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
        else:
            raise error
