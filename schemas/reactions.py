from datetime import datetime

from pydantic import BaseModel


class Reaction(BaseModel):
    id: int
    group_id: int
    post_id: int
    full_amount: int
    left_amount: int

    started: int
    completed: int
    stopped: int
    reaction_deleted: int

    last_update: datetime
    created_date: datetime


class ReactionWithGroupInfo(BaseModel):
    id: int
    group_id: int
    post_id: int
    full_amount: int
    left_amount: int
    hour: int

    started: int
    completed: int
    stopped: int
    reaction_deleted: int

    last_update: datetime
    created_date: datetime

    group_link: str
