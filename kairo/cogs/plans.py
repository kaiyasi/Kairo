import discord
from discord.ext import commands
from discord import app_commands
from ..utils.brand import create_brand_embed, create_success_embed, create_error_embed
from ..utils.tenant import tenant_db
from datetime import datetime
import sqlite3

class PlansCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_current_week(self) -> str:
        """Get current week in YYYY-WXX format"""
        now = datetime.now()
        return f"{now.year}-W{now.isocalendar().week:02d}"

    async def send_plan_notification(self, guild_id: int, week: str, group: str, content: str):
        """Send plan notification to routing channel if configured"""
        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.execute(
                "SELECT channel_id FROM routing WHERE guild_id = ? AND key = 'plan_status'",
                (guild_id,)
            )
            row = cursor.fetchone()

            if row:
                channel_id = row[0]
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = create_brand_embed(
                        title="📚 新課綱發布",
                        description=f"**週次：** {week}\n**組別：** {group}",
                        guild_name=channel.guild.name
                    )
                    embed.add_field(name="課程內容", value=content[:1000] + ("..." if len(content) > 1000 else ""), inline=False)

                    try:
                        await channel.send(embed=embed)
                    except:
                        pass  # Ignore if sending fails

    @app_commands.command(name="plan_set", description="設定週課綱")
    @app_commands.describe(
        week="週次（如2025-W37，留空為當週）",
        group="組別名稱",
        content="課程內容"
    )
    async def plan_set(
        self,
        interaction: discord.Interaction,
        group: str,
        content: str,
        week: str = None
    ):
        guild_id = interaction.guild.id

        if not week:
            week = self.get_current_week()

        # Validate week format
        if not week.startswith("20") or "-W" not in week:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 週次格式錯誤",
                    description="週次格式應為 YYYY-WXX（如 2025-W37）",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Save plan
        with sqlite3.connect("data/tenant.db") as conn:
            conn.execute("""
                INSERT OR REPLACE INTO plans (guild_id, week_key, group_name, content)
                VALUES (?, ?, ?, ?)
            """, (guild_id, week, group, content))

        embed = create_success_embed(
            title="✅ 課綱已設定",
            description=f"**週次：** {week}\n**組別：** {group}",
            guild_name=interaction.guild.name
        )
        embed.add_field(name="課程內容", value=content[:1000] + ("..." if len(content) > 1000 else ""), inline=False)

        await interaction.response.send_message(embed=embed)

        # Send notification to routing channel
        await self.send_plan_notification(guild_id, week, group, content)

    @app_commands.command(name="plan_show", description="顯示週課綱")
    @app_commands.describe(
        week="週次（如2025-W37，留空為當週）",
        group="組別名稱（留空為自動判斷）"
    )
    async def plan_show(
        self,
        interaction: discord.Interaction,
        week: str = None,
        group: str = None
    ):
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        if not week:
            week = self.get_current_week()

        # If no group specified, get user's group
        if not group:
            with sqlite3.connect("data/tenant.db") as conn:
                cursor = conn.execute(
                    "SELECT group_name FROM plan_groups WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id)
                )
                row = cursor.fetchone()
                group = row[0] if row else "default"

        # Get plan content
        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.execute(
                "SELECT content FROM plans WHERE guild_id = ? AND week_key = ? AND group_name = ?",
                (guild_id, week, group)
            )
            row = cursor.fetchone()

        if not row:
            embed = create_error_embed(
                title="📚 無課綱",
                description=f"**週次：** {week}\n**組別：** {group}\n\n尚未設定此週課綱。",
                guild_name=interaction.guild.name
            )
        else:
            embed = create_brand_embed(
                title=f"📚 週課綱 ({week})",
                description=row[0],
                guild_name=interaction.guild.name
            )
            embed.add_field(name="組別", value=group, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="plan_group_set", description="設定成員組別")
    @app_commands.describe(
        member="要設定的成員",
        group="組別名稱"
    )
    async def plan_group_set(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        group: str
    ):
        guild_id = interaction.guild.id

        # Check if user has permission (server admin or has specific role)
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有幹部或管理員可以設定成員組別。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Set group
        with sqlite3.connect("data/tenant.db") as conn:
            conn.execute("""
                INSERT OR REPLACE INTO plan_groups (guild_id, user_id, group_name)
                VALUES (?, ?, ?)
            """, (guild_id, member.id, group))

        embed = create_success_embed(
            title="✅ 組別已設定",
            description=f"**成員：** {member.mention}\n**組別：** {group}",
            guild_name=interaction.guild.name
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PlansCog(bot))