# Screenshots — capture checklist

Deliverable 5 asks for proof that the dev setup works. These are the only items in the assignment
that cannot be produced ahead of time. Save each as the filename listed and it will render in the
table at the bottom without further edits.

Run these first, from the repo root:

```bash
./scripts/bootstrap-github.sh   # pushes code, creates issues, board, branches
docker compose down -v          # clean slate, so the seed runs
docker compose up --build
```

---

## 1. `01-docker-build.png` — successful build

Capture the terminal at the end of `docker compose up --build`, showing the final
`Container vigil-worker-1  Started` lines.

> Scroll up slightly so a few `=> naming to docker.io/library/vigil-api` lines are visible too —
> it proves the images were built here rather than pulled.

## 2. `02-compose-ps.png` — all five containers healthy

```bash
docker compose ps
```

Wait ~30 seconds after startup so the healthchecks have passed. All five services must show `Up`,
and `db`, `cache`, and `api` must show `(healthy)`.

## 3. `03-worker-logs.png` — the probe loop running

```bash
docker compose logs --tail 20 worker
```

Wait for at least two cycles so a `cycle complete, 4 monitor(s) checked` line appears.

## 4. `04-dashboard.png` — the app in the browser

http://localhost:3000 — sign in as `demo@vigil.dev` / `vigil-demo-2026`.

Include the browser address bar showing `localhost:3000` in the capture. That is what makes it proof
of a local run rather than a screenshot of a deployed site.

## 5. `05-monitor-detail.png` — response-time chart

Click any monitor. Capture the detail page with the 24-hour chart and the latest-checks list.

## 6. `06-status-page.png` — the public status page

http://localhost:3000/status/demo — open it in a private window to demonstrate it needs no login.

## 7. `07-health-endpoint.png` — health check

```bash
curl -s localhost:8000/health | python -m json.tool
```

All three dependencies reporting `ok`.

## 8. `08-github-branches.png` — branches on GitHub

`scripts/bootstrap-github.sh` already created and pushed `feat/us-16-public-status-page`.

Screenshot https://github.com/vatsal-agra/vigil/branches showing `main` plus the feature branch.

## 9. `09-github-readme.png` — repo landing page

The repo home page with the README rendering, folder structure visible above it.

## 10. `10-project-board.png` — the backlog board

`scripts/bootstrap-github.sh` already built the board with the `MoSCoW`, `Epic`, and `Points`
fields populated.

Open it, set the view to **Group by → MoSCoW**, and capture all 25 cards sorted into
Must / Should / Could / Won't columns. Also worth capturing
https://github.com/vatsal-agra/vigil/issues as `10b-issues-list.png` — it shows the 25 issues with
their epic and priority labels.

## 11. `11-pull-request.png` — an open PR with CI green

Open a PR from your feature branch and capture it once all three CI jobs have passed.

---

## Rendered in the report

| # | Proof | File |
|---|---|---|
| 1 | `docker compose up --build` succeeds | ![build](01-docker-build.png) |
| 2 | All five containers healthy | ![ps](02-compose-ps.png) |
| 3 | Probe worker running its cycle | ![worker](03-worker-logs.png) |
| 4 | Dashboard on `localhost:3000` | ![dashboard](04-dashboard.png) |
| 5 | Monitor detail and chart | ![detail](05-monitor-detail.png) |
| 6 | Public status page, no login | ![status](06-status-page.png) |
| 7 | Health endpoint | ![health](07-health-endpoint.png) |
| 8 | Branches on GitHub | ![branches](08-github-branches.png) |
| 9 | Repo page with README | ![readme](09-github-readme.png) |
| 10 | Project board, grouped by MoSCoW | ![board](10-project-board.png) |
| 10b | Issues list with labels | ![issues](10b-issues-list.png) |
| 11 | PR with CI green | ![pr](11-pull-request.png) |
