# HeatPermit AI
### AI-Powered Heat Safety & Event Decision Platform

**"Don't just know how hot it is. Know whether your event should happen."**

Built for the FortyGuard Hackathon — **Track 06 (Agentic AI)**, primary · Track 01 (Resilient Cities & Infrastructure), secondary.

---

## The pitch

A temperature number doesn't tell an event organizer anything actionable. "40°C" doesn't say whether a 10,000-person concert should proceed, be modified, need extra safety measures, or be postponed — and if it should move, *when* it should move to and whether anyone would actually show up at that time.

HeatPermit AI turns FortyGuard's raw hyperlocal heat data into an operational decision: a **Heat Risk Score**, a **spatial heat map**, an **hour-by-hour risk timeline**, an **AI Decision Agent's recommendation**, a **deterministically-searched, LLM-reasoned safer alternative window**, **event-specific role guidance**, and a full **Event Heat Safety Plan** — everything an organizer needs to actually act, not just a number to interpret themselves.

**Primary user:** Event organizers, city event offices, stadium/university operations managers, festival and marathon planners deciding whether, when, and how to safely run an outdoor event.

---

## Why this is a strong agentic product

| | Generic Heat Dashboard | HeatPermit AI |
|---|---|---|
| Output | "Temperature: 39°C" | Heat Risk Score + spatial heat map + timeline + schedule recommendation + safety plan |
| Agent structure | None — static data display | Multi-node LangGraph pipeline with **three separate LLM agents**, each making a distinct decision |
| Decision-making | User interprets the number themselves | Decision Agent classifies risk into PROCEED / MODIFY / ADD_INTERVENTIONS / POSTPONE and can trigger a second agent as a sub-tool |
| Trade-off reasoning | None | Window Selector Agent is handed 3 fully-assessed candidate windows and has to reason about thermal risk *vs.* realistic attendance — the coldest hour (often 2–4 a.m.) is deliberately excluded from consideration, and the agent has to justify its actual pick in writing |
| Honesty over false comfort | N/A | If no realistic window is genuinely safe, the system says so explicitly instead of quietly suggesting something still unsafe |
| Personalization | N/A | Role guidance is generated per-event (attendance, type, duration) by an LLM, not pulled from a fixed template keyed only on risk tier |
| Differentiator | Dozens of teams will build a heat dashboard | **What-If Simulator** — compare two schedules live, with a concrete quantified exposure-reduction percentage |

The pipeline's control flow itself branches on agent output: a `PROCEED` decision skips the entire window-search sub-pipeline; a non-`PROCEED` decision triggers a second full multi-step assessment — candidate search, full risk-assessment of 3 windows, LLM trade-off reasoning, and a safety-gate check before anything is shown to the user. This is a real multi-step reasoning chain with conditional branching, not a fixed sequential workflow wrapped around one API call.

---

## The agent pipeline

```
                    Event Context
              (location, date, window, type, attendance)
                            |
                            v
                     Heat Data Agent
        FortyGuard: Heatmap (tcm / exceedance / persistence)
              + Environmental Parameters, scoped to
                    the event's exact window
                            |
                            v
                   Risk Scoring Agent
         Deterministic 0-100 score - peak temp (40%),
        exceedance hours (35%), persistence (25%), each
              relative to event duration. Pure
                function, unit-testable.
                            |
                            v
                Decision Agent  <-- LLM #1
     Reasons over risk + event context -> recommends
     PROCEED / MODIFY / ADD_INTERVENTIONS / POSTPONE
                            |
              +-------------+-------------+
         PROCEED                    everything else
              |                            |
              |                            v
              |              Window Optimizer (deterministic)
              |           searches REALISTIC same-day hours only
              |            (05:00-20:00 starts) - no unusable
              |                 "coolest hour is 3am" answers
              |                            |
              |                            v
              |              Fully assess top-3 candidates
              |                 (real risk score each)
              |                            |
              |                            v
              |            Window Selector Agent  <-- LLM #2
              |         Reasons about thermal risk vs. realistic
              |          attendance across the 3 candidates,
              |              picks one, justifies why
              |                            |
              |              +-------------+-------------+
              |        genuinely safer              still unsafe
              |       ("Recommended                ("No Safe
              |        Alternative")             Alternative Found")
              |              |                            |
              +--------------+-------------+--------------+
                                            |
                                            v
                          Role Recommendation Agent  <-- LLM #3
                    Event-specific guidance (attendance/type/
                   duration aware) for 5 personas - attendees,
                    medical team, event staff, performers,
                              event manager
                                            |
                                            v
                            Safety Plan Generator
                    Deterministic before/during/emergency plan,
                          computed off the actual start time
                                            |
                                            v
                                    Persistence
                    Risk score, safety plan, and What-If
                        comparisons written to Postgres
```

