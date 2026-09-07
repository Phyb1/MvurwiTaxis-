# Onboarding

## Driver onboarding — in-person script (2 minutes)

Use this at the rank, phone in hand, signing them up live.

> "This is MvurwiTaxis — passengers search here for a taxi and message
> you straight on WhatsApp. It's free to list. You only pay 20 cents when
> we send you a specific passenger request, or $3/week if you want
> unlimited leads and to show up at the top."

Then, on your phone or theirs:

1. Go to `mvurwitaxis.co.zw/signup/`.
2. Fill in: name, phone number, a password they'll remember, car type,
   registration, seats, routes they cover.
3. If you have a car photo ready (or can take one now), attach it —
   listings with a photo get more clicks; this can also be added later
   from their dashboard.
4. Show them the **GO ONLINE** button on the dashboard — this is the one
   habit that matters. A driver who never goes online never shows as
   "Available now" and gets far fewer WhatsApp clicks.
5. Show them their **profile share link** and the one-tap "Share this
   profile" button — get them to post it to their WhatsApp Status right
   there. This is the single highest-leverage thing they can do for
   themselves.

Leave them with one sentence: *"Go online when you're working, and share
your link once — that's most of it."*

## Passenger onboarding — there isn't one, by design

Passengers should never need an account or an explanation. If a passenger
needs onboarding, something on the homepage is unclear — treat that as a
product bug, not a training gap. The one thing worth explaining verbally,
if asked: *"Tap WhatsApp on any driver, or use 'Request Any Taxi' if you
want it sent to everyone available."*

## Admin/operator onboarding (handing this over to someone else)

1. Get Django admin superuser access (`python manage.py createsuperuser`
   if setting up fresh).
2. Read `operations-daily.md` — that's the actual job, day to day.
3. Walk through confirming one real payment in admin before doing it live,
   so the EcoCash-reference-cross-check habit is second nature.
4. Know where the EcoCash merchant number and name live: `.env` →
   `ECOCASH_MERCHANT_NUMBER` / `ECOCASH_MERCHANT_NAME` — these render
   automatically on every payment page, don't hardcode them elsewhere.
