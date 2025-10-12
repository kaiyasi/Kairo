import discord
from discord.ext import commands
from discord import app_commands
from ..utils.brand import create_brand_embed, create_success_embed, create_error_embed
import sqlite3

class RoutingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="org_channel_set", description="設定功能對應頻道")
    @app_commands.describe(
        key="用途關鍵字（如：plan_status、attendance_summary、ctf_notice）",
        channel="目標頻道"
    )
    async def org_channel_set(
        self,
        interaction: discord.Interaction,
        key: str,
        channel: discord.TextChannel
    ):
        # Check permission
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有管理員可以設定頻道路由。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        guild_id = interaction.guild.id

        # Save routing
        with sqlite3.connect("data/tenant.db") as conn:
            conn.execute("""
                INSERT OR REPLACE INTO routing (guild_id, key, channel_id)
                VALUES (?, ?, ?)
            """, (guild_id, key, channel.id))

        embed = create_success_embed(
            title="✅ 路由已設定",
            description=f"**功能：** {key}\n**頻道：** {channel.mention}",
            guild_name=interaction.guild.name
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="org_channel_get", description="查看功能對應頻道")
    @app_commands.describe(key="用途關鍵字")
    async def org_channel_get(
        self,
        interaction: discord.Interaction,
        key: str = None
    ):
        guild_id = interaction.guild.id

        with sqlite3.connect("data/tenant.db") as conn:
            if key:
                # Get specific routing
                cursor = conn.execute(
                    "SELECT channel_id FROM routing WHERE guild_id = ? AND key = ?",
                    (guild_id, key)
                )
                row = cursor.fetchone()

                if row:
                    channel = self.bot.get_channel(row[0])
                    if channel:
                        embed = create_brand_embed(
                            title="🔗 頻道路由",
                            description=f"**功能：** {key}\n**頻道：** {channel.mention}",
                            guild_name=interaction.guild.name
                        )
                    else:
                        embed = create_error_embed(
                            title="⚠️ 頻道不存在",
                            description=f"功能 {key} 設定的頻道已被刪除。",
                            guild_name=interaction.guild.name
                        )
                else:
                    embed = create_error_embed(
                        title="❌ 未設定路由",
                        description=f"功能 {key} 尚未設定對應頻道。",
                        guild_name=interaction.guild.name
                    )
            else:
                # Get all routing
                cursor = conn.execute(
                    "SELECT key, channel_id FROM routing WHERE guild_id = ?",
                    (guild_id,)
                )
                rows = cursor.fetchall()

                if rows:
                    routing_list = []
                    for route_key, channel_id in rows:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            routing_list.append(f"**{route_key}:** {channel.mention}")
                        else:
                            routing_list.append(f"**{route_key}:** ❌ 已刪除")

                    embed = create_brand_embed(
                        title="🔗 所有頻道路由",
                        description="\n".join(routing_list),
                        guild_name=interaction.guild.name
                    )
                else:
                    embed = create_brand_embed(
                        title="🔗 頻道路由",
                        description="尚未設定任何路由。",
                        guild_name=interaction.guild.name
                    )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="org_channel_remove", description="移除功能頻道路由")
    @app_commands.describe(key="用途關鍵字")
    async def org_channel_remove(
        self,
        interaction: discord.Interaction,
        key: str
    ):
        # Check permission
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 權限不足",
                    description="只有管理員可以移除頻道路由。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        guild_id = interaction.guild.id

        with sqlite3.connect("data/tenant.db") as conn:
            # Check if routing exists
            cursor = conn.execute(
                "SELECT 1 FROM routing WHERE guild_id = ? AND key = ?",
                (guild_id, key)
            )
            exists = cursor.fetchone()

            if not exists:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        title="❌ 路由不存在",
                        description=f"功能 {key} 沒有設定路由。",
                        guild_name=interaction.guild.name
                    ),
                    ephemeral=True
                )
                return

            # Remove routing
            conn.execute(
                "DELETE FROM routing WHERE guild_id = ? AND key = ?",
                (guild_id, key)
            )

        embed = create_success_embed(
            title="🗑️ 路由已移除",
            description=f"功能 **{key}** 的頻道路由已移除。",
            guild_name=interaction.guild.name
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RoutingCog(bot))