import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.case import Case
from app.models.party import Party
from app.schemas.party import PartyCreate, PartyOut, PartyUpdate

router = APIRouter(prefix="/api/cases/{case_id}/parties", tags=["parties"])


def _ensure_case(db: Session, case_id: uuid.UUID) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("", response_model=list[PartyOut])
def list_parties(case_id: uuid.UUID, db: Session = Depends(get_db)) -> list[PartyOut]:
    _ensure_case(db, case_id)
    parties = db.query(Party).filter(Party.case_id == case_id).order_by(Party.created_at).all()
    return [PartyOut.model_validate(p) for p in parties]


@router.post("", response_model=PartyOut, status_code=201)
def create_party(
    case_id: uuid.UUID, payload: PartyCreate, db: Session = Depends(get_db)
) -> PartyOut:
    _ensure_case(db, case_id)
    party = Party(case_id=case_id, **payload.model_dump())
    db.add(party)
    db.commit()
    db.refresh(party)
    return PartyOut.model_validate(party)


@router.patch("/{party_id}", response_model=PartyOut)
def update_party(
    case_id: uuid.UUID,
    party_id: uuid.UUID,
    payload: PartyUpdate,
    db: Session = Depends(get_db),
) -> PartyOut:
    party = db.get(Party, party_id)
    if party is None or party.case_id != case_id:
        raise HTTPException(status_code=404, detail="Party not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(party, field, value)
    db.commit()
    db.refresh(party)
    return PartyOut.model_validate(party)