Every LLM node (Decision Agent, Window Selector Agent, Role Recommendation Agent) has a strict Pydantic schema and a deterministic rule-based or templated fallback, so a rate-limited or malformed LLM response degrades the pipeline's *creativity*, never its *reliability*. This was exercised for real during development — an early model hit a 20-request/day preview quota mid-build, and the pipeline kept producing a full, sensible end-to-end result on the rule-based fallback the entire time.

---

## Deterministic Risk Scoring Core

| Factor | Weight | Basis |
|---|---|---|
| Peak temperature | 40% | Normalized 25°C (0) to 45°C (100) |
| Exceedance hours | 35% | Hours above the 35°C threshold / event duration |
| Persistence hours | 25% | Longest continuous run above threshold / event duration |

| Score | Status |
|---|---|
| 0-24 | Low Risk |
| 25-49 | Low-Moderate Risk |
| 50-74 | Moderate Risk |
| 75-100 | High Risk |

Applied to both the current schedule and every candidate alternate schedule — this is what powers the What-If Simulator and the Window Selector Agent's comparisons.

---

## Example output (what the demo shows)

**Input:** Concert, Phoenix AZ, 10,000 attendance, scheduled 14:00-20:00.

```
Heat Risk: 90.3/100 - HIGH RISK
Peak temperature:      40.2 C
Hours above threshold: 6.0 h
Persistence:           6.0 h
Event duration:        6 h
```

**Decision Agent:** *"With an extreme risk score of 90.3 and peak temperatures reaching 40°C for a 6-hour continuous stretch during the hottest part of the day, holding an event for 10,000 attendees poses an unacceptable health and safety hazard."* -> **POSTPONE**

**Window Optimizer** checks 6 realistic same-day candidates, fully assesses the coolest 3, and hands them to the **Window Selector Agent**:

> *"Candidate [0] (05:00-11:00) has the lowest thermal risk, but is too early for a general event of 10,000 people and would result in very poor turnout. Candidate [1] (08:00-14:00) offers a meaningful reduction in heat risk compared to the current schedule while maintaining practical daytime hours for attendance."*

For this specific event, even the agent's chosen daytime window was still Moderate Risk — so the dashboard shows **"No Safe Alternative Found"** rather than a misleading green recommendation, and the original POSTPONE stands.

**On a cooler test event** the same pipeline found a genuine improvement: current schedule 90.3/100 (High Risk) -> recommended 05:00-11:00 window at 35.1/100 (Low-Moderate Risk), an **84% risk reduction**, surfaced directly on the dashboard with the agent's reasoning attached.

**Role-specific output (LLM-generated for this event, not templated):**
- **Attendees:** "Drink at least 500ml of water every hour from the multiple distribution points, wear light clothing, and seek shade immediately if you feel dizzy during the 40°C peak."
- **Medical Team:** "Establish 4 triage tents across the 10,000-person venue equipped for severe heatstroke, maintaining active roving patrols throughout the 6-hour event."
- **Event Staff:** "Work in strict 30-minute rotation schedules in shaded rest areas..."

---

## Tech stack

### Frontend
| Piece | Choice |
|---|---|
| Framework | Next.js (App Router) + React + TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts — heat trend, exceedance, and What-If comparison charts, all with auto-scaled Y-axes so real variation stays visible |
| Spatial heat map | Hand-built SVG tile projection — no external mapping library, renders FortyGuard's raw tile grid directly |
| State | React hooks, no global state library needed |

### Backend
| Piece | Choice |
|---|---|
| Framework | Python + FastAPI |
| Agent orchestration | LangGraph (`StateGraph`) — 7-node pipeline with conditional branching |
| LLM | Google Gemini (`gemini-3.5-flash-lite`) |
| Schema validation | Pydantic — both FastAPI request/response models and every LLM output schema |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| HTTP | `requests`, with a shared submit-then-poll utility for FortyGuard's async job pattern |

### Data source
FortyGuard Temperature Intelligence API — Heatmap (`tcm` / `exceedance` / `persistence`), Environmental Parameters, Heat Intelligence, and async Status polling. Every analysis endpoint is submit-then-poll; none are synchronous.

---

## FortyGuard endpoints used

| Endpoint | Used for |
|---|---|
| `POST /v1/heatmap` (`tcm`) | Peak temperature + the spatial tile grid that powers the heat map |
| `POST /v1/heatmap` (`exceedance`) | Hours above the 35°C threshold, scoped to the event's exact window |
| `POST /v1/heatmap` (`persistence`) | Longest continuous stretch above threshold, scoped to the event's exact window |
| `POST /v1/env_params` | Heat index, wet-bulb temperature, humidity — single-point and hourly range calls |
| `GET /v1/status/{activity_id}` | Async job polling for every analysis call above |
| `POST /v1/heat_intelligence` | Full PDF report generation, Premium-tier feature |

All requests are scoped with `filter_type=2` (range of hours) to the event's *actual* window rather than the whole day — otherwise exceedance and persistence never vary between a current schedule and a proposed alternative, and every What-If comparison would be meaningless.

