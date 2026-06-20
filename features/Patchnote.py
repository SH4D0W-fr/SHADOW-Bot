import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import logging

from modules.I18n import t


# Couleurs disponibles pour l'embed du patch note
PATCHNOTE_COLORS = {
    "green":   {"emoji": "🟢", "color": discord.Color.green()},
    "red":     {"emoji": "🔴", "color": discord.Color.red()},
    "blue":    {"emoji": "🔵", "color": discord.Color.blue()},
    "gold":    {"emoji": "🟡", "color": discord.Color.gold()},
    "orange":  {"emoji": "🟠", "color": discord.Color.orange()},
    "purple":  {"emoji": "🟣", "color": discord.Color.purple()},
    "blurple": {"emoji": "💜", "color": discord.Color.blurple()},
    "dark":    {"emoji": "⚫", "color": discord.Color.dark_theme()},
}

DEFAULT_COLOR_KEY = "blurple"


def _format_section(raw: str | None) -> str | None:
    """Transforme un texte multi-lignes en liste à puces, ou None si vide."""
    if not raw:
        return None
    lines = [line.strip(" -•\t") for line in raw.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return None
    return "\n".join(f"- {line}" for line in lines)


class PatchnoteModal(discord.ui.Modal):
    def __init__(self, color_key: str):
        super().__init__(title=t("patchnote.modal.title", "Créer un patch note"))
        self.color_key = color_key

        self.titre = discord.ui.TextInput(
            label=t("patchnote.modal.title_field", "Titre"),
            placeholder=t("patchnote.modal.title_placeholder", "Mise à jour v1.0.0"),
            required=False,
            max_length=256,
        )
        self.ajouts = discord.ui.TextInput(
            label=t("patchnote.modal.additions_field", "Ajouts"),
            placeholder=t("patchnote.modal.line_placeholder", "Un élément par ligne"),
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1024,
        )
        self.fix = discord.ui.TextInput(
            label=t("patchnote.modal.fixes_field", "Corrections"),
            placeholder=t("patchnote.modal.line_placeholder", "Un élément par ligne"),
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1024,
        )
        self.retraits = discord.ui.TextInput(
            label=t("patchnote.modal.removals_field", "Retraits"),
            placeholder=t("patchnote.modal.line_placeholder", "Un élément par ligne"),
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1024,
        )

        self.add_item(self.titre)
        self.add_item(self.ajouts)
        self.add_item(self.fix)
        self.add_item(self.retraits)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ajouts = _format_section(self.ajouts.value)
            fixes = _format_section(self.fix.value)
            retraits = _format_section(self.retraits.value)

            if not any([ajouts, fixes, retraits]):
                await interaction.response.send_message(
                    t("patchnote.empty", "❌ Vous devez renseigner au moins une section (ajouts, corrections ou retraits)."),
                    ephemeral=True,
                )
                return

            color = PATCHNOTE_COLORS.get(self.color_key, PATCHNOTE_COLORS[DEFAULT_COLOR_KEY])["color"]
            titre = self.titre.value.strip() or t("patchnote.embed.default_title", "📝 Patch Note")

            embed = discord.Embed(
                title=titre,
                color=color,
                timestamp=datetime.now(),
            )

            if ajouts:
                embed.add_field(name=t("patchnote.embed.additions_field", "✨ Ajouts"), value=ajouts, inline=False)
            if fixes:
                embed.add_field(name=t("patchnote.embed.fixes_field", "🛠️ Corrections"), value=fixes, inline=False)
            if retraits:
                embed.add_field(name=t("patchnote.embed.removals_field", "🗑️ Retraits"), value=retraits, inline=False)

            embed.set_footer(text=t("patchnote.embed.footer", "Publié par {user}", user=interaction.user.display_name))

            await interaction.channel.send(embed=embed)
            await interaction.response.send_message(
                t("patchnote.success", "✅ Patch note publié !"),
                ephemeral=True,
            )
            logging.info(f"Patch note publié par {interaction.user} dans le canal {interaction.channel.id}")

        except Exception as e:
            logging.error(f"Erreur lors de la publication du patch note : {str(e)}")
            error_message = t("patchnote.generic_error", "❌ Erreur : {error}", error=str(e))
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)


class PatchnoteColorSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=t(f"patchnote.colors.{key}", key.capitalize()),
                value=key,
                emoji=data["emoji"],
            )
            for key, data in PATCHNOTE_COLORS.items()
        ]
        super().__init__(
            placeholder=t("patchnote.color_placeholder", "Choisissez la couleur de l'embed"),
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PatchnoteModal(self.values[0]))


class PatchnoteColorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(PatchnoteColorSelect())


class PatchnoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="patchnote", description=t("patchnote.commands.description", "Crée et publie un patch note"))
    @app_commands.checks.has_permissions(manage_guild=True)
    async def patchnote(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            t("patchnote.color_prompt", "🎨 Choisissez la couleur de l'embed, puis remplissez le patch note :"),
            view=PatchnoteColorView(),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PatchnoteCog(bot))
