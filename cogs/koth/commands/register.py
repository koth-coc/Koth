import discord
from discord import app_commands

import database
from utils import normalize_tag


def setup(group: app_commands.Group, bot):
    @group.command(name="register", description="Register a player for a KOTH")
    @app_commands.describe(
        id="The koth id",
        player_tag="Your in-game player tag, e.g. #ABC123",
        api="Your API token from in-game settings > More Settings",
    )
    async def register(interaction: discord.Interaction, id: str, player_tag: str, api: str):
        koth = await database.get_koth(id)
        if not koth:
            embed = discord.Embed(description=f"No koth found with id `{id}`.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        if koth["reg_channel_id"] and interaction.channel_id != koth["reg_channel_id"]:
            embed = discord.Embed(
                description=f"Please use <#{koth['reg_channel_id']}> to register for this koth.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
            return

        await interaction.response.defer(thinking=True)

        tag = normalize_tag(player_tag)

        # already registered (same tag)
        if await database.is_tag_registered_for_koth(id, tag):
            embed = discord.Embed(description="That tag is already registered for this koth.", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            return

        # already registered with a different tag (same discord user)
        existing_registrations = await database.get_registrations(id)
        for reg in existing_registrations:
            if reg["discord_id"] == interaction.user.id:
                embed = discord.Embed(
                    description=f"You're already registered for this koth with tag `{reg['player_tag']}`.",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
                return

        player = await bot.coc_client.get_player(tag)
        if player is None:
            embed = discord.Embed(
                description=f"Couldn't verify tag `{tag}` with the Clash of Clans API.",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        token_valid = await bot.coc_client.verify_player_token(tag, api)
        if not token_valid:
            embed = discord.Embed(
                description="Invalid API token. Get it from in-game: Settings > More Settings > API Token.",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        if koth["th_level"] and player.town_hall != koth["th_level"]:
            embed = discord.Embed(
                description=(
                    f"Townhall requirement not met. This koth requires TH{koth['th_level']}, "
                    f"but `{player.name}` is TH{player.town_hall}."
                ),
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        clan_name = player.clan.name if player.clan else "No Clan"
        league = player.league.name if player.league else "Unranked"

        try:
            await database.add_registration(id, interaction.user.id, tag, player.name, clan_name, league)
        except Exception:
            embed = discord.Embed(description="You're already registered for this koth.", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            return

        success_embed = discord.Embed(title="Registration successful", color=discord.Color.green())
        success_embed.add_field(name="Player name", value=player.name, inline=True)
        success_embed.add_field(name="Player tag", value=tag, inline=True)
        success_embed.add_field(name="Town Hall", value=str(player.town_hall), inline=True)
        success_embed.add_field(name="Clan", value=clan_name, inline=True)
        success_embed.add_field(name="League", value=league, inline=True)
        await interaction.followup.send(embed=success_embed)

        if koth["log_channel_id"]:
            log_channel = interaction.guild.get_channel(koth["log_channel_id"])
            if log_channel:
                log_embed = discord.Embed(title="Registration successful", color=discord.Color.gold())
                log_embed.add_field(name="Player name", value=player.name, inline=True)
                log_embed.add_field(name="Player tag", value=tag, inline=True)
                log_embed.add_field(name="Discord", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="Clan", value=clan_name, inline=True)
                log_embed.add_field(name="League", value=league, inline=True)
                await log_channel.send(content=interaction.user.mention, embed=log_embed)
