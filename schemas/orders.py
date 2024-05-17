from pydantic import BaseModel


class Order(BaseModel):
    id: int
    group_id: int
    post_id: int
    full_amount: int
    left_amount: int

    started: int
    completed: int
    stopped: int
    deleted: int


class OrderWithGroupInfo(BaseModel):
    id: int
    group_id: int
    post_id: int
    full_amount: int
    left_amount: int

    started: int
    completed: int
    stopped: int
    deleted: int

    group_link: str
