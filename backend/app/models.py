import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, Uuid
from datetime import datetime, timezone
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    user_prompt = Column(Text, nullable=False)

    requirements = Column(JSON, nullable=False, default=dict)
    components = Column(JSON, nullable=False, default=list)
    bom = Column(JSON, nullable=False, default=list)

    wiring_diagram = Column(Text, nullable=False, default="")
    firmware = Column(Text, nullable=False, default="")
    final_report = Column(Text, nullable=False, default="")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
