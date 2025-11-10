from __future__ import annotations
from pydantic import BaseModel, AnyUrl, Field
from typing import Any, Dict, Optional

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: AnyUrl
    # allow extra fields
    class Config:
        extra = "allow"

class AcceptResponse(BaseModel):
    status: str = Field(default="accepted")
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    reason: str

class SubmitResult(BaseModel):
    correct: Optional[bool] = None
    url: Optional[str] = None
    reason: Optional[str] = None
    # other passthrough fields
    extra: Dict[str, Any] = Field(default_factory=dict)

