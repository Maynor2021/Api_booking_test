"""Booking read, authentication and create-then-read integration coverage."""

from collections.abc import Callable

import pytest
from playwright.sync_api import APIRequestContext
from pytest_check import check

from utils.booking_data import RESPONSE_FIELDS, expected_response

Booking = dict[str, object]


def test_booking_list_without_token_returns_401(api_request: APIRequestContext, room_id: int) -> None:
    response = api_request.get("/api/booking", params={"roomid": room_id})

    check.equal(response.status, 401, f"HTTP {response.status}: {response.text()}")
    check.equal(response.json(), {"error": "Authentication required"})


def test_booking_list_returns_bookings_with_expected_fields(
    authenticated_api: APIRequestContext, room_id: int
) -> None:
    response = authenticated_api.get("/api/booking", params={"roomid": room_id})

    check.equal(response.status, 200, f"HTTP {response.status}: {response.text()}")
    bookings = response.json().get("bookings") if response.ok else None
    check.is_instance(bookings, list, "Response has no 'bookings' list")
    for booking in bookings or []:
        booking_id = booking.get("bookingid")
        check.equal(set(booking), {"bookingid", *RESPONSE_FIELDS}, f"Unexpected fields in booking {booking_id}")
        check.is_true(isinstance(booking_id, int) and booking_id > 0, f"Invalid bookingid {booking_id!r}")
        check.equal(booking.get("roomid"), room_id, f"Booking {booking_id} belongs to another room")


def test_created_booking_is_retrievable_with_submitted_data(
    created_booking: tuple[Booking, Booking],
    find_booking: Callable[[int, int], Booking | None],
) -> None:
    created, submitted = created_booking

    stored = find_booking(submitted["roomid"], created["bookingid"])

    check.is_not_none(stored, f"Booking {created['bookingid']} not found in room listing")
    for field, value in expected_response(submitted).items():
        check.equal((stored or {}).get(field), value, f"Stored field '{field}' does not match the payload")


@pytest.mark.xfail(reason="Observed defect: GET /api/booking/{id} returns HTTP 500 for any id")
def test_get_booking_by_id_returns_created_booking(
    authenticated_api: APIRequestContext, created_booking: tuple[Booking, Booking]
) -> None:
    created, submitted = created_booking

    response = authenticated_api.get(f"/api/booking/{created['bookingid']}")

    check.equal(response.status, 200, f"HTTP {response.status}: {response.text()}")
    body = response.json() if response.ok else {}
    check.equal(body.get("bookingid"), created["bookingid"])
    check.equal(body.get("firstname"), submitted["firstname"])
