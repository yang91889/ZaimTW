# features/add/tabs/__init__.py
# 統一優先使用 tab_base.py；若舊專案仍有 base.py，則退而求其次
try:
    from .tab_base import AddTabBase
except ImportError:
    from .tab_base import AddTabBase  # fallback（若你已刪掉 base.py，不會走到這裡）

from .tab_invoice import InvoiceTab
from .tab_manual import ManualTab
from .tab_common import CommonTab
from .tab_quick import QuickTab
from .manual import ManualTab


__all__ = ["AddTabBase", "InvoiceTab", "ManualTab", "QuickTab", "CommonTab"]
