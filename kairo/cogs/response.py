import discord
from discord.ext import commands
from discord import app_commands
from ..utils.brand import create_brand_embed, create_success_embed
from ..utils.tenant import tenant_db
import os

REVIEW_CHANNEL_ID = int(os.getenv('REVIEW_CHANNEL_ID', '1416406590411509860'))

class ResponseModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="補件回應")

        self.response_content = discord.ui.TextInput(
            label="補件內容",
            placeholder="請提供要求的額外資訊或澄清說明",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000
        )

        self.add_item(self.response_content)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        # Update status to pending
        tenant_db.set_registration_status(guild.id, 'pending')

        # Update status embed
        status_embed = create_brand_embed(
            title="📝 註冊申請狀態",
            description="**狀態：** 🟡 重新審核中 (pending)\n\n已提交補件資訊，請耐心等待管理員重新審核。",
            guild_name=guild.name
        )

        registration = tenant_db.get_registration_status(guild.id)
        if registration:
            status_embed.add_field(name="申請資訊", value=f"""
**學校：** {registration.get('school', 'N/A')}
**社團：** {registration.get('club_name', 'N/A')}
**負責人：** {registration.get('responsible_person', 'N/A')}
**類型：** {registration.get('club_type', 'N/A')}
            """, inline=False)

        status_embed.add_field(name="補件內容", value=self.response_content.value, inline=False)

        await interaction.response.send_message(embed=status_embed)

        # Send to review channel
        review_channel = interaction.client.get_channel(REVIEW_CHANNEL_ID)
        if review_channel:
            review_embed = create_brand_embed(
                title="📄 社團補件回應",
                description=f"**Guild ID：** {guild.id}\n**Guild 名稱：** {guild.name}",
                guild_name="Kairo 管理中心"
            )
            review_embed.add_field(name="補件內容", value=self.response_content.value, inline=False)

            if registration:
                review_embed.add_field(name="原申請資訊", value=f"""
**學校：** {registration.get('school', 'N/A')}
**社團：** {registration.get('club_name', 'N/A')}
**負責人：** {registration.get('responsible_person', 'N/A')}
**類型：** {registration.get('club_type', 'N/A')}
                """, inline=False)

            try:
                await review_channel.send(embed=review_embed)
            except Exception as e:
                print(f"無法發送到審核頻道: {e}")
                # 記錄補件內容到日誌
                print(f"補件回應詳情 - Guild: {guild.name} ({guild.id}), 內容: {self.response_content.value}")

        # Trigger command sync
        await interaction.client.sync_commands_for_guild(guild.id)

class ResponseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="response", description="回應審核要求的補充資訊")
    async def response(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return

        registration = tenant_db.get_registration_status(guild.id)
        if not registration or registration.get('status') != 'needs_more_info':
            await interaction.response.send_message(
                embed=create_brand_embed(
                    title="⚠️ 錯誤",
                    description="目前不需要補充資訊，或狀態不正確。",
                    guild_name=guild.name
                ),
                ephemeral=True
            )
            return

        modal = ResponseModal()
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(ResponseCog(bot))