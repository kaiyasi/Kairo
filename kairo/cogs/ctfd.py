import discord
from discord.ext import commands
from discord import app_commands
from ..utils.brand import create_brand_embed, create_success_embed, create_error_embed
from ..utils.tenant import tenant_db, CryptoManager
import sqlite3
import requests
import os

class CTFdCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        master_key = os.getenv('MASTER_KEY_BASE64')
        if master_key:
            try:
                self.crypto = CryptoManager(master_key)
            except ValueError as e:
                print(f"CTFd 模組警告: {e}")
                print("CTFd 模組將以受限模式運行，無法使用加密組態功能")
                self.crypto = None
        else:
            print("CTFd 模組警告: 未設定 MASTER_KEY_BASE64，將以受限模式運行")
            self.crypto = None

    def get_guild_ctfd_config(self, guild_id: int):
        """Get CTFd configuration for guild"""
        if not self.crypto:
            return None

        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.execute("""
                SELECT ctfd_base_url, ciphertext_ctfd_token, ctfd_push_mode,
                       ctfd_award_name, ctfd_award_category
                FROM org_configs WHERE guild_id = ?
            """, (guild_id,))
            row = cursor.fetchone()

            if not row or not row[0] or not row[1]:
                return None

            try:
                token = self.crypto.decrypt(row[1])
                return {
                    'base_url': row[0].rstrip('/'),
                    'token': token,
                    'push_mode': row[2] or 'award',
                    'award_name': row[3] or 'Discord QA',
                    'award_category': row[4] or 'discord'
                }
            except:
                return None

    async def make_ctfd_request(self, config, method: str, endpoint: str, **kwargs):
        """Make authenticated request to CTFd API"""
        url = f"{config['base_url']}/api/v1{endpoint}"
        headers = {
            'Authorization': f"Token {config['token']}",
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request(method, url, headers=headers, timeout=10, **kwargs)
            return response
        except Exception as e:
            raise Exception(f"CTFd API 請求失敗: {str(e)}")

    @app_commands.command(name="ctfd_link", description="綁定 CTFd 帳號")
    @app_commands.describe(email="CTFd 平台註冊的 Email")
    async def ctfd_link(self, interaction: discord.Interaction, email: str):
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        # Get CTFd config
        config = self.get_guild_ctfd_config(guild_id)
        if not config:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ CTFd 未設定",
                    description="此伺服器尚未設定 CTFd 連動。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Try to find user by email
        ctfd_user_id = None
        try:
            response = await self.make_ctfd_request(config, 'GET', '/users')
            if response.status_code == 200:
                users = response.json().get('data', [])
                for user in users:
                    if user.get('email', '').lower() == email.lower():
                        ctfd_user_id = user.get('id')
                        break
        except Exception as e:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ CTFd 連線失敗",
                    description=f"無法連接到 CTFd 平台：{str(e)}",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Save binding
        with sqlite3.connect("data/tenant.db") as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ctfd_links (guild_id, discord_user_id, email, ctfd_user_id)
                VALUES (?, ?, ?, ?)
            """, (guild_id, user_id, email, ctfd_user_id))

        embed = create_success_embed(
            title="✅ 綁定成功",
            description=f"**Email：** {email}",
            guild_name=interaction.guild.name
        )

        if ctfd_user_id:
            embed.add_field(name="CTFd 用戶 ID", value=str(ctfd_user_id), inline=True)
            embed.add_field(name="狀態", value="✅ 已驗證", inline=True)
        else:
            embed.add_field(name="狀態", value="⚠️ 未找到對應用戶，但已保存綁定", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ctfd_scoreboard", description="顯示 CTFd 排行榜")
    async def ctfd_scoreboard(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        # Get CTFd config
        config = self.get_guild_ctfd_config(guild_id)
        if not config:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ CTFd 未設定",
                    description="此伺服器尚未設定 CTFd 連動。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        try:
            response = await self.make_ctfd_request(config, 'GET', '/scoreboard')
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

            scoreboard_data = response.json().get('data', [])

            if not scoreboard_data:
                embed = create_brand_embed(
                    title="🏆 CTFd 排行榜",
                    description="目前還沒有分數記錄。",
                    guild_name=interaction.guild.name
                )
            else:
                leaderboard = []
                for i, entry in enumerate(scoreboard_data[:10], 1):
                    name = entry.get('name', 'Unknown')
                    score = entry.get('score', 0)

                    medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
                    leaderboard.append(f"{medal} **{name}** - {score} 分")

                embed = create_brand_embed(
                    title="🏆 CTFd 排行榜 (Top 10)",
                    description="\n".join(leaderboard),
                    guild_name=interaction.guild.name
                )

        except Exception as e:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 無法獲取排行榜",
                    description=f"CTFd API 錯誤：{str(e)}",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        await interaction.response.send_message(embed=embed)

    async def award_ctfd_points(self, guild_id: int, user_id: int, points: int):
        """Award points to user on CTFd platform"""
        config = self.get_guild_ctfd_config(guild_id)
        if not config or config['push_mode'] != 'award':
            return False

        # Get user's CTFd binding
        with sqlite3.connect("data/tenant.db") as conn:
            cursor = conn.execute(
                "SELECT ctfd_user_id FROM ctfd_links WHERE guild_id = ? AND discord_user_id = ?",
                (guild_id, user_id)
            )
            row = cursor.fetchone()

            if not row or not row[0]:
                return False

            ctfd_user_id = row[0]

        try:
            # Create award
            award_data = {
                'user_id': ctfd_user_id,
                'name': config['award_name'],
                'category': config['award_category'],
                'value': points,
                'description': f"Discord QA 答題獲得 {points} 分"
            }

            response = await self.make_ctfd_request(
                config, 'POST', '/awards', json=award_data
            )

            return response.status_code == 200

        except:
            return False

async def setup(bot):
    await bot.add_cog(CTFdCog(bot))