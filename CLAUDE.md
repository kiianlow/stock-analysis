# Instructions for Claude

This repo is Kiian's stock analysis system. When he asks to analyse a ticker or company, or asks
whether something is a buy or undervalued, follow this runbook in order. Do not skip steps and do
not improvise a different workflow.

## 0. Setup, every new session

1. The repo is `kiianlow/stock-analysis`. If it is not attached, attach it with add_repo (access: push),
   then clone it to `/home/claude/stock-analysis` and work there.
2. `pip install -r requirements.txt --break-system-packages -q`
3. `python3 -m pytest -q`. Every test must pass before any analysis. If one fails, stop and fix it first.
4. Read `framework/stock-buy-decision-framework.md` and `framework/data-sources.md`.
5. Get today's date and time with the current_time tool. Make `data/<TICKER>/<YYYY-MM-DD>/`.
6. If `analyses/` already holds a report for this ticker, read the latest one. The new report must say what changed since.

## 1. Classify the ticker

- US-listed: Alpha Vantage path, step 2.
- SGX-listed (stocks, S-REITs): manual path, step 5. Alpha Vantage does not cover SGX.

## 2. Pull data, US tickers (Alpha Vantage free key)

Rules:
- Use `mcp__Alpha_Vantage_MCP_Server__TOOL_CALL`. One call at a time, never in parallel.
- Always pass `"return_full_data": true` except for TREASURY_YIELD.
- 25 calls a day. Budget 8 per ticker. On any rate-limit or premium error, stop calling Alpha Vantage
  for the day, list the missing inputs as data gaps and carry on with what you have.

Calls, in this order:

| # | tool_name | arguments | Save |
|---|---|---|---|
| 1 | TIME_SERIES_WEEKLY | {"symbol": T, "datatype": "csv", "return_full_data": true} | weekly.txt |
| 2 | TIME_SERIES_DAILY | {"symbol": T, "outputsize": "compact", "datatype": "csv", "return_full_data": true} | daily.csv |
| 3 | SMA | {"symbol": T, "interval": "daily", "time_period": 200, "series_type": "close", "datatype": "json", "return_full_data": true} | sma200.txt |
| 4 | INCOME_STATEMENT | {"symbol": T, "return_full_data": true} | income.txt |
| 5 | BALANCE_SHEET | {"symbol": T, "return_full_data": true} | balance.txt |
| 6 | CASH_FLOW | {"symbol": T, "return_full_data": true} | cashflow.txt |
| 7 | EARNINGS_ESTIMATES | {"symbol": T, "return_full_data": true} | estimates.json |
| 8 | INSIDER_TRANSACTIONS | {"symbol": T, "return_full_data": true} | insiders.txt |
| once a day | TREASURY_YIELD | {"interval": "daily", "maturity": "10year", "datatype": "json"} | note the latest value |

How to save:
- Large result: the tool message says "Output has been saved to <path>". Run `cp <path> data/T/D/<name>`.
- Inline result: write the exact text with the Write tool.
  - daily.csv: the CSV body exactly as returned, one row per line, header first.
  - estimates.json: `{"symbol": T, "estimates": [...]}` holding, verbatim, the entries for the next two
    fiscal years and the two most recent fiscal quarters. Copy every field of those entries.
- TREASURY_YIELD returns a preview. Take the most recent non-blank value and pass it as a decimal (5.21% is 0.0521).
- Write `meta.json`: {"ticker", "company", "currency", "sector", "industry"} from the 10-K or IR site.

## 3. Run the calculators

```
python3 scripts/analyze.py data/T/D --rf <10-year yield as decimal>
```

Then check, before using any number:
- `data_checks` in summary.json: no OHLC violations, no daily vs weekly mismatches. A mismatch means
  daily.csv was copied wrong. Re-save it and rerun.
- Read every flag. Each flag needs an explanation in the report, found in filings or news.
- Beneish: the kill switch uses the growth-neutral score (`m_growth_neutral`). A raw score above -1.78 caused by sales growth is explained, not disqualifying.
- Feed errors flagged by the script (repeated quarterly values, quarters that do not sum to the annual figure): use annual figures and confirm in the 10-K or earnings release.
- If estimates flag a large EPS change between fiscal years, find the cause (one-off gains, charges)
  and value the company on core earnings, not the distorted figure.
- Net cash: the feed counts only cash and short-term investments. Add long-term marketable investments from the
  latest 10-K or release when the company holds them.

## 4. Research the judgment gates (web search, cite every source)

Primary sources first: 10-K, 10-Q, 8-K and DEF 14A on SEC EDGAR (WebFetch), then company IR, then news.

