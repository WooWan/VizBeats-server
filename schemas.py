from pydantic import BaseModel

class PostBase(BaseModel):
    title: str
    description: str | None = None

    class Config:
        orm_mode = True