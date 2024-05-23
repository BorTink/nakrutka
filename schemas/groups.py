from pydantic import BaseModel


class Group(BaseModel):
    id: int
    name: str
    link: str
    amount: int
    setup: int
    auto_orders: int
    deleted: int
