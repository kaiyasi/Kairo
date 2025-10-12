"""
Kairo - Discord Bot Framework

一個功能豐富的 Discord Bot 框架，提供多種實用功能模組。

Author: Serelix Studio
License: 見 LICENSE 檔案
"""

__version__ = "1.0.0"
__author__ = "Serelix Studio"
__email__ = "serelixstudio@gmail.com"

# 匯入主要模組
from . import utils
from . import cogs

__all__ = [
    "utils",
    "cogs",
]
