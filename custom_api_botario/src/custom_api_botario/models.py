from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BotarioMetadata(BaseModel):
    node_name: str = Field(default="", alias="__node_name__")
    active_story_name: str = Field(default="", alias="__active_story_name__")

    @field_validator("node_name", "active_story_name", mode="before")
    @classmethod
    def none_to_empty(cls, v: Optional[str]) -> str:
        return v if v is not None else ""


class BotarioResponsePayload(BaseModel):
    active_story: str = ""
    metadata: BotarioMetadata = Field(default_factory=BotarioMetadata)
    text: str = ""
    type: str = ""
    streamed: bool = False


class BotarioResponse(BaseModel):
    type: str = ""
    name: str = ""
    payload: BotarioResponsePayload
    timestamp: str = ""
    id: str = ""
    public_event: bool = True


# BotarioCompletion models (outgoing completion request)
class BotarioCompletionPayload(BaseModel):
    type: str = "text"
    text: str


class BotarioCompletion(BaseModel):
    payload: BotarioCompletionPayload
    sessionId: str
    startUrl: str = ""
