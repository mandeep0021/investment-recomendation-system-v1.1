"""Data providers and decision-support calculations for the dashboard."""

import re
import time as time_module
from datetime import date, datetime, time, timedelta, timezone
from typing import Mapping

import numpy as np
import pandas as pd
import requests


TICKER_PATTERN = re.compile(r"^[A-Za-z0-9.^=_-]{1,32}$")
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


class MarketDataError(ValueError):
    """Raised when the public market-data provider cannot return usable data."""


def parse_tickers(value: str, max_tickers: int = 8) -> list[str]:
    """Parse and validate a comma- or whitespace-separated ticker list."""
    if not isinstance(value, str):
        raise ValueError("Ticker input must be text.")
    if not isinstance(max_tickers, int) or isinstance(max_tickers, bool) or max_tickers < 1:
        raise ValueError("The maximum ticker count must be a positive integer.")
    tickers = []
    seen = set()
    for token in re.split(r"[\s,;]+", value.strip()):
        symbol = token.upper()
        if not symbol:
            continue
        if not TICKER_PATTERN.fullmatch(symbol):
            raise ValueError(f"Invalid ticker '{token}'. Use letters, numbers, '.', '^', '=', '_', or '-'.")
        if symbol not in seen:
            tickers.append(symbol)
            seen.add(symbol)
    if not tickers:
        raise ValueError("Enter at least one ticker symbol.")
    if len(tickers) > max_tickers:
        raise ValueError(f"Enter no more than {max_tickers} unique tickers.")
    return tickers


