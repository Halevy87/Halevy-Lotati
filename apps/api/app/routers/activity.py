import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.activity import Activity
from app.models.case import Case
from app.schemas.activity import ActivityOut

router = APIRouter(prefix="/api/cases/{case_id}/activity", tags=["activity"])


@router.get("", response_model=list[ActivityOut])
def list_activity(case_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ActivityOut]:
    if db.get(Case, case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    activities = (
        db.query(Activity)
        .filter(Activity.case_id == case_id)
        .order_by(Activity.created_at.desc())
        .all()
    )
    return [ActivityOut.model_validate(a) for a in activities]
