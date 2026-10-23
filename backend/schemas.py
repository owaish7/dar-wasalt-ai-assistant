from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=2000)
    history: list[Message] = Field(default_factory=list, max_length=8)
    language: Literal["en", "ar"] = "en"

    @field_validator("message")
    @classmethod
    def meaningful(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value

    @model_validator(mode="after")
    def bound_history(self):
        if sum(len(m.content) for m in self.history) > 8000:
            raise ValueError("History is too long")
        return self
