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
cp .env.example .env          # edit SECRET_KEY, ALLOWED_HOSTS, EcoCash number/name
python manage.py makemigrations taxis   # migrations aren't committed — generate them locally first
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_faqs    # optional: adds starter FAQ content
python manage.py runserver
```

`manage.py` defaults to `mvurwitaxis.settings.dev` (debug toolbar on,
console email backend, no collectstatic required). Production entry
points (`wsgi.py`, `passenger_wsgi.py`) default to `mvurwitaxis.settings.prod`.
Override either with `DJANGO_SETTINGS_MODULE` if needed.

> **Migrations are not committed.** They were hand-written models in a
> sandbox with no Django installed, so I couldn't generate real migration
> files — running `makemigrations` yourself the first time is required,
> not optional. After that, commit the generated files as normal.

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
  only; the UI toggles correctly but there's no real redirect/webhook yet —
  `PAYNOW_ENABLED` defaults to `False` so the option stays hidden until it is).
- Analytics view (profile views / WhatsApp clicks tracking) from the spec's
  Week 3 scope — models support it (`Lead.driver_profile_viewed`) but there's
  no aggregation view/template yet.
- crispy-forms is wired in with the `bootstrap5` pack + custom dark-theme CSS
  overrides (`.form-control`, `.form-label`, etc. in `style.css`) rather than
  a hand-built template pack matching every design-system detail — functional
  and on-brand, but worth a visual pass if it needs to match pixel-for-pixel.

## Recent additions (this revision)

- **Fixed the production 500 you hit**: `templates/404.html` extends
  `base.html`, which references `{% static 'manifest.json' %}` — if
  `collectstatic` hasn't run (or ran before a file existed), Django's
  manifest storage raises instead of degrading, so even a harmless 404 was
  becoming a 500. Two fixes: (1) `mvurwitaxis/storage.py` adds a lenient
  manifest storage that logs a warning and serves the unhashed filename
  instead of raising — one missing entry can no longer take down the whole
  site; (2) run `collectstatic` after every deploy regardless (see
  `README` setup steps) — the lenient storage is a safety net, not a
  substitute for that.
- **Taxi PWA icons** generated (`static/img/icon-192.png`, `icon-512.png`)
  — dark rounded-square background, accent-green car silhouette, matches
  the design system. No more missing-icon gap in `manifest.json`.
- **Fixed a debug-toolbar test-isolation bug**: `SHOW_TOOLBAR_CALLBACK` was
  closing over a module-level `DEBUG=True` constant, which disagreed with
  Django's test runner overriding `settings.DEBUG` to `False` mid-session —
  the toolbar middleware kept trying to render a toolbar whose URLs were
  never registered (`NoReverseMatch: 'djdt'`). Fixed by adding
  `mvurwitaxis/settings/test.py` (pytest now points here), which strips
  `debug_toolbar` out entirely for the test process — it was never useful
  inside a test run anyway.

- **Settings split**: `mvurwitaxis/settings/{base,dev,prod}.py`. Dev uses
  plain static storage (no collectstatic needed for tests or local dev);
  prod uses WhiteNoise's manifest storage. `debug_toolbar` is dev-only.
- **Auth**: signup now captures email (optional) + car photo; full password
  reset/change flow via Django's built-in views with dark-themed templates
  in `templates/registration/`.
- **Pro drivers claim hot leads for free** — no EcoCash step, no admin
  confirmation (`taxis:claim_lead_pro`). This is the main lever for cutting
  manual payment-confirmation volume; free-tier drivers still go through
  manual EcoCash confirmation since there's no live gateway API.
- **Email notification to Pro drivers** the instant a hot lead is created
  (`taxis/signals.py`) — so they don't have to keep the dashboard open.
- **FAQ model + `/faqs/` page** + `python manage.py seed_faqs` to seed
  starter content for both passengers and drivers.
- **Admin leads/payments dashboard** at `/admin/leads-dashboard/`, linked
  from the top of the Django admin index.
- **`/docs/`** — marketing plan, daily operations, onboarding script, and
  growth notes for running this as an actual income stream, not just code.
- **Bug fixes**: driver/car photos now actually render on the homepage and
  driver profile (they were captured but never displayed); WhatsApp CTA
  buttons show the driver's full name instead of just the first letter;
  driver signup now correctly accepts the uploaded photo file
  (`request.FILES` was previously dropped).
- Payment pages now name the EcoCash recipient (`ECOCASH_MERCHANT_NAME`)
  alongside the number, and hide the EcoCash proof fields when Paynow is
  selected (JS avoids `:has()` for older Android WebView compatibility).
- Star-rating widget for reviews (CSS-only), help text on ratings and on
  the phone-number/photo signup fields, headings + spacing on the homepage
  filter bar and driver list.
- Custom 404/500 pages; `ADMINS`/email-on-crash wired in `settings/prod.py`;
  signup is wrapped in a DB transaction so a failed Driver create can't
  leave an orphaned User account behind.
