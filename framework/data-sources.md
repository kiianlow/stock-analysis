# Data Sources and Limits (free only)

Verified 15 Oct 2026 with live calls on GOOGL. Re-test if a connector or plan changes.

The whole system runs on free sources: Alpha Vantage free key, web search, SEC EDGAR pages and
files Kiian uploads. Financial Datasets is connected but unfunded, so the workflow never calls it.

## Alpha Vantage free key

- 25 calls per day, at most 1 call per second.
- Call one at a time, never in parallel. Parallel calls trip the per-second limit and waste the daily budget.
- Pass `return_full_data: true`. Large results are saved by the chat to a file and the tool message
  gives the path. Copy that file into the ticker's data folder. Small results come back inline and are
  saved by hand (see CLAUDE.md).

### Verified working (free)

| Tool name | Arguments | Result size | Save as |
|---|---|---|---|
| TIME_SERIES_DAILY | symbol, outputsize compact, datatype csv | Inline, last 100 trading days | daily.csv (verbatim CSV) |
| TIME_SERIES_WEEKLY | symbol, datatype csv | Saved to file, full history | weekly.txt |
| SMA | symbol, interval daily, time_period 200, series_type close, datatype json | Saved to file | sma200.txt |
| INCOME_STATEMENT | symbol | Saved to file, annual and quarterly | income.txt |
| BALANCE_SHEET | symbol | Saved to file | balance.txt |
| CASH_FLOW | symbol | Saved to file | cashflow.txt |
| EARNINGS_ESTIMATES | symbol | Inline | estimates.json |
| INSIDER_TRANSACTIONS | symbol | Saved to file, very large | insiders.txt |
| TREASURY_YIELD | interval daily, maturity 10year | Preview shows the latest value | record the number, pass as --rf |
| GLOBAL_QUOTE | symbol, datatype json | Inline | not needed, daily.csv has the last close |
| RSI and other indicators | symbol, interval, time_period, series_type | Saved to file | optional, the scripts compute these |
| SYMBOL_SEARCH | keywords | Inline | for ticker lookups |

### Premium only on this connector (do not call)

- COMPANY_OVERVIEW (market cap, sector, ratios). Replaced by price x shares from the balance sheet,
  a hand-written meta.json and the scripts' own ratios.
- REALTIME_OPTIONS. Option chains come from Kiian's IBKR app.
- TIME_SERIES_DAILY with outputsize full. The weekly series and the SMA endpoint cover long history.

### Not yet tested (free per Alpha Vantage docs, try when budget allows)

EARNINGS, EARNINGS_CALENDAR, NEWS_SENTIMENT, EARNINGS_CALL_TRANSCRIPT, DIVIDENDS, SPLITS.

## Call budget per US ticker

| # | Call |
|---|---|
| 1 | TIME_SERIES_DAILY compact csv |
| 2 | TIME_SERIES_WEEKLY csv |
| 3 | SMA 200 |
| 4 | INCOME_STATEMENT |
| 5 | BALANCE_SHEET |
| 6 | CASH_FLOW |
| 7 | EARNINGS_ESTIMATES |
| 8 | INSIDER_TRANSACTIONS |

8 calls per ticker plus 1 TREASURY_YIELD call per day. That allows 3 tickers a day if nothing fails.
Plan on 2 to keep a buffer for retries.

## What web search covers

| Framework input | Source |
|---|---|
| Sector, industry, business model, segments | Company 10-K (SEC EDGAR via WebFetch), IR site |
| Stock-based compensation | 10-K cash flow statement |
| Diluted share count | 10-Q cover page or income statement |
| Customer retention, market share, KPIs | Earnings releases, investor decks, industry data |
| Management pay and alignment | DEF 14A proxy statement |
| Short interest | Exchange or data sites via web search |
| Next earnings date and catalysts | Company IR site, news |
| Cause of any estimate or earnings jump | 10-Q, 8-K earnings release, news |
| Beta for WACC | Web search, state the source |
| SGX stocks and S-REITs | SGXNet, company results PDFs, web search |

## Known data quirks

- Weekly series is not split-adjusted. The scripts detect split-like jumps and only use data after the last one.
- Insider feed uses SEC Form 4 codes (P purchase, S sale, A grant, F tax withholding). It contains some
  future-dated rows and filings by fund entities. The script handles all three.
- Statements have no stock-based compensation and no diluted shares. Get both from the 10-K or 10-Q.
- GLOBAL_QUOTE and daily data are end of day. Check the live quote in IBKR before any order.
- Quarterly cash flow lines sometimes repeat the previous quarter exactly (seen in MU capex twice). The script flags repeats and
  quarters that do not sum to the annual figure. Use annual figures and confirm in the release.
- cashAndShortTermInvestments can equal cash alone and never includes long-term marketable investments. MU's net cash was
  understated by $35B. Take cash and investments from the 10-K or earnings release.
- Fiscal year labels use month ends (MU's year ended 3 Sep 2026 shows as 2026-08-31).
- Operating income can differ slightly from the company's GAAP figure (MU FY26: $99.91B feed vs $99.34B release). Quote the release.

## SGX coverage

Alpha Vantage lists only US ADRs and Frankfurt lines for SGX names (for example DBSDY), in USD or EUR.
Do not use those for SGX analysis. Use the manual path in CLAUDE.md: fill templates/financials-manual.json
from the latest annual report and results. For technicals, Kiian can export daily prices as CSV from
TradingView or POEMS (columns: date, open, high, low, close, volume) and upload them.
