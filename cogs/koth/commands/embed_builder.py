import discord
from discord import app_commands

from ..utils import EmbedBuilderView


def setup(group: app_commands.Group, bot):
    @group.command(name="builder", description="Build a custom embed with buttons")
    async def builder(interaction: discord.Interaction):
        view = EmbedBuilderView(interaction.user.id)
        await interaction.response.send_message(embed=view.embed, view=view)
