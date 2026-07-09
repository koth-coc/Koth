import discord
from discord import app_commands

from ..utils import EmbedBuilderView


def setup(group: app_commands.Group, bot):
    @group.command(name="builder", description="Build a custom embed with buttons")
    async def builder(interaction: discord.Interaction):
        guide_embed = discord.Embed(description="This will be the guide to how to make embed message")

        view = EmbedBuilderView(interaction.user.id, default_channel=interaction.channel)
        await interaction.response.send_message(embed=guide_embed, view=view, ephemeral=True)

        preview_embed = discord.Embed(description="This message will be updated as we use the builder")
        preview_msg = await interaction.followup.send(embed=preview_embed, ephemeral=True, wait=True)
        view.preview_message = preview_msg