def fetch_market_history(
    symbol: str,
    start_date: date,
    end_date: date,
    timeout: float = 15,
    max_retries: int = 2,
    retry_backoff: float = 0.5,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Fetch and validate daily prices from Yahoo Finance's public chart endpoint.

    Adjusted close is preferred. If Yahoo omits it, close is retained as an
    explicitly labelled unadjusted fallback so downstream analysis can still
    run without silently implying that dividend/split adjustments were used.
    """
    symbol = str(symbol).strip().upper()
    if not TICKER_PATTERN.fullmatch(symbol):
        raise ValueError(f"Invalid ticker symbol: {symbol}")
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise ValueError("Start date and end date must be date values.")
    if start_date > end_date:
        raise ValueError("Start date must be on or before end date.")
    if isinstance(timeout, (bool, np.bool_)) or isinstance(retry_backoff, (bool, np.bool_)):
        raise ValueError("Timeout must be finite and positive; retries must be a non-negative integer and backoff finite and non-negative.")
    try:
        timeout = float(timeout)
        retry_backoff = float(retry_backoff)
    except (TypeError, ValueError) as error:
        raise ValueError("Timeout must be finite and positive; retries must be a non-negative integer and backoff finite and non-negative.") from error
    if (
        not np.isfinite(timeout) or timeout <= 0
        or not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0
        or not np.isfinite(retry_backoff) or retry_backoff < 0
    ):
        raise ValueError("Timeout must be finite and positive; retries must be a non-negative integer and backoff finite and non-negative.")

    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_exclusive = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    params = {
        "period1": int(start.timestamp()),
        "period2": int(end_exclusive.timestamp()),
        "interval": "1d",
        "events": "div,splits",
    }
    last_error = None
    payload = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                YAHOO_CHART_URL.format(symbol=symbol),
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (compatible; InvestmentResearchDashboard/1.0)"},
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            break
        except (requests.RequestException, ValueError) as error:
            last_error = error
            if attempt >= max_retries:
                break
            time_to_wait = retry_backoff * (2 ** attempt)
            if time_to_wait:
                time_module.sleep(time_to_wait)

    if payload is None:
        if isinstance(last_error, ValueError) and not isinstance(last_error, requests.RequestException):
            raise MarketDataError(f"The market-data response for {symbol} was not valid JSON after {max_retries + 1} attempts.") from last_error
        raise MarketDataError(
            f"Could not retrieve {symbol} after {max_retries + 1} attempts. Check your internet connection; "
            "Yahoo Finance may be temporarily unavailable or rate-limiting requests."
        ) from last_error

    if not isinstance(payload, dict):
        raise MarketDataError(f"The market-data response for {symbol} was not a JSON object.")
    chart = payload.get("chart")
    if not isinstance(chart, dict):
        raise MarketDataError(f"The market-data response for {symbol} did not contain a valid chart object.")
    chart_error = chart.get("error")
    if chart_error:
        if isinstance(chart_error, dict):
            description = chart_error.get("description") or "provider rejected the ticker or request"
        else:
            description = "provider returned an error"
        raise MarketDataError(f"No market data for {symbol}: {description}.")
    results = chart.get("result")
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        raise MarketDataError(
            f"No daily history was returned for {symbol} in the selected date range. "
            "Check the ticker format and available history."
        )

    result = results[0]
    metadata = result.get("meta") if isinstance(result.get("meta"), dict) else {}
    timestamps = result.get("timestamp")
    indicators = result.get("indicators")
    if not isinstance(timestamps, list) or not timestamps or not isinstance(indicators, dict):
        raise MarketDataError(f"The market-data response for {symbol} did not contain daily prices.")
    quote_list = indicators.get("quote")
    if not isinstance(quote_list, list) or not quote_list or not isinstance(quote_list[0], dict):
        raise MarketDataError(f"The market-data response for {symbol} did not contain valid quote data.")

    quote = quote_list[0]
    closes = quote.get("close")
    volumes = quote.get("volume")
    adjusted_groups = indicators.get("adjclose")
    adjusted_closes = None
    if isinstance(adjusted_groups, list) and adjusted_groups and isinstance(adjusted_groups[0], dict):
        adjusted_closes = adjusted_groups[0].get("adjclose")
    adjustment_status = "adjusted"
    adjusted_values = (
        pd.to_numeric(pd.Series(adjusted_closes), errors="coerce").to_numpy(dtype=float)
        if isinstance(adjusted_closes, list) else np.array([], dtype=float)
    )
    if adjusted_closes is None or not (np.isfinite(adjusted_values) & (adjusted_values > 0)).any():
        # Explicit fallback: downstream UI/reporting must disclose this basis.
        adjusted_closes = closes
        adjustment_status = "unadjusted_fallback"
    if not isinstance(closes, list) or not isinstance(adjusted_closes, list):
        raise MarketDataError(f"The market-data response for {symbol} did not contain usable close-price arrays.")
    if len(timestamps) != len(closes) or len(timestamps) != len(adjusted_closes):
        raise MarketDataError(f"The market-data response for {symbol} had inconsistent price arrays.")
    if volumes is None:
        volumes = [None] * len(timestamps)
    if not isinstance(volumes, list) or len(timestamps) != len(volumes):
        raise MarketDataError(f"The market-data response for {symbol} had inconsistent volume values.")

    exchange_timezone = metadata.get("exchangeTimezoneName") or "UTC"
    try:
        numeric_timestamps = pd.to_numeric(pd.Series(timestamps), errors="raise")
        if not np.isfinite(numeric_timestamps.to_numpy(dtype=float)).all():
            raise ValueError("non-finite timestamp")
        dates = pd.to_datetime(numeric_timestamps, unit="s", utc=True).dt.tz_convert(exchange_timezone).dt.tz_localize(None)
    except (TypeError, ValueError, KeyError, OverflowError) as error:
        raise MarketDataError(f"The provider returned invalid timestamps or an unsupported timezone for {symbol}.") from error

    history = pd.DataFrame(
        {
            "adjusted_close": adjusted_closes,
            "close": closes,
            "volume": volumes,
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )
    for column in ("adjusted_close", "close", "volume"):
        history[column] = pd.to_numeric(history[column], errors="coerce")
    history = history.replace([np.inf, -np.inf], np.nan)
    invalid_price_rows = int(history[["adjusted_close", "close"]].isna().any(axis=1).sum())
    history = history.dropna(subset=["adjusted_close", "close"])
    history = history.loc[(history.index.date >= start_date) & (history.index.date <= end_date)]
    history = history[(history["adjusted_close"] > 0) & (history["close"] > 0)]
    duplicate_dates = int(history.index.duplicated(keep="last").sum())
    history = history.loc[~history.index.duplicated(keep="last")].sort_index(kind="stable")
    if len(history) < 3:
        raise MarketDataError(f"Fewer than three usable daily prices were returned for {symbol}.")

    # Yahoo may include today's still-forming daily candle. When its regular
    # session end is supplied, omit that candle until the session has ended.
    current_periods = metadata.get("currentTradingPeriod")
    regular_period = current_periods.get("regular") if isinstance(current_periods, dict) else None
    if isinstance(regular_period, dict):
        session_end = regular_period.get("end")
        try:
            session_end = float(session_end)
            now_utc = datetime.now(timezone.utc).timestamp()
            if np.isfinite(session_end) and now_utc < session_end:
                local_today = datetime.now(timezone.utc).astimezone(
                    __import__("zoneinfo").ZoneInfo(exchange_timezone)
                ).date()
                history = history.loc[history.index.date < local_today]
        except (TypeError, ValueError, OverflowError, KeyError):
            # A malformed optional session field must not invalidate otherwise
            # valid historical data; the quality metadata records no claim here.
            pass
    if len(history) < 3:
        raise MarketDataError(
            f"Fewer than three completed, usable daily prices were returned for {symbol}. "
            "Choose an earlier end date or try again after the market session closes."
        )

    asset_metadata = {
        "symbol": str(metadata.get("symbol") or symbol),
        "name": str(metadata.get("longName") or metadata.get("shortName") or symbol),
        "currency": str(metadata.get("currency") or "Unknown"),
        "exchange": str(metadata.get("fullExchangeName") or metadata.get("exchangeName") or "Unknown"),
        "timezone": exchange_timezone,
        "price_basis": adjustment_status,
        "duplicate_dates_removed": str(duplicate_dates),
        "invalid_price_rows_removed": str(invalid_price_rows),
    }
    return history, asset_metadata


def _clean_price_series(prices: pd.Series) -> pd.Series:
    """Return a positive, sorted, de-duplicated price series."""
    if not isinstance(prices, pd.Series):
        raise ValueError("Prices must be provided as a pandas Series.")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Daily prices must use a DatetimeIndex.")
    series = pd.to_numeric(prices, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    series = series[series > 0]
    return series.loc[~series.index.duplicated(keep="last")].sort_index(kind="stable")


def _daily_risk_free_rate(annual_rate: float) -> float:
    """Convert an annual effective risk-free rate to a 252-session daily rate."""
    if isinstance(annual_rate, (bool, np.bool_)):
        raise ValueError("Risk-free rate must be finite and greater than -100%.")
    try:
        annual_rate = float(annual_rate)
    except (TypeError, ValueError) as error:
        raise ValueError("Risk-free rate must be a finite annual decimal rate.") from error
    if not np.isfinite(annual_rate) or annual_rate <= -1:
        raise ValueError("Risk-free rate must be finite and greater than -100%.")
    return float((1 + annual_rate) ** (1 / 252) - 1)


def calculate_return_metrics(
    prices: pd.Series,
    risk_free_rate_annual: float = 0.02,
) -> dict[str, float | int | str]:
    """Calculate historical performance and risk metrics from daily positive prices.

    risk_free_rate_annual is an annual effective decimal rate (0.02 = 2%).
    Sortino uses downside deviation of daily returns below the daily risk-free
    target. Sharpe uses the sample standard deviation of daily excess returns.
    """
    series = _clean_price_series(prices)
    if len(series) < 3:
        raise ValueError("At least three positive daily prices are required for performance analysis.")
    daily_returns = series.pct_change().dropna()
    daily_rf = _daily_risk_free_rate(risk_free_rate_annual)
    excess_returns = daily_returns - daily_rf
    period_return = (float(series.iloc[-1]) / float(series.iloc[0]) - 1) * 100
    elapsed_days = max((series.index[-1] - series.index[0]).days, 1)
    years = elapsed_days / 365.25
    annualized_return = ((float(series.iloc[-1]) / float(series.iloc[0])) ** (1 / years) - 1) * 100
    daily_std = float(daily_returns.std(ddof=1))
    excess_std = float(excess_returns.std(ddof=1))
    annualized_volatility = float(daily_std * np.sqrt(252) * 100)
    sharpe_ratio = (
        float(excess_returns.mean() / excess_std * np.sqrt(252))
        if np.isfinite(excess_std) and excess_std > 0 else 0.0
    )
    downside = np.minimum(excess_returns.to_numpy(dtype=float), 0.0)
    downside_deviation = float(np.sqrt(np.mean(np.square(downside))))
    sortino_ratio = (
        float(excess_returns.mean() / downside_deviation * np.sqrt(252))
        if np.isfinite(downside_deviation) and downside_deviation > 0 else 0.0
    )
    drawdown = series / series.cummax() - 1
    return {
        "period_return_pct": period_return,
        "annualized_return_pct": annualized_return,
        "annualized_volatility_pct": annualized_volatility,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "max_drawdown_pct": float(drawdown.min() * 100),
        "observations": int(len(series)),
        "latest_price": float(series.iloc[-1]),
    }


def calculate_rolling_volatility(
    prices: pd.Series,
    window: int = 21,
) -> pd.Series:
    """Calculate trailing annualized volatility from rolling daily returns."""
    if not isinstance(window, int) or window < 2:
        raise ValueError("Rolling-volatility window must be an integer of at least 2.")
    series = _clean_price_series(prices)
    if len(series) < 2:
        raise ValueError("At least two positive daily prices are required for rolling volatility.")
    rolling = series.pct_change().rolling(window=window, min_periods=window).std(ddof=1)
    result = rolling * np.sqrt(252) * 100
    result.name = f"{window}-session rolling volatility (%)"
    return result


def compare_to_benchmark(
    asset_prices: pd.Series,
    benchmark_prices: pd.Series,
    risk_free_rate_annual: float = 0.02,
) -> dict[str, float | int]:
    """Compare an asset with a benchmark using common-date daily returns.

    Beta is covariance(asset, benchmark) / variance(benchmark). Alpha is the
    annualized CAPM intercept using arithmetic daily mean excess returns.
    Relative period return is the difference in percentage points over the
    common return window, not a currency-converted result.
    """
    asset = _clean_price_series(asset_prices)
    benchmark = _clean_price_series(benchmark_prices)
    if len(asset) < 3 or len(benchmark) < 3:
        raise ValueError("Asset and benchmark each need at least three prices.")
    common_prices = pd.concat(
        [asset.rename("asset"), benchmark.rename("benchmark")],
        axis=1,
        join="inner",
    ).dropna()
    returns = common_prices.pct_change().dropna()
    if len(returns) < 3:
        raise ValueError("At least three shared daily return observations are required for benchmark analysis.")
    daily_rf = _daily_risk_free_rate(risk_free_rate_annual)
    benchmark_variance = float(returns["benchmark"].var(ddof=1))
    if not np.isfinite(benchmark_variance) or benchmark_variance <= 0:
        raise ValueError("Benchmark returns have zero or invalid variance; beta and alpha cannot be estimated.")
    beta = float(returns["asset"].cov(returns["benchmark"]) / benchmark_variance)
    alpha_daily = float(
        (returns["asset"] - daily_rf).mean()
        - beta * (returns["benchmark"] - daily_rf).mean()
    )
    asset_common_return = float((1 + returns["asset"]).prod() - 1)
    benchmark_common_return = float((1 + returns["benchmark"]).prod() - 1)
    return {
        "beta": beta,
        "alpha_annualized_pct": alpha_daily * 252 * 100,
        "benchmark_period_return_pct": benchmark_common_return * 100,
        "asset_common_period_return_pct": asset_common_return * 100,
        "excess_return_pct": (asset_common_return - benchmark_common_return) * 100,
        "observations": int(len(returns)),
    }


def get_market_screen(
    annualized_return_pct: float,
    annualized_volatility_pct: float,
    latest_price: float,
    trend_average: float,
) -> str:
    """Return a transparent, unpersonalized historical-momentum screening label."""
    if annualized_return_pct >= 8 and annualized_volatility_pct <= 45 and latest_price >= trend_average:
        return "Buy"
    if annualized_return_pct < 0 and latest_price < trend_average:
        return "Sell"
    return "Hold"


def backtest_buy_and_hold(
    adjusted_prices: pd.DataFrame,
    weights: Mapping[str, float],
    initial_investment: float,
    risk_free_rate_annual: float = 0.02,
) -> tuple[pd.Series, dict[str, float | int | str], dict[str, float]]:
    """Simulate static-share buy-and-hold positions with normalized starting allocations."""
    if isinstance(initial_investment, (bool, np.bool_)):
        raise ValueError("Initial investment must be a positive finite amount.")
    try:
        initial_investment = float(initial_investment)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Initial investment must be a positive finite amount.") from error
    if not np.isfinite(initial_investment) or initial_investment <= 0:
        raise ValueError("Initial investment must be a positive finite amount.")
    if not isinstance(adjusted_prices, pd.DataFrame):
        raise ValueError("Portfolio prices must be provided as a pandas DataFrame.")
    if adjusted_prices.empty or not weights:
        raise ValueError("Select at least one asset with historical price data.")
    if set(weights).difference(adjusted_prices.columns):
        raise ValueError("Portfolio weights contain assets without price data.")
    try:
        numeric_weights = {}
        for symbol, weight in weights.items():
            if isinstance(weight, (bool, np.bool_)):
                raise ValueError("Portfolio allocations must be finite and non-negative.")
            numeric_weights[symbol] = float(weight)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Portfolio allocations must be finite and non-negative.") from error
    if any(not np.isfinite(weight) or weight < 0 for weight in numeric_weights.values()):
        raise ValueError("Portfolio allocations must be finite and non-negative.")
    total_weight = sum(numeric_weights.values())
    if total_weight <= 0:
        raise ValueError("Portfolio allocations must add up to more than zero.")

    normalized_weights = {symbol: weight / total_weight for symbol, weight in numeric_weights.items()}
    active_weights = {
        symbol: weight for symbol, weight in normalized_weights.items() if weight > 0
    }
    if not isinstance(adjusted_prices.index, pd.DatetimeIndex):
        raise ValueError("Portfolio prices must use a DatetimeIndex.")
    aligned_prices = adjusted_prices[list(active_weights)].apply(pd.to_numeric, errors="coerce")
    aligned_prices = aligned_prices.replace([np.inf, -np.inf], np.nan)
    aligned_prices = aligned_prices.loc[~aligned_prices.index.duplicated(keep="last")].sort_index(kind="stable")
    aligned_prices = aligned_prices.dropna(how="any")
    aligned_prices = aligned_prices[(aligned_prices > 0).all(axis=1)]
    if len(aligned_prices) < 2:
        raise ValueError("Selected assets need at least two shared valid trading dates for a backtest.")

    indexed_prices = aligned_prices.divide(aligned_prices.iloc[0], axis="columns")
    value = sum(indexed_prices[symbol] * weight for symbol, weight in active_weights.items())
    portfolio_value = value * float(initial_investment)
    portfolio_value.name = "Portfolio value"
    metrics = calculate_return_metrics(portfolio_value, risk_free_rate_annual)
    return portfolio_value, metrics, normalized_weights


