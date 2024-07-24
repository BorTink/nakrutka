from datetime import datetime

from pydantic import BaseModel


class Sub(BaseModel):
    id: int
    group_id: int
    full_amount: int
    left_amount: int
    hour: int

    started: int
    completed: int
    stopped: int
    sub_deleted: int

    last_update: datetime
    created_date: datetime


class SubWithGroupInfo(BaseModel):
    id: int
    group_id: int
    full_amount: int
    left_amount: int
    hour: int

    started: int
    completed: int
    stopped: int
    sub_deleted: int

    last_update: datetime
    created_date: datetime

    group_link: str
