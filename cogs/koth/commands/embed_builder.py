import discord
from discord import app_commands

from ..utils import EmbedBuilderView


def setup(group: app_commands.Group, bot):
    @group.command(name="builder", description="Build a custom embed with buttons")
    async def builder(interaction: discord.Interaction):
        guide_embed = discord.Embed(
            title="📐 Embed Builder",
            description="Design a fully custom embed, then send it anywhere.",
            color=discord.Color.from_rgb(88, 101, 242),
        )
        guide_embed.add_field(name="📝 Title / Description", value="Set the main text content.", inline=True)
        guide_embed.add_field(name="🖼️ Banner", value="Add a large image at the bottom.", inline=True)
        guide_embed.add_field(name="🎨 Color", value="Set the accent color bar.", inline=True)
        guide_embed.add_field(name="🔘 Add Button", value="Attach a Link or Message button (up to 5).", inline=True)
        guide_embed.add_field(name="📍 Channel", value="Pick where this gets sent.", inline=True)
        guide_embed.add_field(name="✅ Send / ❌ Cancel", value="Finish or discard your embed.", inline=True)
        guide_embed.set_footer(text="Live preview updates below as you build")

        view = EmbedBuilderView(interaction.user.id, default_channel=interaction.channel)
        await interaction.response.send_message(embed=guide_embed, view=view, ephemeral=True)

        preview_embed = discord.Embed(
            title="Preview",
            description="Your embed will appear here as you build it.",
            color=discord.Color.from_rgb(47, 49, 54),
        )
        preview_embed.set_footer(text="No channel selected")
        preview_msg = await interaction.followup.send(embed=preview_embed, ephemeral=True, wait=True)
        view.preview_message = preview_msg
