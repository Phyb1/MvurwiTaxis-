# Growth

## What to watch (in order of importance)

1. **Driver retention, not driver signups.** A driver who signs up and
   never goes online again is not a real driver. Track "drivers who went
   online in the last 7 days" over "drivers ever signed up" — the ratio
   matters more than the raw count.
2. **Leads per online driver.** If online drivers aren't getting leads,
   passenger-side awareness (see `marketing-plan.md`) is the bottleneck,
   not driver supply — don't sign up more drivers to fix this.
3. **Free-to-Pro conversion rate.** This is the actual revenue engine.
   Watch it monthly (Django admin, filter drivers by `pro_until`).
4. **Manual confirmation load** (the leads dashboard: "Unlocked today" vs
   "Free Pro claims today"). As Pro adoption grows, this should trend down
   — if it isn't, either Pro isn't attractive enough or admin is spending
   time it shouldn't need to.

## When to raise prices

Not before driver retention (metric 1) is healthy — a price rise on a
platform drivers don't trust yet just kills signups. Reasonable signal to
consider it: free-tier drivers routinely hitting the 3-lead cap *and*
still not upgrading — that's a sign the free tier is too generous relative
to Pro's value, not that hot-lead pricing itself is too low.

## When to expand beyond Mvurwi

Don't, until Mvurwi itself has:
- A stable base of 30+ active (recently-online) drivers
- Passengers using "Request Any Taxi" without being prompted (organic
  demand, not just profile clicks)
- A daily operations routine (`operations-daily.md`) that takes under 15
  minutes — if it's still a heavy manual burden in one town, it will not
  survive being copy-pasted to a second one.

The natural next towns are the ones already on your fare board as
destinations (Bindura, Harare corridor) — but expansion means a second
fare board, a second driver-seeding push, and possibly a second WhatsApp
merchant number if you want clean per-town reconciliation. Treat it as a
second Phase-1 launch (`marketing-plan.md`), not a toggle.

## Product ideas explicitly deferred, and why

- **Paynow automation** — worth doing once EcoCash-manual volume is high
  enough that admin confirmation time is a real bottleneck (see
  `operations-daily.md`), not before. Automating a low-volume process
  saves little and adds integration risk early.
- **SMS notifications** — deliberately dropped in favour of WhatsApp deep
  links + email-to-Pro-drivers, to avoid a paid SMS gateway dependency
  with no revenue offsetting it. Revisit only if WhatsApp/email open rates
  turn out too low in practice.
- **Multi-town / franchise model** — see "When to expand" above.
