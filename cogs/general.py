"""Общие команды: /помощь."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

ABOUT_TEXT = (
    "Смысл **Toxic Battle** — это пространство для неформального общения, шуток "
    "и лёгких провокаций. Здесь можно проявить креатив, посоревноваться и "
    "выпустить накопившийся пар.\n\n"
    "Хочется **высказаться** и дать волю фантазии? Мы ждём вас на батле — "
    "**запрещённых** слов и фраз здесь нет, никаких скучных **дискордовских** "
    "шаблонов.\n\n"
    "☝️ Но помните: уважение к другим участникам и правила общения никто не "
    "отменял ^^"
)


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="помощь",
        description="Информация о Toxic Battle и список команд",
    )
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="⚔️ Toxic Battle — помощь",
            description=ABOUT_TEXT,
            color=discord.Color.dark_red(),
        )
        embed.add_field(
            name="/помощь",
            value="Показать это сообщение.",
            inline=False,
        )
        embed.add_field(
            name="/battle",
            value="Зарегистрироваться на Toxic Battle (никнейм, возраст, опыт).",
            inline=False,
        )
        embed.add_field(
            name="/admin",
            value="Админ-панель: настройка ролей и просмотр заявок "
            "(только для администраторов).",
            inline=False,
        )
        embed.set_footer(text="Уважайте друг друга ^^")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
