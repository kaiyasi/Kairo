import discord
from discord.ext import commands
from discord import app_commands
from utils.brand import create_brand_embed, create_success_embed, create_error_embed
from utils.tenant import tenant_db
from utils.visibility import is_super_admin
import os

REVIEW_CHANNEL_ID = int(os.getenv('REVIEW_CHANNEL_ID', '1416406590411509860'))

class ModulesAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    module_choices = [
        app_commands.Choice(name='attendance', value='attendance'),
        app_commands.Choice(name='plans', value='plans'),
        app_commands.Choice(name='qa', value='qa'),
        app_commands.Choice(name='crypto', value='crypto'),
        app_commands.Choice(name='bookkeeping', value='bookkeeping'),
        app_commands.Choice(name='ctfd', value='ctfd'),
        app_commands.Choice(name='routing', value='routing'),
    ]

    async def update_guild_status_embed(self, guild_id: int, status: str, reason: str = None):
        """Update the status embed in the guild"""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        registration = tenant_db.get_registration_status(guild_id)
        if not registration:
            return

        status_text = {
            'pending': '🟡 審核中 (pending)',
            'approved': '🟢 已通過 (approved)',
            'needs_more_info': '🟠 需要補充資訊 (needs_more_info)',
            'declined': '🔴 已拒絕 (declined)'
        }.get(status, status)

        description = f"**狀態：** {status_text}\n\n"
        if reason:
            description += f"**說明：** {reason}\n\n"

        if status == 'approved':
            description += "恭喜！您的申請已通過，現在可以使用 Kairo 的所有功能。"
        elif status == 'needs_more_info':
            description += "請使用 `/response` 指令提供補充資訊。"
        elif status == 'declined':
            description += "很遺憾，您的申請未通過。如有疑問請聯繫管理員。"

        status_embed = create_brand_embed(
            title="📝 註冊申請狀態",
            description=description,
            guild_name=guild.name
        )

        status_embed.add_field(name="申請資訊", value=f"""
**學校：** {registration.get('school', 'N/A')}
**社團：** {registration.get('club_name', 'N/A')}
**負責人：** {registration.get('responsible_person', 'N/A')}
**類型：** {registration.get('club_type', 'N/A')}
""", inline=False)

        # Try to find and update existing status message
        # For simplicity, we'll send to the system channel or first text channel
        target_channel = guild.system_channel
        if not target_channel:
            target_channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)

        if target_channel:
            await target_channel.send(embed=status_embed)

    @app_commands.command(name="register_accept", description="通過社團註冊申請")
    @app_commands.describe(guild_id="要通過的 Guild ID")
    async def register_accept(self, interaction: discord.Interaction, guild_id: str):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        try:
            gid = int(guild_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 錯誤",
                    description="無效的 Guild ID。"
                ),
                ephemeral=True
            )
            return

        # Update status
        tenant_db.set_registration_status(gid, 'approved')
        tenant_db.enable_default_modules(gid)

        await interaction.response.send_message(
            embed=create_success_embed(
                title="✅ 申請已通過",
                description=f"Guild {gid} 的註冊申請已通過，預設模組已啟用。"
            )
        )

        # Update guild status
        await self.update_guild_status_embed(gid, 'approved')

        # Sync commands for that guild
        await self.bot.sync_commands_for_guild(gid)

    @app_commands.command(name="register_reject_response", description="要求社團補充資訊")
    @app_commands.describe(
        guild_id="要要求補件的 Guild ID",
        reason="需要補充的資訊說明"
    )
    async def register_reject_response(self, interaction: discord.Interaction, guild_id: str, reason: str):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        try:
            gid = int(guild_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 錯誤",
                    description="無效的 Guild ID。"
                ),
                ephemeral=True
            )
            return

        # Update status
        tenant_db.set_registration_status(gid, 'needs_more_info', reason)

        await interaction.response.send_message(
            embed=create_success_embed(
                title="📝 已要求補件",
                description=f"Guild {gid} 需要補充資訊：{reason}"
            )
        )

        # Update guild status
        await self.update_guild_status_embed(gid, 'needs_more_info', reason)

        # Sync commands for that guild
        await self.bot.sync_commands_for_guild(gid)

    @app_commands.command(name="register_decline", description="拒絕社團註冊申請")
    @app_commands.describe(
        guild_id="要拒絕的 Guild ID",
        reason="拒絕原因"
    )
    async def register_decline(self, interaction: discord.Interaction, guild_id: str, reason: str):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        try:
            gid = int(guild_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 錯誤",
                    description="無效的 Guild ID。"
                ),
                ephemeral=True
            )
            return

        # Update status
        tenant_db.set_registration_status(gid, 'declined', reason)

        await interaction.response.send_message(
            embed=create_success_embed(
                title="❌ 申請已拒絕",
                description=f"Guild {gid} 的申請已拒絕：{reason}"
            )
        )

        # Update guild status
        await self.update_guild_status_embed(gid, 'declined', reason)

        # Sync commands for that guild
        await self.bot.sync_commands_for_guild(gid)

    @app_commands.command(name="modules_enable", description="為社團啟用模組")
    @app_commands.describe(
        guild_id="Guild ID",
        module="模組名稱"
    )
    @app_commands.choices(module=module_choices)
    async def modules_enable(self, interaction: discord.Interaction, guild_id: str, module: str):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        try:
            gid = int(guild_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 錯誤",
                    description="無效的 Guild ID。"
                ),
                ephemeral=True
            )
            return

        tenant_db.set_module_enabled(gid, module, True)

        await interaction.response.send_message(
            embed=create_success_embed(
                title="✅ 模組已啟用",
                description=f"Guild {gid} 的 {module} 模組已啟用。"
            )
        )

        # Sync commands for that guild
        await self.bot.sync_commands_for_guild(gid)

    @app_commands.command(name="modules_disable", description="為社團停用模組")
    @app_commands.describe(
        guild_id="Guild ID",
        module="模組名稱"
    )
    @app_commands.choices(module=module_choices)
    async def modules_disable(self, interaction: discord.Interaction, guild_id: str, module: str):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        try:
            gid = int(guild_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 錯誤",
                    description="無效的 Guild ID。"
                ),
                ephemeral=True
            )
            return

        tenant_db.set_module_enabled(gid, module, False)

        await interaction.response.send_message(
            embed=create_success_embed(
                title="🔒 模組已停用",
                description=f"Guild {gid} 的 {module} 模組已停用。"
            )
        )

        # Sync commands for that guild
        await self.bot.sync_commands_for_guild(gid)

    @app_commands.command(name="modules_list", description="查看社團的模組狀態")
    @app_commands.describe(guild_id="Guild ID")
    async def modules_list(self, interaction: discord.Interaction, guild_id: str):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        try:
            gid = int(guild_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 錯誤",
                    description="無效的 Guild ID。"
                ),
                ephemeral=True
            )
            return

        enabled_modules = tenant_db.get_enabled_modules(gid)
        all_modules = ['attendance', 'plans', 'qa', 'crypto', 'bookkeeping', 'ctfd', 'routing']

        module_status = []
        for module in all_modules:
            status = "✅" if module in enabled_modules else "❌"
            module_status.append(f"{status} {module}")

        embed = create_brand_embed(
            title=f"🔧 Guild {gid} 模組狀態",
            description="\n".join(module_status)
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="register_list", description="列出所有註冊申請")
    async def register_list(self, interaction: discord.Interaction):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        import sqlite3

        with sqlite3.connect("data/tenant.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT guild_id, status, school, club_name, responsible_person,
                       responsible_discord_id, club_type, applied_at, reason
                FROM registration_status
                ORDER BY applied_at DESC
"""
            )
            registrations = cursor.fetchall()

        if not registrations:
            embed = create_brand_embed(
                title="📋 註冊申請列表",
                description="目前沒有註冊申請。"
            )
        else:
            embed = create_brand_embed(
                title="📋 註冊申請列表",
                description=f"共 {len(registrations)} 筆申請"
            )

            for reg in registrations[:5]:  # 只顯示前5筆，避免太長
                status_emoji = {
                    'pending': '🟡',
                    'approved': '🟢',
                    'needs_more_info': '🟠',
                    'declined': '🔴',
                    'none': '⚪'
                }.get(reg['status'], '❓')

                guild_info = f"**Guild:** {reg['guild_id']}\n"
                if reg['school']:
                    guild_info += f"**學校：** {reg['school']}\n"
                if reg['club_name']:
                    guild_info += f"**社團：** {reg['club_name']}\n"
                if reg['responsible_person']:
                    guild_info += f"**負責人：** {reg['responsible_person']}\n"
                if reg['reason']:
                    guild_info += f"**備註：** {reg['reason']}"

                embed.add_field(
                    name=f"{status_emoji} {reg['status'].upper()}",
                    value=guild_info,
                    inline=True
                )

            if len(registrations) > 5:
                embed.add_field(
                    name="📄 更多記錄",
                    value=f"還有 {len(registrations) - 5} 筆申請...",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="commands_list", description="列出所有已載入的指令")
    async def commands_list(self, interaction: discord.Interaction):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        embed = create_brand_embed(
            title="🤖 Kairo 指令列表",
            description="以下是所有已載入的指令，按模組分類："
        )

        # 統計所有指令
        total_commands = 0

        for cog_name, cog in self.bot.cogs.items():
            commands = []
            for command in cog.__cog_app_commands__:
                commands.append(f"`/{command.name}`")
                total_commands += 1

            if commands:
                # 模組名稱對應
                display_names = {
                    'RegisterCog': '📝 註冊系統',
                    'ResponseCog': '📄 補件回應',
                    'ModulesAdminCog': '⚙️ 管理員',
                    'AttendanceCog': '✅ 簽到系統',
                    'PlansCog': '📅 週計劃',
                    'QACog': '🧠 問答系統',
                    'CTFdCog': '🚩 CTFd 整合',
                    'CryptoCog': '🔐 加解密',
                    'BookkeepingCog': '💰 記帳系統',
                    'RoutingCog': '📡 頻道路由'
                }

                display_name = display_names.get(cog_name, cog_name)
                commands_text = " ".join(commands)

                embed.add_field(
                    name=display_name,
                    value=commands_text if len(commands_text) <= 1024 else f"{commands_text[:1020]}...",
                    inline=False
                )

        embed.add_field(
            name="📊 統計",
            value=f"總共 **{total_commands}** 個指令，分佈在 **{len([c for c in self.bot.cogs.values() if c.__cog_app_commands__])}** 個模組中。",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="commands_check", description="檢查特定 Guild 的可見指令")
    @app_commands.describe(guild_id="要檢查的 Guild ID")
    async def commands_check(self, interaction: discord.Interaction, guild_id: str):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        try:
            gid = int(guild_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 錯誤",
                    description="無效的 Guild ID。"
                ),
                ephemeral=True
            )
            return

        from utils.visibility import get_visible_commands_for_guild
        from utils.tenant import tenant_db

        # 取得 guild 資訊
        guild = self.bot.get_guild(gid)
        guild_name = guild.name if guild else f"Guild {gid}"

        # 取得註冊狀態
        registration = tenant_db.get_registration_status(gid)
        status = registration.get('status', 'none') if registration else 'none'

        # 取得可見指令
        visible_commands = get_visible_commands_for_guild(gid)

        # 取得已啟用模組
        enabled_modules = tenant_db.get_enabled_modules(gid)

        embed = create_brand_embed(
            title=f"🔍 Guild 指令檢查",
            description=f"**Guild：** {guild_name} (`{gid}`)"
        )

        # 註冊狀態
        status_emoji = {
            'none': '⚪ 未註冊',
            'pending': '🟡 審核中',
            'approved': '🟢 已通過',
            'needs_more_info': '🟠 需補件',
            'declined': '🔴 已拒絕'
        }.get(status, f'❓ {status}')

        embed.add_field(
            name="📋 註冊狀態",
            value=status_emoji,
            inline=True
        )

        # 啟用模組
        if enabled_modules:
            modules_text = "、".join(enabled_modules)
            embed.add_field(
                name="🔧 啟用模組",
                value=modules_text,
                inline=True
            )
        else:
            embed.add_field(
                name="🔧 啟用模組",
                value="無",
                inline=True
            )

        # 可見指令
        if visible_commands:
            commands_text = "、".join([f"`/{cmd}`" for cmd in visible_commands])
            if len(commands_text) > 1024:
                commands_text = commands_text[:1020] + "..."
            embed.add_field(
                name=f"👁️ 可見指令 ({len(visible_commands)} 個)",
                value=commands_text,
                inline=False
            )
        else:
            embed.add_field(
                name="👁️ 可見指令",
                value="無可見指令",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="commands_sync", description="強制重新同步指令")
    @app_commands.describe(guild_id="要同步的 Guild ID（留空同步所有）")
    async def commands_sync(self, interaction: discord.Interaction, guild_id: str = None):
        if not is_super_admin(interaction.user.id):
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有超級管理員可以使用此指令。"
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer()

        if guild_id:
            try:
                gid = int(guild_id)
                guild = self.bot.get_guild(gid)
                if guild:
                    await self.bot.sync_commands_for_guild(gid)
                    embed = create_success_embed(
                        title="✅ 指令同步完成",
                        description=f"已重新同步 Guild {guild.name} (`{gid}`) 的指令。"
                    )
                else:
                    embed = create_error_embed(
                        title="❌ Guild 不存在",
                        description=f"找不到 Guild {gid}。"
                    )
            except ValueError:
                embed = create_error_embed(
                    title="❌ 錯誤",
                    description="無效的 Guild ID。"
                )
        else:
            # 同步所有 guild
            synced_count = 0
            for guild in self.bot.guilds:
                try:
                    await self.bot.sync_commands_for_guild(guild.id)
                    synced_count += 1
                except Exception as e:
                    print(f"同步 Guild {guild.id} 失敗: {e}")

            # 同步管理員 guild
            try:
                await self.bot.sync_super_admin_commands_for_admin_guild()
            except Exception as e:
                print(f"同步管理員指令失敗: {e}")

            embed = create_success_embed(
                title="✅ 全域指令同步完成",
                description=f"已重新同步 {synced_count} 個 Guild 的指令和管理員指令。"
            )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModulesAdminCog(bot))