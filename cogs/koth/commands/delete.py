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
            embed = discord.Embed(
                description=f"No koth found with id `{id}`.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title=f"Delete KOTH: {id}?",
            description="Are you sure you want to delete this koth? This cannot be undone.",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Town Hall", value=str(koth["th"]))
        embed.add_field(name="Start time", value=discord.utils.format_dt(koth["start_time"], "F"))
        log_channel = interaction.guild.get_channel(koth["log_channel_id"])
        reg_channel = interaction.guild.get_channel(koth["reg_channel_id"])
        embed.add_field(name="Log channel", value=log_channel.mention if log_channel else "Unknown")
        embed.add_field(name="Registration channel", value=reg_channel.mention if reg_channel else "Unknown")

        view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()

        if view.value:
            await database.delete_koth(id)
            result_embed = discord.Embed(
                description=f"KOTH `{id}` has been deleted.",
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=result_embed)
        else:
            result_embed = discord.Embed(
                description=f"Deletion of KOTH `{id}` was cancelled.",
                color=discord.Color.greyish() if hasattr(discord.Color, "greyish") else discord.Color.light_grey(),
            )
            await interaction.followup.send(embed=result_embed)
