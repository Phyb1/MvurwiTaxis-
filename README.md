# MvurwiTaxis

Django + PWA taxi directory for Mvurwi. Pay-per-lead + Pro subscription model,
EcoCash-manual payments primary, Paynow as a secondary/automated fallback.

## Requirements

Python 3.10–3.14. Pinned to **Django 5.2 LTS** specifically because 5.1 and
earlier break on Python 3.14 (`LazyObject`/template-context internals raise
`AttributeError: 'super' object has no attribute 'dicts'`) — 5.2 is the first
release with 3.14 support. If your Termux Python is 3.14, don't downgrade
Django to fix this; the pin above already targets the right line.

## Local setup (Termux/Ubuntu proot)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit SECRET_KEY, ALLOWED_HOSTS, EcoCash number
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Running tests

```bash
pytest
```

Covers: haversine geo math, WhatsApp link building, driver model logic
(pro/online windows, monthly free-tier caps, slug generation), the
lead-unlock → payment-confirm revenue path (including the double-unlock
race case), core views (signup/login/dashboard/toggle-online/request-taxi),
and the admin bulk-confirm-payments action.

> This project was scaffolded in a sandboxed environment with no network
> access, so the suite has been syntax-checked but not executed end-to-end.
> Run `pytest` yourself after `pip install -r requirements.txt` before
> deploying — flag anything that fails and I'll fix it in the next revision.

## Deployment (cPanel / Passenger / LiteSpeed — mathxuco pattern)

1. Upload/clone to your app directory, create a virtualenv via cPanel's
   "Setup Python App", point it at `passenger_wsgi.py`.
2. Set env vars in `.env` (not committed) — `DEBUG=False`, real `SECRET_KEY`,
   `ALLOWED_HOSTS`, EcoCash merchant number.
3. `python manage.py migrate`
4. `python manage.py collectstatic --noinput`
5. Static/media are served via the explicit `re_path` routes in
   `mvurwitaxis/urls.py` — same fix as other PHYB projects for Passenger's
   `SCRIPT_NAME` stripping. If you hit static 404s, check that
   `STATIC_ROOT`/`MEDIA_ROOT` resolve correctly under the app's working dir.
6. Restart the app (`touch tmp/restart.txt` or via cPanel UI).

## Design decisions locked from the spec

- **SQLite, not Postgres/PostGIS** — matches shared-hosting reality; distance
  filtering uses plain haversine (`taxis/utils/geo.py`) instead of PostGIS.
  Fine at Mvurwi's driver volume; `busy_timeout` is set for write concurrency.
- **No websockets** — "GO ONLINE" sets a timestamp; a driver is "online" if
  within a rolling window (`ONLINE_STATUS_WINDOW_MINUTES`, default 30).
- **No SMS gateway** — lead notification is a dashboard badge (poll-on-load)
  plus WhatsApp deep links, matching the `whatsapp.py` utility pattern used
  across other PHYB client sites.
- **Payments** — EcoCash manual (reference number and/or proof screenshot,
  admin-confirmed in Django admin via the `confirm_payments` bulk action) is
  primary. Paynow fields exist in settings for a later automated integration
  but nothing in the payment flow assumes it's wired up yet.

## What's not built yet (flag for next revision)

- Paynow automated integration (fields are stubbed in `.env.example`/settings
  only).
- Push-style lead alerts beyond dashboard polling (e.g. WhatsApp Business
  API webhook) — deferred per the "no SMS dependency" decision above.
- PWA icons (`static/img/icon-192.png`, `icon-512.png`) are referenced in
  `manifest.json` but not included — drop in real PNGs before shipping.
- Analytics view (profile views / WhatsApp clicks tracking) from the spec's
  Week 3 scope — models support it (`Lead.driver_profile_viewed`) but there's
  no aggregation view/template yet.
