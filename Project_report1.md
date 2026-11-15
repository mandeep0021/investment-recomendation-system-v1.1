# Investment Recommendation System

## Capstone Project Report

**Project area:** Investment banking and financial analytics  
**Application:** Python and Streamlit  
**Live data source:** Yahoo Finance public chart endpoint  
**Price history:** Requested from Yahoo Finance when a user submits tickers

## Abstract

The Investment Recommendation System is a local research dashboard for loading historical daily prices for public-market tickers, comparing risk and performance, and exploring a same-currency buy-and-hold portfolio backtest. The app calculates period return, annualized return and volatility, Sharpe ratio under a documented zero-risk-free-rate assumption, and maximum drawdown. It uses provider-sourced history only and does not provide personalized advice, predict prices, or execute trades.

## 1. Problem and Objectives

Comparing investment alternatives requires reviewing return, volatility, and downside risk over a common period. This project provides a reproducible interactive workflow that:

- retrieves historical data for user-selected ticker symbols;
- compares assets against an optional benchmark;
- calculates clearly defined historical statistics;
- applies a transparent historical-momentum screen;
- simulates an adjusted-price buy-and-hold portfolio over shared dates;
- exports market summaries, price history, backtest values, and a portfolio summary.

## 2. Scope and Architecture

1. The user submits up to eight ticker symbols and a history period in `App1.py`.
2. `Analysis1.py` requests daily chart data from Yahoo Finance's public chart endpoint.
3. The analytics layer validates and normalizes price rows, computes performance metrics, and runs a portfolio calculation.
4. Streamlit displays market comparisons, charts, errors, methodology, privacy information, terms, and downloadable CSV/text output in a responsive single-page layout.
5. `tests/Test_analysis1.py` verifies calculations, data parsing, validation, and provider error handling without live network calls.

No fictional market dataset is bundled or used as fallback. The project excludes brokerage integration and order execution.

## 3. Market Data and Reliability

The app accepts up to eight ticker symbols using Yahoo Finance conventions, including US symbols such as `AAPL` and NSE symbols such as `INFY.NS`. A benchmark can be requested separately. Daily adjusted-close history, ordinary close, volume, exchange, name, timezone, and currency are parsed from the provider response. Successful data requests are cached in Streamlit for 15 minutes.

The provider endpoint is public and unofficial; availability, ticker coverage, latency, delays, and response format are outside the application's control. The app reports failed symbols, invalid ranges, or insufficient overlapping data explicitly. It does not replace failed requests with synthetic values. Provider data should be independently checked before use. The Streamlit interface sets a browser title, description, and custom favicon, wraps its tabs and input columns on narrow screens, and has no external navigation or contact details configured.

## 4. Analytics Method

Let \(P_0\) be the first adjusted close, \(P_T\) the last adjusted close, and \(t\) the observed calendar duration in years:

- **Period return:** \((P_T/P_0 - 1) \times 100\%\).
- **Annualized return:** \(((P_T/P_0)^{1/t} - 1) \times 100\%\).
- **Annualized volatility:** sample standard deviation of daily percentage returns multiplied by \(\sqrt{252}\).
- **Sharpe ratio:** average daily return divided by daily return sample standard deviation, multiplied by \(\sqrt{252}\); the assumed risk-free rate is 0%.
- **Maximum drawdown:** minimum of price divided by its running maximum minus one.

Adjusted close is used when supplied by the provider so that available corporate-action adjustments are reflected in the historic series.

## 5. Historical-Momentum Screen

The screen uses annualized historical return, annualized volatility, and the latest adjusted close versus the average of up to 50 available sessions:

| Label | Rule |
|---|---|
| Buy | Annualized historical return >= 8%, annualized volatility <= 45%, and latest close >= trailing average |
| Sell | Annualized historical return < 0% and latest close < trailing average |
| Hold | Every other case |

These are educational thresholds, not industry standards, forecasts, or personalized recommendations. Historical observations do not predict future results.

## 6. Portfolio Backtest

Starting allocations are normalized to 100%. The backtest uses adjusted-price rows shared by every selected asset. At the first common close, it allocates starting capital across normalized adjusted-price series and follows the resulting buy-and-hold total-return proxy without periodic rebalancing. Provider adjustments for distributions/splits are included where available; this is not a ledger of actual tradable shares. It reports ending value, cumulative and annualized return, annualized volatility, and maximum drawdown.

The backtest requires assets quoted in the same currency. It does not model transaction fees, taxes, slippage, deposits, withdrawals, rebalancing, or personal tax treatment. A benchmark in another currency is indexed for percentage comparison only; foreign-exchange effects are not converted.

## 7. Privacy and Terms

The app includes privacy and terms tabs backed by `Privacy_policy1.md` and `Terms_and_conditions1.md`. These describe the local data flow, third-party market-data requests, in-memory cache, downloads, financial-use limitations, and the need for legal review before public release. They are project notices, not legal advice.

## 8. Testing

Unit tests cover ticker parsing, mocked Yahoo response parsing, provider error messages, historical-metric calculations, screen thresholds, backtest arithmetic, invalid capital, and nonoverlapping dates. Tests run without making live network requests:

```powershell
python -m unittest discover -s tests -v
python -m compileall App1.py Analysis1.py Generate_deliverables1.py tests
```

## 9. Limitations and Responsible Use

- Data is obtained from a public unofficial endpoint that may be delayed, incomplete, rate-limited, or unavailable.
- A ticker's historical series may be revised, adjusted, or returned in a different format.
- Annualized values on short periods are noisy and sensitive to the selected date range.
- The Sharpe calculation assumes a 0% risk-free rate and does not model fees.
- Historical momentum rules do not account for goals, suitability, liquidity needs, taxes, or an investor's circumstances.
- Multi-currency portfolios are rejected; benchmark currency effects are not converted.
- This application is not financial advice, is not a forecast, and does not execute or route trades.

## 10. Conclusion

The project demonstrates a research workflow using fetched historical prices rather than hand-entered example metrics. Its price-analysis formulas, portfolio assumptions, provider limitations, and privacy and terms notices are explicit. Users should verify provider data and seek qualified advice before real financial decisions. The app is not publicly launched; a custom domain and policy review are required first.
