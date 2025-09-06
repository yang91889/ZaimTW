# features/add/tabs/manual/controller.py
from __future__ import annotations

class ManualController:
    def __init__(self, *, decimals: int = 0,
                 on_render=None, on_highlight=None, on_equals_mode=None):
        # 狀態
        self.mode = "expense"
        self.buffer = "0"
        self.left = None
        self.op = None

        # 流程旗標
        self.equals_mode = False        # UI 是否顯示 '='
        self.just_evaluated = False     # 剛按過 '='
        self.fresh = True               # 剛換運算子、等待右值第一顆數字
        self.awaiting_rhs = False       # 正在等右運算元（已選了運算子）

        # 小數位
        self.decimals = int(decimals or 0)

        # UI 回呼（view 會丟進來）
        self.on_render = on_render or (lambda _text: None)
        self.on_highlight = on_highlight or (lambda _sym: None)
        self.on_equals_mode = on_equals_mode or (lambda _on: None)

        self._render()

    # ───── 公開給 view 呼叫的事件 ─────
    def set_mode(self, m: str):
        self.mode = m

    def set_currency_decimals(self, d: int):
        self.decimals = int(d or 0)
        self.buffer = self._normalize(self.buffer)
        self._render()

    def on_num(self, token: str):
        if self.just_evaluated:
            self._reset_formula_only()

        if self.fresh:
            self.buffer = "0" if token == "00" else token
            self.fresh = False
        else:
            if token == "00":
                if "." in self.buffer:
                    self.buffer += "00"
                else:
                    self.buffer = (self.buffer.lstrip("0") or "0") + "00"
            else:
                self.buffer += token

        self.buffer = self._normalize(self.buffer)
        self._render()

    def on_dot(self):
        if self.decimals <= 0:
            return
        if self.just_evaluated:
            self._reset_formula_only()

        if self.fresh:
            self.buffer = "0."
            self.fresh = False
            self._render()
            return

        if "." not in self.buffer:
            self.buffer += "."
            self.buffer = self._normalize(self.buffer)
            self._render()

    def on_op(self, ui_sym: str):
        mapping = {"+": "+", "−": "-", "×": "*", "÷": "/"}
        new_op = mapping[ui_sym]

        # 已有運算子、尚未輸右值 → 只換運算子，不清不算
        if self.op is not None and self.fresh:
            self.op = new_op
            self._highlight(ui_sym)
            self._set_equals_mode(True)
            self.just_evaluated = False
            return

        # 一般：掛上/串算
        self._apply_pending(op_switch=new_op)

        self.awaiting_rhs = True
        self.fresh = True
        self.just_evaluated = False

        self._highlight(ui_sym)
        self._set_equals_mode(True)

    def on_equals(self):
        if self.op is None or self.left is None:
            self._set_equals_mode(False)
            self._highlight(None)
            return

        cur = self._parse(self.buffer)
        res = self._calc(self.left, cur, self.op)

        self.buffer = self._format(res)
        self.left, self.op = None, None
        self._highlight(None)
        self._set_equals_mode(False)

        self.awaiting_rhs = False
        self.fresh = True
        self.just_evaluated = True
        self._render()

    def on_next(self) -> bool:
        """回傳 True 表示 view 應該執行『送出/下一步』；False 表示應該先做 equals。"""
        if self.equals_mode:
            self.on_equals()
            return False
        return True

    def on_backspace(self):
        if self.just_evaluated:
            self.just_evaluated = False

        if self.fresh:
            return

        s = self.buffer[:-1] if len(self.buffer) > 1 else "0"
        self.buffer = self._normalize(s, for_backspace=True)
        self._render()

    # ───── 內部邏輯 ─────
    def _apply_pending(self, op_switch: str | None):
        cur = self._parse(self.buffer)
        if self.op is None:
            self.left = cur
        else:
            self.left = self._calc(self.left, cur, self.op)
            self.buffer = self._format(self.left)
            self._render()
        self.op = op_switch
        self.buffer = "0"

    def _calc(self, a: float, b: float, op: str) -> float:
        try:
            if op == "+": return a + b
            if op == "-": return a - b
            if op == "*": return a * b
            if op == "/": return a / b if b != 0 else a
        except Exception:
            pass
        return b

    def _parse(self, s: str) -> float:
        try:
            return float(s)
        except Exception:
            return 0.0

    def _normalize(self, s: str, *, for_backspace: bool = False) -> str:
        s = (s or "").strip()
        if s in ("", "+", "-"):
            return "0"

        neg = s.startswith("-")
        body = s[1:] if neg else s

        d = int(self.decimals or 0)
        if "." in body:
            int_part, frac = body.split(".", 1)
            int_part = (int_part.lstrip("0") or "0")
            if d >= 0:
                frac = frac[:d]
            if for_backspace and frac == "":
                body = int_part           # "1." → "1"
            else:
                if d == 0:
                    body = int_part       # 幣種不允許小數
                else:
                    body = int_part + "." + frac
        else:
            body = (body.lstrip("0") or "0")

        if body == "0":
            neg = False                   # -0 → 0
        return ("-" if neg else "") + body

    def _format(self, v: float) -> str:
        d = int(self.decimals or 0)
        s = f"{v:.{d}f}"
        s = s.rstrip("0").rstrip(".")
        if s in ("", "-0", "-0.0"):
            s = "0"
        return s or "0"

    def _reset_formula_only(self):
        self.left = None
        self.op = None
        self.equals_mode = False
        self._highlight(None)
        self.awaiting_rhs = False
        self.fresh = True
        self.just_evaluated = False
        self.buffer = "0"

    # ───── UI 回呼封裝 ─────
    def _render(self):
        self.on_render(self.buffer)

    def _highlight(self, sym: str | None):
        self.on_highlight(sym)

    def _set_equals_mode(self, on: bool):
        self.equals_mode = bool(on)
        self.on_equals_mode(self.equals_mode)
