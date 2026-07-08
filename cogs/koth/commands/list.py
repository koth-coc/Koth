import discord
from discord import app_commands

import database


def setup(group: app_commands.Group, bot):
    @group.command(name="list", description="List all koths in this server")
    async def koth_list(interaction: discord.Interaction):
        koths = await database.get_all_koths(interaction.guild_id)
        if not koths:
            await interaction.response.send_message("No koths have been created yet.", ephemeral=True)
            return

        embed = discord.Embed(title="KOTHs", color=discord.Color.bruple())
        for k in koths:
            lines = [
                f"Status: {k['status']}",
                f"Town Hall: {k['th_level'] or 'Not set'}",
            ]
            if k["start_time"]:
                lines.append(f"Start: {discord.utils.format_dt(k['start_time'], 'F')}")
            if k["reg_channel_id"]:
                lines.append(f"Register in: <#{k['reg_channel_id']}>")
            lines.append(f"Registered: {k['registration_count']}")
            embed.add_field(name=k["id"], value="\n".join(lines), inline=False)

        await interaction.response.send_message(embed=embed)
