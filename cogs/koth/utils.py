import discord
from datetime import datetime, timezone

import database

TIME_FORMAT = "%d-%m-%YT%H:%M"


def parse_koth_time(value: str) -> datetime:
    return datetime.strptime(value, TIME_FORMAT).replace(tzinfo=timezone.utc)


class ConfirmView(discord.ui.View):
    """Yes/No confirmation, used by /koth delete."""

    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Yes, delete it", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()


# ---------------------------------------------------------------------------
# /koth setup panel
# ---------------------------------------------------------------------------

class ThModal(discord.ui.Modal, title="Set Town Hall Level"):
    th = discord.ui.TextInput(label="Town Hall level", placeholder="e.g. 16", max_length=2)

    def __init__(self, koth_id: str, panel: "SetupView"):
        super().__init__()
        self.koth_id = koth_id
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            th_level = int(self.th.value)
        except ValueError:
            embed = discord.Embed(description="Town hall level must be a number.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return
        await database.update_koth(self.koth_id, th_level=th_level)
        await self.panel.refresh(interaction)


class TimeModal(discord.ui.Modal, title="Set Start Time"):
    time_input = discord.ui.TextInput(
        label="Start time (dd-mm-yyyyThh:mm)",
        placeholder="e.g. 08-07-2026T18:30",
    )

    def __init__(self, koth_id: str, panel: "SetupView"):
        super().__init__()
        self.koth_id = koth_id
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            dt = parse_koth_time(self.time_input.value)
        except ValueError:
            embed = discord.Embed(
                description="Invalid format. Use dd-mm-yyyyThh:mm, e.g. 08-07-2026T18:30.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
            return
        if dt <= datetime.now(timezone.utc):
            embed = discord.Embed(description="Start time must be in the future.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return
        await database.update_koth(self.koth_id, start_time=dt)
        await self.panel.refresh(interaction)


class SetupView(discord.ui.View):
    def __init__(self, koth_id: str, author_id: int):
        super().__init__(timeout=300)
        self.koth_id = koth_id
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            embed = discord.Embed(
                description="Only the person who ran /koth setup can use this.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
            return False
        return True

    async def build_embed(self) -> discord.Embed:
        koth = await database.get_koth(self.koth_id)
        e = discord.Embed(title=f"KOTH setup - {self.koth_id}", color=discord.Color.blurple())
        e.add_field(name="Town Hall", value=str(koth["th_level"] or "Not set"), inline=True)
        e.add_field(
            name="Start time",
            value=discord.utils.format_dt(koth["start_time"], "F") if koth["start_time"] else "Not set",
            inline=True,
        )
        e.add_field(
            name="Log channel",
            value=f"<#{koth['log_channel_id']}>" if koth["log_channel_id"] else "Not set",
            inline=True,
        )
        e.add_field(
            name="Registration channel",
            value=f"<#{koth['reg_channel_id']}>" if koth["reg_channel_id"] else "Not set",
            inline=True,
        )
        e.add_field(name="Status", value=koth["status"], inline=True)
        return e

    async def refresh(self, interaction: discord.Interaction):
        embed = await self.build_embed()
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Set Town Hall", style=discord.ButtonStyle.primary, row=0)
    async def set_th(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ThModal(self.koth_id, self))

    @discord.ui.button(label="Set Start Time", style=discord.ButtonStyle.primary, row=0)
    async def set_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TimeModal(self.koth_id, self))

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set log channel",
        row=1,
    )
    async def set_log_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        await database.update_koth(self.koth_id, log_channel_id=select.values[0].id)
        await self.refresh(interaction)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set registration channel",
        row=2,
    )
    async def set_reg_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        await database.update_koth(self.koth_id, reg_channel_id=select.values[0].id)
        await self.refresh(interaction)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.success, row=3)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(description="Setup closed.", color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=None)


# ---------------------------------------------------------------------------
# /embed builder
# ---------------------------------------------------------------------------

class EmbedContentModal(discord.ui.Modal, title="Embed content"):
    embed_title = discord.ui.TextInput(label="Title", required=False, max_length=256)
    description = discord.ui.TextInput(
        label="Description", style=discord.TextStyle.paragraph, required=False, max_length=4000
    )
    color = discord.ui.TextInput(label="Color hex (e.g. #5865F2)", required=False, max_length=7)
    image_url = discord.ui.TextInput(label="Image URL", required=False)
    footer = discord.ui.TextInput(label="Footer text", required=False, max_length=2048)

    def __init__(self, builder: "EmbedBuilderView"):
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction):
        e = self.builder.embed
        e.title = self.embed_title.value or None
        e.description = self.description.value or None
        if self.color.value:
            try:
                e.color = discord.Color(int(self.color.value.lstrip("#"), 16))
            except ValueError:
                pass
        if self.image_url.value:
            e.set_image(url=self.image_url.value)
        if self.footer.value:
            e.set_footer(text=self.footer.value)
        await self.builder.refresh(interaction)


class AddButtonModal(discord.ui.Modal, title="Add a button"):
    label = discord.ui.TextInput(label="Button label", max_length=80)
    url = discord.ui.TextInput(label="Button URL", placeholder="https://...")

    def __init__(self, builder: "EmbedBuilderView"):
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction):
        if len(self.builder.link_buttons) >= 5:
            embed = discord.Embed(description="Max 5 buttons.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return
        self.builder.link_buttons.append((self.label.value, self.url.value))
        await self.builder.refresh(interaction)


class EmbedBuilderView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=600)
        self.author_id = author_id
        self.embed = discord.Embed(description="Use *Edit content* to fill this embed in.")
        self.link_buttons: list[tuple[str, str]] = []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    async def refresh(self, interaction: discord.Interaction):
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=self.embed, view=self)
        else:
            await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="Edit content", style=discord.ButtonStyle.primary, row=0)
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedContentModal(self))

    @discord.ui.button(label="Add button", style=discord.ButtonStyle.secondary, row=0)
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddButtonModal(self))

    @discord.ui.button(label="Send", style=discord.ButtonStyle.success, row=1)
    async def send(self, interaction: discord.Interaction, button: discord.ui.Button):
        final_view = discord.ui.View()
        for label, url in self.link_buttons:
            final_view.add_item(discord.ui.Button(label=label, url=url))
        await interaction.channel.send(embed=self.embed, view=final_view if self.link_buttons else None)
        embed = discord.Embed(description="Sent.", color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(description="Cancelled.", color=discord.Color.light_grey())
        await interaction.response.edit_message(embed=embed, view=None)
