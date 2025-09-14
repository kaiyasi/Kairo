import discord
from discord.ext import commands
from discord import app_commands
from utils.brand import create_brand_embed, create_success_embed, create_error_embed
from utils.tenant import tenant_db, AttendanceSettings
from datetime import datetime, timedelta
import sqlite3
import io
import secrets
import string
import asyncio
from typing import Optional, Literal


class SigninView(discord.ui.View):
    def __init__(self, session_id: int):
        super().__init__(timeout=None)
        self.session_id = session_id

    async def check_and_rename_nickname(self, interaction: discord.Interaction) -> bool:
        """Checks nickname against guild settings and renames if necessary."""
        member = interaction.user
        guild = interaction.guild

        settings = tenant_db.get_attendance_settings(guild.id)

        # 1. If renaming is disabled, pass the check
        if not settings.rename_enabled:
            return True

        # 2. Determine user's role and target format
        is_staff = False
        if settings.staff_role_id:
            staff_role = guild.get_role(settings.staff_role_id)
            if staff_role and staff_role in member.roles:
                is_staff = True

        target_format = settings.rename_format_staff if is_staff else settings.rename_format_member

        # 3. Construct the new nickname
        # Use member.name as a fallback if display_name is weird
        base_name = member.name 
        new_nickname = target_format.format(name=base_name)

        # 4. If nickname is already correct, pass the check
        if member.display_name == new_nickname:
            return True

        # 5. Attempt to rename
        try:
            await member.edit(nick=new_nickname)
            # Send a quiet confirmation
            await interaction.followup.send(
                embed=create_success_embed("✅ 暱稱已自動更新", f"您的暱稱已更新為 `{new_nickname}` 以符合伺服器規範。" ),
                ephemeral=True
            )
            return True
        except discord.Forbidden:
            await interaction.followup.send(
                embed=create_error_embed("❌ 權限不足", f"我無法將您的暱稱更新為 `{new_nickname}`，請聯繫管理員處理我的權限問題。" ),
                ephemeral=True
            )
            return False
        except Exception as e:
            await interaction.followup.send(
                embed=create_error_embed("❌ 更新暱稱時發生錯誤", str(e)),
                ephemeral=True
            )
            return False

    @discord.ui.button(label="簽到", style=discord.ButtonStyle.primary, emoji="✅")
    async def signin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Nickname check is the first step
        if not await self.check_and_rename_nickname(interaction):
            # Stop processing, error message was sent in the check function
            # We need to edit the original deferred response to stop the 'thinking' state
            await interaction.edit_original_response(content="簽到流程已中止。", embed=None, view=None)
            return

        # If nickname is valid, proceed to sign in
        await self.handle_signin(interaction)

    async def handle_signin(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        # Use the updated display_name
        username = interaction.user.display_name

        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.cursor()
            # Check if session is still active
            cursor.execute(
                "SELECT active, canva_url, outline FROM sessions WHERE id = ? AND guild_id = ?",
                (self.session_id, guild_id)
            )
            session = cursor.fetchone()

            if not session or not session[0]:
                embed = create_error_embed("❌ 簽到已結束", "此簽到場次已經結束。" )
                await interaction.edit_original_response(embed=embed, view=None)
                return

            # Check if already signed in
            cursor.execute(
                "SELECT 1 FROM records WHERE session_id = ? AND user_id = ?",
                (self.session_id, user_id)
            )
            if cursor.fetchone():
                embed = create_error_embed("⚠️ 已簽到", "您已經簽到過了。" )
                await interaction.edit_original_response(embed=embed, view=None)
                return

            # Record attendance
            cursor.execute(
                "INSERT INTO records (session_id, user_id, username) VALUES (?, ?, ?)",
                (self.session_id, user_id, username)
            )
            conn.commit()

        # Success response
        success_embed = create_success_embed(
            title="✅ 簽到成功",
            description=f"**{username}** 簽到成功！"
        )
        canva_url, outline = session[1], session[2]
        if canva_url or outline:
            extra_info = []
            if canva_url:
                extra_info.append(f"📊 **簡報：** [Canva]({canva_url})")
            if outline:
                extra_info.append(f"📝 **大綱：** {outline}")
            success_embed.add_field(name="課程資訊", value="\n".join(extra_info), inline=False)

        await interaction.edit_original_response(embed=success_embed, view=None)


class AttendanceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Settings Command Group ---
    attendance_settings = app_commands.Group(name="attendance_settings", description="設定簽到相關功能", default_permissions=discord.Permissions(manage_guild=True))

    @attendance_settings.command(name="set_enabled", description="啟用或停用簽到時的自動暱稱管理")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_rename_enabled(self, interaction: discord.Interaction, enabled: bool):
        tenant_db.set_attendance_setting(interaction.guild.id, 'attendance_rename_enabled', enabled)
        status = "啟用" if enabled else "停用"
        await interaction.response.send_message(
            embed=create_success_embed("✅ 設定已更新", f"簽到自動暱稱管理已 **{status}**。" ),
            ephemeral=True
        )

    @attendance_settings.command(name="set_staff_role", description="設定被視為「幹部」的身份組")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_staff_role(self, interaction: discord.Interaction, role: discord.Role):
        tenant_db.set_attendance_setting(interaction.guild.id, 'attendance_staff_role_id', role.id)
        await interaction.response.send_message(
            embed=create_success_embed("✅ 設定已更新", f"幹部身份組已設定為 {role.mention}。" ),
            ephemeral=True
        )

    @attendance_settings.command(name="set_format", description="設定社員/幹部的暱稱格式 (使用 {name} 作為名字變數)")
    @app_commands.describe(role_type="要設定格式的身份類別", format="暱稱格式，例如: 幹部 | {name}")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_format(self, interaction: discord.Interaction, role_type: Literal['社員', '幹部'], format: str):
        if '{name}' not in format:
            await interaction.response.send_message(
                embed=create_error_embed("❌ 格式錯誤", "格式字串中必須包含 `{name}` 變數。" ),
                ephemeral=True
            )
            return

        key = 'attendance_rename_format_staff' if role_type == '幹部' else 'attendance_rename_format_member'
        tenant_db.set_attendance_setting(interaction.guild.id, key, format)
        await interaction.response.send_message(
            embed=create_success_embed("✅ 設定已更新", f"**{role_type}** 的暱稱格式已更新為 `{format}`。" ),
            ephemeral=True
        )

    @attendance_settings.command(name="show", description="顯示目前的簽到設定")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def show_settings(self, interaction: discord.Interaction):
        settings = tenant_db.get_attendance_settings(interaction.guild.id)
        status = "✅ 啟用" if settings.rename_enabled else "❌ 停用"
        
        staff_role = interaction.guild.get_role(settings.staff_role_id) if settings.staff_role_id else None
        staff_role_mention = staff_role.mention if staff_role else "未設定"

        embed = create_brand_embed("⚙️ 目前簽到設定", "")
        embed.add_field(name="自動暱稱管理", value=status, inline=False)
        embed.add_field(name="幹部身份組", value=staff_role_mention, inline=False)
        embed.add_field(name="幹部暱稱格式", value=f"`{settings.rename_format_staff}`", inline=False)
        embed.add_field(name="社員暱稱格式", value=f"`{settings.rename_format_member}`", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- Original Commands ---
    @app_commands.command(name="signin_start", description="開始一個新的簽到活動")
    @app_commands.describe(minutes="簽到持續時間（分鐘）", canva_url="Canva簡報連結", outline="課程大綱")
    async def signin_start(self, interaction: discord.Interaction, minutes: int = 30, canva_url: str = None, outline: str = None):
        guild_id = interaction.guild.id
        code = ''.join(secrets.choice(string.digits) for _ in range(4))
        expire_at = datetime.now() + timedelta(minutes=minutes)

        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (guild_id, channel_id, code, expire_at, canva_url, outline) VALUES (?, ?, ?, ?, ?, ?)",
                (guild_id, interaction.channel.id, code, expire_at, canva_url, outline)
            )
            session_id = cursor.lastrowid
            conn.commit()

        embed = create_brand_embed(
            title="🎯 簽到開始",
            description=f"**簽到碼：** `{code}`\n**時限：** {minutes} 分鐘"
        )
        if canva_url:
            embed.add_field(name="📊 簡報", value=f"[Canva]({canva_url})", inline=False)
        if outline:
            embed.add_field(name="📝 大綱", value=outline, inline=False)

        view = SigninView(session_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="signin_end", description="結束當前的簽到活動")
    async def signin_end(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sessions WHERE guild_id = ? AND active = 1", (guild_id,))
            session = cursor.fetchone()

            if not session:
                await interaction.response.send_message(embed=create_error_embed("⚠️ 無進行中的簽到"), ephemeral=True)
                return

            session_id = session[0]
            conn.execute("UPDATE sessions SET active = 0 WHERE id = ?", (session_id,))
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM records WHERE session_id = ?", (session_id,))
            count = cursor.fetchone()[0]

        embed = create_success_embed("🏁 簽到已結束", f"本次簽到結束，共有 **{count}** 人簽到。" )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="signin_report", description="顯示最新簽到活動的詳細報告")
    async def signin_report(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id

        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sessions WHERE guild_id = ? ORDER BY id DESC LIMIT 1", (guild_id,))
            session = cursor.fetchone()

            if not session:
                await interaction.followup.send(embed=create_error_embed("⚠️ 無簽到記錄"), ephemeral=True)
                return

            session_id = session[0]
            cursor.execute("SELECT user_id, username, ts FROM records WHERE session_id = ? ORDER BY ts", (session_id,))
            records = cursor.fetchall()

        if not records:
            await interaction.followup.send(embed=create_error_embed("⚠️ 此場次無人簽到"), ephemeral=True)
            return

        report_content = "```md\n"
        report_content += '{:<20} | {:<25} | {}'.format('簽到時間', '暱稱', '使用者ID')
        report_content += "-" * 65 + "\n"
        for record in records:
            ts = datetime.fromisoformat(record[2]).strftime('%Y-%m-%d %H:%M:%S')
            report_content += f"{ts:<20} | {record[1]:<25} | {record[0]}\n"
        report_content += "```"

        embed = create_brand_embed(
            title=f"📋 簽到報告 (場次 #{session_id})",
            description=f"共 **{len(records)}** 人簽到。\n{report_content}"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="signin_summary", description="顯示最新簽到活動的摘要 (已簽到/未簽到)")
    async def signin_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild.id

        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sessions WHERE guild_id = ? ORDER BY id DESC LIMIT 1", (guild_id,))
            session = cursor.fetchone()

            if not session:
                await interaction.followup.send(embed=create_error_embed("⚠️ 無簽到記錄"))
                return

            session_id = session[0]
            cursor.execute("SELECT user_id FROM records WHERE session_id = ?", (session_id,))
            signed_in_ids = {row[0] for row in cursor.fetchall()}

        signed_in_members = []
        not_signed_in_members = []

        for member in interaction.guild.members:
            if member.bot:
                continue
            if member.id in signed_in_ids:
                signed_in_members.append(f"<@{member.id}>")
            else:
                not_signed_in_members.append(f"<@{member.id}>")

        embed = create_brand_embed(title=f"📊 簽到摘要 (場次 #{session_id})")
        
        signed_in_text = "\n".join(signed_in_members) if signed_in_members else "無人簽到"
        if len(signed_in_text) > 1024:
            signed_in_text = f"人數過多，共 {len(signed_in_members)} 人"
            
        not_signed_in_text = "\n".join(not_signed_in_members) if not_signed_in_members else "全員到齊"
        if len(not_signed_in_text) > 1024:
            not_signed_in_text = f"人數過多，共 {len(not_signed_in_members)} 人"

        embed.add_field(name=f"✅ 已簽到 ({len(signed_in_members)})", value=signed_in_text, inline=False)
        embed.add_field(name=f"❌ 未簽到 ({len(not_signed_in_members)})", value=not_signed_in_text, inline=False)

        await interaction.followup.send(embed=embed)

    # --- Nickname Management Commands ---
    @app_commands.command(name="nickname_set", description="設定您或他人的暱稱")
    @app_commands.describe(user="要設定的成員", class_id="學號", name="名字")
    async def nickname_set(self, interaction: discord.Interaction, user: discord.Member, class_id: str, name: str):
        if interaction.user.id != user.id and not interaction.user.guild_permissions.manage_nicknames:
            await interaction.response.send_message(embed=create_error_embed("權限不足", "您沒有權限修改他人暱稱。" ), ephemeral=True)
            return

        new_nickname = f"{class_id} | {name}"
        try:
            await user.edit(nick=new_nickname)
            await interaction.response.send_message(embed=create_success_embed("✅ 暱稱已更新", f"已將 {user.mention} 的暱稱更新為 `{new_nickname}`" ), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(embed=create_error_embed("❌ 權限不足", f"我沒有權限修改 {user.mention} 的暱稱。請檢查我的權限設定。" ), ephemeral=True)

    @app_commands.command(name="nickname_clear", description="批次清除伺服器成員的暱稱")
    @app_commands.describe(except_role="此身分組的成員將不會被清除暱稱")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nickname_clear(self, interaction: discord.Interaction, except_role: Optional[discord.Role] = None):
        await interaction.response.defer(ephemeral=True, thinking=True)

        excluded_members = set(except_role.members) if except_role else set()
        tasks = []
        
        for member in interaction.guild.members:
            if member.bot or member in excluded_members:
                continue
            if member.nick: # Only clear if they have a nickname
                tasks.append(member.edit(nick=None))

        if not tasks:
            await interaction.followup.send(embed=create_brand_embed("✨ 無需操作", "沒有需要清除暱稱的成員。" ), ephemeral=True)
            return

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        fail_count = len(results) - success_count

        embed = create_success_embed("🧹 暱稱清除完成", f"成功清除了 **{success_count}** 位成員的暱稱。" )
        if fail_count > 0:
            embed.add_field(name="⚠️ 失敗", value=f"有 **{fail_count}** 位成員無法清除，可能是我對他們的權限不足。" )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @nickname_clear.error
    async def on_nickname_clear_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(embed=create_error_embed("權限不足", "您需要 `管理暱稱` 權限才能使用此指令。" ), ephemeral=True)
        else:
            await interaction.response.send_message(embed=create_error_embed("發生未知錯誤", str(error)), ephemeral=True)


async def setup(bot):
    await bot.add_cog(AttendanceCog(bot))