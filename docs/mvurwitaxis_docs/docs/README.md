# MvurwiTaxis — Business Docs

Operating documents for running MvurwiTaxis as an income stream, not
just a codebase. Living documents — edit them as reality diverges from
the plan.

**This folder replaces two earlier, unreconciled campaign drafts** — the
numbered set (`01_14_day_campaign.md` through `06_social_graphic_explained.md`
plus the 12 poster images) and the separate `docs/docs/` set
(`14-day-calendar.md`, `content-bank.md`, `driver-message-variants.md`,
`status-variants.md`, `video-variants.md`, `campaign-tracker.md`). Both
were written before in-platform messaging shipped, so both lead with
"tap WhatsApp" as the primary CTA — which is no longer accurate. Archive
or delete those; everything current lives here now. The 12 poster
images are still good visual assets — reuse them, but pair them with
the copy in `campaign-14-day.md`, not their original captions.

## Running the business

- [`onboarding.md`](./onboarding.md) — the driver onboarding script,
  end to end: signup, first login, first lead.
- [`operations-daily.md`](./operations-daily.md) — the daily admin
  checklist: what to do, in what order, every day.
- [`operations-manual.md`](./operations-manual.md) — the procedures
  behind the checklist: how to verify a driver, settle a tab, handle a
  dispute, hand over admin access. Read this once; refer to
  `operations-daily.md` day to day.
- [`growth.md`](./growth.md) — what to watch, when to raise prices,
  when to expand beyond Mvurwi.

## Running the campaign

- [`campaign-14-day.md`](./campaign-14-day.md) — the single, current
  14-day driver-recruitment calendar. Day 1 is today.
- [`campaign-content-bank.md`](./campaign-content-bank.md) — driver DM
  variants and WhatsApp Status posts, ready to use in rotation.
- [`campaign-video-ideas.md`](./campaign-video-ideas.md) — short video
  concepts and scripts for the fortnight.
- [`campaign-tracker.md`](./campaign-tracker.md) — the fortnight
  tracking sheet.
- [`homepage-messaging.md`](./homepage-messaging.md) — what's already
  shipped on the homepage, and what's still worth testing next.

## The one number that matters early on

Drivers won't pay for a platform with no leads. Passengers won't use a
directory with no drivers. Cold-start risk is the single biggest threat
to this business — everything in these docs is ordered to attack that
first.

## What's actually live right now (baseline for every doc in this folder)

- **5 drivers listed.** Every "X/20" reference in the campaign docs
  starts counting from here.
- **In-platform messaging is the primary booking flow.** A passenger
  taps "Message" on a driver's card, not WhatsApp — that sends the trip
  details straight to the driver (who's alerted by push + email, but
  doesn't see the passenger's number until they respond) and gives the
  passenger a private status link that updates itself and offers
  WhatsApp or another driver if the first one doesn't reply. WhatsApp is
  still on every profile as a backup, not the headline.
- **Pricing**: free tier is $0 to list, 3 free leads/month, ranked at
  the bottom. Pro is $3/week or $10/month — unlimited free unlocks, top
  placement.
- **The tab system**: unlocking a lead past your free quota adds $0.20
  to a running tab rather than asking for payment in the moment — no
  payment step, no waiting on admin before you can call the passenger.
  The tab must be settled once it hits $1.00 or is 7 days old.
- **Verification**: admin checks license + vehicle registration.
  Verified drivers rank higher and get trusted more by passengers.
