# MvurwiTaxis

Django + PWA taxi directory for Mvurwi. Drivers list for free; each driver
gets a monthly free-lead quota, then further leads go on a running tab
settled via EcoCash (manual) or Paynow (optional). Pro is a flat
subscription for unlimited free unlocks and top placement.

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
python manage.py generate_vapid_keys   # prints VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY for .env
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
free-quota → tab → settlement unlock path (including the double-unlock
race case), direct-message requests and their push/email notification,
core views (signup/login/dashboard/toggle-online/request-taxi), and the
admin bulk-confirm-payments action.

## Deployment (cPanel / Passenger / LiteSpeed — mathxuco pattern)

1. Upload/clone to your app directory, create a virtualenv via cPanel's
   "Setup Python App", point it at `passenger_wsgi.py`.
2. Set env vars in `.env` (not committed) — `DEBUG=False`, real `SECRET_KEY`,
   `ALLOWED_HOSTS`, EcoCash merchant number, `VAPID_PUBLIC_KEY`/
   `VAPID_PRIVATE_KEY` (see `manage.py generate_vapid_keys` above).
3. `python manage.py migrate`
4. `python manage.py collectstatic --noinput`
5. Static/media are served via the explicit `re_path` routes in
   `mvurwitaxis/urls.py` — same fix as other PHYB projects for Passenger's
   `SCRIPT_NAME` stripping. If you hit static 404s, check that
   `STATIC_ROOT`/`MEDIA_ROOT` resolve correctly under the app's working dir.
6. `python manage.py send_tab_reminders` on a weekly cron, to email drivers
   who have an unsettled tab balance.
7. Restart the app (`touch tmp/restart.txt` or via cPanel UI).

## Design decisions

- **SQLite, not Postgres/PostGIS** — matches shared-hosting reality; distance
  filtering uses plain haversine (`taxis/utils/geo.py`) instead of PostGIS.
  Fine at Mvurwi's driver volume; `busy_timeout` is set for write concurrency.
- **No websockets** — "GO ONLINE" sets a timestamp; a driver is "online" if
  within a rolling window (`ONLINE_STATUS_WINDOW_MINUTES`, default 30).
  Lead alerts use Web Push (`taxis/utils/push.py`) + email instead of a
  live socket connection.
- **Unlock pricing lives in `taxis/services.py`**, one rule order for every
  caller: Pro unlocks free; free-tier drivers get `FREE_TIER_LEAD_CAP` free
  unlocks/month; after that each unlock adds `HOT_LEAD_PRICE_USD` to a
  running tab instead of a pay-before-you-see-it step per lead. The tab
  falls due at `TAB_LIMIT_USD` or `TAB_MAX_DAYS`, whichever comes first;
  a driver settles it any time from `/dashboard/tab/`, via EcoCash
  (manual, admin-confirmed in Django admin) or Paynow.
- **Direct-message requests keep the lead on-platform.** A passenger can
  message one driver directly (`taxis:direct_request`) instead of only
  seeing a WhatsApp link; the driver gets a push + email, never the
  passenger's number until they unlock it. The passenger's status page is
  keyed by `Lead.token` (a UUID), not the sequential id, and every WhatsApp
  button — including the direct-message fallback — routes through
  `taxis:whatsapp_redirect` so the tap is still logged as a `Lead` even
  once the conversation moves to WhatsApp.
- **Paynow fields exist in settings for an optional automated payment path**
  but nothing assumes it's wired up; `PAYNOW_ENABLED` defaults to `False`.

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
- A real chat thread between passenger and driver. The direct-message
  feature is intentionally a one-shot request + push/email + WhatsApp
  handoff, not in-app back-and-forth — see the design-decisions note above
  for why.

## Changelog

**Direct-message requests + tab-based pricing**
- FAQ copy refreshed to describe the direct-message flow and tab pricing instead of the old WhatsApp-only / pay-per-lead wording; prices/limits are now pulled from settings instead of hardcoded.
- "Message {driver}" replaces the bare WhatsApp button on driver cards/
  profiles; reuses `RequestTaxiForm`'s fields via `LeadFormBase` so
  validation/help text match exactly.
- Unlock rules unified into `taxis/services.py`, replacing the old
  per-lead-payment `unlock_lead`/`claim_lead_pro` views with one
  `UnlockLeadView`. Weekly tab reminders via
  `python manage.py send_tab_reminders`.
- Email is now **required** at signup (`DriverSignupForm.email`); drivers
  who signed up before that are prompted in-dashboard (`needs_email`)
  until they add one. New signups get a welcome email with onboarding
  steps (`send_welcome_email`, `taxis/utils/emails.py`).
- Service worker moved to `/service-worker.js` (served by
  `taxis.views.service_worker`, not `/static/`) so its push scope covers
  the whole site, including `/dashboard/`.
- A floating "Chat with admin" WhatsApp button appears site-wide
  (`taxis/context_processors.py::site_contact`) whenever
  `WHATSAPP_ADMIN_NUMBER` is set.
- `driver_required` decorator added for the function-based driver views
  (dashboard, toggle-online, edit-profile, go-pro, post-going-to, push
  subscribe/unsubscribe), matching `DriverRequiredMixin` on the
  class-based ones — a logged-in account with no `Driver` profile now
  gets a clean 403 instead of a 500.

**Reliability fixes**
- `templates/404.html` extends `base.html`, which references
  `{% static 'manifest.json' %}` — if `collectstatic` hadn't run, Django's
  manifest storage raised instead of degrading, turning a harmless 404
  into a 500. `mvurwitaxis/storage.py` now logs a warning and serves the
  unhashed filename instead; still run `collectstatic` after every deploy.
- Fixed a debug-toolbar test-isolation bug (`SHOW_TOOLBAR_CALLBACK` closed
  over a stale `DEBUG=True` constant that disagreed with the test runner).
  `mvurwitaxis/settings/test.py` strips `debug_toolbar` out for the test
  process entirely.
- Taxi PWA icons generated (`static/img/icon-192.png`, `icon-512.png`).

**Foundations**
- Settings split: `mvurwitaxis/settings/{base,dev,prod,test}.py`. Dev uses
  plain static storage; prod uses WhiteNoise's manifest storage;
  `debug_toolbar` is dev-only.
- Full password reset/change flow via Django's built-in views, dark-themed
  templates in `templates/registration/`.
- Email notification to Pro drivers the instant a hot lead is created
  (`taxis/signals.py`).
- FAQ model + `/faqs/` page + `python manage.py seed_faqs` (idempotent; pass `--update-existing` after editing the seed copy to also refresh rows that already exist, e.g. pricing changes).
- Admin leads/payments dashboard at `/admin/leads-dashboard/`, linked from
  the top of the Django admin index.
- `/docs/` — marketing plan, daily operations, onboarding script, and
  growth notes for running this as an actual income stream, not just code.
- Star-rating widget for reviews (CSS-only); help text on every form field;
  custom 404/500 pages; `ADMINS`/email-on-crash wired in `settings/prod.py`;
  signup wrapped in a DB transaction so a failed Driver create can't leave
  an orphaned User account behind.