- Gate 1: business model, segments, which segment makes the profit.
- Gate 2: moat type and the numbers that prove it, moat direction.
- Gate 3: customer retention, market share. Stock-based compensation from the 10-K, then FCF minus SBC.
- Gate 6: anything the scripts flagged on accounting.
- Gate 7: capital allocation record, insider ownership, pay metrics from the proxy.
- Gate 9: every quiet-breakage signal in the framework. Say which are firing and which are clear.
- Gate 11: short interest, estimate revision direction (from the script).
- Gate 12: rates and macro context that bears on this company.
- Gate 14: next earnings date and other dated catalysts.

## 5. Manual path (SGX or anything Alpha Vantage lacks)

1. Fill `templates/financials-manual.json` from the latest annual report and results. Save as `data/T/D/manual.json`.
   Use the company's reporting currency. Leave a field out rather than guess it.
2. Prices: ask Kiian to export daily prices as CSV from TradingView or POEMS and upload them. Save as daily.csv.
   Without prices, say the technical gate is incomplete.
3. Banks and REITs: the industrial metrics (Altman, Beneish) do not apply. Use framework section 8.9.
   For S-REITs check MAS limits: aggregate leverage cap 50%, minimum interest coverage 1.5x.
4. Run `python3 scripts/analyze.py data/T/D` as usual.

## 6. Valuation

- Cost of equity by CAPM: risk-free = US 10-year yield, equity risk premium 5% unless there is a reason
  to change it (state it), beta from a cited source. Use `python3 scripts/valuation.py wacc ...`.
- Reverse DCF on TTM free cash flow, or on normalised FCF when capex or one-offs distort it (explain which):
  `python3 scripts/valuation.py reverse-dcf ...`. Compare the implied growth with history and market size.
- Bull, base and bear values with stated assumptions and probabilities that add to 1:
  `python3 scripts/valuation.py scenarios ...`. Upside/downside should be at least 2 to 1.
- Expected annual return (Gate 8.4): `python3 scripts/valuation.py expected ...`.
- Hurdle (convention for this repo): required return = US 10-year yield + 5 points
  (3-point equity premium plus 2-point single-stock margin). Below it means `--below-hurdle` in step 7.
- Cyclicals (memory, semis, energy, materials, autos, shipping): use normalised earnings (framework 8.8) with
  `python3 scripts/valuation.py cyclical --boom-fcf 130,60 --mid-revenue 120e9 --mid-margin 0.28 --tax 0.15 --shares 1.147e9 --multiple 15 --discount 0.127 --net-cash 59.55 --price 914.13`.
  Run bull, base and bear. Check through-cycle margins from at least 10 years of annual statements. Report the mid-cycle EPS the price implies.

## 7. Score

- Score each of the 10 categories 1 to 5 using the rubric table in the framework's Scorecard section.
- Write one line of evidence for every score. Decide scores before looking at the resulting rating,
  and never change a score to reach a rating.
- Run `python3 scripts/scorecard.py --scores '<json>' [--kill-switch] [--below-hurdle]`.

## 8. Entry plan

- Kiian enters mainly with cash-secured puts on IBKR. Suggest a strike at or below the S1 or S2 zone from
  the technicals output and below the base-case value after margin of safety.
- Never invent option prices. Ask Kiian for the live chain: strike, expiry, bid/ask, IV, open interest.
  Then run `python3 scripts/valuation.py csp --strike X --premium Y --dte Z`.
- Flag any earnings date before expiry.
- Size within the framework limits. Remind him in one line that sizing depends on his liquidity and horizon.

## 9. Report, log and save

1. Copy `templates/analysis-report.md` to `analyses/<YYYY-MM-DD>-<TICKER>.md` and fill every section.
   Every number carries its source and date. Label facts, estimates and opinions.
2. Append one row to `analyses/decision-log.csv`.
3. `git add analyses && git commit -m "Analysis: <TICKER> <YYYY-MM-DD>"` (follow the session's commit
   attribution rules), then `git push`. Raw data under `data/` stays out of git.
4. Send the report with SendUserFile. In chat: verdict first, then a short summary, the entry idea and data gaps.

## 10. Writing style for anything Kiian reads

Short sentences. Active voice. Verdict first. No em dashes, no semicolons, no filler, no hype words.
Address Kiian directly. One line saying this is not licensed financial advice.

## 11. When something breaks

- A script error: fix the script, add a test for the case, run the full test suite, commit the fix.
- A data quirk: handle it in code, document it in `framework/data-sources.md`, commit.
- Never paper over a missing input with an estimate presented as fact.
