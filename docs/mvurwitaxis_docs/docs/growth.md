# Growth

## What to watch (in order of importance)

1. **Driver retention, not driver signups.** A driver who signs up and
   never goes online again is not a real driver. Track "drivers who
   went online in the last 7 days" over "drivers ever signed up" — the
   ratio matters more than the raw count.
2. **Message-to-response rate, not just leads sent.** Now that booking
   goes through in-platform messaging first, the number that actually
   reflects driver reliability is how many messages get a driver
   response before the passenger's status page falls back to WhatsApp
   or another driver. A driver getting leads but not responding to them
   is a retention problem wearing a demand problem's clothes.
3. **Leads per online driver.** If online drivers aren't getting leads,
   passenger-side awareness (see `campaign-14-day.md` and beyond) is the
   bottleneck, not driver supply — don't sign up more drivers to fix
   this.
4. **Free-to-Pro conversion rate.** The actual recurring revenue engine.
   Watch it monthly (Django admin, filter drivers by `pro_until`).
5. **Tab settlement lag.** How long, on average, between a tab hitting
   its threshold and a driver actually settling it. A growing lag here
   is an early warning sign for driver trust or cash-flow friction,
   worth catching before it shows up as churn.

## When to raise prices

Not before driver retention (metric 1) is healthy — a price rise on a
platform drivers don't trust yet just kills signups. Reasonable signal
to consider it: free-tier drivers routinely hitting the 3-lead cap *and*
still not upgrading to Pro — that's a sign the free tier is too generous
relative to Pro's value, not that the $0.20 unlock price itself is too
low.

## On Paynow

Paynow is already available where enabled, alongside EcoCash-manual, for
settling a tab or going Pro. Worth checking periodically whether Paynow
uptake is meaningfully reducing manual EcoCash-reference confirmation
work in `operations-daily.md` — if it is, that's a signal to make it the
more prominently offered option; if it isn't, leave the current balance
alone rather than pushing a preference nobody's actually using.

## When to expand beyond Mvurwi

Don't, until Mvurwi itself has:
- A stable base of 30+ active (recently-online) drivers
- Passengers using "Request Any Taxi" without being prompted (organic
  demand, not just profile clicks)
- A daily operations routine (`operations-daily.md`) that takes under 15
  minutes on a normal day — if it's still a heavy manual burden in one
  town, it will not survive being copy-pasted to a second one.

The natural next towns are the ones already on your fare board as
destinations (Bindura, Harare corridor) — but expansion means a second
fare board, a second driver-seeding push, and possibly a second EcoCash
merchant number if you want clean per-town reconciliation. Treat it as a
second Phase-1 launch (start a fresh `campaign-14-day.md`-style push for
that town), not a toggle.

## Product ideas explicitly deferred, and why

- **SMS notifications** — deliberately dropped in favour of push +
  email, to avoid a paid SMS gateway dependency with no revenue
  offsetting it. Revisit only if push/email open rates turn out too low
  in practice, not as a default upgrade.
- **Automated tab settlement reminders beyond the current weekly email**
  — the weekly reminder email exists; a second escalation tier (e.g. a
  push notification once a tab is actually paused) is a reasonable next
  step once tab settlement lag (see above) shows it's needed.
- **Multi-town / franchise model** — see "When to expand" above.
