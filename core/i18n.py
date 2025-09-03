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

        # Add sub-tabs
        "ADD_TAB_INVOICE": "Invoice",
        "ADD_TAB_MANUAL": "Manual",
        "ADD_TAB_COMMON": "Common",
        "ADD_TAB_QUICK": "Quick",
        "SELECT_IMAGE": "Select Image (stub)",
        "SCAN_OCR": "Scan (OCR - later)",
        "RECENT": "Recent",
        "FREQUENT": "Frequent",
        "SELECTED_CATEGORY": "Selected: {name}",
        "ADD": "Add",
        "DUPLICATE": "Duplicate",
        "NO_DATA": "No data",
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

        "ADD_TAB_INVOICE": "發票",
        "ADD_TAB_MANUAL": "手動輸入",
        "ADD_TAB_COMMON": "常用",
        "ADD_TAB_QUICK": "快速",
        "SELECT_IMAGE": "選擇圖片（暫代）",
        "SCAN_OCR": "掃描（OCR 稍後）",
        "RECENT": "最近使用",
        "FREQUENT": "常用",
        "SELECTED_CATEGORY": "已選：{name}",
        "ADD": "加入",
        "DUPLICATE": "複製",
        "NO_DATA": "沒有資料",
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

        "ADD_TAB_INVOICE": "領収書",
        "ADD_TAB_MANUAL": "手動",
        "ADD_TAB_COMMON": "よく使う",
        "ADD_TAB_QUICK": "クイック",
        "SELECT_IMAGE": "画像を選択（仮）",
        "SCAN_OCR": "スキャン（OCR 後で）",
        "RECENT": "最近",
        "FREQUENT": "頻繁",
        "SELECTED_CATEGORY": "選択: {name}",
        "ADD": "追加",
        "DUPLICATE": "複製",
        "NO_DATA": "データなし",
    },
}

def t(key: str, **fmt) -> str:
    table = _STRINGS.get(LANG, _STRINGS["en"])
    s = table.get(key, _STRINGS["en"].get(key, key))
    return s.format(**fmt) if fmt else s
