# LMIS: Labour Market Intelligence System

Prototype for Smart India Hackathon 2026, problem statement 26246 (MSDE): AI-Enabled Labour Market Intelligence and Skill Demand-Supply Forecasting Engine.

The pilot covers 4 states, 20 districts, 2 sectors and 10 trades. It uses 36 months of synthetic monthly data, modelled on the structure of NCS, PLFS, e-Shram and NCVT.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the dashboard

```bash
streamlit run app.py
```

Open http://localhost:8501. The first run builds every forecast, which takes about 40 seconds, and caches the result in `.cache/`. To rebuild after changing `lmis/config.py`, run `python -m lmis.pipeline`.

## Run the API

```bash
uvicorn lmis.api:app --port 8000
```

- `GET /api/gaps?state=&district=&trade=&sector=&status=`
- `GET /api/warnings?state=&district=&trade=`
- `GET /api/meta`
- Interactive docs: http://localhost:8000/docs

## Layout

- `app.py`: the entry point, navigation and language switch
- `views/`: one file per page
- `lmis/config.py`: states, districts, trades, NCO/QP/NSQF codes, weights, thresholds and the planted stories
- `lmis/data.py`: the synthetic data generator (fixed seed)
- `lmis/normalise.py`: title-to-NCO mapping, z-scores, demand index and calibration
- `lmis/forecast.py`: Holt-Winters forecasts and the backtest
- `lmis/gaps.py`: supply, gap ratio, status, early warnings and ranking
- `lmis/recommend.py`: seat reallocation
- `lmis/api.py`: the FastAPI export layer
- `lmis/i18n.py`: English and Hindi strings
- `lmis/ui.py`: shared styling, tables and charts
