# Investment Recommendation System

A local research dashboard for analyzing historical market data retrieved from Yahoo Finance. It compares tickers, calculates historical risk and return measures, applies a transparent screen, and simulates same-currency portfolios. No synthetic price history or pre-filled market metrics are included.

**Public demo:** [Open the dashboard](https://investment-recomendation-system-v11.streamlit.app/). It is a read-only educational demo and does not execute trades.

> Historical performance is not a forecast or personalized investment advice. The app does not execute trades.

## Run locally

Use Python 3.10 or later. Open a terminal in this folder:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run App1.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.
The app is configured to bind to `127.0.0.1` and is intended for this computer only. Do not expose it on a LAN, through port forwarding, or through a tunnel.

On Windows, double-click [`Run_dashboard1.bat`](Run_dashboard1.bat). Keep its console open while using the app. Closing it stops the local server.

## Use the dashboard

1. Enter up to eight Yahoo Finance ticker symbols, such as `AAPL`, `MSFT`, `INFY.NS`, or `TCS.NS`.
2. Optionally enter a benchmark such as `^GSPC`, `^NSEI`, or `SPY`.
3. Choose a history period, then select **Fetch market history**.
4. Review the market snapshot for the loaded universe, then compare adjusted-price returns, volatility, Sharpe and Sortino ratios, drawdown, and the historical screen.
5. Set the annual risk-free-rate assumption in the sidebar to adjust risk-adjusted metrics.
6. If a benchmark is selected and there are enough common dates in the same currency, review beta, CAPM alpha, and excess return.
7. Inspect an asset's deep-dive metrics, price history, and 21-session rolling annualized volatility chart.
8. In **Portfolio backtest**, select assets quoted in one currency, set allocations, and review the simulation and allocation chart.
9. Download the market report, adjusted-price CSV, portfolio backtest CSV, or portfolio summary TXT.

Successful requests are cached in memory for 15 minutes. A failed symbol is reported; synthetic data is not substituted. The provider is unofficial and may delay, change, rate-limit, or block requests.

The interface uses a cool-neutral design system with an off-white canvas, white elevated cards, slate typography, and a teal accent. Responsive spacing, clear metric and chart surfaces, visible focus states, and subtle transitions keep the dashboard readable across screen sizes. The sidebar starts collapsed; use its menu button to open research settings and the risk-free-rate assumption. The app has a browser title, description, custom favicon, clickable brand header, and dynamically dated footer. Streamlit usage statistics are disabled in the local project configuration.

## Privacy and terms

The **Privacy policy** and **Terms and conditions** tabs display [Privacy_policy1.md](Privacy_policy1.md) and [Terms_and_conditions1.md](Terms_and_conditions1.md). These are plain-language project notices, not legal advice. They require review before any public release.

## Calculations and limitations

- Adjusted closes are used when supplied by the provider.
- Annualized return compounds the first-to-last price change over the observed calendar period.
- Annualized volatility uses daily return sample standard deviation multiplied by the square root of 252.
- Sharpe and Sortino ratios use a user-configurable annual effective risk-free-rate assumption (default 2%), converted to a 252-session daily rate. This is not a live yield.
- Beta and CAPM alpha use aligned daily returns against the selected benchmark; at least three shared return observations and non-zero benchmark variance are required. Cross-currency CAPM comparisons are suppressed.
- Rolling volatility uses a trailing 21-return sample standard deviation annualized by the square root of 252.
- Maximum drawdown is measured against the running adjusted-price high.
- Buy/Hold/Sell labels use the documented historical-momentum thresholds. They do not predict future results.
- Portfolio weights are normalized across the selected assets. The backtest is a total-return proxy without periodic rebalancing, fees, taxes, or FX conversion.

## Verify and regenerate

```powershell
python -m unittest discover -s tests -v
python -m compileall App1.py Analysis1.py Generate_deliverables1.py tests
python Generate_deliverables1.py
```

## Project files

- `App1.py` - Streamlit application
- `Analysis1.py` - market data client, validation, analytics, and backtest
- `.streamlit/config.toml` - active Streamlit theme, telemetry, and local server settings
- `assets/Favicon1.svg` and `assets/Favicon1.png` - custom browser icon
- `Privacy_policy1.md` and `Terms_and_conditions1.md` - policy pages displayed in the app
- `tests/Test_analysis1.py` - offline tests; no network calls required
- `PHASE1_CHANGELOG1.md`, `PHASE2_CHANGELOG1.md`, and `PHASE3_CHANGELOG1.md` - implementation notes
- `Project_report1.md` and `Project_report1.pdf` - capstone report
- `Presentation_outline1.md` and `Presentation1.pptx` - presentation deliverables
- `Deployment1.md` - Phase 5 deployment and release guide
- `Dockerfile1`, `Docker-compose1.yml`, `.Dockerignore1` - hardened container package
- `Run_dashboard1.bat` - Windows launcher

The public demo is hosted on Streamlit Community Cloud and has no authentication; do not enter personal or confidential information. It is for educational demonstration only, not a production financial service. Phase 5 also includes a hardened Docker/Compose package for local or authenticated private use. Review `Deployment1.md` before changing the access model.

## Phase 4 security and quality checks

Phase 4 adds stricter validation for ticker input, network retry settings, portfolio allocations, and starting capital, plus regression tests and GitHub Actions quality/security checks. See `PHASE4_SECURITY1.md` for the implemented controls, limitations, and local commands. The CI workflow runs unit tests, Python compilation, `pip-audit`, and Bandit.

## Phase 5 deployment package

Phase 5 adds a non-root Docker image, a loopback-only Docker Compose service, container health checks, a reduced-privilege/read-only runtime, deployment guidance for private authenticated access, and deployment-configuration regression tests. The educational demo is publicly available at [investment-recomendation-system-v11.streamlit.app](https://investment-recomendation-system-v11.streamlit.app/). Build the local Docker package with `docker compose up --build -d`; see `Deployment1.md`.
