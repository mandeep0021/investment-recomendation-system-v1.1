# Phase 2 — Advanced investment analytics

## Implemented

- Added a configurable annual effective risk-free-rate assumption (default 2%) in the dashboard sidebar. It is explicitly described as an assumption, not a live government yield.
- Updated Sharpe ratio to use daily excess returns over the 252-session equivalent risk-free rate.
- Added Sortino ratio using downside deviation below the daily risk-free target.
- Added benchmark comparison using common price dates before calculating returns.
- Added beta, annualized CAPM alpha, compounded excess period return, and common-observation count.
- Suppresses CAPM and excess-return comparisons when asset and benchmark quote currencies differ.
- Added a 21-session rolling annualized volatility series and dashboard chart.
- Added Sharpe and Sortino to portfolio backtest metrics and exports.
- Updated dashboard methodology, README, market report, and generated capstone deliverables.
- Added eight focused tests for risk-free rate behavior, Sortino, rolling volatility, beta, alpha, excess return, insufficient overlap, and zero benchmark variance.

## Verification

- `python -m py_compile Analysis1.py App1.py tests/Test_analysis1.py` — passed.
- `python -m unittest discover -s tests -v` — 22 tests passed.
- Tests use synthetic in-memory series and mocked HTTP responses; they do not fetch live market data.
- A live Streamlit browser smoke test remains unverified in this build environment.

## Interpretation limits

- Risk-free rate defaults to 2% and must be changed by the user when a different assumption is appropriate.
- Beta and alpha are historical estimates sensitive to the selected benchmark, period, missing dates, and data quality.
- Annualized CAPM alpha is an arithmetic daily-return intercept multiplied by 252, not a forecast.
- Rolling volatility is backward-looking; none of these metrics guarantees future performance.
- Cross-currency performance is not FX-adjusted.
