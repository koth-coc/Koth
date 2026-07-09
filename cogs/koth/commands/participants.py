import discord
from discord import app_commands

import database

PER_PAGE = 15


class ParticipantsView(discord.ui.View):
    def __init__(self, author_id: int, koth_id: str, registrations: list):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.koth_id = koth_id
        self.registrations = registrations
        self.page = 0
        self.max_page = max(0, (len(registrations) - 1) // PER_PAGE)
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    def update_buttons(self):
        self.previous_page.disabled = self.page == 0
        self.next_page.disabled = self.page == self.max_page

    def build_embed(self) -> discord.Embed:
        start = self.page * PER_PAGE
        end = start + PER_PAGE
        page_regs = self.registrations[start:end]

        lines = [
            f"{start + i + 1}. <@{reg['discord_id']}> - {reg['player_name']} - `{reg['player_tag']}`"
            for i, reg in enumerate(page_regs)
        ]

        embed = discord.Embed(
            title=f" TH15 KOTH PARTICIPANTS ",
            description=f"**{len(self.registrations)}** player(s) registered\n\n" + "\n".join(lines),
            color=discord.Color.from_rgb(255, 255, 255),
        )
        embed.set_footer(text=f"Page {self.page + 1} of {self.max_page + 1}")
        return embed

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="<:emoji_16:1524750436677189662>")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="<:emoji_15:1524750369908068423>")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


def setup(group: app_commands.Group, bot):
    @group.command(name="participants", description="See all participants registered for a koth")
    @app_commands.describe(id="The koth id")
    async def participants(interaction: discord.Interaction, id: str):
        koth = await database.get_koth(id)
        if not koth:
            embed = discord.Embed(description=f"No koth found with id `{id}`.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return

        registrations = await database.get_registrations(id)
        if not registrations:
            embed = discord.Embed(
                description=f"No one has registered for koth `{id}` yet.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await interaction.response.send_message(embed=embed)
            return

        view = ParticipantsView(interaction.user.id, id, registrations)
        await interaction.response.send_message(embed=view.build_embed(), view=view)
