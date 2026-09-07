# Marketing Plan

## The cold-start problem, stated plainly

A directory with 3 drivers looks dead. A directory with 0 passenger
requests looks pointless to a driver. You have to seed both sides in the
same week, or the first users who try it bounce and don't come back.

## Phase 1 — Driver-side seeding (Week 1, before any passenger push)

Goal: 15–20 drivers listed before you tell a single passenger the site
exists. An empty directory kills trust instantly; a directory with real
names, real cars, and a few "Verified" badges doesn't.

1. Walk the existing rank (Mvurwi's taxi rank/mushika-shika base) in
   person. Don't cold-call — show up, show the site on your phone, sign
   the driver up on the spot using the signup form. Free tier, so there's
   no money objection.
2. Prioritise drivers who are already active in WhatsApp groups people use
   for "who has transport" requests — they'll naturally cross-post their
   profile link there once they have one (see `onboarding.md` for the
   exact WhatsApp script to hand them).
3. Get at least 5 drivers to "Verified" status in week 1 — check
   license/vehicle registration on the spot, tick it in Django admin.
   Verified badges are the trust signal that makes 3 more drivers sign up
   without you asking.

## Phase 2 — Passenger-side awareness (Week 2 onward)

Only start this once the directory has real drivers in it.

1. **WhatsApp Status + groups** — the cheapest channel for Mvurwi. Post a
   screenshot of the "24 taxis available now" homepage in 3–5 local
   groups (community, church, school-parent, vendor groups). One post,
   not a campaign — spammy repetition burns trust in a small town faster
   than it builds reach.
2. **Fare Board as the hook** — "What's the real price to Harare?" is a
   recurring argument at the rank. Screenshot the Fares page and post it
   whenever that argument comes up in a group. This is evergreen content,
   reusable indefinitely.
3. **Driver-as-marketer** — every driver's profile has a share button that
   copies a pre-written WhatsApp message. This is free distribution you
   don't have to run — but it only works once there's something on the
   other end of the link worth sharing (see Phase 1 first).
4. **Physical**: a printed A5 flyer with the fare board + "MvurwiTaxis.co.zw"
   at 2–3 high-traffic spots (rank, a shop counter, a church noticeboard)
   — cheap, and Mvurwi is small enough that word-of-mouth off one flyer
   travels.

## Phase 3 — Convert free drivers to Pro (ongoing)

Don't push Pro before a driver has felt at least one real free-tier lead
come through — pushing it earlier reads as a paywall, not a value prop.

- After a driver's 2nd or 3rd hot lead in a month (approaching the free
  cap), message them directly: "You're close to your free lead limit —
  Pro is $3/week and leads on top of that are free." This is a warm,
  specific pitch, not a broadcast.
- Track this manually at first (see `operations-daily.md`) — with driver
  volumes this low, a spreadsheet or the Django admin driver list sorted
  by `leads_used_this_month` is enough. Don't over-build automation for a
  problem you can watch by eye at this scale.

## What NOT to do early

- Don't run paid ads. Mvurwi's whole addressable market is small enough
  that free channels (WhatsApp, word of mouth, the rank itself) cover it;
  ad spend has no room to pay back at this scale yet.
- Don't discount the $0.20 hot-lead price to "grow faster" — it's already
  priced low enough to be a non-decision for a driver who just got a
  paying passenger. The bottleneck is awareness, not price resistance.
