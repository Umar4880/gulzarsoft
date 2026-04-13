from typing import TypedDict

class StateSchema(TypedDict):
    order_id: str
    order: list[str]
    delivered: bool