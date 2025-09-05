# features/add/tabs/tab_manual.py
# 兼容舊路徑：把類別從新的拆分模組 re-export 出來
from .manual.view import ManualTab
from .manual.widgets.key import Key
from .manual.widgets.currency_chip import CurrencyChip
from .manual.widgets.category_chip import CategoryChip
from .manual.currencies import CURRENCIES

__all__ = ["ManualTab", "Key", "CurrencyChip", "CategoryChip", "CURRENCIES"]
