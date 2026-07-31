# Vigil — Product Backlog

25 user stories across 6 epics, prioritised with MoSCoW and estimated in story points
(modified Fibonacci: 1, 2, 3, 5, 8).

Every story here exists as a GitHub Issue on the
[Vigil project board](../../projects). Run `scripts/seed-issues.sh` to recreate them.

**Release plan**

| Release | Contents | Size |
|---|---|---|
| **M1 — Walking skeleton** | All *Must have* stories. A user can sign up, add a URL, and see it go down. | 16 stories, 58 pts |
| **M2 — Usable product** | *Should have*. Status page, alerts, auto-refresh, CI. | 6 stories, 22 pts |
| **M3 — Polish** | *Could have*. Only if the semester allows. | 2 stories, 6 pts |
| *Deferred* | *Won't have* this release. | 1 story, 5 pts |

**Total: 25 stories, 91 points.**

---

## Epic A — Accounts and access

### US-01 · Create an account
**As a** developer running side projects
**I want** to sign up with an email and password
**so that** my monitors are private to me.

*Acceptance criteria*
- Given a valid email and a password of 8+ characters, when I submit, then an account is created and I land on the dashboard already signed in.
- Given an email that already exists, when I submit, then I see "That email already has an account." and no duplicate is created.
- Passwords are stored as PBKDF2-SHA256 hashes with a per-user salt, never in plain text.

**MoSCoW** Must have · **Points** 3 · `epic:accounts` `backend` `frontend`

---

### US-02 · Sign in
**As** a returning user
**I want** to sign in
**so that** I can reach my dashboard.

*Acceptance criteria*
- Correct credentials return a JWT valid for 24 hours.
- Wrong credentials return HTTP 401 and the message "Email or password is incorrect." The response does not reveal whether the email exists.
- The token is stored client-side and attached as `Authorization: Bearer <token>` on every API call.

**MoSCoW** Must have · **Points** 3 · `epic:accounts` `backend` `frontend`

---

### US-03 · Stay signed in, and sign out on demand
**As** a user
**I want** my session to survive a page refresh, and a sign-out button that actually ends it
**so that** I am not retyping my password all day, and can leave a shared machine safely.

*Acceptance criteria*
- Refreshing the browser keeps me signed in until the token expires.
- Signing out clears the stored token and redirects to `/login`.
- An expired or tampered token results in a redirect to `/login`, not a blank screen.

**MoSCoW** Must have · **Points** 2 · `epic:accounts` `frontend`

---

### US-04 · Never see another account's data
**As** a user
**I want** hard isolation between accounts
**so that** self-hosting for a small team is safe.

*Acceptance criteria*
- Every monitor and incident query is filtered by `owner_id`.
- Requesting a monitor I do not own returns 404, not 403 — the existence of the resource is not leaked.
- A request with no `Authorization` header to any `/api/monitors` route returns 401.

**MoSCoW** Must have · **Points** 3 · `epic:accounts` `backend` `security`

---

## Epic B — Monitors

### US-05 · See everything I watch on one screen
**As** a developer
**I want** a single dashboard listing every monitor with its current state
**so that** I know whether anything is broken in under five seconds.

*Acceptance criteria*
- The list shows name, URL, status pill (up / degraded / down / pending), 24-hour uptime %, average response time, and time since the last check.
- Statuses are colour-coded and also carry a text label, so the screen is readable without colour vision.
- With zero monitors, the screen shows "Nothing is being watched yet" and a path to add one.

**MoSCoW** Must have · **Points** 5 · `epic:monitors` `frontend`

---

### US-06 · Add a monitor in under ten seconds
**As** a developer
**I want** to add a URL with just a name
**so that** setup is not a chore.

*Acceptance criteria*
- Name and URL are the only required fields; method defaults to GET, expected status to 200, interval to 60s.
- The monitor appears in the list immediately with status `pending`.
- The worker picks it up on its next cycle without a restart.

**MoSCoW** Must have · **Points** 3 · `epic:monitors` `backend` `frontend`

---

### US-07 · Configure how a check is made
**As** a backend developer
**I want** to set the HTTP method, expected status code, and check interval
**so that** I can monitor API health endpoints, not just web pages.

*Acceptance criteria*
- Method, expected status, and interval are editable on create and on edit.
- The interval is clamped server-side to 30–3600 seconds; out-of-range values return 422 with a readable message.
- A check counts as failed when the response status differs from the expected status.

**MoSCoW** Must have · **Points** 3 · `epic:monitors` `backend`

---

### US-08 · Judge health from the list, not the detail page
**As** a user
**I want** 24-hour uptime and average response time on each row
**so that** I can spot a service that is technically up but getting slower.

