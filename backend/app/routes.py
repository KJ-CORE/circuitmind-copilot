from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil

from app.database import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectResponse
from agents.graph import build_workflow
from rag.vector_db import ingest_datasheet

router = APIRouter()

@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    try:
        workflow = build_workflow()
        initial_state = {
            "user_prompt": payload.user_prompt,
            "iteration_count": 0,
            "feedback_notes": ""
        }

        final_state = workflow.invoke(initial_state)

        reqs = final_state.get("requirements", {})
        components = final_state.get("components", [])
        connections = final_state.get("connections", [])
        validation = final_state.get("validation", {})
        firmware = final_state.get("firmware", "")
        final_report = final_state.get("final_report", "")

        bom = []
        for index, comp in enumerate(components, 1):
            bom.append({
                "item_no": index,
                "name": comp.get("name"),
                "reason": comp.get("reason"),
                "quantity": 1
            })

        title = reqs.get("microcontroller", "Embedded System") + " Design"

        new_project = Project(
            title=title,
            user_prompt=payload.user_prompt,
            requirements=reqs,
            components=components,
            bom=bom,
            wiring_diagram=final_report.split("## 3. Physical Pin Connections")[0],
            firmware=firmware,
            final_report=final_report
        )

        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        return new_project

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Pipeline generation failed: {str(e)}")

@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    import uuid
    try:
        uuid_obj = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    project = db.query(Project).filter(Project.id == uuid_obj).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/rag/ingest", status_code=200)
async def ingest_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF datasheets are supported.")

    temp_dir = "temp_datasheets"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        chunks_count = ingest_datasheet(file_path)
        return {"status": "success", "filename": file.filename, "chunks_ingested": chunks_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)
