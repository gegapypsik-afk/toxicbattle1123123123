"""Команда /battle — регистрация участника через модальное окно."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import storage

log = logging.getLogger("toxicbattle.battle")


class RegistrationModal(discord.ui.Modal, title="Регистрация на Toxic Battle"):
    """Форма с тремя полями: никнейм, возраст и опыт участия в батлах."""

    nickname = discord.ui.TextInput(
        label="1. Никнейм",
        placeholder="Как вас называть на батле?",
        max_length=100,
        required=True,
    )
    age = discord.ui.TextInput(
        label="2. Возраст",
        placeholder="Только число, например 18",
        max_length=3,
        required=True,
    )
    experience = discord.ui.TextInput(
        label="3. Опыт участия в батлах",
        placeholder="Расскажите о своём опыте (или напишите, что вы новичок)",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        age_raw = self.age.value.strip()
        if not age_raw.isdigit() or not (1 <= int(age_raw) <= 120):
            await interaction.response.send_message(
                "❌ Возраст должен быть числом от 1 до 120. Попробуйте ещё раз "
                "через /battle.",
                ephemeral=True,
            )
            return

        entry = {
            "user_id": interaction.user.id,
            "user_tag": str(interaction.user),
            "nickname": self.nickname.value,
            "age": int(age_raw),
            "experience": self.experience.value,
            "timestamp": discord.utils.utcnow().isoformat(),
        }

        if interaction.guild is not None:
            storage.add_registration(interaction.guild.id, entry)

        confirm = discord.Embed(
            title="✅ Заявка принята!",
            description="Ваша регистрация на Toxic Battle сохранена.",
            color=discord.Color.green(),
        )
        confirm.add_field(name="1. Никнейм", value=self.nickname.value, inline=False)
        confirm.add_field(name="2. Возраст", value=str(int(age_raw)), inline=False)
        confirm.add_field(
            name="3. Опыт участия в батлах",
            value=self.experience.value,
            inline=False,
        )
        await interaction.response.send_message(embed=confirm, ephemeral=True)

        await self._notify_channel(interaction, entry)

    async def _notify_channel(
        self, interaction: discord.Interaction, entry: dict
    ) -> None:
        """Опубликовать заявку в настроенном канале регистраций (если задан)."""
        if interaction.guild is None:
            return
        cfg = storage.get_guild_config(interaction.guild.id)
        channel_id = cfg.get("registration_channel_id")
        if not channel_id:
            return
        channel = interaction.guild.get_channel(int(channel_id))
        if not isinstance(channel, discord.abc.Messageable):
            return

        notify = discord.Embed(
            title="📝 Новая заявка на Toxic Battle",
            color=discord.Color.dark_red(),
        )
        notify.add_field(name="1. Никнейм", value=entry["nickname"], inline=False)
        notify.add_field(name="2. Возраст", value=str(entry["age"]), inline=False)
        notify.add_field(
            name="3. Опыт участия в батлах",
            value=entry["experience"],
            inline=False,
        )
        notify.set_footer(text=f"От {entry['user_tag']}")
        try:
            await channel.send(embed=notify)
        except discord.DiscordException:
            log.warning("Не удалось отправить заявку в канал %s", channel_id)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        log.exception("Ошибка при обработке заявки", exc_info=error)
        message = "❌ Что-то пошло не так при отправке заявки. Попробуйте позже."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


class Battle(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="battle",
        description="Зарегистрироваться на Toxic Battle",
    )
    async def battle(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(RegistrationModal())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Battle(bot))
