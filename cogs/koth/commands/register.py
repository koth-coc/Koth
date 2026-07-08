import discord
from discord import app_commands

import database
from utils import normalize_tag


def setup(group: app_commands.Group, bot):
    @group.command(name="register", description="Register a player for a KOTH")
    @app_commands.describe(id="The koth id", player_tag="Your in-game player tag, e.g. #ABC123")
    async def register(interaction: discord.Interaction, id: str, player_tag: str):
        koth = await database.get_koth(id)
        if not koth:
            await interaction.response.send_message(f"No koth found with id `{id}`.", ephemeral=True)
            return

        if koth["reg_channel_id"] and interaction.channel_id != koth["reg_channel_id"]:
            await interaction.response.send_message(
                f"Please use <#{koth['reg_channel_id']}> to register for this koth.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        tag = normalize_tag(player_tag)

        if await database.is_tag_registered_for_koth(id, tag):
            await interaction.followup.send("That tag is already registered for this koth.", ephemeral=True)
            return

        player = await bot.coc_client.get_player(tag)
        if player is None:
            await interaction.followup.send(
                f"Couldn't verify tag `{tag}` with the Clash of Clans API.", ephemeral=True
            )
            return

        clan_name = player.clan.name if player.clan else "No Clan"
        league = player.league.name if player.league else "Unranked"

        try:
            await database.add_registration(id, interaction.user.id, tag, player.name, clan_name, league)
        except Exception:
            await interaction.followup.send("You're already registered for this koth.", ephemeral=True)
            return

        await interaction.followup.send("Registration successful!", ephemeral=True)

        if koth["log_channel_id"]:
            log_channel = interaction.guild.get_channel(koth["log_channel_id"])
            if log_channel:
                embed = discord.Embed(title="Registration successful", color=discord.Color.gold())
                embed.add_field(name="Player name", value=player.name, inline=True)
                embed.add_field(name="Player tag", value=tag, inline=True)
                embed.add_field(name="Discord", value=interaction.user.mention, inline=True)
                embed.add_field(name="Clan", value=clan_name, inline=True)
                embed.add_field(name="League", value=league, inline=True)
                await log_channel.send(content=interaction.user.mention, embed=embed)
