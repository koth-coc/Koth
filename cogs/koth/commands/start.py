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
            embed = discord.Embed(description=f"No koth found with id `{id}`.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        registrations = await database.get_registrations(id)
        if not registrations:
            embed = discord.Embed(description="No one has registered for this koth yet.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        await interaction.response.defer(thinking=True)

        await database.update_koth(id, status="started", clan_link=clan)

        dm_embed = discord.Embed(
            title=f"KOTH `{id}` is now open!",
            description=f"Join fast!\n\n**Clan:** {clan}",
            color=discord.Color.green(),
        )

        dm_success = 0
        dm_failed = []
        for r in registrations:
            member = interaction.guild.get_member(r["discord_id"])
            if member is None:
                dm_failed.append(r["discord_id"])
                continue
            try:
                await member.send(embed=dm_embed)
                dm_success += 1
            except discord.Forbidden:
                dm_failed.append(r["discord_id"])

        target_channel = interaction.channel
        if koth["reg_channel_id"]:
            target_channel = interaction.guild.get_channel(koth["reg_channel_id"]) or interaction.channel

        announce_embed = discord.Embed(
            title=f"KOTH `{id}` is now open!",
            description=f"Clan is now open, join fast!\n\n**Clan:** {clan}",
            color=discord.Color.green(),
        )
        mentions = " ".join(f"<@{r['discord_id']}>" for r in registrations)
        await target_channel.send(content=mentions, embed=announce_embed)

        result_embed = discord.Embed(title="Start complete", color=discord.Color.blurple())
        result_embed.add_field(name="Announced in", value=target_channel.mention, inline=True)
        result_embed.add_field(name="DMs sent", value=str(dm_success), inline=True)
        if dm_failed:
            result_embed.add_field(
                name="DMs failed",
                value=f"{len(dm_failed)} player(s) couldn't be DMed (DMs closed or left server).",
                inline=False,
            )
        await interaction.followup.send(embed=result_embed)

    @start.error
    async def start_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(description="You don't have permission to use this command.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
        else:
            raise error
