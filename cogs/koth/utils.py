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

class TitleModal(discord.ui.Modal, title="Set Title"):
    value = discord.ui.TextInput(label="Title", max_length=256)

    def __init__(self, builder: "EmbedBuilderView"):
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction):
        self.builder.embed.title = self.value.value
        await interaction.response.defer()
        await self.builder.update_preview()


class DescriptionModal(discord.ui.Modal, title="Set Description"):
    value = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=4000)

    def __init__(self, builder: "EmbedBuilderView"):
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction):
        self.builder.embed.description = self.value.value
        await interaction.response.defer()
        await self.builder.update_preview()


class BannerModal(discord.ui.Modal, title="Set Banner Image"):
    value = discord.ui.TextInput(label="Image URL", placeholder="https://...")

    def __init__(self, builder: "EmbedBuilderView"):
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction):
        self.builder.embed.set_image(url=self.value.value)
        await interaction.response.defer()
        await self.builder.update_preview()


class FooterModal(discord.ui.Modal, title="Set Footer"):
    value = discord.ui.TextInput(label="Footer text", max_length=2048)

    def __init__(self, builder: "EmbedBuilderView"):
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction):
        self.builder.embed.set_footer(text=self.value.value)
        await interaction.response.defer()
        await self.builder.update_preview()


class ColorModal(discord.ui.Modal, title="Set Color"):
    value = discord.ui.TextInput(label="Hex color (e.g. #5865F2)", max_length=7)

    def __init__(self, builder: "EmbedBuilderView"):
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.builder.embed.color = discord.Color(int(self.value.value.lstrip("#"), 16))
        except ValueError:
            pass
        await interaction.response.defer()
        await self.builder.update_preview()


class AddLinkButtonModal(discord.ui.Modal, title="Add a button"):
    label = discord.ui.TextInput(label="Button label", max_length=80)
    url = discord.ui.TextInput(label="Button URL", placeholder="https://...")

    def __init__(self, builder: "EmbedBuilderView"):
        super().__init__()
        self.builder = builder

    async def on_submit(self, interaction: discord.Interaction):
        if len(self.builder.link_buttons) >= 5:
            await interaction.response.send_message("Max 5 buttons.", ephemeral=True)
            return
        self.builder.link_buttons.append((self.label.value, self.url.value))
        await interaction.response.defer()
        await self.builder.update_preview()


class EmbedBuilderView(discord.ui.View):
    def __init__(self, author_id: int, default_channel: discord.TextChannel = None):
        super().__init__(timeout=600)
        self.author_id = author_id
        self.embed = discord.Embed(description="This message will be updated as we use the builder")
        self.link_buttons: list[tuple[str, str]] = []
        self.target_channel: discord.TextChannel = default_channel
        self.preview_message: discord.WebhookMessage | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    async def update_preview(self):
        if self.preview_message is None:
            return

        footer_note = f"Will send to: #{self.target_channel.name}" if self.target_channel else "No channel selected"
        preview = self.embed.copy()
        base_footer = preview.footer.text
        preview.set_footer(text=f"{base_footer}  •  {footer_note}" if base_footer else footer_note)

        preview_buttons_view = None
        if self.link_buttons:
            preview_buttons_view = discord.ui.View()
            for label, url in self.link_buttons:
                preview_buttons_view.add_item(discord.ui.Button(label=label, url=url))

        await self.preview_message.edit(embed=preview, view=preview_buttons_view)

    @discord.ui.button(label="Title", style=discord.ButtonStyle.primary, row=0)
    async def set_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TitleModal(self))

    @discord.ui.button(label="Description", style=discord.ButtonStyle.primary, row=0)
    async def set_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DescriptionModal(self))

    @discord.ui.button(label="Banner", style=discord.ButtonStyle.primary, row=0)
    async def set_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BannerModal(self))

    @discord.ui.button(label="Footer", style=discord.ButtonStyle.primary, row=0)
    async def set_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FooterModal(self))

    @discord.ui.button(label="Color", style=discord.ButtonStyle.secondary, row=1)
    async def set_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorModal(self))

    @discord.ui.button(label="Add Button", style=discord.ButtonStyle.secondary, row=1)
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddLinkButtonModal(self))

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Channel",
        row=2,
    )
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.target_channel = interaction.guild.get_channel(select.values[0].id)
        await interaction.response.defer()
        await self.update_preview()

    @discord.ui.button(label="Send", style=discord.ButtonStyle.success, row=3)
    async def send(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.target_channel is None:
            await interaction.response.send_message("Please select a channel first.", ephemeral=True)
            return

        final_view = None
        if self.link_buttons:
            final_view = discord.ui.View()
            for label, url in self.link_buttons:
                final_view.add_item(discord.ui.Button(label=label, url=url))

        await self.target_channel.send(embed=self.embed, view=final_view)

        confirm_embed = discord.Embed(description=f"Sent to {self.target_channel.mention}.", color=discord.Color.green())
        await interaction.response.edit_message(embed=confirm_embed, view=None)
        if self.preview_message:
            await self.preview_message.edit(embed=confirm_embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=3)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        cancel_embed = discord.Embed(description="Cancelled.", color=discord.Color.light_grey())
        await interaction.response.edit_message(embed=cancel_embed, view=None)
        if self.preview_message:
            await self.preview_message.edit(embed=cancel_embed, view=None)
