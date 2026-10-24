# Restful Booker Platform – Booking API tests

API tests for the booking endpoints of <https://automationintesting.online>, written in Python with Pytest and Playwright's `APIRequestContext` (HTTP only, no browser).

## Approach

I first probed the live API to find out its actual behavior (status codes, auth, response shape), then wrote tests that assert that behavior exactly. Shared setup (base URL, request contexts, login, room lookup) lives in `conftest.py`. Payload builders live in `utils/booking_data.py`. Each test creates its own booking with a unique name and random far-future dates, because overlapping stays return 409 and the demo is shared and resets often. Nothing depends on existing data or on test order, and `roomid` is read from `/api/room` at runtime. Tests use soft assertions (`pytest-check`): every failed check is reported and the test keeps running to the end. Fixtures keep hard `assert`s, because a test cannot continue if its setup (login, booking creation) fails.

## What is automated, and why

| Area | Tests |
|---|---|
| Create (`POST /api/booking`, public) | Valid booking → 201, exact response fields, positive ID, data matches payload |
| Validation | Empty / incomplete payload → 400 with field errors; checkout before check-in → 409; overlapping dates for the same room → 409 |
| Read (`GET /api/booking?roomid=`) | No token → 401; with token → 200 with expected fields; **create → read back** by ID with matching data |
| Known defects (`xfail`) | `GET /api/booking/{id}` returns **500** for any ID; omitting `bookingdates` makes the request **hang** (no response) |

These cover the core booking flow and the validation rules a guest can hit. Known defects are marked `xfail` with a reason: they show as `XFAIL` and do not break the run, and they will show as `XPASS` once fixed.

### Known defects (expected failures)

Marked with `@pytest.mark.xfail(reason=...)`, the pytest equivalent of Playwright's `test.fail()`. They are reported as `XFAIL` with their reason and do not fail the run:

| Test | Defect |
|---|---|
| `test_get_booking_by_id_returns_created_booking` | `GET /api/booking/{id}` returns HTTP 500 for any ID, even for a booking that was just created and is visible in the room listing |
| `test_booking_without_dates_returns_client_error` | `POST /api/booking` without `bookingdates` never responds (request times out after 10 s) instead of returning a 4xx validation error |

**Not automated:** update/delete (`DELETE` also returns 500, so created bookings cannot be cleaned up; the demo reset handles that), rooms/branding/messages endpoints, the UI, and load testing.

## Install and run

Prerequisites: **Python 3.10+** and internet access.

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in the demo admin credentials shown on the site
pytest -v
```

No `playwright install` is needed. Each run writes an HTML report to `report/report.html`; the committed copy is the evidence of a run.

## Slow or unavailable site

Every request has a 15 s timeout. Tests that fail because of a network error or a 5xx response from setup are retried up to 2 times, 3 s apart (`pytest-rerunfailures`). Assertion failures are never retried, so real bugs are not hidden. Without credentials in `.env`, the tests that need a token are skipped and the rest still run.

## Assumptions

- Expected statuses and responses come from the live service's observed behavior (2026-10-23).
- The 409 for reversed dates has the same body as the overlap error. Random, non-overlapping dates make sure the date order is the cause.
- Credentials come from `.env`, which is git-ignored.

## With more time

- Field-level validation (email/phone format, name length, invalid `roomid`) as a data-driven table.
- JSON-schema validation of responses.
- A UI end-to-end flow: book as a guest, then verify the booking in the admin area.
- A CI pipeline with a scheduled run.
