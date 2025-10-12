import discord
from discord.ext import commands
from discord import app_commands
from ..utils.brand import create_brand_embed, create_success_embed
from ..utils.tenant import tenant_db
import os

REVIEW_CHANNEL_ID = int(os.getenv('REVIEW_CHANNEL_ID', '1416406590411509860'))

class RegistrationModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="社團註冊申請")

        self.school = discord.ui.TextInput(
            label="學校名稱",
            placeholder="請輸入學校名稱",
            required=True,
            max_length=100
        )

        self.club_name = discord.ui.TextInput(
            label="社團名稱",
            placeholder="請輸入社團名稱",
            required=True,
            max_length=100
        )

        self.responsible_person = discord.ui.TextInput(
            label="負責人姓名",
            placeholder="請輸入負責人真實姓名",
            required=True,
            max_length=50
        )

        self.responsible_discord_id = discord.ui.TextInput(
            label="負責人 Discord ID",
            placeholder="請輸入負責人的 Discord 用戶 ID",
            required=True,
            max_length=20
        )

        self.club_type = discord.ui.TextInput(
            label="社團類型",
            placeholder="如：程式設計社、資訊研習社等",
            required=True,
            max_length=50
        )

        self.add_item(self.school)
        self.add_item(self.club_name)
        self.add_item(self.responsible_person)
        self.add_item(self.responsible_discord_id)
        self.add_item(self.club_type)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        # Validate Discord ID
        try:
            discord_id = int(self.responsible_discord_id.value)
        except ValueError:
            await interaction.response.send_message(
                embed=create_brand_embed(
                    title="❌ 錯誤",
                    description="Discord ID 必須為數字",
                    guild_name=guild.name
                ),
                ephemeral=True
            )
            return

        # Save registration
        tenant_db.save_registration(
            guild_id=guild.id,
            school=self.school.value,
            club_name=self.club_name.value,
            responsible_person=self.responsible_person.value,
            responsible_discord_id=discord_id,
            club_type=self.club_type.value
        )

        # Create status embed in current channel
        status_embed = create_brand_embed(
            title="📝 註冊申請狀態",
            description="**狀態：** 🟡 審核中 (pending)\n\n請耐心等待管理員審核。",
            guild_name=guild.name
        )
        status_embed.add_field(name="申請資訊", value=f"""
**學校：** {self.school.value}
**社團：** {self.club_name.value}
**負責人：** {self.responsible_person.value}
**類型：** {self.club_type.value}
        """, inline=False)

        await interaction.response.send_message(embed=status_embed)

        # Send to review channel
        review_channel = interaction.client.get_channel(REVIEW_CHANNEL_ID)
        if review_channel:
            review_embed = create_brand_embed(
                title="🔍 新的社團註冊申請",
                description=f"**Guild ID：** {guild.id}\n**Guild 名稱：** {guild.name}",
                guild_name="Kairo 管理中心"
            )
            review_embed.add_field(name="申請資訊", value=f"""
**學校：** {self.school.value}
**社團：** {self.club_name.value}
**負責人：** {self.responsible_person.value}
**Discord ID：** {discord_id}
**類型：** {self.club_type.value}
            """, inline=False)

            try:
                await review_channel.send(embed=review_embed)
            except Exception as e:
                print(f"無法發送到審核頻道: {e}")
                # 可以選擇發送到系統頻道或記錄日誌
                print(f"註冊申請詳情 - Guild: {guild.name} ({guild.id}), 學校: {self.school.value}, 社團: {self.club_name.value}")

        # Trigger command sync
        await interaction.client.sync_commands_for_guild(guild.id)

class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register", description="申請註冊社團使用 Kairo 機器人")
    async def register(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        # Check current status
        registration = tenant_db.get_registration_status(guild.id)
        if registration and registration.get('status') not in ['none', 'declined']:
            await interaction.response.send_message(
                embed=create_brand_embed(
                    title="⚠️ 提醒",
                    description="此伺服器已有註冊申請記錄，無需重複申請。",
                    guild_name=guild.name
                ),
                ephemeral=True
            )
            return

        modal = RegistrationModal()
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(RegisterCog(bot))