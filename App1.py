import base64
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

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

PROJECT_DIR = Path(__file__).resolve().parent
FAVICON_PATH = PROJECT_DIR / "assets" / "Favicon1.png"
LOGO_SVG_PATH = PROJECT_DIR / "assets" / "Favicon1.svg"
PRIVACY_POLICY_PATH = PROJECT_DIR / "Privacy_policy1.md"
TERMS_PATH = PROJECT_DIR / "Terms_and_conditions1.md"
LOOKBACK_DAYS = {"1 month": 31, "3 months": 93, "6 months": 186, "1 year": 366, "3 years": 1096, "5 years": 1827}


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_history(symbol: str, start_date: str, end_date: str):
    return fetch_market_history(symbol, date.fromisoformat(start_date), date.fromisoformat(end_date))


def build_market_summary(
    histories, metadata, benchmark_history=None, benchmark_metadata=None, risk_free_rate_annual=0.02
):
    rows = []
    benchmark_prices = (
        benchmark_history["adjusted_close"]
        if benchmark_history is not None else None
    )
    for symbol, history in histories.items():
        metrics = calculate_return_metrics(history["adjusted_close"], risk_free_rate_annual)
        benchmark_metrics = {}
        same_currency = (
            benchmark_metadata is None
            or metadata[symbol]["currency"] == benchmark_metadata.get("currency")
        )
        if benchmark_prices is not None and same_currency:
            try:
                benchmark_metrics = compare_to_benchmark(
                    history["adjusted_close"], benchmark_prices, risk_free_rate_annual
                )
            except ValueError:
                # Missing/insufficient overlap is reported as unavailable, not fabricated.
                benchmark_metrics = {}
        trend_window = min(50, len(history))
        trend_average = float(history["adjusted_close"].tail(trend_window).mean())
        rows.append(
            {
                "Ticker": symbol,
                "Name": metadata[symbol]["name"],
                "Exchange": metadata[symbol]["exchange"],
                "Currency": metadata[symbol]["currency"],
                "Price basis": metadata[symbol].get("price_basis", "unknown"),
                "Latest analysis price": metrics["latest_price"],
                "Period return (%)": metrics["period_return_pct"],
                "Annualized return (%)": metrics["annualized_return_pct"],
                "Annualized volatility (%)": metrics["annualized_volatility_pct"],
                "Sharpe ratio": metrics["sharpe_ratio"],
                "Sortino ratio": metrics["sortino_ratio"],
                "Beta vs benchmark": benchmark_metrics.get("beta", np.nan),
                "Alpha vs benchmark (annualized %)": benchmark_metrics.get("alpha_annualized_pct", np.nan),
                "Excess return vs benchmark (pp)": benchmark_metrics.get("excess_return_pct", np.nan),
                "Maximum drawdown (%)": metrics["max_drawdown_pct"],
                "Screen": get_market_screen(
                    metrics["annualized_return_pct"],
                    metrics["annualized_volatility_pct"],
                    metrics["latest_price"],
                    trend_average,
                ),
                "Latest date": history.index[-1].date().isoformat(),
            }
        )
    return pd.DataFrame(rows)


def build_report(summary, benchmark, lookback_label, start_date, end_date, risk_free_rate_annual):
    lines = [
        "Investment Recommendation System - Historical Market Analysis",
        "=" * 68,
        f"Data source: Yahoo Finance public chart endpoint (historical daily data)",
        f"Requested period: {lookback_label} ({start_date} through {end_date})",
        f"Generated: {date.today().isoformat()}",
        "",
        "Historical results describe the requested period; they do not predict future results.",
        "The technical screen is a transparent educational heuristic, not financial advice.",
        f"Annual effective risk-free-rate assumption: {risk_free_rate_annual * 100:.2f}% (user-configured; not a live yield).",
        "Adjusted closes are used where available; unadjusted fallbacks are disclosed per asset. Sharpe and Sortino use the configured annual effective risk-free rate and daily returns. Beta and alpha use common-date daily returns against the selected benchmark.",
        "",
        f"Benchmark: {benchmark or 'Not selected'}",
        "Benchmark-relative statistics are shown only when benchmark and asset currencies match and sufficient common dates exist.",
        "",
    ]
    for row in summary.to_dict("records"):
        lines.extend(
            [
                f"{row['Ticker']}: {row['Name']} ({row['Exchange']}, {row['Currency']})",
                f"  Latest analysis price: {row['Latest analysis price']:.4f} {row['Currency']}",
                f"  Latest available date: {row['Latest date']}",
                f"  Price basis: {row.get('Price basis', 'unknown')}",
                f"  Period return: {row['Period return (%)']:.2f}%",
                f"  Annualized return: {row['Annualized return (%)']:.2f}%",
                f"  Annualized volatility: {row['Annualized volatility (%)']:.2f}%",
                f"  Sharpe ratio: {row['Sharpe ratio']:.2f}",
                f"  Sortino ratio: {row['Sortino ratio']:.2f}",
                f"  Beta vs benchmark: {row['Beta vs benchmark']:.2f}" if pd.notna(row["Beta vs benchmark"]) else "  Beta vs benchmark: unavailable",
                f"  Alpha vs benchmark (annualized): {row['Alpha vs benchmark (annualized %)']:.2f}%" if pd.notna(row["Alpha vs benchmark (annualized %)"]) else "  Alpha vs benchmark (annualized): unavailable",
                f"  Excess return vs benchmark: {row['Excess return vs benchmark (pp)']:.2f} percentage points" if pd.notna(row["Excess return vs benchmark (pp)"]) else "  Excess return vs benchmark: unavailable",
                f"  Maximum drawdown: {row['Maximum drawdown (%)']:.2f}%",
                f"  Heuristic screen: {row['Screen']}",
                "",
            ]
        )
    return "\n".join(lines)


