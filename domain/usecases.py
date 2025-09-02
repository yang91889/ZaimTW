from __future__ import annotations
from core.eventbus import EventBus, EV_TX_CREATED
from core.utils import now_iso
from data.dao import TxDao


class UseCases:
def __init__(self, bus: EventBus):
self.bus = bus
self.txdao = TxDao()


def quick_add_tx(self, amount: float, category_id: int | None = None,
account_id: int = 1, book_id: int = 1,
tx_type: str = 'expense', currency: str = 'TWD',
note: str | None = None) -> int:
now = now_iso()
tx_id = self.txdao.insert_tx(
book_id=book_id, account_id=account_id, tx_type=tx_type,
amount=amount, currency=currency, category_id=category_id,
member_id=1, merchant=None, note=note, date=now,
updated_at=now, device_id='dev_local')
self.bus.publish(EV_TX_CREATED, {"tx_id": tx_id, "amount": amount})
return tx_id