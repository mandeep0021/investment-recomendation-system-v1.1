import unittest
from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from Analysis1 import (
    MarketDataError,
    backtest_buy_and_hold,
    calculate_return_metrics,
    calculate_rolling_volatility,
    compare_to_benchmark,
    fetch_market_history,
    get_market_screen,
    parse_tickers,
)


class AnalysisTests(unittest.TestCase):
    def test_ticker_parser_normalizes_deduplicates_and_limits(self):
        self.assertEqual(parse_tickers("aapl, MSFT AAPL; infy.ns"), ["AAPL", "MSFT", "INFY.NS"])
        with self.assertRaisesRegex(ValueError, "at least one"):
            parse_tickers(" , ")
        with self.assertRaisesRegex(ValueError, "no more than 2"):
            parse_tickers("AAPL, MSFT, NVDA", max_tickers=2)
        with self.assertRaisesRegex(ValueError, "Invalid ticker"):
            parse_tickers("AAPL/../private")

    @patch("Analysis1.requests.get")
    def test_fetch_market_history_parses_adjusted_daily_prices(self, get):
        get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "chart": {
                    "error": None,
                    "result": [
                        {
                            "meta": {
                                "symbol": "AAPL",
                                "longName": "Apple Inc.",
                                "currency": "USD",
                                "exchangeName": "NMS",
                                "exchangeTimezoneName": "America/New_York",
                            },
                            "timestamp": [1735765200, 1735851600, 1735938000],
                            "indicators": {
                                "quote": [{"close": [100, 103, 106], "volume": [1000, 1100, 1200]}],
                                "adjclose": [{"adjclose": [99, 102, 105]}],
                            },
                        }
                    ],
                }
            },
        )
        get.return_value.raise_for_status.return_value = None

        history, metadata = fetch_market_history(
            "AAPL", date(2025, 1, 1), date(2025, 1, 3)
        )

        self.assertEqual(history["adjusted_close"].tolist(), [99, 102, 105])
        self.assertEqual(metadata["currency"], "USD")
        self.assertEqual(metadata["name"], "Apple Inc.")
        get.assert_called_once()

    @patch("Analysis1.requests.get")
    def test_fetch_market_history_reports_ticker_errors(self, get):
        get.return_value = Mock(
            json=lambda: {
                "chart": {
                    "error": {"description": "Not found"},
                    "result": None,
                }
            }
        )
        get.return_value.raise_for_status.return_value = None

        with self.assertRaisesRegex(MarketDataError, "No market data for INVALID"):
            fetch_market_history("INVALID", date(2025, 1, 1), date(2025, 1, 3))


    @patch("Analysis1.requests.get")
    def test_fetch_market_history_labels_unadjusted_fallback_and_sorts_deduplicates(self, get):
        timestamps = [
            int(pd.Timestamp("2025-01-02", tz="UTC").timestamp()),
            int(pd.Timestamp("2025-01-01", tz="UTC").timestamp()),
            int(pd.Timestamp("2025-01-02", tz="UTC").timestamp()),
            int(pd.Timestamp("2025-01-03", tz="UTC").timestamp()),
        ]
        get.return_value = Mock(
            json=lambda: {
                "chart": {
                    "error": None,
                    "result": [{
                        "meta": {"symbol": "ABC", "exchangeTimezoneName": "UTC"},
                        "timestamp": timestamps,
                        "indicators": {
                            "quote": [{"close": [101, 100, 102, 103], "volume": [10, 10, 20, 30]}]
                        },
                    }],
                }
            }
        )
        get.return_value.raise_for_status.return_value = None

        history, metadata = fetch_market_history("abc", date(2025, 1, 1), date(2025, 1, 3))

        self.assertEqual(history.index.tolist(), list(pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"])))
        self.assertEqual(history["adjusted_close"].tolist(), [100, 102, 103])
        self.assertEqual(metadata["price_basis"], "unadjusted_fallback")
        self.assertEqual(metadata["duplicate_dates_removed"], "1")

    @patch("Analysis1.time_module.sleep")
    @patch("Analysis1.requests.get")
    def test_fetch_market_history_retries_temporary_request_failure(self, get, sleep):
        success = Mock()
        success.raise_for_status.return_value = None
        success.json.return_value = {
            "chart": {
                "error": None,
                "result": [{
                    "meta": {"symbol": "ABC", "exchangeTimezoneName": "UTC"},
                    "timestamp": [
                        int(pd.Timestamp(day, tz="UTC").timestamp())
                        for day in ("2025-01-01", "2025-01-02", "2025-01-03")
                    ],
                    "indicators": {
                        "quote": [{"close": [100, 101, 102], "volume": [1, 2, 3]}],
                        "adjclose": [{"adjclose": [100, 101, 102]}],
                    },
                }],
            }
        }
        get.side_effect = [__import__("requests").ConnectionError("temporary"), success]

        history, _ = fetch_market_history(
            "ABC", date(2025, 1, 1), date(2025, 1, 3), retry_backoff=0
        )

        self.assertEqual(len(history), 3)
        self.assertEqual(get.call_count, 2)


    @patch("Analysis1.requests.get")
    def test_fetch_market_history_excludes_incomplete_current_session(self, get):
        today = datetime.now(timezone.utc).date()
        days = [today - pd.Timedelta(days=3), today - pd.Timedelta(days=2), today - pd.Timedelta(days=1), today]
        timestamps = [int(pd.Timestamp(day, tz="UTC").timestamp()) for day in days]
        get.return_value = Mock(
            json=lambda: {
                "chart": {
                    "error": None,
                    "result": [{
                        "meta": {
                            "symbol": "ABC",
                            "exchangeTimezoneName": "UTC",
                            "currentTradingPeriod": {
                                "regular": {"end": int(datetime.now(timezone.utc).timestamp()) + 3600}
                            },
                        },
                        "timestamp": timestamps,
                        "indicators": {
                            "quote": [{"close": [100, 101, 102, 103], "volume": [1, 2, 3, 4]}],
                            "adjclose": [{"adjclose": [100, 101, 102, 103]}],
                        },
                    }],
                }
            }
        )
        get.return_value.raise_for_status.return_value = None

        history, _ = fetch_market_history("ABC", days[0], today)

        self.assertEqual(len(history), 3)
        self.assertLess(history.index[-1].date(), today)

    def test_return_metrics_sort_unsorted_datetime_prices(self):
        prices = pd.Series(
            [102, 100, 101],
            index=pd.to_datetime(["2025-01-03", "2025-01-01", "2025-01-02"]),
        )
        metrics = calculate_return_metrics(prices)
        self.assertAlmostEqual(metrics["period_return_pct"], 2.0)

    def test_backtest_sorts_unsorted_dates_before_simulation(self):
        prices = pd.DataFrame(
            {"A": [120, 100, 110]},
            index=pd.to_datetime(["2025-01-03", "2025-01-01", "2025-01-02"]),
        )
        values, metrics, _ = backtest_buy_and_hold(prices, {"A": 100}, 1000)
        self.assertEqual(values.index[0], pd.Timestamp("2025-01-01"))
        self.assertAlmostEqual(metrics["period_return_pct"], 20.0)

    @patch("Analysis1.requests.get")
    def test_fetch_market_history_rejects_malformed_chart_payload(self, get):
        get.return_value.json.return_value = {"chart": []}
        get.return_value.raise_for_status.return_value = None
        with self.assertRaisesRegex(MarketDataError, "valid chart object"):
            fetch_market_history("ABC", date(2025, 1, 1), date(2025, 1, 3), max_retries=0)

    def test_market_metrics_and_screen_are_calculated_from_history(self):
        dates = pd.date_range("2024-01-01", periods=253, freq="B")
        prices = pd.Series(np.linspace(100, 120, len(dates)), index=dates)
        metrics = calculate_return_metrics(prices)
        self.assertAlmostEqual(metrics["period_return_pct"], 20.0)
        self.assertEqual(metrics["observations"], 253)
        self.assertGreater(metrics["annualized_volatility_pct"], 0)
        self.assertEqual(get_market_screen(12, 20, 120, 115), "Buy")
        self.assertEqual(get_market_screen(-10, 30, 90, 100), "Sell")
        self.assertEqual(get_market_screen(5, 60, 110, 100), "Hold")

    def test_market_metrics_reject_insufficient_observations(self):
        prices = pd.Series(
            [100, 101],
            index=pd.date_range("2025-01-01", periods=2, freq="B"),
        )
        with self.assertRaisesRegex(ValueError, "At least three"):
            calculate_return_metrics(prices)

    def test_buy_and_hold_backtest_uses_fixed_shares_and_normalized_weights(self):
        dates = pd.date_range("2024-01-01", periods=4, freq="B")
        prices = pd.DataFrame(
            {"A": [100, 110, 120, 120], "B": [100, 95, 90, 90]},
            index=dates,
        )
        values, metrics, weights = backtest_buy_and_hold(prices, {"A": 75, "B": 25}, 10000)
        self.assertAlmostEqual(values.iloc[-1], 11250)
        self.assertAlmostEqual(metrics["period_return_pct"], 12.5)
        self.assertAlmostEqual(weights["A"], 0.75)
        self.assertAlmostEqual(sum(weights.values()), 1)

    def test_backtest_rejects_non_positive_capital_and_unaligned_prices(self):
        prices = pd.DataFrame({"A": [100, 110]}, index=pd.date_range("2024-01-01", periods=2))
        with self.assertRaisesRegex(ValueError, "positive finite"):
            backtest_buy_and_hold(prices, {"A": 100}, 0)
        unaligned = pd.DataFrame(
            {"A": [100, np.nan], "B": [np.nan, 200]},
            index=pd.date_range("2024-01-01", periods=2),
        )
        with self.assertRaisesRegex(ValueError, "shared valid trading dates"):
            backtest_buy_and_hold(unaligned, {"A": 50, "B": 50}, 1000)

    def test_zero_weight_assets_do_not_restrict_backtest_dates(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="B")
        prices = pd.DataFrame(
            {"A": [100, 105, 110], "B": [np.nan, np.nan, 200]},
            index=dates,
        )
        values, _, weights = backtest_buy_and_hold(
            prices, {"A": 100, "B": 0}, 1000
        )
        self.assertAlmostEqual(values.iloc[-1], 1100)
        self.assertEqual(weights, {"A": 1.0, "B": 0.0})

    def test_ticker_parser_rejects_non_text_and_invalid_limit(self):
        for value in (None, 123, ["AAPL"]):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "must be text"):
                parse_tickers(value)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            parse_tickers("AAPL", max_tickers=0)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            parse_tickers("AAPL", max_tickers=True)

    @patch("Analysis1.requests.get")
    def test_fetch_market_history_rejects_non_finite_timeout_and_backoff(self, get):
        for kwargs in ({"timeout": float("nan")}, {"retry_backoff": float("inf")}, {"max_retries": 1.5}, {"timeout": True}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, "Timeout must be finite"):
                fetch_market_history("ABC", date(2025, 1, 1), date(2025, 1, 3), **kwargs)
        get.assert_not_called()

    def test_backtest_rejects_non_numeric_and_non_finite_allocations(self):
        prices = pd.DataFrame({"A": [100, 101, 102]}, index=pd.date_range("2025-01-01", periods=3))
        for allocation in ("not-a-number", float("nan"), float("inf"), -1, True):
            with self.subTest(allocation=allocation), self.assertRaisesRegex(ValueError, "finite and non-negative"):
                backtest_buy_and_hold(prices, {"A": allocation}, 1000)

    def test_backtest_rejects_non_numeric_initial_investment(self):
        prices = pd.DataFrame({"A": [100, 101, 102]}, index=pd.date_range("2025-01-01", periods=3))
        with self.assertRaisesRegex(ValueError, "positive finite"):
            backtest_buy_and_hold(prices, {"A": 100}, "invalid")
        with self.assertRaisesRegex(ValueError, "positive finite"):
            backtest_buy_and_hold(prices, {"A": 100}, True)


class AdvancedAnalyticsTests(unittest.TestCase):
    def test_sortino_ratio_uses_downside_deviation_and_is_reported(self):
        prices = pd.Series(
            [100, 110, 105, 115, 108, 120],
            index=pd.date_range("2025-01-01", periods=6, freq="B"),
        )
        metrics = calculate_return_metrics(prices, risk_free_rate_annual=0.0)
        self.assertIn("sortino_ratio", metrics)
        self.assertGreater(metrics["sortino_ratio"], 0)
        self.assertTrue(np.isfinite(metrics["sortino_ratio"]))

    def test_risk_free_rate_changes_sharpe_and_sortino(self):
        prices = pd.Series(
            [100, 102, 101, 104, 103, 106, 105],
            index=pd.date_range("2025-01-01", periods=7, freq="B"),
        )
        zero_rf = calculate_return_metrics(prices, 0.0)
        higher_rf = calculate_return_metrics(prices, 0.05)
        self.assertLess(higher_rf["sharpe_ratio"], zero_rf["sharpe_ratio"])
        self.assertLess(higher_rf["sortino_ratio"], zero_rf["sortino_ratio"])

    def test_risk_free_rate_rejects_invalid_values(self):
        prices = pd.Series([100, 101, 99], index=pd.date_range("2025-01-01", periods=3))
        with self.assertRaisesRegex(ValueError, "greater than -100"):
            calculate_return_metrics(prices, -1.0)
        with self.assertRaisesRegex(ValueError, "greater than -100"):
            calculate_return_metrics(prices, True)

    def test_rolling_volatility_uses_trailing_window(self):
        prices = pd.Series(
            [100, 101, 99, 102, 100, 103, 101],
            index=pd.date_range("2025-01-01", periods=7, freq="B"),
        )
        rolling = calculate_rolling_volatility(prices, window=3)
        self.assertTrue(rolling.iloc[:3].isna().all())
        self.assertTrue(np.isfinite(rolling.iloc[3:]).all())
        self.assertTrue((rolling.dropna() >= 0).all())

    def test_rolling_volatility_rejects_invalid_window(self):
        prices = pd.Series([100, 101, 99], index=pd.date_range("2025-01-01", periods=3))
        with self.assertRaisesRegex(ValueError, "at least 2"):
            calculate_rolling_volatility(prices, window=1)

    def test_benchmark_beta_alpha_and_excess_return(self):
        benchmark_returns = np.array([0.010, -0.010, 0.020, 0.005, 0.015, -0.005])
        asset_returns = 2.0 * benchmark_returns + 0.001
        dates = pd.date_range("2025-01-01", periods=len(benchmark_returns) + 1, freq="B")
        benchmark_prices = pd.Series(100 * np.r_[1.0, np.cumprod(1 + benchmark_returns)], index=dates)
        asset_prices = pd.Series(100 * np.r_[1.0, np.cumprod(1 + asset_returns)], index=dates)

        comparison = compare_to_benchmark(asset_prices, benchmark_prices, 0.0)

        self.assertAlmostEqual(comparison["beta"], 2.0, places=10)
        self.assertAlmostEqual(comparison["alpha_annualized_pct"], 25.2, places=8)
        self.assertEqual(comparison["observations"], len(benchmark_returns))
        self.assertAlmostEqual(
            comparison["excess_return_pct"],
            comparison["asset_common_period_return_pct"] - comparison["benchmark_period_return_pct"],
        )

    def test_benchmark_comparison_requires_shared_return_dates(self):
        asset = pd.Series([100, 101, 102], index=pd.date_range("2025-01-01", periods=3, freq="B"))
        benchmark = pd.Series([100, 101, 102], index=pd.date_range("2025-02-01", periods=3, freq="B"))
        with self.assertRaisesRegex(ValueError, "shared daily return"):
            compare_to_benchmark(asset, benchmark)

    def test_benchmark_comparison_rejects_zero_variance_benchmark(self):
        dates = pd.date_range("2025-01-01", periods=5, freq="B")
        asset = pd.Series([100, 101, 102, 103, 104], index=dates)
        benchmark = pd.Series([100, 100, 100, 100, 100], index=dates)
        with self.assertRaisesRegex(ValueError, "zero or invalid variance"):
            compare_to_benchmark(asset, benchmark)


if __name__ == "__main__":
    unittest.main()
