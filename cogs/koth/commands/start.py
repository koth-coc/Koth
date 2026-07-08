import discord
from discord import app_commands

import database


def setup(group: app_commands.Group, bot):
    @group.command(name="start", description="Announce a koth clan is open")
    @app_commands.describe(id="The koth id", clan="The in-game clan link")
    @app_commands.checks.has_permissions(administrator=True)
    async def start(interaction: discord.Interaction, id: str, clan: str):
        koth = await database.get_koth(id)
        if not koth:
            await interaction.response.send_message(f"No koth found with id `{id}`.", ephemeral=True)
            return

        registrations = await database.get_registrations(id)
        if not registrations:
            await interaction.response.send_message("No one has registered for this koth yet.", ephemeral=True)
            return

        await database.update_koth(id, status="started", clan_link=clan)

        mentions = " ".join(f"<@{r['discord_id']}>" for r in registrations)
        target_channel = interaction.channel
        if koth["reg_channel_id"]:
            target_channel = interaction.guild.get_channel(koth["reg_channel_id"]) or interaction.channel

        await target_channel.send(f"{mentions}\nClan is now open, join fast! {clan}")
        await interaction.response.send_message("Started and pinged all registered players.", ephemeral=True)
