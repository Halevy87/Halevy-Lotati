import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.activity import Activity
from app.models.address_resolution import AddressResolution
from app.models.case import Case
from app.models.enums import ActivityType
from app.schemas.address_resolution import (
    AddressResolutionOut,
    ManualResolutionRequest,
    ResolveAddressRequest,
)
from app.services import govmap

router = APIRouter(prefix="/api/cases", tags=["address-resolution"])

_ADDR_RE = re.compile(r"^(.*?)[\s,]*(\d+)(?:[/\-]\d+)?\s*$")


def _get_case_or_404(db: Session, case_id: uuid.UUID) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _split_address(address: str) -> tuple[str, str]:
    """Best-effort split of a free-text address into (street, number).

    Known limitation: addresses ending in a Hebrew apartment suffix (e.g. "הרצל 12א")
    won't match and are returned as (full_address, ""). GovMap autocomplete usually
    still resolves these via fuzzy matching.
    """
    m = _ADDR_RE.match((address or "").strip())
    if m:
        street = re.sub(r"[\s,/\-]+$", "", m.group(1)).strip()
        return street, m.group(2)
    return (address or "").strip(), ""


@router.post("/{case_id}/resolve-address", response_model=AddressResolutionOut)
def resolve_address(
    case_id: uuid.UUID, payload: ResolveAddressRequest, db: Session = Depends(get_db)
) -> AddressResolution:
    case = _get_case_or_404(db, case_id)

    street, number = payload.street, payload.number
    if not street or not number:
        parsed_street, parsed_number = _split_address(case.property_address)
        street = street or parsed_street
        number = number or parsed_number

    result = govmap.resolve(case.property_city, street, number)

    row = AddressResolution(
        case_id=case.id,
        city=case.property_city,
        street=street,
        number=number,
        apartment_number_claimed=payload.apartment_number_claimed,
        status=result.status,
        resolved_gush=result.gush,
        resolved_chelka=result.chelka,
        coordinates=result.coordinates,
        method=result.method,
        raw_response=result.raw_response,
        resolution_time_ms=result.resolution_time_ms,
    )
    db.add(row)

    if payload.apartment_number_claimed:
        case.apartment_number_claimed = payload.apartment_number_claimed

    if result.status == "auto_resolved":
        case.resolved_gush = result.gush
        case.resolved_chelka = result.chelka
        case.property_coordinates = result.coordinates
        if not case.block:
            case.block = result.gush
        if not case.parcel:
            case.parcel = result.chelka
        db.add(Activity(
            case_id=case.id,
            type=ActivityType.scraping_completed,
            description="כתובת נפתרה לגוש/חלקה",
            activity_metadata={"gush": result.gush, "chelka": result.chelka},
        ))
    else:
        db.add(Activity(
            case_id=case.id,
            type=ActivityType.scraping_failed,
            description="פתרון כתובת נכשל",
            activity_metadata={"status": result.status, "reason": result.reason},
        ))

    db.commit()
    db.refresh(row)
    return row


@router.get("/{case_id}/address-resolution", response_model=AddressResolutionOut)
def get_address_resolution(
    case_id: uuid.UUID, db: Session = Depends(get_db)
) -> AddressResolution:
    _get_case_or_404(db, case_id)
    row = (
        db.query(AddressResolution)
        .filter(AddressResolution.case_id == case_id)
        .order_by(AddressResolution.resolved_at.desc())
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="No address resolution yet")
    return row


@router.patch("/{case_id}/address-resolution/manual", response_model=AddressResolutionOut)
def manual_resolution(
    case_id: uuid.UUID, payload: ManualResolutionRequest, db: Session = Depends(get_db)
) -> AddressResolution:
    case = _get_case_or_404(db, case_id)

    row = AddressResolution(
        case_id=case.id,
        city=case.property_city,
        street="",  # manual entry has no street/number inputs; columns are NOT NULL
        number="",
        status="manual_entry",
        method="manual",
        resolved_gush=payload.gush,
        resolved_chelka=payload.chelka,
        resolved_tat_chelka=payload.tat_chelka,
    )
    db.add(row)

    case.resolved_gush = payload.gush
    case.resolved_chelka = payload.chelka
    case.resolved_tat_chelka = payload.tat_chelka
    if not case.block:
        case.block = payload.gush
    if not case.parcel:
        case.parcel = payload.chelka
    if payload.tat_chelka and not case.sub_parcel:
        case.sub_parcel = payload.tat_chelka

    db.add(Activity(
        case_id=case.id,
        type=ActivityType.note_added,
        description="גוש/חלקה הוזנו ידנית",
        activity_metadata={"gush": payload.gush, "chelka": payload.chelka},
    ))

    db.commit()
    db.refresh(row)
    return row