---

## MVP scope delivered

**Must-have:**
1. Event creation (location, date, time window, type, attendance)
2. Live FortyGuard Heatmap (`tcm` + `exceedance` + `persistence`) + Environmental Parameters
3. Deterministic 0-100 Heat Risk Score engine
4. Hourly timeline breakdown (risk tier per hour)
5. What-If Simulator with live quantified comparison
6. Decision Agent (LLM): PROCEED / MODIFY / ADD_INTERVENTIONS / POSTPONE
7. Role-specific recommendations (5 personas)
8. Full dashboard: Overview, Spatial Heat Map, Timeline, AI Recommendations

**Delivered beyond the original scope:**
9. Full Event Heat Safety Plan generator
10. Heat Intelligence PDF report generation
11. **Window Selector Agent** — a second LLM reasoning over trade-offs between thermal safety and realistic attendance
12. **Honest "no safe alternative" fallback** — the system never shows a misleading recommendation just because it found *something* cooler
13. **Event-specific (not template-only) role guidance**, generated per event by a third LLM call

**Cut from build (roadmap only):** multi-tenant SaaS billing/auth, non-US geography, real-time in-event monitoring integrations, Satellite/Street View shade context, multi-event portfolio comparison view.

---

## Key engineering decisions & bugs fixed

- **GeoJSON coordinate order is `[longitude, latitude]`**, not `[lat, lng]` — the single most common first-day bug per the FortyGuard handbook, centralized in one polygon-builder function so it can only exist in one place.
- **`tcm`'s `map_data.features`** returns a full tile grid, not a single value — peak temperature is the *maximum* across all tiles, and that same grid is reused directly to render the spatial heat map with zero extra API calls.
- **Overnight (cross-midnight) time windows** aren't reliably supported by FortyGuard's heatmap endpoint — they return `500`s or hang until timeout. A shared `validate_same_day_window()` utility rejects these early with a clear `400`, applied everywhere a time window is accepted: event creation, the manual What-If Simulator, and the agent's own automatic candidate-window search.
- **`0.0` is falsy in Python.** Several calculations originally used `or`-chaining that silently fell through to a fallback whenever the real value was genuinely zero — this broke exposure-reduction percentage (always `None` for any already-safe comparison) and peak-temperature extraction. Fixed with explicit `is not None` / `> 0` checks throughout.
- **Realistic-hours constraint on the window optimizer.** A purely thermal search will happily recommend 2 a.m. as the "safest" time for a 10,000-person concert. Candidate hours are restricted to 05:00-20:00 starts, and the Window Selector Agent is explicitly prompted to weigh realistic attendance for each time of day, not just temperature.
- **Foreign-key-safe cascading delete.** `WhatIfComparison` and `SafetyPlan` both reference `HeatAssessment`; deleting an event that had ever been fully assessed used to violate that constraint. Deletes now happen in dependency order.
- **Network-timeout resilience in the polling loop.** A single slow status check used to raise an unhandled timeout and crash the whole request. The poller now retries transient network errors within its own loop.
- **Deterministic fallback on every LLM call**, exercised for real when a preview-tier Gemini model hit its daily quota mid-build — the pipeline kept working end-to-end on rule-based fallbacks.

---

## Running locally

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows; `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
# create a .env with DATABASE_URL, FORTYGUARD_API_KEY, GOOGLE_API_KEY
python -m uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://127.0.0.1:8000` by default.

---

## Constraints (by design, not hidden)

- **US-only coverage** — a launch-market choice matching FortyGuard's own coverage.
- **Same-day event windows only** — overnight events crossing midnight aren't supported yet, rejected with a clear error at creation time.
- FortyGuard's `tcm` model is a climate-pattern prediction, not a short-range weather forecast — intentional for this use case, since event organizers plan months in advance, long before a day-of forecast would exist.

---

## Business model

**SaaS subscription** — organizations pay monthly for event planning, risk analysis, monitoring, and reports. **Per-event pricing** alternative — generate a Heat Permit for each individual event. **Enterprise tier** — unlimited events + real-time monitoring + API integration.

**Target markets:** event organizers (concerts, festivals, fairs), sports (marathons, tournaments, outdoor games), cities (public events, municipal activities), universities (outdoor campus events), stadiums (game-day operations), theme parks (visitor safety and scheduling).

**Value proposition:** reduces event-cancellation and heat-illness liability risk, while the What-If Simulator and Window Selector Agent give organizers a concrete, quantified, *reasoned* alternative rather than a vague warning — "here's the number, here's the alternative, here's why" is a stronger commercial pitch than a generic safety-alert tool.

---

## Roadmap

- Multi-event portfolio view (compare risk across several upcoming events at once)
- Satellite / Street View shade context feeding the Decision Agent's reasoning
- Real-time in-event monitoring integrations (weather station feeds, live attendee tracking)
- SaaS subscription and per-event pricing tiers for organizers, cities, and venues
