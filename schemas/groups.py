from pydantic import BaseModel


class Group(BaseModel):
    name: str
    link: str
