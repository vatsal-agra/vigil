# Screenshots — capture checklist

Deliverable 5 asks for proof that the dev setup works. These are the only items in the assignment
that cannot be produced ahead of time. Save each capture into this directory using the exact
filename listed — `docs/build/make_assets.py` picks them up and the document build renders them;
any missing file gets a labelled placeholder frame instead.

Run these first, from the repo root:

```bash
./scripts/bootstrap-github.sh   # pushes code, creates issues, board, branches
docker compose down -v          # clean slate, so the seed runs
docker compose up --build
```

| File | What to capture |
|---|---|
| `s01-repo-readme.png` | https://github.com/vatsal-agra/vigil — landing page: folder structure, README rendering below |
| `s02-branches.png` | https://github.com/vatsal-agra/vigil/branches — `main` plus `feat/us-16-public-status-page` |
| `s03-issues.png` | https://github.com/vatsal-agra/vigil/issues — 25 open issues with epic and MoSCoW labels |
| `s04-project-board.png` | The "Vigil — Product Backlog" project, view set to Group by → MoSCoW |
| `s05-docker-build.png` | Terminal: `docker compose up --build` finishing, five `Started` lines |
| `s06-compose-ps.png` | Terminal: `docker compose ps` after ~30 s — all five `Up`, db/cache/api `(healthy)` |
| `s07-worker-logs.png` | Terminal: `docker compose logs --tail 20 worker` — a `cycle complete, 4 monitor(s) checked` line |
| `s08-dashboard.png` | Browser at `http://localhost:3000`, signed in as `demo@vigil.dev` / `vigil-demo-2026`, address bar visible |
| `s09-detail.png` | Browser: any monitor's detail page with the 24-hour response-time chart and latest checks |
| `s10-status-page.png` | Browser: `http://localhost:3000/status/demo` — public, no login |

`.jpg` also works. After adding or replacing captures, re-run:

```bash
python docs/build/make_assets.py
node docs/build/build_doc.js
```

Extra proof worth keeping (not rendered in the document): an open PR with all three CI jobs green,
and `curl -s localhost:8000/health` showing all three dependencies `ok`.
