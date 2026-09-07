# Daily Operations

What admin (you, or whoever runs this day-to-day) actually needs to do.
Written so someone else could take this over with minimal handover.

## Every day (5–10 minutes, morning and evening)

1. Open **Admin → Leads & Payments Dashboard** (`/admin/leads-dashboard/`,
   linked from the top of the Django admin home page).
2. **Confirm pending payments.** Each row shows the driver, amount, and
   EcoCash reference/proof. Cross-check the reference against your EcoCash
   SMS/statement, then either:
   - Confirm it in Django admin (Payments → select → "Confirm selected
     payments" action) — this auto-unlocks the lead or extends Pro, you
     don't do anything else manually.
   - If it doesn't check out, leave it pending and message the driver.
3. **Check open hot leads with no unlock.** If a lead has been open more
   than ~30 minutes with no driver claiming/paying, WhatsApp a few online
   drivers directly — a live passenger is the thing you can least afford
   to leave hanging.

Note: Pro drivers don't generate a pending-payment row when they claim a
lead — that's free and instant for them (see `README.md` → "Why this
wins" for the reasoning). The dashboard's "Free Pro claims today" number
is what tells you this is working — the higher it is relative to "Unlocked
today", the less manual confirmation work you have.

## Weekly

1. **Verify new drivers.** Check license/vehicle reg for anyone who signed
   up in the last week but isn't yet "Verified" — do this in person or via
   a WhatsApp photo request, then tick it in Django admin (Drivers →
   select → "Mark selected drivers as Verified").
2. **Skim reviews.** Anything under 3 stars — reach out to the driver
   directly; a pattern of low reviews is the one thing that can quietly
   kill passenger trust in the whole platform.
3. **Update the Fare Board** if fuel prices or route conditions changed
   enough that drivers are quoting differently from what's listed — a
   stale fare board undermines the "this is the truth for Mvurwi" pitch.

## Monthly

1. **Reconcile revenue** — sum confirmed EcoCash payments for the month
   against your EcoCash statement (Payments list, filter by month,
   status=Confirmed).
2. **Review the free-tier cap.** If most active drivers are hitting 3
   leads/month comfortably without upgrading, the cap may be too generous
   — see `growth.md` for when/how to reconsider pricing.
3. **Suspend inactive/problem drivers.** Drivers with `is_active_listing`
   still true but no online activity in 60+ days clutter the directory —
   unlist them (Drivers → select → "Suspend selected drivers") rather than
   deleting, so history is kept.

## When something breaks

- Check `logs/django.log` first — errors are logged there with full
  tracebacks.
- In production, unhandled 500 errors also email `ADMIN_EMAIL` (set in
  `.env`) automatically — if you're not getting these emails, check that
  var is set and `EMAIL_HOST` is configured.
- If a driver reports a payment "not going through": check Payments in
  admin first — most "it's broken" reports are actually a payment sitting
  in Pending, waiting on you.
