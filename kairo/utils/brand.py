import discord
from datetime import datetime
from typing import Optional

class BrandColors:
    MORANDI_GRAY_BLUE = 0x8B9DC3
    MORANDI_MIST_PINK = 0xDDB7AB
    MORANDI_MUTED_GREEN = 0xA3B5A0
    MORANDI_SLATE_GRAY = 0x708090
    MORANDI_LIGHT_BROWN = 0xB8A082

    @classmethod
    def get_primary(cls) -> int:
        return cls.MORANDI_GRAY_BLUE

    @classmethod
    def get_secondary(cls) -> int:
        return cls.MORANDI_SLATE_GRAY

    @classmethod
    def get_success(cls) -> int:
        return cls.MORANDI_MUTED_GREEN

    @classmethod
    def get_warning(cls) -> int:
        return cls.MORANDI_LIGHT_BROWN

    @classmethod
    def get_error(cls) -> int:
        return cls.MORANDI_MIST_PINK

def create_brand_embed(
    title: str = None,
    description: str = None,
    color: int = None,
    guild_name: str = "Kairo Service"
) -> discord.Embed:
    if color is None:
        color = BrandColors.get_primary()

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )

    embed.set_author(name=guild_name)
    embed.set_footer(text="Service by Serelix Studio")

    return embed

def create_success_embed(
    title: str = None,
    description: str = None,
    guild_name: str = "Kairo Service"
) -> discord.Embed:
    return create_brand_embed(
        title=title,
        description=description,
        color=BrandColors.get_success(),
        guild_name=guild_name
    )

def create_error_embed(
    title: str = None,
    description: str = None,
    guild_name: str = "Kairo Service"
) -> discord.Embed:
    return create_brand_embed(
        title=title,
        description=description,
        color=BrandColors.get_error(),
        guild_name=guild_name
    )

def create_info_embed(
    title: str = None,
    description: str = None,
    guild_name: str = "Kairo Service"
) -> discord.Embed:
    return create_brand_embed(
        title=title,
        description=description,
        color=BrandColors.get_secondary(),
        guild_name=guild_name
    )