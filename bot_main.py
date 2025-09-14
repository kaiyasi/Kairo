import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
import logging
# Load environment variables first
load_dotenv()

from utils.visibility import get_visible_commands_for_guild, is_super_admin, get_super_admin_commands

ADMIN_GUILD_ID = int(os.getenv('ADMIN_GUILD_ID', '1405176396158079076'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KairoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up Kairo bot...")

        # Load all cogs
        cogs = [
            'cogs.register',
            'cogs.response',
            'cogs.modules_admin',
            'cogs.attendance',
            'cogs.plans',
            'cogs.qa',
            'cogs.ctfd',
            'cogs.crypto_cog',
            'cogs.bookkeeping',
            'cogs.routing'
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

        # 管理員指令將在 on_ready 中同步，確保所有 guild 都已載入
        logger.info("Bot setup complete!")

    async def sync_super_admin_commands_for_admin_guild(self):
        """只在管理員 guild 中同步超級管理員指令"""
        # 使用常數定義的管理員 guild ID

        try:
            admin_guild = self.get_guild(ADMIN_GUILD_ID)
            if not admin_guild:
                logger.error(f"❌ 找不到管理員 Guild: {ADMIN_GUILD_ID}")
                logger.error("請確認機器人已被邀請到管理員伺服器，並檢查 ADMIN_GUILD_ID 是否正確")
                logger.error("超級管理員指令將無法使用")
                return

            # Clear commands for admin guild
            self.tree.clear_commands(guild=admin_guild)

            # Add super admin commands
            modules_admin_cog = self.get_cog('ModulesAdminCog')
            logger.info(f"ModulesAdminCog found: {modules_admin_cog is not None}")
            if modules_admin_cog:
                logger.info(f"ModulesAdminCog commands: {len(modules_admin_cog.__cog_app_commands__)}")
                for command in modules_admin_cog.__cog_app_commands__:
                    self.tree.add_command(command, guild=admin_guild)
                    logger.info(f"Added admin command {command.name} to admin guild")
            else:
                logger.error("ModulesAdminCog not found!")

            # Sync to admin guild only
            synced = await self.tree.sync(guild=admin_guild)
            logger.info(f"Synced {len(synced)} super admin commands to admin guild {ADMIN_GUILD_ID}")

            # Clear global commands to ensure they don't appear elsewhere
            self.tree.clear_commands(guild=None)
            await self.tree.sync(guild=None)  # Sync empty global commands

        except Exception as e:
            logger.error(f"Failed to sync super admin commands to admin guild: {e}")

    async def sync_commands_for_guild(self, guild_id: int):
        """Sync commands for a specific guild based on visibility rules"""
        guild = self.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild {guild_id} not found")
            return

        try:
            # Clear existing guild commands
            self.tree.clear_commands(guild=guild)

            # Get visible commands for this guild
            visible_commands = get_visible_commands_for_guild(guild_id)
            logger.info(f"Guild {guild_id} should see commands: {visible_commands}")

            # Add visible commands
            added_count = 0
            for cog_name, cog in self.cogs.items():
                # 取得 cog 中的所有 app_commands
                for command in cog.__cog_app_commands__:
                    if command.name in visible_commands:
                        self.tree.add_command(command, guild=guild)
                        added_count += 1
                        logger.info(f"Added command {command.name} to guild {guild_id}")

            # Sync to Discord
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} commands for guild {guild_id}")

        except Exception as e:
            logger.error(f"Failed to sync commands for guild {guild_id}: {e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'Kairo bot is ready! Logged in as {self.user}')
        logger.info(f'Bot is in {len(self.guilds)} guilds')

        try:
            # 列出所有 guild（方便檢查）
            logger.info("=" * 50)
            logger.info("📋 機器人已加入的所有伺服器：")
            for guild in self.guilds:
                logger.info(f'   - {guild.name} (ID: {guild.id})')
            logger.info("=" * 50)

            # 檢查環境變數
            logger.info(f"📊 環境變數檢查:")
            logger.info(f"   ADMIN_GUILD_ID = {ADMIN_GUILD_ID}")
            logger.info(f"   目標管理員 Guild 是否存在: {self.get_guild(ADMIN_GUILD_ID) is not None}")

            # 先同步管理員指令（現在所有 guild 都已載入）
            logger.info(f"🔍 開始同步管理員指令...")
            await self.sync_super_admin_commands_for_admin_guild()

            # Sync commands for all guilds (except admin guild)
            logger.info(f"🔄 開始同步一般 Guild 指令...")
            for guild in self.guilds:
                if guild.id != ADMIN_GUILD_ID:  # 跳過管理員 Guild，避免覆蓋管理員指令
                    await self.sync_commands_for_guild(guild.id)
                else:
                    logger.info(f"⏭️ 跳過管理員 Guild {guild.id} 的一般指令同步")

            logger.info("✅ 所有指令同步完成")

        except Exception as e:
            logger.error(f"❌ on_ready 過程中發生錯誤: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")

        # New guilds start with only register command
        await self.sync_commands_for_guild(guild.id)

        # Send welcome message to system channel if possible
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="🤖 歡迎使用 Kairo",
                description="感謝邀請 Kairo 到您的伺服器！\n\n請使用 `/register` 指令開始申請註冊。",
                color=0x8B9DC3,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Service by Serelix Studio")

            try:
                await guild.system_channel.send(embed=embed)
            except:
                pass  # Ignore if we can't send

    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild"""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")

    async def on_application_command_error(self, interaction: discord.Interaction, error):
        """Global error handler for application commands"""
        logger.error(f"Command error in {interaction.guild}: {error}")

        if not interaction.response.is_done():
            embed = discord.Embed(
                title="❌ 指令錯誤",
                description="執行指令時發生錯誤，請稍後再試。",
                color=0xDDB7AB
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                pass

    async def on_error(self, event, *args, **kwargs):
        """Global error handler"""
        logger.error(f"Bot error in {event}: {args}")

async def main():
    """Main function to run the bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        return

    # Create and run bot
    async with KairoBot() as bot:
        await bot.start(token)

if __name__ == '__main__':
    asyncio.run(main())