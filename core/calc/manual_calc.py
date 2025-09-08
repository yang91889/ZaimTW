# features/add/tabs/manual/logic.py
import re
from dataclasses import dataclass

@dataclass
class ManualCalc:
    decimals: int = 0  # 幣種小數位（JPY=0, USD/CNY=2 ...）

    def __post_init__(self):
        self.reset()

    def reset(self):
        self.left = None     # 左運算元
        self.op = None       # '+','-','*','/'
        self.buffer = "0"    # 目前輸入中的字串
        self.await_rhs = False   # 剛按完運算子，等待右運算元
        self.equals_mode = False # 是否把「NEXT」顯示為 '='

    # —— 輸入（數字 / 00 / . / 退格）—————————————
    def input_digit(self, d: str):
        assert d in "0123456789"
        if self.await_rhs:
            self.buffer = "0"  # 開始輸入右運算元，先清
            self.await_rhs = False
        if self.buffer == "0":
            self.buffer = d if d != "0" else "0"
        else:
            self.buffer += d
        self._normalize_typing()

    def input_double_zero(self):
        if self.await_rhs:
            self.buffer = "0"
            self.await_rhs = False
        # 沒有小數點時避免堆出 00000
        if "." in self.buffer:
            self.buffer += "00"
        else:
            self.buffer = self.buffer if self.buffer == "0" else self.buffer + "00"
        self._normalize_typing()

    def input_dot(self):
        if self.await_rhs:
            self.buffer = "0"
            self.await_rhs = False
        if "." not in self.buffer:
            self.buffer += "."
        # 若幣種不允許小數，直接忽略
        if self.decimals == 0:
            self.buffer = self.buffer.replace(".", "")
        self._normalize_typing()

    def backspace(self):
        s = (getattr(self, "buffer", "") or "")
        if not s:
            self.buffer = "0"
            return

        s = s[:-1]

        if s in ("", "-", "-.", "."):
            self.buffer = "0"
        else:
            self.buffer = s

        self._normalize_typing()

        # ★ 這三行：退格後若尾端只剩小數點，收掉它（避免顯示 '51.'）
        if self.buffer.endswith("."):
            self.buffer = self.buffer[:-1] or "0"

    # —— 運算子 / 等號 / 取得結果 ——————————————
    def op_press(self, op: str):
        # op in '+-*/'
        cur = self._to_float(self.buffer)
        if self.op is None:
            self.left = cur
        else:
            # 若已有 pending 且不是剛切換（右值未輸入），只換運算子不計算
            if not self.await_rhs:
                self.left = self._calc(self.left, cur, self.op)
                self.buffer = self._fmt_amount(self.left)
        self.op = op
        self.await_rhs = True
        self.equals_mode = True

    def equals(self):
        if self.op is None or self.left is None:
            self.equals_mode = False
            return self.buffer
        cur = self._to_float(self.buffer)
        res = self._calc(self.left, cur, self.op)
        self.left, self.op, self.await_rhs = None, None, False
        self.buffer = self._fmt_amount(res)
        self.equals_mode = False
        return self.buffer

    # —— 工具 ————————————————————————————————
    def _to_float(self, s: str) -> float:
        try: return float(s)
        except: return 0.0

    def _calc(self, a: float, b: float, op: str) -> float:
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/": return a / b if b != 0 else a
        return b

    def _normalize_typing(self):
        """
        把使用者輸入的數字字串標準化：
        - 容忍 '-', '.', '-.' 這些半完成輸入（轉回 '0'）
        - 僅保留 0-9 和一個小數點
        - 去除多餘前導 0（但保留 '0.xxx'）
        - 避免 '-0'（負零）這種表示
        - 不要破壞使用者剛輸入的 '12.'（允許尾端小數點存在）
        """
        s = (getattr(self, "buffer", "") or "").strip()

        # 半完成輸入 → 回到 '0'
        if s in ("", "-", ".", "-."):
            self.buffer = "0"
            return

        # 處理負號
        neg = s.startswith("-")
        if neg:
            s = s[1:]

        # 只留數字和小數點；如果有多個小數點，只保留第一個
        s = re.sub(r"[^0-9.]", "", s)
        if s.count(".") > 1:
            first, rest = s.split(".", 1)
            rest = rest.replace(".", "")
            s = first + "." + rest

        # 以 '.' 開頭 → 變成 '0.xxx'
        if s.startswith("."):
            s = "0" + s

        # 如果尾端是 '.'（使用者剛按下小數點），暫時保留，不做進一步數值轉換
        if s.endswith("."):
            # 去除整數部位的多餘前導零（'000.' → '0.'）
            int_part = re.sub(r"^0+(?=\d)", "", s[:-1]) or "0"
            self.buffer = ("-" if neg and int_part != "0" else "") + int_part + "."
            return

        if "." in s:
            # 小數
            int_part, frac_part = s.split(".", 1)
            int_part = re.sub(r"^0+(?=\d)", "", int_part) or "0"
            # 僅保留數字小數
            frac_part = re.sub(r"[^0-9]", "", frac_part)

            # 若小數部空了，就只保留整數
            if frac_part == "":
                s_norm = int_part
            else:
                s_norm = int_part + "." + frac_part

            # 避免負零（-0 或 -0.0）
            if int_part == "0" and (frac_part == "" or int(frac_part or "0") == 0):
                neg = False

            self.buffer = ("-" if neg else "") + s_norm
        else:
            # 整數
            int_part = re.sub(r"^0+(?=\d)", "", s) or "0"
            if int_part == "0":
                neg = False
            self.buffer = ("-" if neg else "") + int_part

    def _fmt_amount(self, v: float) -> str:
        # 顯示階段按幣種位數四捨五入
        s = f"{v:.{self.decimals}f}"
        # 去掉 -0.00 -> 0.00
        if float(s) == 0.0:
            s = f"{0:.{self.decimals}f}"
        return s
