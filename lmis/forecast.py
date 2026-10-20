import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from lmis import config

KEYS = ["state", "district", "trade"]


def fit_holt_winters(values):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ExponentialSmoothing(
            values,
            trend="add",
            damped_trend=True,
            seasonal="add",
            seasonal_periods=12,
            initialization_method="estimated",
        )
        return model.fit(optimized=True, use_brute=False)


def forecast_series(values, steps):
    fit = fit_holt_winters(np.asarray(values, dtype=float))
    mean = np.clip(fit.forecast(steps), 0, None)
    residual_sd = np.std(fit.resid, ddof=1)
    widen = np.sqrt(np.arange(1, steps + 1))
    lower = np.clip(mean - 1.96 * residual_sd * widen, 0, None)
    upper = mean + 1.96 * residual_sd * widen
    return mean, lower, upper


def forecast_all(index_frame):
    last_month = index_frame["month"].max()
    future = pd.period_range(last_month + 1, periods=config.FORECAST_MONTHS, freq="M")
    frames = []
    for key, group in index_frame.groupby(KEYS, sort=False):
        series = group.sort_values("month")["openings"].to_numpy()
        mean, lower, upper = forecast_series(series, config.FORECAST_MONTHS)
        frames.append(pd.DataFrame({
            "state": key[0],
            "district": key[1],
            "trade": key[2],
            "month": future,
            "forecast": mean,
            "lower": lower,
            "upper": upper,
        }))
    return pd.concat(frames, ignore_index=True)


def mape(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mask = actual > 0
    return float(np.mean(np.abs(actual[mask] - predicted[mask]) / actual[mask]) * 100)


def backtest(index_frame):
    hold = config.BACKTEST_MONTHS
    rows = []
    for key, group in index_frame.groupby(KEYS, sort=False):
        series = group.sort_values("month")["openings"].to_numpy()
        train, test = series[:-hold], series[-hold:]
        mean, _, _ = forecast_series(train, hold)
        naive = np.repeat(train[-12:].mean(), hold)
        rows.append({
            "state": key[0],
            "district": key[1],
            "trade": key[2],
            "mape": mape(test, mean),
            "naive_mape": mape(test, naive),
            "actual_6m": test.sum(),
            "forecast_6m": mean.sum(),
        })
    return pd.DataFrame(rows)
