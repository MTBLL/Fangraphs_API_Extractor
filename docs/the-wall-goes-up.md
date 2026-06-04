# The Wall Goes Up: Surviving Fangraphs' Cloudflare Challenge

*The day the `updates` and `ros` pulls started returning 403, and what it took
to get them back. A record of every dead-end we tried before the one that
worked — so nobody re-walks the same blocked paths.*

---

## What broke

In-season, the `projs_updated` and `ros` slots began failing with HTTP **403**.
The pre-season `projections` slot looked fine — but only because its data had
been scraped back in spring, before the wall went up. The "updated/ros only"
pattern was a *timeline artifact*, not an endpoint-specific block: those two
slots only publish mid-season, so they were simply the first pulls to hit the
new defense.

The 403 body told the real story:

```
cf-mitigated: challenge
server: cloudflare
...
Just a moment...
Performing security verification
Ray ID: ...
```

Fangraphs had put the entire `fangraphs.com` zone behind a **Cloudflare managed
JS challenge** (`_cf_chl_opt`, `/cdn-cgi/challenge-platform/...`). Every request
to `/api/projections` — and even the homepage — now gets an interstitial that
must execute challenge JavaScript and return a `cf_clearance` cookie. Unprotected
paths like `/robots.txt` stayed `200`, which is how we confirmed it was a
path-scoped challenge and not an IP ban.

## The dead-ends (all 403)

Every header/fingerprint trick fails against a managed JS challenge, because the
challenge is not checking *what you claim to be* — it's checking *whether you can
run its JavaScript in a real browser environment*. For the record, what we tried
and what we got:

| Approach | Result | Why it failed |
|---|---|---|
| `requests` + browser User-Agent | 403 | No JS engine; UA is irrelevant to a managed challenge |
| `requests` + `Referer`/`Accept`/`Accept-Language` | 403 | Same — headers don't execute the challenge |
| `curl_cffi` `impersonate="chrome"` (TLS/JA3 match) | 403 | Beats *passive* fingerprinting, not an *active* JS challenge |
| `cloudscraper` (legacy IUAM solver) | 403 | Solves the older JS challenge, not the modern managed/Turnstile one |
| Playwright **headless** (bundled Chromium) | stuck on "Just a moment" | Automation + open-source Chromium build detected |
| `patchright` (stealth) headless | stuck | Same environment signals |
| `patchright` **headful** | stuck | — |
| `patchright` real **Chrome** channel, headful | stuck | — |

The headful failures were initially alarming — a real browser *should* pass. Two
explanations were confounded and could not be separated from the test machine:
(a) Cloudflare detecting the CDP/automation channel even under stealth, or (b)
the test IP getting penalty-boxed after ~40 failed solves. The clean tie-breaker:
opening `https://www.fangraphs.com/projections` in a **normal human Chrome on the
same machine/IP** loaded instantly. Same IP, real browser passes, automated
browser doesn't → the wall is **automation detection**, not IP reputation.

That ruled out "bake Playwright into the image and drive it ourselves" — our best
stealth attempt with a real Chrome binary still couldn't pass.

## What worked: FlareSolverr as a sidecar

[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) runs a stealth-patched
browser purpose-built to clear Cloudflare challenges. You POST it a URL; it drives
its browser through the challenge and hands back the `cf_clearance` cookie plus the
exact User-Agent it used. We then replay those against the API with plain
`requests`:

```
POST flaresolverr:8191/v1  {cmd: request.get, url: .../projections}
  -> status: ok, "Challenge solved!"
  -> solution.cookies[cf_clearance], solution.userAgent

requests.get(/api/projections?type=steamerr, cookie+UA)  -> 200
```

Verified end-to-end through the real extractor:

```
Obtained Cloudflare clearance via FlareSolverr
Slot 'projections':   4186 hitters, 5367 pitchers
Slot 'projs_updated': 4377 hitters, 5588 pitchers   (was 403)
Slot 'ros':            630 hitters, 3361 pitchers    (was 403)
```

## The load-bearing constraint: cf_clearance is bound to UA + egress IP

Cloudflare ties the `cf_clearance` cookie to the **exact User-Agent** and the
**egress IP** that solved the challenge. The cookie is only honored when both
match on replay. Two consequences shape the design:

1. **Adopt FlareSolverr's User-Agent.** The solver runs a Linux Chrome; we
   override the static `USER_AGENT_HEADER` with whatever UA it reports. Sending
   the old hardcoded UA with its cookie → instant 403.
2. **Co-locate solver and consumer.** The solver and the extractor must share an
   egress IP. In the Prefect compose stack both the `flaresolverr` container and
   the `runner` container NAT out through the host's public IP → same egress →
   cookie valid. A solver-as-a-service in a different datacenter would mint a
   cookie keyed to the *wrong* IP and every replay would 403. This is why we run
   FlareSolverr as a **local sidecar**, not a remote dependency.

## How it's wired

- **`utils/constants.py`** — `FANGRAPHS_CHALLENGE_URL` (the HTML page solved
  against; clearance is zone-wide so it authorizes the same-zone API).
- **`requests/core_fangraphs.py`** — reads `FLARESOLVERR_URL` from the
  environment. On the first `_get`, `_ensure_clearance()` solves once and caches
  the cookie + UA on the session. A mid-run 403 triggers exactly one re-solve and
  retry (the cookie has a TTL). When `FLARESOLVERR_URL` is unset the extractor
  behaves as before — useful for environments where the challenge isn't active.
- **`MTBL_Prefect/docker-compose.yml`** — adds the `flaresolverr` service and
  sets `FLARESOLVERR_URL=http://flaresolverr:8191/v1` on the runner. Published on
  `127.0.0.1:8191` for host-direct flows; loopback-bound because the solver
  proxies arbitrary URLs through a real browser and must never face the LAN.

### A bug fixed along the way

The pre-existing `_get` called module-level `requests.get()` and only forwarded
cookies — it never used `self.session`, so the session's User-Agent (and any
future `cf_clearance`) was silently dropped between calls. That made cookie reuse
impossible. `_get` now goes through `self.session.get()`, which both fixes the
latent bug and is what makes the clearance cookie stick.

## If the wall changes again

FlareSolverr tracks Cloudflare's evolving challenges but is not guaranteed to
clear every future variant. If `status: ok` stops coming back: update the
FlareSolverr image first. If that fails, the fallbacks in rough order of effort
are a residential-proxy egress, a logged-in Fangraphs member session (the site
runs WordPress with member auth — untested as a challenge bypass), or an
alternate projections source. Header/TLS-impersonation tricks are *not* on that
list — this document is the evidence that they don't work against a managed JS
challenge.