*Acceptance criteria*
- Uptime is `successful checks ÷ total checks` over the trailing 24 hours, to two decimals.
- Average response time is calculated over successful checks only, so timeouts do not distort it.
- A monitor with no checks yet shows "—" rather than 0%.

**MoSCoW** Must have · **Points** 3 · `epic:monitors` `backend`

---

### US-09 · Watch the dashboard update itself
**As** a user with the dashboard open on a second screen
**I want** it to refresh without me touching it
**so that** it works as an ambient status display.

*Acceptance criteria*
- The dashboard re-fetches every 15 seconds.
- The poll is cancelled on unmount so no timers leak between routes.
- A failed poll shows an inline error and keeps retrying instead of blanking the screen.

**MoSCoW** Should have · **Points** 2 · `epic:monitors` `frontend`

---

### US-10 · Read the response-time history of one service
**As** a developer investigating slowness
**I want** a 24-hour response-time chart for a single monitor
**so that** I can tell a spike from a trend.

*Acceptance criteria*
- The chart plots every successful check in the window, oldest to newest.
- Failed checks are drawn as vertical markers so gaps are explained rather than invisible.
- With fewer than two samples, the chart is replaced by "Not enough samples yet."

**MoSCoW** Must have · **Points** 5 · `epic:monitors` `frontend`

---

### US-11 · Read the raw check log
**As** a developer
**I want** the last ten checks with status code, latency, and error text
**so that** I can see exactly what the server returned.

*Acceptance criteria*
- Each row shows relative time, status code or error, and latency.
- Errors are phrased for a human: "No response within 8s", not `ReadTimeout`.
- Successes and failures are visually distinguishable.

**MoSCoW** Must have · **Points** 2 · `epic:monitors` `frontend`

---

### US-12 · Pause or remove a monitor
**As** a user decommissioning a service
**I want** to pause checking or delete the monitor entirely
**so that** a retired service stops paging me.

*Acceptance criteria*
- Pausing sets `is_active = false`; the worker skips it and the row shows as paused.
- Deleting removes the monitor and cascades to its checks and incidents.
- Deletion asks for confirmation before it fires.

**MoSCoW** Must have · **Points** 3 · `epic:monitors` `backend` `frontend`

---

## Epic C — Checking engine

### US-13 · Have outages detected without me watching
**As** a developer asleep at 3am
**I want** the system to notice failures on its own
**so that** monitoring is not something I have to remember to do.

*Acceptance criteria*
- A dedicated worker container probes every active monitor whose interval has elapsed.
- After 2 consecutive failed checks, the monitor flips to `down` and an incident opens.
- A single failed check does not open an incident — this is the flap guard.

**MoSCoW** Must have · **Points** 8 · `epic:engine` `backend`

---

### US-14 · Have recoveries detected too
**As** a user
**I want** incidents to close themselves when the service comes back
**so that** the incident list reflects reality without manual filing.

*Acceptance criteria*
- The first successful check after a failure resolves the open incident and sets `resolved_at`.
- The incident gets a plain-English summary: what broke, how long it lasted, and the current response time.
- The failure counter resets to zero on success.

**MoSCoW** Must have · **Points** 5 · `epic:engine` `backend`

---

### US-15 · See the incident history
**As** a team lead
**I want** a reverse-chronological incident feed with filters
**so that** I can answer "how often does this break?"

*Acceptance criteria*
- The feed shows monitor name, cause, start time, duration, and open/resolved state.
- I can filter to open incidents only.
- The feed is capped at 100 records per request.

**MoSCoW** Must have · **Points** 3 · `epic:engine` `backend` `frontend`

---

## Epic D — Public status

### US-16 · Publish a status page my users can read
**As** a solo founder
**I want** a public page showing which of my services are healthy
**so that** customers stop emailing me during an outage.

*Acceptance criteria*
- `/status/<handle>` is readable with no authentication.
- It shows an overall banner (operational / degraded / major outage) derived from the worst individual status.
- It never exposes monitor URLs, internal errors, or any other account's services.

**MoSCoW** Should have · **Points** 5 · `epic:status` `backend` `frontend`

---

### US-17 · Choose what is public
**As** a user
**I want** a per-monitor toggle for status-page visibility
**so that** internal services stay internal.

*Acceptance criteria*
- Monitors default to private.
- Toggling updates the public page within one cache TTL (20 seconds).
- A page with no public monitors renders an empty state, not an error.

**MoSCoW** Should have · **Points** 3 · `epic:status` `backend` `frontend`

---

### US-18 · Acknowledge an incident
**As** an on-call developer
**I want** to mark an incident as acknowledged
**so that** my teammates know someone is already on it.

*Acceptance criteria*
- Acknowledging is one click from the incident feed.
- The acknowledged state persists and is visible to every user on the account.
- Acknowledging does not resolve the incident.

**MoSCoW** Should have · **Points** 2 · `epic:status` `backend` `frontend`

