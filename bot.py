"""Точка входа Discord-бота Toxic Battle.

Запуск локально:
    1. Скопируйте .env.example в .env и впишите DISCORD_TOKEN.
    2. pip install -r requirements.txt
    3. python bot.py

Запуск на Railway:
    Процесс описан в Procfile (`worker: python -u bot.py`).
    Переменную DISCORD_TOKEN задайте в разделе Variables проекта Railway.
"""

from __future__ import annotations

import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger("toxicbattle")

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

INITIAL_EXTENSIONS = (
    "cogs.general",
    "cogs.battle",
    "cogs.admin",
)


class ToxicBattleBot(commands.Bot):
    def __init__(self) -> None:
        # Слэш-команды не требуют привилегированных интентов, поэтому берём
        # стандартный набор — так бот заработает без лишних настроек в Portal.
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        for extension in INITIAL_EXTENSIONS:
            await self.load_extension(extension)
            log.info("Загружено расширение: %s", extension)

        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Синхронизировано %d команд на сервере %s", len(synced), GUILD_ID)
        else:
            synced = await self.tree.sync()
            log.info("Синхронизировано %d глобальных команд", len(synced))

    async def on_ready(self) -> None:
        log.info("Бот запущен как %s (ID: %s)", self.user, getattr(self.user, "id", "?"))
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.competing,
                name="Toxic Battle ⚔️",
            )
        )


def main() -> None:
    if not TOKEN:
        raise SystemExit(
            "DISCORD_TOKEN не задан. Укажите переменную окружения DISCORD_TOKEN "
            "(локально — в файле .env, на Railway — в разделе Variables)."
        )
    bot = ToxicBattleBot()
    bot.run(TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
