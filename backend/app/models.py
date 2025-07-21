from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId

# This is a custom type to handle MongoDB's ObjectId.
# Pydantic V2 requires this setup for custom types.
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, *args, **kwargs) -> ObjectId:
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: dict, handler) -> None:
        schema.update(type="string")


class Category(str, Enum):
    RISK = "Risk-focused"
    OPPORTUNITY = "Opportunity-focused"

class ContentType(str, Enum):
    ARTICLE = "Article"
    PODCAST = "Podcast"
    PAPER = "Paper"

class ContentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Content(BaseModel):
    # Use our custom PyObjectId type for the id field.
    # It will be aliased as '_id' in the database.
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    url: HttpUrl
    title: str
    summary: List[str]
    original_text: Optional[str] = None
    transcript: Optional[str] = None
    source: str # e.g., RSS feed name, website name
    content_type: ContentType
    category: Category
    relevance_score: float = Field(default=0.0)
    helpful_votes: int = Field(default=0)
    not_helpful_votes: int = Field(default=0)
    status: ContentStatus = Field(default=ContentStatus.PENDING)
    editor_notes: Optional[str] = None
    metadata: Optional[dict] = None
    feedback: Optional[List[dict]] = None
    published_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    curated: bool = Field(default=False)

    # Use ConfigDict for Pydantic V2 configuration.
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True, # Allow custom types like PyObjectId
        json_encoders={ObjectId: str}, # Tell Pydantic how to serialize ObjectId to JSON
    )
