from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.case import Case


def next_case_number(db: Session, *, now: datetime | None = None) -> str:
    """Generate the next case number in YYYY-NNNN format, sequential within the year."""
    year = (now or datetime.now(timezone.utc)).year
    prefix = f"{year}-"
    count = (
        db.query(func.count(Case.id)).filter(Case.case_number.like(f"{prefix}%")).scalar() or 0
    )
    return f"{prefix}{count + 1:04d}"
