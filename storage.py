"""Простое хранилище настроек и регистраций на JSON-файлах.

Данные хранятся в каталоге ``data/`` рядом с этим модулем:
    * ``config.json``        — настройки по серверам (роли админ-панели и т.п.);
    * ``registrations.json`` — заявки, поданные через команду ``/battle``.

Формат прост и человекочитаем — этого достаточно для первой версии бота.
Для постоянного хранения на Railway подключите том (volume), примонтированный
к каталогу ``data/`` (иначе файлы обнуляются при каждом деплое).
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
REGISTRATIONS_PATH = os.path.join(DATA_DIR, "registrations.json")

# JSON-файлы читаются/пишутся из одного event loop, но блокировка защищает от
# гонок, если в будущем появятся фоновые задачи в отдельных потоках.
_lock = threading.Lock()


def _read(path: str, default: dict[str, Any]) -> dict[str, Any]:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(path):
        return json.loads(json.dumps(default))  # свежая копия default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return json.loads(json.dumps(default))


def _write(path: str, data: dict[str, Any]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # атомарная замена, чтобы не оставить битый файл


# --------------------------------------------------------------------------- #
# Настройки сервера
# --------------------------------------------------------------------------- #

def _default_guild_config() -> dict[str, Any]:
    return {"admin_roles": [], "registration_channel_id": None}


def get_guild_config(guild_id: int) -> dict[str, Any]:
    """Вернуть настройки сервера (со значениями по умолчанию)."""
    data = _read(CONFIG_PATH, {"guilds": {}})
    cfg = data.get("guilds", {}).get(str(guild_id), {})
    merged = _default_guild_config()
    merged.update(cfg)
    return merged


def set_admin_roles(guild_id: int, role_ids: list[int]) -> None:
    """Сохранить список ролей, имеющих доступ к админ-панели."""
    with _lock:
        data = _read(CONFIG_PATH, {"guilds": {}})
        guilds = data.setdefault("guilds", {})
        guild = guilds.setdefault(str(guild_id), _default_guild_config())
        guild["admin_roles"] = [int(r) for r in role_ids]
        _write(CONFIG_PATH, data)


def set_registration_channel(guild_id: int, channel_id: int | None) -> None:
    """Сохранить канал, куда публикуются новые заявки."""
    with _lock:
        data = _read(CONFIG_PATH, {"guilds": {}})
        guilds = data.setdefault("guilds", {})
        guild = guilds.setdefault(str(guild_id), _default_guild_config())
        guild["registration_channel_id"] = int(channel_id) if channel_id else None
        _write(CONFIG_PATH, data)


# --------------------------------------------------------------------------- #
# Регистрации на батл
# --------------------------------------------------------------------------- #

def add_registration(guild_id: int, entry: dict[str, Any]) -> None:
    """Добавить заявку участника для указанного сервера."""
    with _lock:
        data = _read(REGISTRATIONS_PATH, {"guilds": {}})
        guilds = data.setdefault("guilds", {})
        guilds.setdefault(str(guild_id), []).append(entry)
        _write(REGISTRATIONS_PATH, data)


def get_registrations(guild_id: int) -> list[dict[str, Any]]:
    """Вернуть все заявки указанного сервера."""
    data = _read(REGISTRATIONS_PATH, {"guilds": {}})
    return data.get("guilds", {}).get(str(guild_id), [])
