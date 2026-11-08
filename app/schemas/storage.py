import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.storage import DocumentType


class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    product_category: str | None = Field(None, max_length=100)


class DocumentResponse(BaseModel):
    id: uuid.UUID
    folder_id: uuid.UUID
    document_name: str
    file_type: DocumentType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FolderResponse(BaseModel):
    id: uuid.UUID
    name: str
    product_category: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)