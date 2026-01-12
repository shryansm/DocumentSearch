from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentIn(BaseModel):
    id: str
    title: str
    content: str

class DocumentStored(BaseModel):
    tenant: str
    docId: str
    title: str
    content: str
    createdAt: datetime
