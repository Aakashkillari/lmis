# Pramaan

Pramaan shows skill planners where jobs will open in the next 12 months, whether enough people are being trained for them, and where training seats should move. Built for Smart India Hackathon 2026, problem statement 26246 (MSDE).

Pilot: 2 states (Tamil Nadu and Karnataka), 8 districts each, 10 trades, 2 fields (Electrical & power, Vehicles). The pilot runs on a demo dataset that follows the structure of NCS, e-Shram, PLFS and NCVT data.

## What is in it

- **National view** (`/india`): both states side by side, every trade compared, and the worst gaps in the country ranked.
- **State dashboard, Explore, Plan seats**: district map, 12-month forecasts, early warnings, and seat moves that keep the total unchanged.
- **Ask Pramaan**: plain-language AI answers in the chosen language, told who is asking.
- **How it works** (`/method`): the full methodology with the live weights, rules and accuracy.
- **Languages**: English, Tamil, Hindi and Kannada. Translations live in `frontend/src/locales/` with English text as the key; `strings.en.json` lists every string.
- **Sign-in with roles**: national planner, state planning cell, district officer and sector council each open on their own view.

## Stack

- Frontend: React, Vite, TypeScript, custom SVG charts and maps, IBM Plex Sans and Noto Sans Tamil
- Backend: FastAPI (Python), pandas, statsmodels Holt-Winters forecasts, RapidFuzz title matching
- AI assistant: NVIDIA's OpenAI-compatible API, model set in `.env`
- Sign-in: PBKDF2-SHA256 password hashes, httpOnly session cookie, lockout after 5 wrong tries

## Run for a demo (one command)

```bash
cd frontend && npm install && npm run build && cd ..
.venv\Scripts\python -m uvicorn server:app --port 8000
```

Open http://localhost:8000.

## Run while developing

```bash
.venv\Scripts\python -m uvicorn server:app --port 8000 --reload
cd frontend && npm run dev
```

Open http://localhost:5173. The dev server forwards `/api` and `/docs` to port 8000.

## Accounts

Four demo accounts are defined in `pramaan/users.py` and can be opened from the sign-in page without a password. The demo password is set by `PRAMAAN_DEMO_PASSWORD` (default in `pramaan/users.py`). Turn one-click demo sign-in off with `PRAMAAN_DEMO_LOGINS=off`, and set `PRAMAAN_SECURE_COOKIE=on` when serving over HTTPS.

## AI assistant

Put your key in `.env` after `NVIDIA_API_KEY=`. `.env` is never committed. Without a key, Ask Pramaan answers from built-in rules.

## Adding a state

Add its districts and story rules to `STATES` in `pramaan/settings.py`, put its district shapes in `assets/` (same format as `tn_districts.json`), and add the name to `PILOT_STATES` in `frontend/src/auth.tsx`. Forecasts, warnings, seat moves and exports then work the same way.

## API

Full reference at `/docs`.

- `GET /api/national`: every pilot state compared, with all district and trade gaps
- `GET /api/data?state=`: one state's forecasts, warnings and seat moves
- `GET /api/gaps?state=&district=&trade=`: current gaps with NCO codes and NSQF levels
- `GET /api/export/{gaps|forecast|warnings|moves}.csv?state=&sector=&district=&trade=`: spreadsheets (sign-in needed; `state=all` for every state)
- `GET /api/match?q=`: match a job title to a trade (sign-in needed)
- `POST /api/ask`: streamed answer to a question (sign-in needed)
- `POST /api/login`, `POST /api/login/demo`, `GET /api/me`, `POST /api/logout`: sign-in
