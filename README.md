# Stock Analysis

Kiian's system for deciding whether a stock is a buy. It runs inside a Claude chat, uses only free
data, and saves every analysis here so decisions can be reviewed later.

## How to use it

1. Open a chat in the Finance project on claude.ai.
2. Type: `Analyse NVDA with my stock-analysis repo`. If the stock-analysis skill is saved, `Analyse NVDA` is enough.
3. Approve the repo attach if Claude asks.
4. Claude pulls the data, runs the calculators, researches the judgment calls and scores the company.
   This takes a few minutes. You can leave and come back.
5. You get a verdict in chat and a full report file. The report is also committed to `analyses/`.
6. If the verdict suggests a put, open the IBKR option chain at the suggested strike and send Claude
   the expiry, bid/ask, IV and open interest. Claude returns breakeven and annualised yield.
7. Check the live quote in IBKR before you place anything.

For SGX stocks and S-REITs, upload the latest results PDF and, for technicals, a daily price CSV
exported from TradingView or POEMS (date, open, high, low, close, volume).

## Limits (free only)

- Alpha Vantage free key: 25 calls a day. One US ticker uses 8. Plan on 2 tickers a day, 3 at most.
- No live option chains. They come from your IBKR app.
- No SGX data from the connectors. SGX runs on filings, web search and your uploads.
- Prices are end of day.
- Company overview and full daily history are premium on Alpha Vantage. The scripts rebuild what they need from free data.

## What is in here

| Path | What it does |
|---|---|
| `CLAUDE.md` | The runbook Claude follows for every analysis |
| `framework/stock-buy-decision-framework.md` | The 15 gates, formulas, thresholds, scorecard and overrides |
| `framework/data-sources.md` | Which free source feeds which input, call budget, known data quirks |
| `scripts/analyze.py` | Runs every calculator on one ticker's data folder |
| `scripts/technicals.py` | RSI, MACD, ATR, ADX, Bollinger, stage, Fibonacci, pivots, support and resistance zones |
| `scripts/fundamentals.py` | Margins, ROIC, FCF, leverage, Altman Z, Piotroski F, Beneish M, stronger-vs-bigger test |
| `scripts/estimates.py` | Forward P/E, estimate revisions, one-off earnings flags |
| `scripts/insiders.py` | Insider buys and sales, with grants, tax withholding and fund entities separated |
| `scripts/valuation.py` | DCF, reverse DCF, expected return, scenarios, WACC, put breakeven and yield |
| `scripts/scorecard.py` | Weighted score, rating map and overrides |
| `tests/` | Formula tests. Claude runs them before every analysis |
| `templates/analysis-report.md` | Report layout |
| `templates/financials-manual.json` | Manual input for SGX or uncovered companies |
| `analyses/` | Every report, plus `decision-log.csv` |
| `skill/SKILL.md` | Optional claude.ai skill that points Claude at this repo |

## Data checks built in

- Hand-copied daily prices are rebuilt into weeks and matched against the connector's weekly file.
- OHLC logic is checked on every bar.
- Split-like jumps in unadjusted series are detected and older data is cut off.
- Balance sheets that do not tie and gross profit that does not match revenue minus cost are flagged.
- Large gaps between this year's and next year's consensus EPS are flagged for investigation.

## Running it yourself

```
pip install -r requirements.txt
python3 -m pytest -q
python3 scripts/analyze.py data/GOOGL/2026-10-15 --rf 0.0521
python3 scripts/valuation.py csp --strike 330 --premium 6.2 --dte 35
```

Not licensed financial advice. The framework improves the odds of a good decision. It cannot guarantee one.
