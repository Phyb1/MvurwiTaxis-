# Daily Operations

What admin actually does each day to keep the platform trustworthy and
the 14-day campaign moving. Written so someone else could take this
over with minimal handover — see `operations-manual.md` for the
procedures behind each item below.

## Every day (10–15 minutes, more during the campaign — see below)

1. **Confirm pending Tab settlements and Pro payments.** Check EcoCash/
   Paynow against the reference or screenshot submitted, then confirm
   in admin. Drivers can keep unlocking leads while a settlement's
   pending, so there's no urgency pressure here — but don't let it sit
   past the same day if you can help it, since a driver watching their
   tab is watching how reliable you are.
2. **Check for drivers whose tab has hit $1.00 or is 7 days old** and
   hasn't been settled — their new unlocks are now paused. A quick
   WhatsApp nudge here recovers a driver who simply forgot, rather than
   losing them to frustration at an unexplained pause.
3. **Check for unread/unanswered passenger messages sitting more than
   ~20–30 minutes.** If a driver hasn't responded, that passenger's
   status page will start offering WhatsApp or another driver anyway —
   but a direct nudge to the driver first often saves the lead before
   it gets there.
4. **Remind any driver who isn't online.** A driver who never taps GO
   ONLINE gets zero leads — check who's been offline for more than a
   day and reach out.

## During the 14-day campaign specifically (see `campaign-14-day.md`)

- Post the day's scheduled content (WhatsApp Status/social).
- Personally contact that day's target number of new drivers.
- Follow up with anyone warm from the day before.
- Log every contact in `campaign-tracker.md` the same day — source,
  status (contacted → interested → signed up → verified → active), not
  at the end of the week.
- Update the running driver count wherever it's referenced in that
  day's post before it goes out.

## Weekly

1. **Verify new drivers.** License + vehicle registration, then confirm
   in admin — see `operations-manual.md` for the verification
   procedure.
2. **Check notification setup for drivers who seem to be missing
   leads** — this is very often an iPhone driver who never added the
   site to their home screen, not a platform bug.
3. **Send yourself a reminder-email test** to confirm the weekly
   tab-reminder email is actually going out — this is dashboard-user-
   facing trust, worth a manual spot check rather than assuming it's
   working.
4. **Reconcile the week's confirmed payments** against your EcoCash/
   Paynow statements.

## When something breaks

- Check the Django error log first.
- A driver reporting "I never got notified" — check (1) email is set
  on their account, (2) they've tapped "Turn on request notifications,"
  (3) if iPhone, whether they added the site to their home screen
  first. In that order — it's almost always one of these three, not a
  platform bug.
- A driver disputing their tab total — check the unlock history on
  their dashboard against admin's record before assuming either side is
  wrong; see `operations-manual.md`'s dispute procedure.
- A passenger reporting "the driver never responded" — this is expected
  to self-resolve via the status page's WhatsApp/another-driver fallback,
  not something admin needs to intervene on directly unless it's
  happening with the same driver repeatedly.
