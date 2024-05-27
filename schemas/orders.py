from datetime import datetime

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
    order_deleted: int

    last_update: datetime
    created_date: datetime


class OrderWithGroupInfo(BaseModel):
    id: int
    group_id: int
    post_id: int
    full_amount: int
    left_amount: int
    hour: int

    started: int
    completed: int
    stopped: int
    order_deleted: int

    last_update: datetime
    created_date: datetime

    group_link: str
