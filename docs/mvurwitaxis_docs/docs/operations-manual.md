# Operations Manual

Step-by-step procedures for running MvurwiTaxis day to day. Written so
anyone taking over admin duties — including future-you, six months from
now — can follow these without having to remember why each step exists.
`operations-daily.md` is the short daily checklist; this is what backs
it up.

## 1. Driver verification procedure

**Trigger:** a driver sends a photo of their license and vehicle
registration, or asks to be verified.

1. Confirm the name on the license matches the driver's profile name.
2. Confirm the vehicle registration is current (not expired).
3. If both check out: mark the driver Verified in admin. They'll now
   rank higher in the directory and show the Verified badge.
4. If something doesn't match or looks off: message the driver directly
   asking for a clearer photo or an explanation — don't verify on a
   guess, and don't leave them wondering why nothing happened. A
   verification that turns out to be wrong costs more trust than a
   short delay ever will.
5. Log the verification date — useful later if a registration needs
   re-checking after renewal.

**Target turnaround:** same day, ideally within a few hours — a driver
who sends documents and hears nothing for days starts to doubt the
platform is actually staffed by anyone.

## 2. Tab settlement / Pro payment confirmation procedure

**Trigger:** a driver submits an EcoCash reference (or screenshot) or a
Paynow payment on their Tab page.

1. Open the pending Payment in admin.
2. Cross-check the reference against your own EcoCash/Paynow statement
   for that amount.
3. If it matches: confirm the payment. For a tab settlement, this zeroes
   their tab. For a Pro payment, this activates/extends Pro status.
4. If it doesn't match (wrong amount, reference not found): don't
   confirm — message the driver asking them to double check what they
   sent, and hold the payment as pending until it's resolved.
5. Confirmation should happen within minutes during the day, not
   overnight — drivers are told they can keep unlocking leads while a
   settlement's pending, but a payment sitting unconfirmed for a full
   day still reads as neglect, not as "no urgency."

## 3. Dispute procedure (a driver questions their tab total)

1. Pull up the driver's unlock history on their dashboard — every
   unlock past their free quota is logged with a timestamp.
2. Compare it against what they're disputing. Most disputes are a
   driver genuinely forgetting an unlock, not an error — walk them
   through the specific entries rather than just asserting the total is
   right.
3. If the log genuinely shows a mistake (a duplicate charge, an unlock
   that shouldn't have counted): adjust it manually in admin and tell
   the driver plainly what was wrong and what you fixed.
4. If the log is correct and the driver still disagrees: this is a
   trust conversation, not a technical one — explain the mechanism
   (20 cents per unlock past quota) clearly rather than just repeating
   the total.

## 4. Notification troubleshooting procedure

**Trigger:** a driver says they're not getting alerted to new leads.

Check in this order — it's almost always one of these three:

1. **Is an email set on their account?** If not, add one — nothing
   after this step works without it.
2. **Have they tapped "Turn on request notifications" on their
   dashboard?** If not, walk them through it.
3. **Are they on iPhone, and did they add the site to their home screen
   first (Share → Add to Home Screen)?** Push notifications don't work
   from Safari directly on iOS — this single step accounts for most
   "notifications don't work" reports from iPhone drivers.

Only escalate as a platform bug once all three check out and the driver
still isn't getting alerted.

## 5. Driver suspension / removal procedure

**Trigger:** a driver is unresponsive to passengers repeatedly, a
passenger reports a serious problem, or a driver's documents turn out
to be invalid.

1. For a first unresponsiveness pattern: message the driver directly
   first — this is often fixable with a reminder, not a suspension.
2. For a repeated pattern, or a serious passenger complaint: suspend the
   listing (don't delete — history is worth keeping) and message the
   driver explaining exactly why.
3. For invalid documents discovered after verification: un-verify
   immediately and follow up for corrected documents before restoring
   Verified status.
4. Always leave a clear, dated note on the driver's record — you or
   whoever's running admin next will need the context later.

## 6. Admin handover procedure

If someone else is taking over admin duties, even temporarily:

1. Give them Django admin superuser access.
2. Walk them through `operations-daily.md` live — don't just hand them
   the document.
3. Have them shadow one real tab confirmation and one real verification
   before doing either alone.
4. Make sure they know where the platform's own EcoCash/Paynow details
   live and how to check a payment against them.
5. Point them to this manual and tell them plainly: when something
   doesn't fit a documented procedure, the right move is to ask, not
   guess — these procedures exist because guessing wrong here costs
   driver trust, which is the hardest thing to rebuild in a market this
   small.

## 7. Refund / goodwill procedure

**Trigger:** a driver or passenger has a legitimate complaint that
warrants a gesture (a charged unlock for a lead that turned out to be
fake, a verification error that cost a driver visibility for days).

There's no formal refund mechanism built into the platform — handle
this manually:

1. Confirm the complaint is legitimate using the relevant procedure
   above (dispute procedure for tab issues, verification procedure for
   badge issues).
2. For a tab issue: adjust the tab manually in admin, as in the dispute
   procedure.
3. For anything else (lost visibility, a bug that affected them): use
   judgment — a free week of Pro or a tab credit is a reasonable
   goodwill gesture for a real platform failure. Document what was
   given and why.
