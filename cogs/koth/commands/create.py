import discord
from discord import app_commands
from datetime import datetime, timezone

import database
from ..utils import parse_koth_time


def setup(group: app_commands.Group, bot):
    @group.command(name="create", description="Create a new KOTH event")
    @app_commands.describe(
        id="A short unique id for this koth",
        th="Town hall level for this koth",
        time="Start time as ddmmyyyyThhmm, e.g. 08072026T1830 (UTC), must be in the future",
        log_channel="Channel where registration info will be posted",
        reg_channel="Channel where /koth register will be accepted",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create(
        interaction: discord.Interaction,
        id: str,
        th: app_commands.Range[int, 1, 17],
        time: str,
        log_channel: discord.TextChannel,
        reg_channel: discord.TextChannel,
    ):
        if await database.get_koth(id):
            await interaction.response.send_message(f"A koth with id `{id}` already exists.", ephemeral=True)
            return

        try:
            start_time = parse_koth_time(time)
        except ValueError:
            await interaction.response.send_message(
                "Invalid time format. Use ddmmyyyyThhmm, e.g. 08072026T1830.", ephemeral=True
            )
            return

        if start_time <= datetime.now(timezone.utc):
            await interaction.response.send_message("Start time must be in the future.", ephemeral=True)
            return

        await database.create_koth(id, interaction.guild_id, th, start_time, log_channel.id, reg_channel.id)

        embed = discord.Embed(title=f"KOTH created: {id}", color=discord.Color.green())
        embed.add_field(name="Town Hall", value=str(th))
        embed.add_field(name="Start time", value=discord.utils.format_dt(start_time, "F"))
        embed.add_field(name="Log channel", value=log_channel.mention)
        embed.add_field(name="Registration channel", value=reg_channel.mention)
        await interaction.response.send_message(embed=embed)
