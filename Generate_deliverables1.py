"""Generate the capstone PDF report and PowerPoint presentation."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
NAVY = RGBColor(20, 42, 74)
TEAL = RGBColor(0, 130, 140)
PALE = RGBColor(235, 243, 247)
INK = RGBColor(36, 48, 61)


SLIDES = [
    (
        "Project overview",
        [
            "Historical market research dashboard for user-selected public-market tickers.",
            "Compares performance, volatility, Sharpe and Sortino ratios, beta, CAPM alpha, and maximum drawdown.",
            "Includes a same-currency buy-and-hold total-return simulation.",
            "Built with Python, Streamlit, Pandas, NumPy, Plotly, and Requests.",
        ],
    ),
    (
        "Objectives and scope",
        [
            "Retrieve daily adjusted-price history by ticker and date range.",
            "Compare assets to an optional market benchmark.",
            "Calculate return and risk metrics using documented assumptions.",
            "Explore adjusted-price portfolios without periodic rebalancing or trade execution.",
        ],
    ),
    (
        "Data source and reliability",
        [
            "Daily history comes from Yahoo Finance's public chart endpoint.",
            "Ticker examples: AAPL, MSFT, INFY.NS, TCS.NS, ^GSPC, ^NSEI.",
            "Responses are cached locally for 15 minutes; failed data is shown as an error.",
            "The endpoint may delay, change, rate-limit, or block requests.",
        ],
    ),
    (
        "System workflow",
        [
            "Ticker form -> provider request -> validation -> descriptive analytics.",
            "Asset comparison and benchmark chart -> CSV and text downloads.",
            "Portfolio weights -> shared-date buy-and-hold backtest -> CSV export.",
            "Privacy and terms information is available in dedicated tabs.",
        ],
    ),
    (
        "Historical performance measures",
        [
            "Period return: first-to-last adjusted-price change.",
            "Annualized return compounds the observed change over calendar time.",
            "Annualized volatility uses daily sample standard deviation x sqrt(252).",
            "Sharpe and Sortino use the configurable annual risk-free-rate assumption (default 2%).",
            "Beta, CAPM alpha, excess return, and 21-session rolling volatility are available.",
            "Drawdown uses the running peak.",
        ],
    ),
    (
        "Historical-momentum screen",
        [
            "BUY: annualized historical return >= 8%, volatility <= 45%, and price >= trailing average.",
            "SELL: annualized historical return < 0% and price < trailing average.",
            "HOLD: all other outcomes.",
            "This fixed heuristic is descriptive and educational, not a prediction or advice.",
        ],
    ),
    (
        "Portfolio backtest",
        [
            "Normalize initial allocations across adjusted-price series on the first shared trading date.",
            "Follow a buy-and-hold total-return proxy without periodic rebalancing.",
            "Require overlapping prices and a single quote currency.",
            "Provider distribution/split adjustments are included where available; this is not a share ledger.",
            "No FX conversion, fees, taxes, or cash flows are modeled.",
        ],
    ),
    (
        "Dashboard and exports",
        [
            "Live market analysis: summary table, indexed price comparison, selected-asset chart.",
            "Portfolio backtest: capital, asset selection, and allocation controls.",
            "Download adjusted-price history, backtest values, market report, and portfolio summary.",
            "Methodology, privacy, and terms are available in dedicated tabs.",
            "Responsive tabs and input columns support narrow mobile screens.",
        ],
    ),
    (
        "Testing and validation",
        [
            "Mocked API tests validate successful parsing and provider errors without internet.",
            "Ticker parsing and historical performance formulas are tested.",
            "Backtest arithmetic, normalization, and invalid input are covered.",
            "Run: python -m unittest discover -s tests -v",
        ],
    ),
    (
        "Limitations and responsible use",
        [
            "Public provider data can be delayed, incomplete, revised, or unavailable.",
            "Annualized results from short periods can be noisy.",
            "No fees, taxes, suitability, FX conversion, or future returns are modeled.",
            "Historical performance does not guarantee future results; not financial advice.",
            "Public release waits for a connected custom domain and reviewed policies.",
        ],
    ),
    (
        "Conclusion and demo",
        [
            "The app displays provider-sourced history instead of pre-entered market examples.",
            "Run locally with: python -m streamlit run App1.py",
            "Choose a ticker, fetch data, review statistics, then run a portfolio backtest.",
        ],
    ),
]


def build_pdf() -> None:
    output = ROOT / "Project_report1.pdf"
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Investment Recommendation System - Capstone Report",
        author="Student Project",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ProjectTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=29,
            textColor=colors.HexColor("#142A4A"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#00828C"),
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(ParagraphStyle(name="SmallBody", parent=styles["BodyText"], leading=15, spaceAfter=6))

    story = [
        Spacer(1, 28 * mm),
        Paragraph("Investment Recommendation System", styles["ProjectTitle"]),
        Paragraph("Investment Banking with Finance Capstone Project", styles["Heading2"]),
        Spacer(1, 6 * mm),
        Paragraph(
            "<b>Project type:</b> Historical-market research dashboard<br/>"
            "<b>Technology:</b> Python, Streamlit, Pandas, NumPy, Plotly, Requests<br/>"
            "<b>Market data:</b> Yahoo Finance public chart endpoint<br/>"
            "<b>Market history:</b> Retrieved from the provider when requested",
            styles["BodyText"],
        ),
        Spacer(1, 12 * mm),
        Paragraph(
            "<b>Important:</b> Historical results do not predict future returns. "
            "The public provider may delay or limit data. Outputs are not financial advice.",
            styles["SmallBody"],
        ),
        PageBreak(),
    ]

    sections = [
        (
            "Abstract",
            "This project implements a local historical-market research dashboard. Users request public daily "
            "price history by ticker, compare assets and an optional benchmark, inspect return/risk statistics, "
            "and simulate a same-currency buy-and-hold portfolio. The app uses provider-sourced history only and "
            "does not substitute synthetic prices. The system is descriptive, not a forecast, trading system, or advice.",
        ),
        (
            "1. Objectives and Workflow",
            "The user enters ticker symbols and a history period in Streamlit. Analysis1.py requests daily prices "
            "from Yahoo Finance's public chart endpoint, validates and aligns the results, and calculates metrics. "
            "The app renders a comparison, indexed history charts, a portfolio backtest, market reports, a portfolio summary, and CSV downloads. "
            "Its responsive layout adapts navigation and input columns for narrow screens. "
            "A 15-minute cache avoids repeating successful requests during the session.",
        ),
        (
            "2. Data Source and Reliability",
            "The app accepts up to eight tickers, including US symbols such as AAPL and NSE symbols such as INFY.NS. "
            "Daily adjusted-close prices and provider metadata are used where available. Yahoo Finance's public "
            "endpoint is unofficial and may delay, change, rate-limit, or block requests. Failures are reported "
            "directly; the app does not substitute synthetic values for missing market history.",
        ),
        (
            "3. Performance Measures",
            "Period return is the first-to-last adjusted-price change. Annualized return compounds that change "
            "over the observed calendar period. Annualized volatility is the sample standard deviation of daily "
            "returns multiplied by the square root of 252. Sharpe and Sortino use a configurable annual effective "
            "risk-free-rate assumption (default 2%), converted to a 252-session daily rate. Sortino uses downside "
            "deviation below that daily target. Beta and CAPM alpha use aligned asset/benchmark daily returns; "
            "excess return compares compounded returns over shared dates. Cross-currency CAPM comparisons are suppressed. "
            "A trailing 21-return rolling volatility chart is available. Maximum drawdown is measured against the "
            "running adjusted-price high. Annualized statistics from short periods are noisy.",
        ),
    ]
    for heading, content in sections:
        story.extend(
            [
                Paragraph(heading, styles["Section"]),
                Paragraph(content, styles["SmallBody"]),
            ]
        )

    rule_table = Table(
        [
            ["Label", "Rule"],
            ["Buy", "Annualized return >= 8%, volatility <= 45%, and latest close >= trailing average."],
            ["Hold", "Every other case except the Sell rule."],
            ["Sell", "Annualized return < 0% and latest close < trailing average."],
        ],
        colWidths=[26 * mm, 130 * mm],
    )
    rule_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#142A4A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C6D1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F3F7F9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend(
        [
            Paragraph("4. Historical-Momentum Screen", styles["Section"]),
            Paragraph(
                "The screen compares annualized historical return and volatility with the latest adjusted "
                "close versus the average of up to 50 available sessions. These fixed thresholds are educational "
                "heuristics, not industry standards, predictions, or personalized recommendations.",
                styles["SmallBody"],
            ),
            rule_table,
            Paragraph("5. Portfolio Backtest", styles["Section"]),
            Paragraph(
                "Starting allocations are normalized to 100%. Using prices shared by every selected asset, "
                "the backtest follows an adjusted-price buy-and-hold total-return proxy without periodic rebalancing. "
                "Provider adjustments for distributions/splits are reflected where available; this is not a ledger "
                "of actual tradable shares. Assets must use a single quote currency. Fees, taxes, slippage, and FX "
                "conversion are excluded.",
                styles["SmallBody"],
            ),
            Paragraph("6. Testing", styles["Section"]),
            Paragraph(
                "Offline unit tests cover ticker parsing, mocked provider responses, provider errors, historical "
                "statistics, screen boundaries, backtest arithmetic, and invalid "
                "inputs. Run `python -m unittest discover -s tests -v` from the project directory.",
                styles["SmallBody"],
            ),
            Paragraph("7. Privacy, Terms, and Responsible Use", styles["Section"]),
            Paragraph(
                "The app includes privacy and terms pages describing the market-data request, short in-memory cache, "
                "downloads, and financial-use limitations. It does not bundle synthetic market values. Public market "
                "data may be delayed, incomplete, revised, or unavailable; verify values independently. A public release "
                "must wait for a connected custom domain and review of the policy and hosting details. This application "
                "does not execute trades and is not financial advice.",
                styles["SmallBody"],
            ),
            Paragraph("8. Conclusion", styles["Section"]),
            Paragraph(
                "The project demonstrates a practical research workflow from historical price retrieval through "
                "risk/return analysis, visualization, buy-and-hold simulation, tests, and report export, while making "
                "provider constraints and financial assumptions visible.",
                styles["SmallBody"],
            ),
        ]
    )

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#687786"))
        canvas.drawString(20 * mm, 12 * mm, "Investment Recommendation System | Historical research")
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, str(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Created {output}")


def set_cell_text(cell, text: str, *, size: int, bold: bool, color: RGBColor) -> None:
    cell.text = text
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    for paragraph in cell.text_frame.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Aptos"
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = color


def build_presentation() -> None:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    cover = presentation.slides.add_slide(presentation.slide_layouts[6])
    cover.background.fill.solid()
    cover.background.fill.fore_color.rgb = NAVY
    cover_accent = cover.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(1.25), Inches(0.16), Inches(4.7)
    )
    cover_accent.fill.solid()
    cover_accent.fill.fore_color.rgb = TEAL
    cover_accent.line.fill.background()

    cover_title = cover.shapes.add_textbox(Inches(1.45), Inches(1.65), Inches(10.8), Inches(2.0))
    cover_title.text_frame.text = "Investment Recommendation System"
    cover_title_frame = cover_title.text_frame
    cover_title_frame.word_wrap = True
    cover_title_paragraph = cover_title_frame.paragraphs[0]
    cover_title_paragraph.font.name = "Aptos Display"
    cover_title_paragraph.font.size = Pt(36)
    cover_title_paragraph.font.bold = True
    cover_title_paragraph.font.color.rgb = RGBColor(255, 255, 255)

    cover_subtitle = cover.shapes.add_textbox(Inches(1.5), Inches(4.0), Inches(10.5), Inches(1.0))
    cover_subtitle.text_frame.text = "Investment Banking with Finance Capstone Project"
    cover_subtitle_paragraph = cover_subtitle.text_frame.paragraphs[0]
    cover_subtitle_paragraph.font.name = "Aptos"
    cover_subtitle_paragraph.font.size = Pt(22)
    cover_subtitle_paragraph.font.color.rgb = RGBColor(210, 224, 234)

    cover_note = cover.shapes.add_textbox(Inches(1.5), Inches(5.2), Inches(10.5), Inches(0.6))
    cover_note.text_frame.text = "Historical market research | Provider-sourced data | Not investment advice"
    cover_note_paragraph = cover_note.text_frame.paragraphs[0]
    cover_note_paragraph.font.name = "Aptos"
    cover_note_paragraph.font.size = Pt(14)
    cover_note_paragraph.font.color.rgb = RGBColor(125, 216, 208)

    for slide_number, (title, bullets) in enumerate(SLIDES, start=1):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        background = slide.background.fill
        background.solid()
        background.fore_color.rgb = RGBColor(248, 250, 252)

        header = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), presentation.slide_width, Inches(1.16)
        )
        header.fill.solid()
        header.fill.fore_color.rgb = NAVY
        header.line.fill.background()

        title_box = slide.shapes.add_textbox(Inches(0.65), Inches(0.26), Inches(12), Inches(0.65))
        title_frame = title_box.text_frame
        title_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        title_frame.text = title
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.font.name = "Aptos Display"
        title_paragraph.font.size = Pt(28)
        title_paragraph.font.bold = True
        title_paragraph.font.color.rgb = RGBColor(255, 255, 255)

        accent = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.65), Inches(1.55), Inches(0.11), Inches(4.85)
        )
        accent.fill.solid()
        accent.fill.fore_color.rgb = TEAL
        accent.line.fill.background()

        content = slide.shapes.add_textbox(Inches(1.05), Inches(1.5), Inches(11.5), Inches(5.35))
        frame = content.text_frame
        frame.word_wrap = True
        frame.margin_left = Inches(0.1)
        frame.margin_right = Inches(0.1)
        for index, bullet in enumerate(bullets):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.text = f"• {bullet}"
            paragraph.level = 0
            paragraph.font.name = "Aptos"
            paragraph.font.size = Pt(22 if len(bullets) <= 4 else 19)
            paragraph.font.color.rgb = INK
            paragraph.space_after = Pt(20)

        footer = slide.shapes.add_textbox(Inches(0.65), Inches(7.08), Inches(12), Inches(0.22))
        footer_frame = footer.text_frame
        footer_frame.text = (
            "Academic research project. Not investment advice."
            if slide_number == 1
            else f"Investment Recommendation System  |  {slide_number + 1:02d} / {len(SLIDES) + 1:02d}"
        )
        footer_paragraph = footer_frame.paragraphs[0]
        footer_paragraph.font.name = "Aptos"
        footer_paragraph.font.size = Pt(9)
        footer_paragraph.font.color.rgb = RGBColor(92, 107, 120)
        footer_paragraph.alignment = PP_ALIGN.RIGHT

    output = ROOT / "Presentation1.pptx"
    presentation.save(output)
    print(f"Created {output}")


if __name__ == "__main__":
    build_pdf()
    build_presentation()
