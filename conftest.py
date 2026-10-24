"""Shared Playwright API fixtures for the booking tests."""

import os
from collections.abc import Callable, Generator

import pytest
from dotenv import load_dotenv
from playwright.sync_api import APIRequestContext, Playwright

from utils.booking_data import make_booking_payload

load_dotenv()  # Reads credentials from a local, git-ignored .env file.

BASE_URL = os.getenv("BOOKER_BASE_URL", "https://automationintesting.online").rstrip("/")
TIMEOUT_MS = 15_000

Booking = dict[str, object]


def _new_context(playwright: Playwright, headers: dict[str, str] | None = None) -> APIRequestContext:
    return playwright.request.new_context(
        base_url=BASE_URL,
        extra_http_headers={"Accept": "application/json", **(headers or {})},
        timeout=TIMEOUT_MS,
    )


@pytest.fixture(scope="session")
def api_request(playwright: Playwright) -> Generator[APIRequestContext, None, None]:
    """Unauthenticated context; booking creation is public."""
    context = _new_context(playwright)
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def authenticated_api(
    playwright: Playwright, api_request: APIRequestContext
) -> Generator[APIRequestContext, None, None]:
    """Context carrying the admin `token` cookie, required to list bookings."""
    username = os.getenv("BOOKER_USERNAME")
    password = os.getenv("BOOKER_PASSWORD")
    if not username or not password:
        pytest.skip("Set BOOKER_USERNAME and BOOKER_PASSWORD in .env to run authenticated booking tests")

    response = api_request.post("/api/auth/login", data={"username": username, "password": password})
    assert response.status == 200, f"Login failed: HTTP {response.status}: {response.text()}"
    token = response.json().get("token")
    assert isinstance(token, str) and token, "Login response did not contain a token"

    context = _new_context(playwright, {"Cookie": f"token={token}"})
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def room_id(api_request: APIRequestContext) -> int:
    """Use a room that exists now, since the demo data resets periodically."""
    response = api_request.get("/api/room")
    assert response.status == 200, f"Room listing failed: HTTP {response.status}"
    rooms = response.json()["rooms"]
    assert rooms, "The demo environment has no rooms to book"
    return rooms[0]["roomid"]


@pytest.fixture
def booking_payload(room_id: int) -> Booking:
    return make_booking_payload(room_id)


@pytest.fixture
def created_booking(api_request: APIRequestContext, booking_payload: Booking) -> tuple[Booking, Booking]:
    """Create a fresh booking and return (response body, submitted payload).

    No cleanup: DELETE /api/booking/{id} currently returns HTTP 500; the demo resets its data.
    """
    response = api_request.post("/api/booking", data=booking_payload)
    assert response.status == 201, f"Create booking failed: HTTP {response.status}: {response.text()}"
    return response.json(), booking_payload


@pytest.fixture
def find_booking(authenticated_api: APIRequestContext) -> Callable[[int, int], Booking | None]:
    """Look a booking up through the room listing, the working read endpoint."""

    def _find(room: int, booking_id: int) -> Booking | None:
        response = authenticated_api.get("/api/booking", params={"roomid": room})
        assert response.status == 200, f"Booking listing failed: HTTP {response.status}: {response.text()}"
        return next((b for b in response.json()["bookings"] if b["bookingid"] == booking_id), None)

    return _find
