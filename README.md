# Pramaan: skill demand intelligence

Pramaan shows Tamil Nadu skill planners where jobs will open in the next 12 months and whether training seats match them, by district and trade. Built for SIH 2026, problem statement 26246 (MSDE).

Pilot scope: 8 districts, 10 trades, 2 sectors (Electrical & Power, Automotive).

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The first start builds the forecasts, which takes about 10 seconds, and caches them in `.cache/`.

## AI assistant

Open `.env` and paste your NVIDIA API key after `NVIDIA_API_KEY=`. The model and endpoint are set in the same file. `.env` is never committed. Without a key, Ask Pramaan answers from built-in rules.

## API

```bash
uvicorn api:app --port 8000
```

- `GET /api/gaps?district=&trade=&sector=&status=`
- `GET /api/warnings`
- `GET /api/health`

## Layout

- `app.py`: navigation, language and the sidebar
- `pages/`: Dashboard, Explore, Plan, Ask Pramaan, How it works
- `pramaan/settings.py`: districts, trades, weights and status bands
- `pramaan/model.py`: demand index, forecast, gaps, warnings, seat moves and the title matcher
- `pramaan/assistant.py`: AI assistant context and calls
- `pramaan/charts.py` and `pramaan/theme.py`: visuals
- `pramaan/text.py`: English, Tamil and Hindi
