"""Auth stub for Foundation.

There is NO real authentication in Foundation (by design — see the spec). This dependency
exists so that swapping in real magic-link + 2FA auth later is a one-line change: replace
the body to resolve the session user instead of returning the seeded dev user.
"""

from sqlalchemy.orm import Session

from app.models.user import User

DEV_USER_EMAIL = "ron@halevi-luttati.example"  # seeded dev user


def get_current_user(db: Session) -> User | None:
    """TODO: auth — return the authenticated user. For now, the first seeded dev user."""
    return db.query(User).filter(User.email == DEV_USER_EMAIL).first()
