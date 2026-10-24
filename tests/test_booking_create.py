"""Positive booking creation coverage."""

from pytest_check import check

from utils.booking_data import RESPONSE_FIELDS, expected_response

Booking = dict[str, object]


def test_create_booking_returns_201_with_id_and_submitted_data(
    created_booking: tuple[Booking, Booking],
) -> None:
    # The `created_booking` fixture already asserts HTTP 201.
    created, submitted = created_booking

    check.equal(set(created), {"bookingid", *RESPONSE_FIELDS}, "Unexpected response fields")
    check.is_true(isinstance(created.get("bookingid"), int) and created["bookingid"] > 0, "bookingid is not a positive integer")
    for field, value in expected_response(submitted).items():
        check.equal(created.get(field), value, f"Field '{field}' does not match the payload")
