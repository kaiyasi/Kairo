import discord
from discord.ext import commands
from discord import app_commands
from ..utils.brand import create_brand_embed, create_success_embed, create_error_embed
from ..utils.crypto import CRYPTO_FUNCTIONS, is_long_text, create_text_file
import io

class CryptoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_input_text(self, interaction: discord.Interaction, text: str = None) -> str:
        """Get input text from parameter or attachment"""
        if text:
            return text

        # Check for attachment
        if interaction.message and interaction.message.attachments:
            for attachment in interaction.message.attachments:
                if attachment.filename.endswith('.txt'):
                    try:
                        content = await attachment.read()
                        return content.decode('utf-8')
                    except:
                        pass

        return ""

    def get_available_algorithms(self) -> str:
        """Get formatted list of available algorithms"""
        algorithms = list(CRYPTO_FUNCTIONS.keys())
        return "、".join(algorithms[:15]) + f" 等 {len(algorithms)} 種演算法"

    @app_commands.command(name="crypto_encrypt", description="加密文本")
    @app_commands.describe(
        algo="加密演算法",
        text="要加密的文本（或上傳 .txt 檔案）",
        key="密鑰（AES 需要）",
        shift="偏移量（Caesar、Rail Fence 需要）"
    )
    async def crypto_encrypt(
        self,
        interaction: discord.Interaction,
        algo: str,
        text: str = None,
        key: str = None,
        shift: int = None
    ):
        # Get input text
        input_text = await self.get_input_text(interaction, text)
        if not input_text:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 缺少輸入",
                    description="請提供要加密的文本或上傳 .txt 檔案。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Check if algorithm exists
        algo_lower = algo.lower()
        if algo_lower not in CRYPTO_FUNCTIONS:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 不支援的演算法",
                    description=f"支援的演算法：{self.get_available_algorithms()}",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        encrypt_func, _ = CRYPTO_FUNCTIONS[algo_lower]

        # Check if algorithm is hash-only
        if encrypt_func and algo_lower in ['md5', 'sha1', 'sha256']:
            try:
                result = encrypt_func(input_text)

                embed = create_success_embed(
                    title=f"🔐 {algo.upper()} 雜湊",
                    guild_name=interaction.guild.name
                )

                if is_long_text(result):
                    file = await create_text_file(result, f"{algo_lower}_hash.txt")
                    embed.description = "結果過長，已輸出為附件。"
                    await interaction.response.send_message(embed=embed, file=file)
                else:
                    embed.description = f"```\n{result}\n```"
                    await interaction.response.send_message(embed=embed)

            except Exception as e:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        title="❌ 雜湊失敗",
                        description=str(e),
                        guild_name=interaction.guild.name
                    ),
                    ephemeral=True
                )
            return

        try:
            # Prepare parameters
            kwargs = {}
            if algo_lower in ['caesar'] and shift is not None:
                kwargs['shift'] = shift
            elif algo_lower in ['vigenere'] and key:
                kwargs['key'] = key
            elif algo_lower in ['railfence'] and shift is not None:
                kwargs['rails'] = shift
            elif algo_lower in ['aes-gcm', 'aesgcm', 'aes-cbc', 'aescbc']:
                if not key:
                    await interaction.response.send_message(
                        embed=create_error_embed(
                            title="❌ 缺少密鑰",
                            description="AES 加密需要 Base64 格式的 32 字節密鑰。",
                            guild_name=interaction.guild.name
                        ),
                        ephemeral=True
                    )
                    return
                kwargs['key_b64'] = key

            result = encrypt_func(input_text, **kwargs)

            embed = create_success_embed(
                title=f"🔐 {algo.upper()} 加密",
                guild_name=interaction.guild.name
            )

            if is_long_text(result):
                file = await create_text_file(result, f"{algo_lower}_encrypted.txt")
                embed.description = "結果過長，已輸出為附件。"
                await interaction.response.send_message(embed=embed, file=file)
            else:
                embed.description = f"```\n{result}\n```"
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 加密失敗",
                    description=str(e),
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )

    @app_commands.command(name="crypto_decrypt", description="解密文本")
    @app_commands.describe(
        algo="解密演算法",
        text="要解密的文本（或上傳 .txt 檔案）",
        key="密鑰（AES 需要）",
        shift="偏移量（Caesar、Rail Fence 需要）"
    )
    async def crypto_decrypt(
        self,
        interaction: discord.Interaction,
        algo: str,
        text: str = None,
        key: str = None,
        shift: int = None
    ):
        # Get input text
        input_text = await self.get_input_text(interaction, text)
        if not input_text:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 缺少輸入",
                    description="請提供要解密的文本或上傳 .txt 檔案。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        # Check if algorithm exists
        algo_lower = algo.lower()
        if algo_lower not in CRYPTO_FUNCTIONS:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 不支援的演算法",
                    description=f"支援的演算法：{self.get_available_algorithms()}",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        _, decrypt_func = CRYPTO_FUNCTIONS[algo_lower]

        # Check if decryption is available
        if not decrypt_func:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 不支援解密",
                    description="此演算法只支援單向操作（如雜湊）。",
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )
            return

        try:
            # Prepare parameters
            kwargs = {}
            if algo_lower in ['caesar'] and shift is not None:
                kwargs['shift'] = shift
            elif algo_lower in ['vigenere'] and key:
                kwargs['key'] = key
            elif algo_lower in ['railfence'] and shift is not None:
                kwargs['rails'] = shift
            elif algo_lower in ['aes-gcm', 'aesgcm', 'aes-cbc', 'aescbc']:
                if not key:
                    await interaction.response.send_message(
                        embed=create_error_embed(
                            title="❌ 缺少密鑰",
                            description="AES 解密需要 Base64 格式的 32 字節密鑰。",
                            guild_name=interaction.guild.name
                        ),
                        ephemeral=True
                    )
                    return
                kwargs['key_b64'] = key

            result = decrypt_func(input_text, **kwargs)

            embed = create_success_embed(
                title=f"🔓 {algo.upper()} 解密",
                guild_name=interaction.guild.name
            )

            if is_long_text(result):
                file = await create_text_file(result, f"{algo_lower}_decrypted.txt")
                embed.description = "結果過長，已輸出為附件。"
                await interaction.response.send_message(embed=embed, file=file)
            else:
                embed.description = f"```\n{result}\n```"
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_error_embed(
                    title="❌ 解密失敗",
                    description=str(e),
                    guild_name=interaction.guild.name
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(CryptoCog(bot))