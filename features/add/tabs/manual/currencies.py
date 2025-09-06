# features/add/tabs/manual/currencies.py
CURRENCIES = [
    {"code": "JPY", "symbol": "¥",  "decimals": 0},
    {"code": "TWD", "symbol": "NT$", "decimals": 0},   # 若想顯示角分，改成 2
    {"code": "USD", "symbol": "$",  "decimals": 2},
    {"code": "EUR", "symbol": "€",  "decimals": 2},
    {"code": "CNY", "symbol": "¥",  "decimals": 2},
    {"code": "HKD", "symbol": "HK$","decimals": 2},
    {"code": "KRW", "symbol": "₩",  "decimals": 0},
]

CURRENCY_DECIMALS = {c["code"]: c["decimals"] for c in CURRENCIES}

def on_currency_changed(self, code: str):
    dp = CURRENCY_DECIMALS.get(code, 2)
    self.calc.decimals = dp  # 只設定，別重算 buffer
    self._refresh_amount_label()