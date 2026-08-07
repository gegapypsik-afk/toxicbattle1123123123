"""Админ-панель: /admin.

Панель доступна серверным администраторам, а также участникам с ролями,
которые заданы через саму панель («Настройка ролей»). Настройки хранятся
в data/config.json по каждому серверу отдельно.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import storage

PANEL_TIMEOUT = 180  # секунды жизни эфемерной панели


def is_admin(interaction: discord.Interaction) -> bool:
    """True, если пользователь — админ сервера или имеет настроенную роль."""
    member = interaction.user
    if not isinstance(member, discord.Member) or interaction.guild is None:
        return False
    if member.guild_permissions.administrator:
        return True
    admin_roles = set(storage.get_guild_config(interaction.guild.id)["admin_roles"])
    return any(role.id in admin_roles for role in member.roles)


async def deny(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "⛔ У вас нет доступа к админ-панели.", ephemeral=True
    )


# --------------------------------------------------------------------------- #
# Настройка ролей
# --------------------------------------------------------------------------- #

class AdminRoleSelect(discord.ui.RoleSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Выберите роли с доступом к админ-панели…",
            min_values=0,
            max_values=25,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        role_ids = [role.id for role in self.values]
        storage.set_admin_roles(interaction.guild.id, role_ids)
        if self.values:
            mentions = ", ".join(role.mention for role in self.values)
            text = f"✅ Роли с доступом к админ-панели обновлены: {mentions}"
        else:
            text = (
                "✅ Список ролей очищен. Теперь панель доступна только серверным "
                "администраторам."
            )
        await interaction.response.edit_message(content=text, embed=None, view=None)


class RoleConfigView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=PANEL_TIMEOUT)
        self.add_item(AdminRoleSelect())


# --------------------------------------------------------------------------- #
# Настройка канала регистраций
# --------------------------------------------------------------------------- #

class RegistrationChannelSelect(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Выберите канал для новых заявок…",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.values:
            channel = self.values[0]
            storage.set_registration_channel(interaction.guild.id, channel.id)
            text = f"✅ Заявки теперь публикуются в {channel.mention}."
        else:
            storage.set_registration_channel(interaction.guild.id, None)
            text = "✅ Канал регистраций отключён."
        await interaction.response.edit_message(content=text, embed=None, view=None)


class ChannelConfigView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=PANEL_TIMEOUT)
        self.add_item(RegistrationChannelSelect())


# --------------------------------------------------------------------------- #
# Сама панель
# --------------------------------------------------------------------------- #

class AdminPanelView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=PANEL_TIMEOUT)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if is_admin(interaction):
            return True
        await deny(interaction)
        return False

    @discord.ui.button(
        label="Настройка ролей", emoji="⚙️", style=discord.ButtonStyle.primary
    )
    async def configure_roles(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        cfg = storage.get_guild_config(interaction.guild.id)
        current = cfg["admin_roles"]
        if current:
            mentions = ", ".join(f"<@&{rid}>" for rid in current)
            description = f"Сейчас доступ имеют роли: {mentions}"
        else:
            description = (
                "Сейчас доступ к панели есть только у серверных администраторов.\n"
                "Выберите роли ниже, чтобы выдать им доступ."
            )
        embed = discord.Embed(
            title="⚙️ Настройка ролей админ-панели",
            description=description,
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(
            embed=embed, view=RoleConfigView(), ephemeral=True
        )

    @discord.ui.button(
        label="Канал регистраций", emoji="📢", style=discord.ButtonStyle.secondary
    )
    async def configure_channel(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        cfg = storage.get_guild_config(interaction.guild.id)
        channel_id = cfg.get("registration_channel_id")
        if channel_id:
            description = f"Текущий канал заявок: <#{channel_id}>"
        else:
            description = "Канал заявок пока не выбран."
        embed = discord.Embed(
            title="📢 Канал регистраций",
            description=f"{description}\n\nВыберите канал, куда будут приходить "
            "новые заявки с /battle.",
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(
            embed=embed, view=ChannelConfigView(), ephemeral=True
        )

    @discord.ui.button(
        label="Заявки", emoji="📋", style=discord.ButtonStyle.secondary
    )
    async def show_registrations(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        registrations = storage.get_registrations(interaction.guild.id)
        embed = discord.Embed(
            title="📋 Заявки на Toxic Battle",
            color=discord.Color.dark_red(),
        )
        if not registrations:
            embed.description = "Заявок пока нет."
        else:
            embed.description = f"Всего заявок: **{len(registrations)}**"
            for entry in registrations[-5:]:
                embed.add_field(
                    name=f"{entry['nickname']} · {entry['age']} лет",
                    value=f"{entry['experience']}\n— {entry['user_tag']}",
                    inline=False,
                )
            if len(registrations) > 5:
                embed.set_footer(text="Показаны последние 5 заявок.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="admin", description="Открыть админ-панель Toxic Battle")
    @app_commands.guild_only()
    async def admin(self, interaction: discord.Interaction) -> None:
        if not is_admin(interaction):
            await deny(interaction)
            return
        embed = discord.Embed(
            title="🛠️ Админ-панель Toxic Battle",
            description=(
                "Управляйте настройками бота:\n"
                "⚙️ **Настройка ролей** — кто имеет доступ к этой панели.\n"
                "📢 **Канал регистраций** — куда публиковать новые заявки.\n"
                "📋 **Заявки** — посмотреть поданные заявки."
            ),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(
            embed=embed, view=AdminPanelView(), ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
