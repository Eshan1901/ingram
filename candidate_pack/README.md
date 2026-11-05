# Data & AI Engineering Challenge — Candidate Pack
**Duration:** 180 minutes | **Format:** individual, open-book, AI permitted with disclosure | **Recommended:** Python 3 + pandas + SQLite/DuckDB

## The business problem
You are a Data & AI intern at a B2B e-commerce company. The Growth team reports: **“Revenue dropped in September 2026 versus August 2026. Is it a real business change or a data problem?”**

Three synthetic exports are provided in `data/`: `orders.csv`, `customers.csv`, `products.csv`. They contain deliberately messy records. **Do not assume the exports are authoritative.**

## Definitions supplied by Finance
- Report **August and September 2026** as two separate calendar months.
- Revenue = `quantity × order unit_price` for **completed** orders only. Exclude `cancelled` and `refunded` orders; do not subtract refunds (there is no refund amount or transaction-level history).
- Convert **USD → INR at exactly ₹85 per USD** (a simplified assessment assumption; not a historical market rate). Other currency codes are **not supported** unless you document a justified treatment.
- Trim surrounding spaces and case-normalize `status`; valid completed status is `completed`. Do **not automatically equate** `COMPLETE` with `completed`.
- Only count orders with a parseable date, valid customer and product keys, positive quantity, and positive unit_price.
- An **identical repeated row** may be safely deduplicated by `order_id` if every field matches. **Conflicting rows with the same `order_id`** must be quarantined until clarified: do not arbitrarily choose one.
- Define **new vs repeat** by a customer's first valid completed order **in the available August–September dataset** (not their true lifetime CRM tenure). Same-day first orders count as new; later dates are repeat. Clearly state this limitation.
- The goal is an **evidence-backed**, *not necessarily complete*, management answer. Show how exclusions affect confidence.

## Levels & expected outputs
| Level | What to do | Submission evidence |
|---|---|---|
| 1. Inspect (foundation) | Load files, identify schemas, rows, missingness, duplicate IDs, invalid dates | Data-health snapshot |
| 2. Trust (foundation) | Establish explicit decisions; deduplicate exact rows; quarantine invalid and conflicting records; build clean dataset | Cleaned orders / rejection log + assumptions |
| 3. Analyze (core) | SQL for monthly revenue, top 10 products by completed revenue, new vs repeat contributions | `queries.sql` + KPI results |
| 4. Communicate (core) | Present 2 findings, 1 uncertainty and a practical next action | 150–250-word `executive_summary.md` |
| 5. AI with verification (stretch) | Use AI to draft one insight or explanation; log prompt/response and verify every numerical/factual claim | `ai_verification.md` with claims vs evidence |

**Suggested pacing:** inspection 20m; clean + SQL 100m; verify + AI 35m; submit 25m. Advanced task is optional: add a sensitivity analysis for excluded records or a useful automated data-quality test.

## Deliverables
- `analysis.py` or `analysis.ipynb` (reproducible, not screenshots only)
- `queries.sql` (must contain executed SQL; choose SQLite/DuckDB/other and say which)
- `README.md` (how to run, choices, limitations)
- `executive_summary.md`, and ideally `clean_orders.csv`, `rejected_orders.csv`
- `ai_verification.md` (or say explicitly AI was not used; evaluation will emphasize verification, not tool access)
- Git repository link **if Git is available**, otherwise a ZIP with a clear directory structure. Do not publish candidate personal details or private credentials.

## Fairness & logistics
You may use documentation and AI assistants; disclose meaningful assistance. Internet/tool outages will not cause automatic failure. You are not graded on UI, charts, slides or deploying cloud services. At the end, submit a 3-minute explanation **via a short recording or during a later interview**; it is **not part of the 180-minute build**. Do not collaborate or share answers during the session.

## Decision question
Is the apparent revenue drop supported by **trusted rows**, and which excluded records might change the conclusion? Do not invent root causes (e.g. a promotion or seasonality) without supporting data.
