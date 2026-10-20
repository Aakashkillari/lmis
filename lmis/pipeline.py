import pickle
from datetime import date
from pathlib import Path

from lmis import config, data, forecast, gaps, normalise

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "pipeline.pkl"


def build():
    raw = data.generate()
    index_frame, title_mapping = normalise.build_signals(raw)
    forecasts = forecast.forecast_all(index_frame)
    gap_frame = gaps.gap_table(raw["capacity"], index_frame, forecasts)
    return {
        "raw": raw,
        "index": index_frame,
        "title_mapping": title_mapping,
        "forecasts": forecasts,
        "gaps": gap_frame,
        "warnings": gaps.early_warnings(gap_frame, index_frame, forecasts),
        "backtest": forecast.backtest(index_frame),
        "refreshed": date.today().strftime("%d %b %Y"),
        "seed": config.SEED,
    }


def load(rebuild=False):
    if CACHE.exists() and not rebuild:
        with CACHE.open("rb") as handle:
            result = pickle.load(handle)
        if result.get("seed") == config.SEED:
            return result
    result = build()
    CACHE.parent.mkdir(exist_ok=True)
    with CACHE.open("wb") as handle:
        pickle.dump(result, handle)
    return result


if __name__ == "__main__":
    load(rebuild=True)
    print("Pipeline rebuilt:", CACHE)