st.set_page_config(
    page_title="Investment Recommendation System | Historical Market Research",
    page_icon=str(FAVICON_PATH),
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "Historical market research for education. Results are not financial advice."
    },
)
st.html(
    """
    <script>
      (function () {
        const descriptionText =
          "Explore historical market performance, risk metrics, transparent screening rules, and portfolio backtests.";
        let descriptionTag = document.head.querySelector('meta[name="description"]');
        if (!descriptionTag) {
          descriptionTag = document.createElement("meta");
          descriptionTag.name = "description";
          document.head.appendChild(descriptionTag);
        }
        descriptionTag.content = descriptionText;
      })();
    </script>
    """,
    unsafe_allow_javascript=True,
)
logo_data = base64.b64encode(LOGO_SVG_PATH.read_bytes()).decode("ascii")
st.markdown(
    f"""
    <section class="hero-banner" aria-labelledby="app-home">
      <h1 id="app-home" class="brand-heading">
        <a class="brand-link" href="#app-home" aria-label="Investment Recommendation System home">
          <img src="data:image/svg+xml;base64,{logo_data}" alt="" width="42" height="42">
          <span>Investment Recommendation System</span>
        </a>
      </h1>
      <p class="hero-description">A clear workspace for historical performance, portfolio risk, and benchmark research.</p>
    </section>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
      :root {
        --irs-ink: #172B36;
        --irs-muted: #60727D;
        --irs-teal: #176B75;
        --irs-line: rgba(34, 55, 66, .12);
        --irs-panel: #F5F8F9;
      }
      .block-container { max-width: 1440px; padding-top: 1.6rem; padding-bottom: 3rem; }
      .hero-banner {
        margin: 0 0 1.35rem;
        padding: 1.65rem 1.8rem;
        background: linear-gradient(115deg, #F1F7F7 0%, #F7F8FA 58%, #EDF3F5 100%);
        border: 1px solid var(--irs-line);
        border-radius: 18px;
        box-shadow: 0 8px 26px rgba(28, 54, 65, .045);
        animation: hero-enter 300ms ease-out both;
      }
      .brand-heading { margin: 0; color: var(--irs-ink); font-size: clamp(1.65rem, 3.1vw, 2.45rem); line-height: 1.16; letter-spacing: -.035em; }
      .brand-link { display: inline-flex; align-items: center; gap: .8rem; color: inherit; text-decoration: none; }
      .brand-link:hover { color: inherit; text-decoration: none; }
      .hero-description { margin: .65rem 0 0 3.5rem; color: #526771; font-size: 1rem; }
      .app-footer { margin-top: 2.5rem; padding: 1.2rem 0 .5rem; border-top: 1px solid var(--irs-line); color: var(--irs-muted); font-size: .84rem; }
      [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid var(--irs-line);
        border-radius: 13px;
        padding: .9rem 1rem;
        box-shadow: 0 3px 12px rgba(28, 54, 65, .035);
      }
      [data-testid="stMetricLabel"] { color: var(--irs-muted); font-weight: 600; }
      [data-testid="stMetricValue"] { color: var(--irs-ink); letter-spacing: -.025em; }
      [data-testid="stTabs"] [role="tablist"] {
        gap: .35rem;
        border-bottom: 1px solid var(--irs-line);
      }
      [data-testid="stTabs"] button[role="tab"] {
        border-radius: 10px 10px 0 0;
        padding: .7rem 1rem;
        font-weight: 600;
      }
      [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
        border: 1px solid var(--irs-line);
        border-radius: 13px;
        overflow: hidden;
        background: #FFFFFF;
      }
      button[data-testid^="stBaseButton"] { border-radius: 10px !important; font-weight: 600; }
      input, [data-baseweb="select"] > div { border-radius: 9px !important; }
      div[data-testid="stForm"] {
        border: 1px solid var(--irs-line);
        border-radius: 15px;
        padding: 1.1rem 1.25rem 1.25rem;
        background: #FFFFFF;
      }
      @keyframes hero-enter {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @media (prefers-reduced-motion: reduce) {
        .hero-banner { animation: none; }
      }
      @media (max-width: 900px) {
        div[role="tablist"] { flex-wrap: wrap !important; overflow: visible !important; white-space: normal !important; gap: .2rem; }
        button[role="tab"] { flex: 1 1 30% !important; width: auto !important; min-width: 0 !important; white-space: normal !important; min-height: 2.7rem; }
      }
      @media (max-width: 760px) {
        .block-container { padding: 1rem .85rem 2rem; }
        .hero-banner { padding: 1.05rem 1rem; border-radius: 14px; }
        .brand-link { gap: .55rem; }
        .brand-link img { width: 34px; height: 34px; }
        .hero-description { margin-left: 2.6rem; font-size: .9rem; }
        .stHorizontalBlock { flex-wrap: wrap !important; gap: .65rem; }
        .stHorizontalBlock > div[data-testid="column"] { flex: 1 1 calc(50% - .65rem) !important; min-width: min(46%, 10rem) !important; }
        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"], [data-testid="stTable"] { max-width: 100%; }
        [data-testid="stMetric"] { padding: .7rem .75rem; }
      }
      @media (max-width: 420px) {
        .stHorizontalBlock > div[data-testid="column"] { flex-basis: 100% !important; min-width: 100% !important; }
        button[role="tab"] { flex-basis: 100% !important; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Research settings")
    st.caption("Yahoo Finance historical data. Quotes may be delayed; availability and coverage depend on the provider.")
    st.info("Ticker examples: AAPL, MSFT, INFY.NS, TCS.NS, HDFCBANK.NS, ^NSEI")
    st.caption("Research workspace · Historical data only · No trading or brokerage connection.")
    risk_free_rate_pct = st.number_input(
        "Annual risk-free rate (%)",
        min_value=-99.0,
        max_value=100.0,
        value=2.0,
        step=0.25,
        help="Annual effective rate used for Sharpe, Sortino, and CAPM alpha. This is an assumption, not a live Treasury or government-bond yield.",
    )
risk_free_rate_annual = risk_free_rate_pct / 100.0

with st.form("market_data_form"):
    st.subheader("Choose your research universe")
    input_col, benchmark_col, period_col = st.columns([3, 1, 1])
    tickers_input = input_col.text_input(
        "Tickers (comma-separated, up to 8)",
        value="AAPL, MSFT, GOOGL, NVDA",
        help="Use Yahoo Finance ticker format. Add .NS for NSE-listed symbols, for example INFY.NS.",
    )
    benchmark_input = benchmark_col.text_input(
        "Benchmark (optional)",
        value="^GSPC",
        help="Examples: ^GSPC (S&P 500), ^NSEI (Nifty 50), SPY.",
    )
    lookback_label = period_col.selectbox("History", list(LOOKBACK_DAYS), index=3)
    fetch_submitted = st.form_submit_button("Fetch market history", type="primary")

if fetch_submitted:
    for key in (
        "market_histories",
        "market_metadata",
        "market_errors",
        "market_assets",
        "market_benchmark",
        "market_period",
        "market_start_date",
        "market_end_date",
        "market_success",
    ):
        st.session_state.pop(key, None)
    try:
        requested_symbols = parse_tickers(tickers_input)
        benchmark_symbols = parse_tickers(benchmark_input, max_tickers=1) if benchmark_input.strip() else []
        if benchmark_symbols and benchmark_symbols[0] in requested_symbols:
            raise ValueError("Choose a benchmark that is different from the assets being analyzed.")
    except ValueError as error:
        st.error(str(error))
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=LOOKBACK_DAYS[lookback_label])
        symbols_to_fetch = requested_symbols + benchmark_symbols
        fetched_histories = {}
        fetched_metadata = {}
        fetch_errors = {}
        progress = st.progress(0, text="Requesting daily history...")
        for index, symbol in enumerate(symbols_to_fetch, start=1):
            try:
                history, asset_metadata = get_cached_history(
                    symbol, start_date.isoformat(), end_date.isoformat()
                )
                fetched_histories[symbol] = history
                fetched_metadata[symbol] = asset_metadata
            except MarketDataError as error:
                fetch_errors[symbol] = str(error)
            progress.progress(index / len(symbols_to_fetch), text=f"Retrieved {symbol} ({index}/{len(symbols_to_fetch)})")
        progress.empty()

        st.session_state["market_histories"] = fetched_histories
        st.session_state["market_metadata"] = fetched_metadata
        st.session_state["market_errors"] = fetch_errors
        st.session_state["market_assets"] = requested_symbols
        st.session_state["market_benchmark"] = benchmark_symbols[0] if benchmark_symbols else ""
        st.session_state["market_period"] = lookback_label
        st.session_state["market_start_date"] = start_date.isoformat()
        st.session_state["market_end_date"] = end_date.isoformat()
        loaded_asset_count = sum(symbol in fetched_histories for symbol in requested_symbols)
        if loaded_asset_count:
            st.session_state["market_success"] = (
                f"Loaded market history for {loaded_asset_count} of "
                f"{len(requested_symbols)} requested asset(s)."
            )
        else:
            st.session_state["market_success"] = ""

histories = st.session_state.get("market_histories", {})
metadata = st.session_state.get("market_metadata", {})
fetch_errors = st.session_state.get("market_errors", {})
asset_symbols = [
    symbol for symbol in st.session_state.get("market_assets", []) if symbol in histories
]
benchmark = st.session_state.get("market_benchmark", "")
lookback_label = st.session_state.get("market_period", lookback_label)
start_date_text = st.session_state.get("market_start_date", "")
end_date_text = st.session_state.get("market_end_date", "")

for symbol, message in fetch_errors.items():
    st.error(f"{symbol}: {message}")

if st.session_state.get("market_success"):
    st.success(st.session_state["market_success"])
elif fetch_errors and not asset_symbols:
    st.error("No requested asset history could be loaded. Review the ticker errors above and try again.")

if not asset_symbols:
    st.info("Enter tickers and select **Fetch market history** to load historical market prices.")

live_tab, portfolio_tab, methodology_tab, privacy_tab, terms_tab = st.tabs(
    ["Market analysis", "Portfolio backtest", "Methodology", "Privacy policy", "Terms and conditions"]
)

summary = pd.DataFrame()
with live_tab:
    st.subheader("Historical asset comparison")
    if asset_symbols:
        asset_histories = {symbol: histories[symbol] for symbol in asset_symbols}
        asset_metadata = {symbol: metadata[symbol] for symbol in asset_symbols}
        benchmark_history = histories.get(benchmark) if benchmark else None
        summary = build_market_summary(
            asset_histories,
            asset_metadata,
            benchmark_history,
            metadata.get(benchmark) if benchmark else None,
            risk_free_rate_annual,
        )
        currency_list = sorted(summary["Currency"].unique().tolist())
        if len(currency_list) > 1:
            st.warning(
                "Selected assets use different currencies. Returns are shown in each asset's local currency; "
                "no foreign-exchange conversion is applied."
            )
        unadjusted_symbols = [
            symbol for symbol in asset_symbols
            if metadata[symbol].get("price_basis") == "unadjusted_fallback"
        ]
        if unadjusted_symbols:
            st.warning(
                "Yahoo Finance did not provide adjusted-close values for "
                f"{', '.join(unadjusted_symbols)}. Their analysis uses unadjusted close prices, "
                "so dividend and split adjustments may be missing."
            )
        cleaned_symbols = [
            symbol for symbol in asset_symbols
            if int(metadata[symbol].get("duplicate_dates_removed", "0")) > 0
            or int(metadata[symbol].get("invalid_price_rows_removed", "0")) > 0
        ]
        if cleaned_symbols:
            st.info(
                "Duplicate dates or invalid price rows were removed during data validation for: "
                f"{', '.join(cleaned_symbols)}."
            )
        st.markdown("#### Market snapshot")
        overview_cols = st.columns(4)
        strongest_row = summary.loc[summary["Period return (%)"].idxmax()]
        overview_cols[0].metric("Assets loaded", f"{len(summary)}")
        overview_cols[1].metric(
            "Highest period return",
            f"{strongest_row['Period return (%)']:+.2f}%",
            str(strongest_row["Ticker"]),
            help="Highest historical return in this selected group and period; not a forward-looking recommendation.",
        )
        overview_cols[2].metric(
            "Median volatility",
            f"{summary['Annualized volatility (%)'].median():.2f}%",
            help="Median annualized historical volatility across the selected assets.",
        )
        overview_cols[3].metric(
            "Median max drawdown",
            f"{summary['Maximum drawdown (%)'].median():.2f}%",
            help="Median peak-to-trough historical drawdown across the selected assets.",
        )
        st.caption(
            f"Period: {start_date_text} to {end_date_text} · Benchmark: {benchmark or 'not selected'} · "
            f"Risk-free assumption: {risk_free_rate_pct:.2f}% annually"
        )
        st.markdown("#### Compare assets")
        st.caption(
            "All figures describe the selected historical window. Returns remain in each asset's quote currency; "
            "the snapshot is descriptive and does not rank future investment potential."
        )
        st.dataframe(
            summary.style.format(
                {
                    "Latest analysis price": "{:,.2f}",
                    "Period return (%)": "{:+.2f}",
                    "Annualized return (%)": "{:+.2f}",
                    "Annualized volatility (%)": "{:.2f}",
                    "Sharpe ratio": "{:.2f}",
                    "Sortino ratio": "{:.2f}",
                    "Beta vs benchmark": "{:.2f}",
                    "Alpha vs benchmark (annualized %)": "{:+.2f}",
                    "Excess return vs benchmark (pp)": "{:+.2f}",
                    "Maximum drawdown (%)": "{:.2f}",
                }
            ),
            width="stretch",
            hide_index=True,
        )

        st.markdown("#### Relative performance")
        st.caption("Each series is rebased to 100 at its first available observation. This compares percentage movement, not absolute prices.")
        chart_symbols = asset_symbols.copy()
        if benchmark and benchmark in histories:
            chart_symbols.append(benchmark)
        normalized_series = []
        for symbol in chart_symbols:
            closes = histories[symbol]["adjusted_close"].dropna()
            normalized = closes / closes.iloc[0] * 100
            normalized_series.append(normalized.rename(symbol))
        indexed_performance = pd.concat(normalized_series, axis=1)
        performance_figure = px.line(
            indexed_performance,
            title="Indexed price performance",
            labels={"value": "Indexed value", "index": "Date", "variable": "Ticker"},
            template="plotly_white",
        )
        performance_figure.update_layout(
            hovermode="x unified",
            margin=dict(l=20, r=20, t=65, b=20),
            legend_title_text="",
            yaxis_title="Indexed value (start = 100)",
        )
        st.plotly_chart(performance_figure, width="stretch")
        st.caption("The first available close for each series is rebased to 100; start dates can differ by symbol.")

        st.markdown("#### Asset deep dive")
        selected_symbol = st.selectbox("Choose an asset to inspect", asset_symbols)
        selected_history = histories[selected_symbol]
        selected_close = selected_history["adjusted_close"].dropna()
        selected_window = min(50, len(selected_close))
        moving_average = selected_close.rolling(selected_window, min_periods=selected_window).mean()
        asset_figure = px.line(
            pd.DataFrame(
                {
                    "Analysis price": selected_close,
                    f"{selected_window}-session moving average": moving_average,
                }
            ),
            title=f"{metadata[selected_symbol]['name']}: daily analysis price",
            template="plotly_white",
        )
        asset_figure.update_layout(
            yaxis_title=f"Analysis price ({metadata[selected_symbol]['currency']})",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=65, b=20),
            legend_title_text="",
        )
        st.plotly_chart(asset_figure, width="stretch")
        selected_metrics = calculate_return_metrics(selected_close, risk_free_rate_annual)
        deep_dive_cols = st.columns(4)
        deep_dive_cols[0].metric("Period return", f"{selected_metrics['period_return_pct']:+.2f}%")
        deep_dive_cols[1].metric("Sharpe ratio", f"{selected_metrics['sharpe_ratio']:.2f}")
        deep_dive_cols[2].metric("Sortino ratio", f"{selected_metrics['sortino_ratio']:.2f}")
        deep_dive_cols[3].metric("Max drawdown", f"{selected_metrics['max_drawdown_pct']:.2f}%")
        st.caption(
            "The moving average uses up to 50 available trading sessions. These metrics and the historical screen "
            "describe past data and do not forecast future performance."
        )
        rolling_volatility = calculate_rolling_volatility(selected_close, window=21)
        volatility_figure = px.line(
            rolling_volatility.to_frame(),
            title="21-session rolling annualized volatility",
            labels={"value": "Annualized volatility (%)", "index": "Date"},
            template="plotly_white",
        )
        volatility_figure.update_layout(
            hovermode="x unified",
            margin=dict(l=20, r=20, t=65, b=20),
            showlegend=False,
        )
        st.plotly_chart(volatility_figure, width="stretch")
        st.caption(
            "Rolling volatility is based on the previous 21 daily returns and annualized with √252. "
            "The first 21-session window is blank because a full window is not yet available."
        )

        report = build_report(
            summary,
            benchmark if benchmark in histories else "",
            st.session_state.get("market_period", ""),
            start_date_text,
            end_date_text,
            risk_free_rate_annual,
        )
        st.download_button(
            "Download market analysis report",
            report,
            file_name="historical_market_analysis.txt",
            mime="text/plain",
        )
        export_frames = []
        for symbol in chart_symbols:
            frame = histories[symbol][["adjusted_close"]].rename(
                columns={"adjusted_close": symbol}
            )
            export_frames.append(frame)
        price_export = pd.concat(export_frames, axis=1)
        st.download_button(
            "Download price history (CSV)",
            price_export.to_csv(index_label="date").encode("utf-8"),
            file_name="adjusted_price_history.csv",
            mime="text/csv",
        )
    else:
        st.caption("The live analysis appears here after a successful history fetch.")

with portfolio_tab:
    st.subheader("Portfolio backtest")
    st.caption("Explore how a fixed starting allocation would have behaved over the selected historical window.")
    if not asset_symbols:
        st.info("Fetch market history first to enable the backtest.")
    else:
        selected_portfolio = st.multiselect(
            "Select assets for the portfolio",
            asset_symbols,
            default=asset_symbols[: min(3, len(asset_symbols))],
            max_selections=8,
        )
        if not selected_portfolio:
            st.info("Select at least one asset.")
        else:
            selected_currencies = {
                metadata[symbol]["currency"] for symbol in selected_portfolio
            }
            if len(selected_currencies) != 1 or "Unknown" in selected_currencies:
                st.error(
                    "Choose assets quoted in the same known currency. The backtest does not convert foreign exchange."
                )
            else:
                currency = next(iter(selected_currencies))
                initial_investment = st.number_input(
                    f"Starting investment ({currency})",
                    min_value=1.0,
                    value=10000.0,
                    step=1000.0,
                )
                allocation_columns = st.columns(min(len(selected_portfolio), 4))
                allocations = {}
                for index, symbol in enumerate(selected_portfolio):
                    with allocation_columns[index % len(allocation_columns)]:
                        allocations[symbol] = st.number_input(
                            f"{symbol} allocation (%)",
                            min_value=0,
                            max_value=100,
                            value=max(1, 100 // len(selected_portfolio)),
                            key=f"backtest_weight_{symbol}",
                        )
                if sum(allocations.values()) == 0:
                    st.error("Give at least one asset a positive allocation.")
                else:
                    selected_prices = pd.concat(
                        {
                            symbol: histories[symbol]["adjusted_close"]
                            for symbol in selected_portfolio
                        },
                        axis=1,
                    )
                    try:
                        portfolio_value, portfolio_metrics, normalized_weights = backtest_buy_and_hold(
                            selected_prices, allocations, initial_investment, risk_free_rate_annual
                        )
                    except ValueError as error:
                        st.error(str(error))
                    else:
                        total_allocation = sum(allocations.values())
                        st.caption(
                            f"Entered allocations total {total_allocation}%; weights are normalized to 100%. "
                            "This is an adjusted-price total-return simulation where adjusted data is available: provider corporate-action "
                            "adjustments are reflected, and the portfolio is not periodically rebalanced."
                        )
                        st.success("Portfolio analysis is ready. You can download the values or summary below.")
                        metric_columns = st.columns(6)
                        metric_columns[0].metric(
                            "Ending value",
                            f"{currency} {portfolio_value.iloc[-1]:,.2f}",
                            f"{portfolio_metrics['period_return_pct']:+.2f}%",
                        )
                        metric_columns[1].metric(
                            "Annualized return",
                            f"{portfolio_metrics['annualized_return_pct']:+.2f}%",
                        )
                        metric_columns[2].metric(
                            "Annualized volatility",
                            f"{portfolio_metrics['annualized_volatility_pct']:.2f}%",
                        )
                        metric_columns[3].metric(
                            "Maximum drawdown",
                            f"{portfolio_metrics['max_drawdown_pct']:.2f}%",
                        )
                        metric_columns[4].metric("Sharpe ratio", f"{portfolio_metrics['sharpe_ratio']:.2f}")
                        metric_columns[5].metric("Sortino ratio", f"{portfolio_metrics['sortino_ratio']:.2f}")

                        portfolio_index = portfolio_value / initial_investment * 100
                        backtest_chart = pd.DataFrame(
                            {"Portfolio index (start = 100)": portfolio_index}
                        )
                        if benchmark and benchmark in histories:
                            benchmark_currency = metadata[benchmark]["currency"]
                            if benchmark_currency != currency:
                                st.warning(
                                    f"Benchmark {benchmark} is in {benchmark_currency}, while the portfolio is in "
                                    f"{currency}. The indexed chart compares percentage movements only and does not convert currencies."
                                )
                            benchmark_prices = histories[benchmark]["adjusted_close"].dropna()
                            benchmark_index = benchmark_prices / benchmark_prices.iloc[0] * 100
                            backtest_chart[benchmark] = benchmark_index.reindex(backtest_chart.index)
                            if benchmark_currency != currency:
                                st.info("Benchmark beta, alpha, and excess return are not calculated across different currencies. Convert both series to one currency first.")
                            else:
                                try:
                                    portfolio_benchmark = compare_to_benchmark(
                                        portfolio_value, benchmark_prices, risk_free_rate_annual
                                    )
                                except ValueError as error:
                                    st.info(f"Benchmark risk comparison unavailable: {error}")
                                else:
                                    st.markdown("**Portfolio vs benchmark (shared dates and currency)**")
                                    benchmark_cols = st.columns(4)
                                    benchmark_cols[0].metric("Beta", f"{portfolio_benchmark['beta']:.2f}")
                                    benchmark_cols[1].metric("CAPM alpha (annualized)", f"{portfolio_benchmark['alpha_annualized_pct']:+.2f}%")
                                    benchmark_cols[2].metric("Excess period return", f"{portfolio_benchmark['excess_return_pct']:+.2f} pp")
                                    benchmark_cols[3].metric("Shared return observations", f"{portfolio_benchmark['observations']:,}")
                        figure = px.line(
                            backtest_chart,
                            title="Backtest value indexed to 100",
                            labels={"value": "Indexed value", "index": "Date", "variable": "Series"},
                            template="plotly_white",
                        )
                        st.plotly_chart(figure, width="stretch")
                        st.markdown("#### Portfolio allocation")
                        allocation_frame = pd.DataFrame(
                            [
                                {
                                    "Ticker": symbol,
                                    "Weight (%)": weight * 100,
                                }
                                for symbol, weight in normalized_weights.items()
                            ]
                        )
                        allocation_figure = px.bar(
                            allocation_frame.sort_values("Weight (%)", ascending=True),
                            x="Weight (%)",
                            y="Ticker",
                            orientation="h",
                            title="Normalized starting weights",
                            text=allocation_frame.sort_values("Weight (%)", ascending=True)["Weight (%)"].map(lambda value: f"{value:.1f}%"),
                            template="plotly_white",
                        )
                        allocation_figure.update_layout(
                            showlegend=False,
                            margin=dict(l=20, r=20, t=60, b=20),
                            xaxis_title="Allocation (%)",
                            yaxis_title="",
                        )
                        st.plotly_chart(allocation_figure, width="stretch")
                        st.dataframe(
                            pd.DataFrame(
                                [
                                    {
                                        "Ticker": symbol,
                                        "Normalized allocation (%)": weight * 100,
                                        "Currency": currency,
                                    }
                                    for symbol, weight in normalized_weights.items()
                                ]
                            ).style.format({"Normalized allocation (%)": "{:.2f}"}),
                            width="stretch",
                            hide_index=True,
                        )
                        portfolio_report_lines = [
                            "Investment Recommendation System - Portfolio Backtest Summary",
                            "=" * 64,
                            f"Period: {portfolio_value.index[0].date()} through {portfolio_value.index[-1].date()}",
                            f"Currency: {currency}",
                            f"Starting investment: {currency} {initial_investment:,.2f}",
                            f"Ending value: {currency} {portfolio_value.iloc[-1]:,.2f}",
                            f"Period return: {portfolio_metrics['period_return_pct']:+.2f}%",
                            f"Annualized return: {portfolio_metrics['annualized_return_pct']:+.2f}%",
                            f"Annualized volatility: {portfolio_metrics['annualized_volatility_pct']:.2f}%",
                            f"Sharpe ratio: {portfolio_metrics['sharpe_ratio']:.2f}",
                            f"Sortino ratio: {portfolio_metrics['sortino_ratio']:.2f}",
                            f"Maximum drawdown: {portfolio_metrics['max_drawdown_pct']:.2f}%",
                            f"Assumed annual risk-free rate: {risk_free_rate_pct:.2f}%",
                            "",
                            "Normalized allocations:",
                        ]
                        portfolio_report_lines.extend(
                            f"  {symbol}: {weight * 100:.2f}%"
                            for symbol, weight in normalized_weights.items()
                        )
                        portfolio_report_lines.extend(
                            [
                                "",
                                "Method: adjusted-price buy-and-hold total-return proxy without periodic rebalancing.",
                                "This is not a ledger of actual tradable shares. Fees, taxes, and FX are excluded.",
                                "Historical results do not predict future performance; this is not financial advice.",
                            ]
                        )
                        download_columns = st.columns(2)
                        download_columns[0].download_button(
                            "Download backtest values (CSV)",
                            portfolio_value.to_frame().to_csv(index_label="date").encode("utf-8"),
                            file_name="portfolio_backtest.csv",
                            mime="text/csv",
                        )
                        download_columns[1].download_button(
                            "Download portfolio summary (TXT)",
                            "\n".join(portfolio_report_lines),
                            file_name="portfolio_backtest_summary.txt",
                            mime="text/plain",
                        )

with methodology_tab:
    st.subheader("Methodology and data quality")
    st.markdown(
        """
        **Market data:** Daily price history is requested from Yahoo Finance's public chart endpoint when you submit the ticker form.
        The provider is unofficial, may delay, change, rate-limit, or block requests, and may not return every symbol or date.
        Results are cached in memory by the running app for 15 minutes. A failed symbol is reported; no synthetic prices are
        substituted when a provider request fails.

        **Ticker format:** US examples include `AAPL`, `MSFT`, and `^GSPC`. NSE listings use Yahoo suffixes such as `INFY.NS`,
        `TCS.NS`, `HDFCBANK.NS`, and `^NSEI`.

        **Performance measures:** Provider adjusted closes are used when available and include provider adjustments for
        distributions/splits. If adjusted closes are missing, the dashboard explicitly labels the affected asset as using
        unadjusted close prices. Period return is the first-to-last analysis-price change. Annualized return is compounded
        over the observed calendar period. Annualized volatility uses daily return standard deviation multiplied by √252.
        Sharpe and Sortino ratios use the annual effective risk-free-rate assumption configured in the sidebar, converted to a 252-session daily rate. Sharpe divides mean daily excess return by the sample standard deviation of daily excess returns and annualizes by √252. Sortino divides mean daily excess return by the root-mean-square downside deviation below the daily risk-free target and annualizes by √252. Maximum drawdown is measured against the running analysis-price peak.

        **Benchmark-relative measures:** Beta is covariance of aligned daily asset and benchmark returns divided by benchmark return variance. CAPM alpha is the annualized arithmetic intercept from those same aligned daily returns after subtracting the configured daily risk-free rate. Excess return is the difference between compounded asset and benchmark returns over their common daily-return window. At least three shared daily return observations and non-zero benchmark variance are required. Results are unavailable rather than inferred when overlap is insufficient. Rolling volatility uses the trailing 21 daily returns and √252 annualization.

        **Buy / Hold / Sell screen:** Buy when annualized historical return is at least 8%, annualized volatility is at most 45%,
        and the latest analysis price is at or above its available trailing 50-session average. Sell when annualized historical
        return is negative and price is below that average. All other cases are Hold. These fixed historical-momentum rules are
        simple educational heuristics, not forecasts or personalized advice.

        **Portfolio backtest:** Uses normalized starting allocations to simulate a buy-and-hold total-return portfolio from
        provider adjusted closes where available (otherwise the explicitly disclosed unadjusted fallback) over the first
        shared history window. Provider adjustments reflect splits and distributions where available; this is not a ledger of
        tradeable shares. It requires assets quoted in one currency and does not
        periodically rebalance. It excludes fees, taxes, slippage beyond provider adjustments, currency conversion, and cash flows.
        Benchmark performance is indexed by percentage return; cross-currency index charts do not convert currencies. Benchmark beta, alpha, and excess-return comparisons are suppressed when quote currencies differ.

        Historical performance does not guarantee future results. This application does not execute trades or connect to a broker.
        """
    )

with privacy_tab:
    st.markdown(PRIVACY_POLICY_PATH.read_text(encoding="utf-8"))

with terms_tab:
    st.markdown(TERMS_PATH.read_text(encoding="utf-8"))

st.markdown(
    f'<footer class="app-footer">Copyright {date.today().year} Investment Recommendation System. Educational research only; not financial advice. Privacy and terms are available in the tabs above.</footer>',
    unsafe_allow_html=True,
)
