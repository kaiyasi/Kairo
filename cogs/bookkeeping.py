import discord
from discord.ext import commands
from discord import app_commands
from utils.brand import create_brand_embed, create_success_embed, create_error_embed
from utils.excel import append_journal_entry, read_journal_balance, export_journal_csv, get_guild_excel_path
from utils.google_sheets import GoogleSheetsManager, get_guild_google_sheets_url, set_guild_google_sheets_url
from utils.tenant import tenant_db, BookkeepingSettings
import os
import io
from datetime import datetime

# --- UI Components ---
class BookkeepingLayoutModal(discord.ui.Modal, title='記帳版面設定'):
    def __init__(self, current_settings: BookkeepingSettings):
        super().__init__()
        self.current_settings = current_settings

        self.start_row = discord.ui.TextInput(
            label='起始列數',
            placeholder='例如：2',
            default=str(current_settings.start_row),
            required=True
        )
        self.date_col = discord.ui.TextInput(
            label='日期欄位',
            placeholder='例如：A',
            default=current_settings.date_col,
            required=True
        )
        self.category_col = discord.ui.TextInput(
            label='類別欄位',
            placeholder='例如：B',
            default=current_settings.category_col,
            required=True
        )
        self.amount_col = discord.ui.TextInput(
            label='金額欄位',
            placeholder='例如：C',
            default=current_settings.amount_col,
            required=True
        )
        self.memo_col = discord.ui.TextInput(
            label='備註欄位',
            placeholder='例如：D',
            default=current_settings.memo_col,
            required=True
        )
        self.user_col = discord.ui.TextInput(
            label='記錄者欄位',
            placeholder='例如：E',
            default=current_settings.user_col,
            required=True
        )

        self.add_item(self.start_row)
        self.add_item(self.date_col)
        self.add_item(self.category_col)
        self.add_item(self.amount_col)
        self.add_item(self.memo_col)
        self.add_item(self.user_col)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        try:
            start_row = int(self.start_row.value)
            if start_row < 1:
                raise ValueError("起始列數必須大於 0")
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed(title="❌ 格式錯誤", description="起始列數必須是有效的數字。", guild_name=interaction.guild.name),
                ephemeral=True
            )
            return

        def is_valid_column(col_str: str) -> bool:
            return isinstance(col_str, str) and col_str.isalpha() and len(col_str) < 3

        cols = {
            'date_col': self.date_col.value.upper(),
            'category_col': self.category_col.value.upper(),
            'amount_col': self.amount_col.value.upper(),
            'memo_col': self.memo_col.value.upper(),
            'user_col': self.user_col.value.upper(),
        }

        for name, col in cols.items():
            if not is_valid_column(col):
                await interaction.response.send_message(
                    embed=create_error_embed(title="❌ 格式錯誤", description=f"{name} 必須是有效的欄位名稱 (A, B, AA 等)。", guild_name=interaction.guild.name),
                    ephemeral=True
                )
                return

        new_settings = BookkeepingSettings(
            start_row=start_row,
            **cols
        )
        tenant_db.set_bookkeeping_settings(guild_id, new_settings)

        embed = create_success_embed(
            title="✅ 版面設定已儲存",
            description="新的記帳記錄將會依照此版面設定寫入。",
            guild_name=interaction.guild.name
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class BookkeepingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.google_sheets = GoogleSheetsManager()

    def get_excel_path_or_url(self, guild_id: int) -> str:
        guild_path = get_guild_google_sheets_url(guild_id)
        if guild_path:
            return guild_path
        return os.getenv('EXCEL_PATH', '/mnt/data_pool_b/kaiyasi/club_book.xlsx')

    def is_google_sheets_url(self, path_or_url: str) -> bool:
        return 'docs.google.com/spreadsheets' in path_or_url

    @app_commands.command(name="book_add", description="新增記帳記錄")
    @app_commands.describe(
        category="類別（如：零食、文具、活動費等）",
        amount="金額（正數為收入，負數為支出）",
        memo="備註（可選）"
    )
    async def book_add(
        self,
        interaction: discord.Interaction,
        category: str,
        amount: float,
        memo: str = ""
    ):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id
        user_name = interaction.user.display_name
        path_or_url = self.get_excel_path_or_url(guild_id)

        success = False
        file_info = ""

        if self.is_google_sheets_url(path_or_url):
            sheet_id = self.google_sheets.extract_sheet_id(path_or_url)
            if sheet_id:
                self.google_sheets.create_journal_sheet(sheet_id)
                
                settings = tenant_db.get_bookkeeping_settings(guild_id)
                record_data = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'category': category,
                    'amount': amount,
                    'memo': memo,
                    'user': user_name
                }

                success = self.google_sheets.write_record_by_layout(sheet_id, settings, record_data)
                file_info = "Google Sheets"
        else:
            success = append_journal_entry(
                excel_path=path_or_url,
                category=category,
                amount=amount,
                memo=memo,
                user=user_name
            )
            file_info = os.path.basename(path_or_url)

        if success:
            embed = create_success_embed(
                title="✅ 記帳成功",
                description=f"**類別：** {category}\n**金額：** {amount:,.2f}\n**備註：** {memo or '無'}",
                guild_name=interaction.guild.name
            )
            embed.add_field(name="記錄者", value=user_name, inline=True)
            embed.add_field(name="檔案", value=file_info, inline=True)
        else:
            embed = create_error_embed(
                title="❌ 記帳失敗",
                description="無法寫入記帳檔案，請檢查設定或權限。",
                guild_name=interaction.guild.name
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="book_balance", description="查詢帳本餘額")
    async def book_balance(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id
        path_or_url = self.get_excel_path_or_url(guild_id)

        balance_info = None
        file_info = ""

        if self.is_google_sheets_url(path_or_url):
            sheet_id = self.google_sheets.extract_sheet_id(path_or_url)
            if sheet_id:
                balance = self.google_sheets.get_balance_from_summary(sheet_id)
                if balance is not None:
                    balance_info = {'balance': balance, 'source': 'Google Sheets Summary'}
                else:
                    settings = tenant_db.get_bookkeeping_settings(guild_id)
                    balance_info = self.google_sheets.calculate_balance_from_journal(sheet_id, settings.amount_col)
                file_info = "Google Sheets"
        else:
            if not os.path.exists(path_or_url):
                await interaction.followup.send(embed=create_error_embed(title="❌ 找不到帳本", description="Excel 檔案不存在，請先新增記錄。", guild_name=interaction.guild.name))
                return
            balance_info = read_journal_balance(path_or_url)
            file_info = os.path.basename(path_or_url)

        if balance_info is None:
            embed = create_error_embed(title="❌ 讀取失敗", description="無法讀取餘額資訊。", guild_name=interaction.guild.name)
        else:
            balance = balance_info['balance']
            source = balance_info['source']
            color = "🟢" if balance >= 0 else "🔴"
            status = "盈餘" if balance >= 0 else "虧損"
            embed = create_brand_embed(title="💰 帳本餘額", description=f"{color} **{balance:,.2f}** 元 ({status})", guild_name=interaction.guild.name)
            embed.add_field(name="資料來源", value=source, inline=True)
            embed.add_field(name="檔案", value=file_info, inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="book_export", description="匯出記帳記錄")
    async def book_export(self, interaction: discord.Interaction):
        # This command would need to be updated to handle custom layouts as well
        # For now, we leave it as is, potentially exporting the raw sheet.
        await interaction.response.send_message("此功能待更新以支援自訂版面。", ephemeral=True)

    @app_commands.command(name="book_set_sheets", description="設定 Google Sheets 記帳檔案")
    @app_commands.describe(url="Google Sheets 連結")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def book_set_sheets(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id
        if not self.is_google_sheets_url(url):
            await interaction.followup.send(embed=create_error_embed(title="❌ URL 格式錯誤", description="請提供有效的 Google Sheets 連結。", guild_name=interaction.guild.name))
            return

        sheet_id = self.google_sheets.extract_sheet_id(url)
        if not sheet_id:
            await interaction.followup.send(embed=create_error_embed(title="❌ 無法解析 URL", description="無法從連結中提取 Sheet ID。", guild_name=interaction.guild.name))
            return

        set_guild_google_sheets_url(guild_id, url)
        embed = create_success_embed(title="✅ Google Sheets 已設定", description="記帳功能現在會使用指定的 Google Sheets。", guild_name=interaction.guild.name)
        embed.add_field(name="Sheet ID", value=sheet_id, inline=True)

        if self.google_sheets.create_journal_sheet(sheet_id):
            embed.add_field(name="狀態", value="✅ Journal 工作表已準備", inline=True)
        else:
            embed.add_field(name="狀態", value="⚠️ 請確認工作表權限", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="book_set_layout", description="設定記帳功能的 Google Sheets 版面")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def book_set_layout(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        current_settings = tenant_db.get_bookkeeping_settings(guild_id)
        modal = BookkeepingLayoutModal(current_settings)
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(BookkeepingCog(bot))