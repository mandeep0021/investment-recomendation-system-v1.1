# Phase 1 — Data and calculation correctness

## Implemented

- Added bounded exponential-backoff retries for temporary Yahoo Finance request/HTTP/JSON failures.
- Added defensive validation for the chart response, quote arrays, timestamps, time zones, and price/volume array lengths.
- Made missing adjusted-close handling explicit: close prices are used only as a labelled `unadjusted_fallback`, and the dashboard warns that dividend/split adjustments may be missing.
- Detects invalid price rows and duplicate dates, removes them, and sorts the resulting history chronologically.
- Excludes the current day's still-forming daily candle when Yahoo supplies a regular-session end time and the session has not ended.
- Requires datetime-indexed daily price series for performance calculations and sorts/deduplicates them before computing returns.
- Sorts/deduplicates portfolio price dates before aligning assets for a backtest.
- Updated dashboard labels, exported report wording, and methodology text to avoid claiming all prices are adjusted when a fallback is used.
- Added automated tests for retries, malformed responses, unadjusted fallback disclosure, duplicate/out-of-order dates, incomplete current sessions, and sorted calculations.

## Verification

- `python -m unittest discover -s tests -v` — 14 tests passed.
- `python -m py_compile Analysis1.py App1.py` — passed.
- Streamlit server smoke test could not be run in this build environment because the `streamlit` executable is not installed. Install the project's requirements before launching the dashboard.

## Important limitations

- This phase improves data handling; it does not validate whether the Buy/Hold/Sell heuristic predicts future returns.
- Yahoo Finance remains an unofficial data source and can change, delay, rate-limit, or omit data.
- When only unadjusted close is available, returns and risk statistics will not include missing dividend/split adjustments; the dashboard now discloses that basis.
