from pydantic import BaseModel


class Group(BaseModel):
    id: int
    name: str
    link: str
    amount: int
    reactions_amount: int
    setup: int
    auto_orders: int
    auto_reactions: int
    deleted: int
