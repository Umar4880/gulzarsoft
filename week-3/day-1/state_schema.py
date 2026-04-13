from typing import TypedDict, Annotated
import operator
class StateSchema(TypedDict):
    #user details
    user_name: str
    phone_no: int

    #order_details
    order_id: str
    order_list: Annotated[list[str], operator.add]
    is_delivered: bool

    #time details
    order_placed_time: float
