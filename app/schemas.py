from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class QuestionCreate(BaseModel):
    leetcode_id: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=255)
    approach: str = Field(min_length=1)


class QuestionRead(BaseModel):
    id: int
    leetcode_id: str
    title: str
    approach: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
