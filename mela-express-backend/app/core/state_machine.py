"""
Parcel status state machine.
Pure Python — no FastAPI or SQLAlchemy imports.

ALLOWED_TRANSITIONS: maps each ParcelStatus to its set of permitted next statuses.
validate_transition: raises ValueError on disallowed transitions.
"""
# TODO: implement (Task 4.1)