---

## Epic E — Alerting

### US-19 · Get an email when something breaks
**As** a developer
**I want** an email the moment an incident opens
**so that** I do not need the dashboard open to find out.

*Acceptance criteria*
- An email is sent on incident open and on incident close, never on individual failed checks.
- SMTP settings come from environment variables; with none configured the feature is silently disabled and logged once at startup.
- A failed send is retried twice, then logged — it never crashes the worker.

**MoSCoW** Should have · **Points** 5 · `epic:alerting` `backend`

---

### US-20 · Get alerts in Slack
**As** a small team
**I want** incidents posted to a Slack channel
**so that** alerts land where we already talk.

*Acceptance criteria*
- A webhook URL is configurable per account.
- The message names the service, the cause, and links to the monitor.
- Slack being down does not affect probing or incident recording.

**MoSCoW** Could have · **Points** 3 · `epic:alerting` `backend`

---

### US-21 · Read a plain-English explanation of an outage
**As** a non-technical founder
**I want** the incident described in a sentence I understand
**so that** I can decide whether to tell customers.

*Acceptance criteria*
- Every resolved incident carries a summary naming the service, the duration, the trigger, and the current response time.
- The summary is generated at resolution time and stored, so reading it later never depends on an external service.
- No jargon: "No response within 8 seconds", not "ReadTimeout on GET".

**MoSCoW** Could have · **Points** 3 · `epic:alerting` `backend`

---

### US-22 · Quiet hours
**As** a developer who needs sleep
**I want** to suppress non-critical alerts overnight
**so that** a flaky staging box does not wake me.

*Acceptance criteria*
- A per-account quiet window is configurable with a timezone.
- Suppressed alerts are still recorded as incidents and shown in the morning digest.
- Monitors flagged critical bypass quiet hours.

**MoSCoW** Won't have (this release) · **Points** 5 · `epic:alerting` `backend`

---

## Epic F — Operations

### US-23 · Run the whole stack with one command
**As** a new contributor
**I want** `docker compose up` to give me a working system
**so that** I am productive on day one.

*Acceptance criteria*
- One command starts db, cache, api, worker, and web with no manual setup steps.
- The API waits for Postgres to be healthy before it starts, so first boot does not race.
- Demo data is seeded on an empty database, so the UI is populated immediately.

**MoSCoW** Must have · **Points** 5 · `epic:ops` `devops`

---

### US-24 · Check whether Vigil itself is healthy
**As** an operator
**I want** a health endpoint that reports on its own dependencies
**so that** Docker and my reverse proxy can make routing decisions.

*Acceptance criteria*
- `GET /health` returns the API, database, and cache status individually.
- It returns 200 with `"status": "degraded"` when a dependency is down, so the endpoint itself is always reachable.
- The container `HEALTHCHECK` uses it.

**MoSCoW** Must have · **Points** 2 · `epic:ops` `devops` `backend`

---

### US-25 · Ship changes without breaking main
**As** a maintainer
**I want** CI to run tests and build both images on every pull request
**so that** `main` stays deployable.

*Acceptance criteria*
- Every PR runs `pytest`, `next build`, and `docker build` for both services.
- A failing job blocks the merge.
- Merging to `main` publishes tagged images that the Pi can pull.

**MoSCoW** Should have · **Points** 5 · `epic:ops` `devops` `ci`

---

## MoSCoW summary

| Priority | Stories | Points | % of backlog | Story IDs |
|---|---|---|---|---|
| **Must have** | 16 | 58 | 64% | US-01, 02, 03, 04, 05, 06, 07, 08, 10, 11, 12, 13, 14, 15, 23, 24 |
| **Should have** | 6 | 22 | 24% | US-09, 16, 17, 18, 19, 25 |
| **Could have** | 2 | 6 | 7% | US-20, 21 |
| **Won't have** (this release) | 1 | 5 | 5% | US-22 |
| | **25** | **91** | | |

A 64% Must-have share is high for a commercial backlog, where 60% is the usual ceiling. It is
defensible here because this is a v1 with no existing users: there is no working product to fall
back on if a Must slips, so the walking skeleton genuinely is all-or-nothing. The mitigation is that
M1 stories are small — the median is 3 points and only one story is an 8.

**Why these are the Musts.** The core loop is: *sign in → add a URL → the system checks it → the
system tells you when it broke.* Every Must-have story is load-bearing for that sentence. Remove any
one of them and Vigil is not a monitoring tool.

**Why the status page is only a Should.** It is the strongest differentiator against a cron job and
a curl, but a developer monitoring their own side projects gets full value without it. It ships in
M2.

**Why quiet hours is a Won't.** It needs per-account timezone handling and a scheduler, and it only
matters once alerting is heavily used. Deferring it is cheaper than half-building it.
