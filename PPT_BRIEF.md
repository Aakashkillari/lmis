# LMIS: PPT brief for SIH 2026

This file has everything needed to build the presentation. Every number below comes from the working prototype. Keep the deck to 6 to 8 slides. SIH usually gives a fixed idea-submission template; if it does, map the slides below onto it in the same order.

---

## Basics

| Field | Value |
|---|---|
| Problem Statement ID | 26246 |
| Title | AI-Enabled Labour Market Intelligence and Skill Demand-Supply Forecasting Engine |
| Organisation | Ministry of Skill Development and Entrepreneurship (MSDE) |
| Category | Software |
| Theme | Miscellaneous |
| Product name | LMIS (Labour Market Intelligence System) |
| Team name | <fill in> |
| Team leader | <fill in> |

---

## Design rules (important)

The deck should look like an Indian government planning document, not a startup pitch.

- White background, navy text and headings (#0B2E59), one saffron accent (#E07B00) used only for thin rules or one highlight per slide.
- No gradients, glows, stock photos, 3D icons, emoji or "AI" robot images.
- Use tables and real screenshots of the app. Do not use decorative illustrations.
- Show status as a text label with a colour chip, never colour alone:
  - Oversupply: light blue
  - Watch (rising): light amber
  - Balanced: light green
  - Watch (falling): light orange
  - Shortage: light red
- Use official terms: NSQF, NCO, Qualification Pack (QP), sanctioned seats, ITI, PMKVY, Sector Skill Council.
- Font: one plain sans serif (Segoe UI, Noto Sans or Arial). For Hindi text, use Noto Sans Devanagari.
- Put a small footer on every slide: "Synthetic data modelled on the structure of NCS, PLFS, e-Shram and NCVT."

---

## Slide 1: Title

- LMIS: Labour Market Intelligence System
- Subtitle: Forecasting skill demand and supply at district and trade level for MSDE
- PS ID 26246 | Team name | College
- No images except an optional plain logo strip at the top.

## Slide 2: The problem

- India trains lakhs of candidates every year, but seats per trade per district are fixed without granular demand data.
- The result: some trades are chronically oversupplied (for example Domestic Electrician, Two-Wheeler Technician) while growth trades (EV, Solar) are short.
- Demand data is scattered across job portals, NCS, industry surveys and e-Shram, and is never combined into one decision-ready view.
- Planners discover a mismatch only after placement results come in, a full year too late.

One line at the bottom: **"Who uses it: MSDE, NCVET, Sector Skill Councils, State Skill Missions."**

## Slide 3: Our solution (what LMIS does)

A dashboard and API that:

1. **Aggregates** 4 demand signals: job portal postings, NCS vacancies, industry hiring outlook, e-Shram registrations.
2. **Normalises** raw job titles to NCO codes (for example "Wireman" or "Electrical Fitter" maps to Electrician (Domestic)).
3. **Blends** them into one Demand Index and converts it into estimated job openings.
4. **Forecasts** demand 12 months ahead per district and trade (Holt-Winters, with a confidence band).
5. **Compares** demand with certified supply from sanctioned seats.
6. **Ranks** trade-district pairs by severity and **flags early warnings** before they become a problem.
7. **Recommends** moving seats from oversupplied to short trades within a state.
8. **Exports** to CSV and a JSON API so the forecasts can feed target-setting workflows.
9. Works in **English and Hindi**.

Screenshot: Overview page.

## Slide 4: Methodology (the core slide)

Show this as a simple left-to-right flow diagram with plain boxes and arrows:

`4 data sources → Normalise (NCO mapping + z-score) → Demand Index → Calibrate to openings → Holt-Winters forecast → Gap ratio → Status + Early warning + Ranking`

Formulas (put them in a small table):

| Step | Formula |
|---|---|
| Demand Index | 0.35 x Portal + 0.30 x NCS + 0.20 x Industry + 0.15 x e-Shram (all as z-scores) |
| Supply | Sanctioned seats x Completion rate x Certification rate |
| Gap ratio | Supply / Forecast demand (next 12 months) |
| Severity | absolute value of (Supply minus Demand), in people |

Status thresholds:

| Gap ratio | Status | Planning action |
|---|---|---|
| above 1.5 | Oversupply | Cut or freeze seats, review course |
| 1.2 to 1.5 | Watch (rising) | Hold seats, monitor placements |
| 0.8 to 1.2 | Balanced | No change |
| 0.6 to 0.8 | Watch (falling) | Prepare to add capacity |
| below 0.6 | Shortage | Add seats or new centres |

**Early warning:** a pair is flagged if it is projected to enter Oversupply or Shortage within the next 6 months, and the month of crossing is shown.

## Slide 5: Results from the pilot

Pilot scope: 4 States (Tamil Nadu, Karnataka, Delhi, Uttar Pradesh), 20 districts, 2 sectors (Electrical and Power, Automotive), 10 trades, so 200 district-trade pairs, with 36 months of history.

| Indicator | Value |
|---|---|
| Forecast demand, next 12 months | 85,014 openings |
| Certified supply per year | 81,404 candidates |
| Pairs in Oversupply | 22 of 200 |
| Pairs in Shortage | 26 of 200 |
| Early warnings (next 6 months) | 10 |
| Forecast accuracy (backtest, last 6 months held out) | 10.1% median MAPE, against 14.5% for a naive average |

What the system found:

- **EV Service Technician and Solar PV Installer:** acute shortage in Bengaluru Urban, Chennai, Coimbatore and Gautam Buddha Nagar (gap ratio around 0.4), with EV demand growing about 32% a year.
- **Electrician (Domestic):** oversupply in East and North West Delhi, Kanpur Nagar, Lucknow and Varanasi (ratio 1.7 to 1.9).
- **Two-Wheeler Service Technician:** oversupply in several UP and Delhi districts (ratio up to 2.4), with demand declining.
- **Automotive Painter and Auto Body Repair:** balanced almost everywhere, Watch (falling) in Tumakuru and Dharwad.

Screenshot: the "Top 10 short" table, or the Early warnings page.

## Slide 6: Key features (use screenshots, 2 x 3 grid)

1. Drill-down from National to State to District to Trade
2. Trade forecast chart with confidence band and source contribution
3. Early warnings with the month of crossing
4. What-if simulator: move a seat slider and watch the status change live
5. Seat reallocation: for example, move Two-Wheeler seats to EV in the same state
6. Job title normaliser: paste a posting, get the trade, NCO code and confidence

## Slide 7: Technology stack and feasibility

| Layer | Technology |
|---|---|
| Dashboard | Python, Streamlit (9 screens) |
| Data processing | pandas, numpy |
| Forecasting | statsmodels Holt-Winters, 80% band, backtest MAPE |
| Title matching | rapidfuzz fuzzy match with confidence 0 to 100 |
| Config | config.yaml for weights and thresholds |
| Charts | Plotly |
| API | FastAPI (`/api/gaps`, `/api/health`) |
| Languages | English and Hindi, from one translations file |

Feasibility points:

- Runs fully offline on one laptop or a state data centre server. It needs no paid services.
- Every weight and threshold sits in one config file, so a planner can change them without touching code.
- Real data can replace the synthetic data source by source: NCS API, e-Shram, PLFS tables, and job portal feeds.
- Adding more states or sectors only means adding rows to the config.

## Slide 8: Impact and next steps

Impact:

- Planners see mismatches **6 to 12 months earlier**, in time for annual target-setting.
- Seats move to trades that have jobs, so placement rates improve and training money is used better.
- One common demand index for MSDE, NCVET, SSCs and state missions.
- Evidence for NSQF course revisions and for new centre approvals.

Next steps:

- Connect to live NCS and e-Shram data.
- Learn the source weights from actual placement outcomes.
- Model migration between districts.
- Add more sectors and all states, plus more Indian languages.

---

## Screenshots to take from the app

Run `streamlit run app.py` and take full-width screenshots of:

1. Overview: KPI row and the top-10 tables
2. Drill-down with the State set to Tamil Nadu
3. Trade forecast for Coimbatore, EV Service Technician (the chart)
4. Early warning table
5. Reallocation and what-if for Uttar Pradesh (Kanpur Nagar, Electrician (Domestic))
6. Emerging trades radar
7. Job title normaliser with "Electrition"
8. Data and refresh, after uploading a sample month
9. Methodology: the weights and backtest section
10. Any page with the language switched to Hindi

## Two-minute demo script (also useful for the video)

1. Overview: "Here are 85,014 forecast openings against 81,404 certified candidates, but the totals hide 26 shortage pairs and 22 oversupply pairs."
2. Drill-down to Tamil Nadu, then Coimbatore. The district x trade matrix shows EV and Solar in shortage.
3. Forecast for EV in Coimbatore: rising demand, a flat supply line, the 80% band and the backtest MAPE.
4. Early warnings: "These pairs will tip over within 6 months, with the month shown."
5. Reallocation and what-if (Uttar Pradesh): the system suggests moving Electrician and Two-Wheeler seats to Solar and EV, with total seats unchanged. Cut Kanpur Nagar Electrician seats in the simulator and watch the status and suggestions update.
6. Normaliser: type "Electrition", get Electrician (Domestic), NCO 7411.0100, with a confidence of 82.
7. Data and refresh: upload next month's sample CSV, the pipeline re-runs and the refresh date changes. Show the API JSON.
8. Switch to Hindi.
