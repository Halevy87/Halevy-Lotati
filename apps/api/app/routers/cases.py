import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.case_number import next_case_number
from app.core.db import get_db
from app.models.activity import Activity
from app.models.case import Case
from app.models.enums import ActivityType, CaseStatus
from app.models.party import Party
from app.schemas.case import (
    CaseCreate,
    CaseDetail,
    CaseList,
    CaseListItem,
    CaseUpdate,
)

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _get_case_or_404(db: Session, case_id: uuid.UUID) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("", response_model=CaseList)
def list_cases(
    db: Session = Depends(get_db),
    status: CaseStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> CaseList:
    query = db.query(Case)
    if status is not None:
        query = query.filter(Case.status == status)
    total = query.with_entities(func.count(Case.id)).scalar() or 0
    items = (
        query.order_by(Case.opened_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return CaseList(
        items=[CaseListItem.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CaseDetail, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> CaseDetail:
    lawyer_id = payload.primary_lawyer_id
    if lawyer_id is None:
        user = get_current_user(db)
        lawyer_id = user.id if user else None

    case = Case(
        case_number=next_case_number(db),
        status=CaseStatus.intake_pending,
        deal_type=payload.deal_type,
        block=payload.block,
        parcel=payload.parcel,
        sub_parcel=payload.sub_parcel,
        property_address=payload.property_address,
        property_city=payload.property_city,
        deal_value_ils=payload.deal_value_ils,
        primary_lawyer_id=lawyer_id,
        counterparty_lawyer_name=payload.counterparty_lawyer_name,
        counterparty_lawyer_phone=payload.counterparty_lawyer_phone,
    )
    db.add(case)
    db.flush()  # assign case.id

    if payload.primary_client is not None:
        db.add(Party(case_id=case.id, **payload.primary_client.model_dump()))

    db.add(
        Activity(
            case_id=case.id,
            user_id=lawyer_id,
            type=ActivityType.case_opened,
            description="התיק נפתח",  # "Case opened"
            activity_metadata={"case_number": case.case_number},
        )
    )
    db.commit()
    db.refresh(case)
    return CaseDetail.model_validate(case)


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: uuid.UUID, db: Session = Depends(get_db)) -> CaseDetail:
    return CaseDetail.model_validate(_get_case_or_404(db, case_id))


@router.patch("/{case_id}", response_model=CaseDetail)
def update_case(
    case_id: uuid.UUID, payload: CaseUpdate, db: Session = Depends(get_db)
) -> CaseDetail:
    case = _get_case_or_404(db, case_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return CaseDetail.model_validate(case)


@router.delete("/{case_id}", status_code=204)
def delete_case(case_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    case = _get_case_or_404(db, case_id)
    db.delete(case)
    db.commit()
