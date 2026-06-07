from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

class ProjectCreate(BaseModel):
    user_prompt: str = Field(..., description="The natural language electronics requirements prompt.")

class ProjectBase(BaseModel):
    title: str
    user_prompt: str
    requirements: Dict[str, Any]
    components: List[Dict[str, Any]]
    bom: List[Dict[str, Any]]
    wiring_diagram: str
    firmware: str
    final_report: str

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    components: Optional[List[Dict[str, Any]]] = None
    bom: Optional[List[Dict[str, Any]]] = None
    wiring_diagram: Optional[str] = None
    firmware: Optional[str] = None
    final_report: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ComponentSelectionRequest(BaseModel):
    requirements: Dict[str, Any]

class ValidationRequest(BaseModel):
    components: List[Dict[str, Any]]
    requirements: Dict[str, Any]
