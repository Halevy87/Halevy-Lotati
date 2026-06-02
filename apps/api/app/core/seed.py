"""Seed local dev data. FAKE data only — Foundation must not hold real PII."""

from app.core.db import SessionLocal
from app.models.enums import UserRole
from app.models.user import User

DEV_USERS = [
    {
        "email": "ron@halevi-luttati.example",
        "full_name": "רון הלוי",
        "role": UserRole.partner,
        "bar_license_number": "00000",
    },
    {
        "email": "lev@halevi-luttati.example",
        "full_name": "לב לוטטי",
        "role": UserRole.partner,
        "bar_license_number": "00001",
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        for data in DEV_USERS:
            if not db.query(User).filter(User.email == data["email"]).first():
                db.add(User(**data))
        db.commit()
        print(f"Seeded {len(DEV_USERS)} dev users (fake).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
