# core/i18n.py
from __future__ import annotations
from typing import Dict
from .settings import LANG

_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "TAB_HOME": "Home",
        "TAB_BALANCE": "Balance",
        "TAB_ADD": "Add",
        "TAB_HISTORY": "History",
        "TAB_ANALYSIS": "Analysis",
        "QUICK_ADD": "Quick Add",
        "AMOUNT": "Amount",
        "ADD_EXPENSE": "Expense",
        "CLEAR": "Clear",
        "ENTER_AMOUNT": "Please enter amount",
        "RECORDED_TX": "Recorded transaction #{id}",
        "ANALYSIS_PLACEHOLDER": "Analysis (placeholder)",
    },
    "zh-TW": {
        "TAB_HOME": "首頁",
        "TAB_BALANCE": "餘額",
        "TAB_ADD": "新增",
        "TAB_HISTORY": "歷史",
        "TAB_ANALYSIS": "分析",
        "QUICK_ADD": "快速記帳",
        "AMOUNT": "金額",
        "ADD_EXPENSE": "支出",
        "CLEAR": "清除",
        "ENTER_AMOUNT": "請輸入金額",
        "RECORDED_TX": "已記錄交易 #{id}",
        "ANALYSIS_PLACEHOLDER": "分析（佔位）",
    },
    "ja": {
        "TAB_HOME": "ホーム",
        "TAB_BALANCE": "残高",
        "TAB_ADD": "追加",
        "TAB_HISTORY": "履歴",
        "TAB_ANALYSIS": "分析",
        "QUICK_ADD": "クイック入力",
        "AMOUNT": "金額",
        "ADD_EXPENSE": "支出",
        "CLEAR": "クリア",
        "ENTER_AMOUNT": "金額を入力してください",
        "RECORDED_TX": "取引を記録しました #{id}",
        "ANALYSIS_PLACEHOLDER": "分析（プレースホルダー）",
    },
}

def t(key: str, **fmt) -> str:
    table = _STRINGS.get(LANG, _STRINGS["en"])
    s = table.get(key, _STRINGS["en"].get(key, key))
    return s.format(**fmt) if fmt else s
