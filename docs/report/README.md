# Review 3 — Project report

[`Vigil_Project_Report.pdf`](Vigil_Project_Report.pdf) is the single PDF for Digital Assignment 3.

| Part | Contents |
|---|---|
| A. Review 3 evidence | Integration, regression and mutation testing · version management and system building · developed functionalities · tools and technologies · demo script |
| B. Project report | Problem statement · user stories · system architecture and design · design of tests |
| Appendices | SRS · DFD (levels 0 and 1) · ERD · UML (use case, class, two sequence, state machine) · code listing and GitHub link |

`screenshots/` holds every capture used in the report:

| Prefix | What |
|---|---|
| `t0*` | Test runs: unit, integration, regression, coverage, end-to-end, mutation |
| `v0*` | Version management: commit graph, branches and tags, pull requests, releases, CI runs, GitHub pages |
| `b0*` | System building: `docker compose build`, running containers, images, CI pipeline steps |
| `f*` | Developed functionalities, captured from the running stack |

Terminal captures show the real output of the command on their first line. Browser captures are of the stack started by
`docker compose up`, signed in as the seeded demo account.

## Rebuilding

```bash
python scripts/make_report_diagrams.py && python scripts/export_diagrams.py   # DFD + UML diagrams
python docs/build/build_report.py                                             # the PDF, with real page numbers
```
