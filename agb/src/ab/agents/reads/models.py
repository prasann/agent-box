"""Source-independent bookmark snapshot contract."""

from datetime import datetime
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator


class Bookmark(BaseModel):
    item_id: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1, max_length=8192)
    title: str = Field(max_length=4096)
    folder_path: str = Field(default="", max_length=4096)
    saved_at: datetime | None = None

    @field_validator("url")
    @classmethod
    def web_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Bookmarks require an HTTP(S) URL without credentials")
        return value


class Snapshot(BaseModel):
    source_id: str = Field(min_length=1, max_length=512)
    profile_id: str = Field(min_length=1, max_length=512)
    folder_id: str = Field(min_length=1, max_length=512)
    revision: int = Field(ge=1)
    complete: bool = False
    items: list[Bookmark] = Field(max_length=10_000)

    @model_validator(mode="after")
    def unique_items(self) -> "Snapshot":
        if len({item.item_id for item in self.items}) != len(self.items):
            raise ValueError("Snapshot contains duplicate bookmark IDs")
        return self