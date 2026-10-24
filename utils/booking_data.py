"""Booking test data builders, kept separate from test logic."""

import random
from datetime import date, timedelta
from uuid import uuid4

# Fields the API echoes back on create and in the room listing (email/phone are write-only).
RESPONSE_FIELDS = ("roomid", "firstname", "lastname", "depositpaid", "bookingdates")


def random_stay(nights: int = 2) -> dict[str, str]:
    """Return a far-future stay unlikely to overlap other runs, since overlaps return 409."""
    checkin = date.today() + timedelta(days=random.randint(400, 4000))
    checkout = checkin + timedelta(days=nights)
    return {"checkin": checkin.isoformat(), "checkout": checkout.isoformat()}


def make_booking_payload(room_id: int, **overrides: object) -> dict[str, object]:
    unique = uuid4().hex[:8]
    payload: dict[str, object] = {
        "roomid": room_id,
        "firstname": f"Qa{unique}",
        "lastname": "Automation",
        "depositpaid": True,
        "email": f"qa-{unique}@example.com",
        "phone": "07123456789",
        "bookingdates": random_stay(),
    }
    payload.update(overrides)
    return payload


def expected_response(payload: dict[str, object]) -> dict[str, object]:
    return {field: payload[field] for field in RESPONSE_FIELDS}
