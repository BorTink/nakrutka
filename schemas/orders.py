from pydantic import BaseModel


class Order(BaseModel):
    id: int
    group_id: str
    post_id: str
    full_amount: int
    left_amount: int
    completed: int
    stopped: int

