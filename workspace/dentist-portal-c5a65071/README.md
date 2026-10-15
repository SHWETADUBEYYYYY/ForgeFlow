# Anna Dental Clinic Portal

A clean, responsive website and staff portal for Anna Dental Clinic, built with
FastAPI, Jinja2, SQLite (SQLAlchemy), and vanilla JavaScript.

## Features

- Public landing page with clinic info, services, opening hours, and contact details.
- Appointment request form with server-side and client-side validation.
- Staff login with pbkdf2_hmac password hashing and signed session cookies (itsdangerous).
- Staff dashboard to review appointment requests and update their status
  (new / contacted / closed).
- Responsive layout that adapts to mobile widths.

## Running locally

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Then open http://127.0.0.1:8000/ for the public site and
http://127.0.0.1:8000/login for the staff portal.

## Demo staff credentials

On first run a demo staff user is created:

- Username: `staff`
- Password: `dental123`

Override these with the `STAFF_USERNAME` and `STAFF_PASSWORD` environment
variables. Set `SESSION_SECRET` in production; otherwise a random per-process
secret is generated (sessions reset on restart).

## Notes

- Appointment requests are stored locally in `dental_clinic.db` (SQLite).
- This is a demo portal: no real payments are processed and requests are not
  real bookings.

## Tests

```bash
python -m pytest -q
```
