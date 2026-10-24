"""Validation and date edge cases, asserted against the behavior observed on the live API."""

import pytest
from playwright.sync_api import APIRequestContext, Error
from pytest_check import check

from utils.booking_data import make_booking_payload

Booking = dict[str, object]


@pytest.mark.parametrize(
    ("payload", "expected_errors"),
    [
        pytest.param(
            {},
            {"must be greater than or equal to 1", "Firstname should not be blank", "Lastname should not be blank"},
            id="empty-object",
        ),
        pytest.param(
            {"firstname": "Ana", "lastname": "Tester"},
            {"must be greater than or equal to 1"},
            id="missing-roomid-and-dates",
        ),
    ],
)
def test_incomplete_booking_returns_400_with_field_errors(
    api_request: APIRequestContext, payload: Booking, expected_errors: set[str]
) -> None:
    response = api_request.post("/api/booking", data=payload)

    check.equal(response.status, 400, f"HTTP {response.status}: {response.text()}")
    errors = set(response.json().get("errors", [])) if response.status == 400 else set()
    for message in expected_errors:
        check.is_in(message, errors, f"Missing validation error '{message}'")


def test_checkout_before_checkin_is_rejected_with_409(
    api_request: APIRequestContext, booking_payload: Booking
) -> None:
    # Random far-future dates ensure the 409 comes from the date order, not an overlap.
    dates = booking_payload["bookingdates"]
    booking_payload["bookingdates"] = {"checkin": dates["checkout"], "checkout": dates["checkin"]}

    response = api_request.post("/api/booking", data=booking_payload)

    check.equal(response.status, 409, f"HTTP {response.status}: {response.text()}")
    check.equal(response.json(), {"error": "Failed to create booking"})


def test_overlapping_booking_for_same_room_is_rejected_with_409(
    api_request: APIRequestContext, created_booking: tuple[Booking, Booking], room_id: int
) -> None:
    _, first = created_booking
    overlapping = make_booking_payload(room_id, bookingdates=first["bookingdates"])

    response = api_request.post("/api/booking", data=overlapping)

    check.equal(response.status, 409, f"HTTP {response.status}: {response.text()}")


@pytest.mark.xfail(raises=Error, reason="Observed defect: omitting bookingdates leaves the request hanging")
def test_booking_without_dates_returns_client_error(api_request: APIRequestContext, booking_payload: Booking) -> None:
    del booking_payload["bookingdates"]

    response = api_request.post("/api/booking", data=booking_payload, timeout=10_000)

    check.between_equal(response.status, 400, 499, f"HTTP {response.status}: {response.text()}")
