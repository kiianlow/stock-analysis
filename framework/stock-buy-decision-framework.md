# Stock Buy Decision Framework

Built 15 Oct 2026 for Kiian. Use it on any US or SGX listed company before money goes in, whether by direct purchase or a cash-secured put.

---

## How to use this

- Run the gates in order. Any Gate 0 kill switch ends the analysis. A cheap price never overrides a broken business.
- Gates 1 to 7 answer one question: is this a good business that is getting stronger?
- Gate 8 answers: is the price fair?
- Gate 9 answers: is something quietly breaking?
- Gates 10 to 15 answer: is now a sensible time, and does it fit the portfolio?
- Score the company in the Scorecard section. The score sets the rating. The overrides can cap it.
- Use at least 5 years of data, 10 where available. One year shows a number, not a trend.
- Label everything in your notes as one of three things. Fact (reported in a filing). Estimate (consensus or your forecast). Opinion (narrative). Most bad decisions come from treating the third as the first.
- Thresholds marked (convention) are practitioner rules of thumb, not laws. Sector norms beat generic thresholds. A utility at 5x net debt/EBITDA can be normal. A software company at 5x is not.
- Trace every key number back to the filing. Check it in two sources. Data vendors make errors, especially around splits, restatements, fiscal year ends and share classes.

---

## The core philosophy

Three questions decide every buy:

1. Is it a good business that is getting stronger, not just bigger?
2. Is the price fair relative to its growth, its cash generation and its own history?
3. Is anything quietly breaking under the surface?

Two failure modes this framework is built to stop:

- Bad company at a good price. A value trap. Cheap for a reason, and the reason keeps getting worse.
- Great company at an expensive price. The business can execute perfectly and you still earn little for years. Microsoft did not regain its December 1999 high until 2016, while its earnings grew many times over.

---

## Gate 0: Kill switches

Any one of these means stop. Do not score the company.

| Kill switch | Where to check |
|---|---|
| Going concern doubt in the auditor's report | Annual report, auditor's opinion |
| Auditor resigned or was dismissed with disagreements | US 8-K Item 4.01, SGXNet announcements |
| Unresolved material weakness in internal controls | 10-K Item 9A, auditor's ICFR opinion |
| Restatement of prior financials in the last 3 years beyond trivial items | 8-K Item 4.02, 10-K/A |
| Late filing notices (NT 10-K, NT 10-Q) | SEC EDGAR |
| Active accounting investigation by a regulator, or credible fraud allegations the company has not rebutted with evidence | News, 10-K legal proceedings, short-seller reports |
| Beneish M-score above -1.78 with sales growth neutralised (SGI set to 1). A raw score above -1.78 driven only by growth is a flag to explain, not a kill switch (see Gate 6) | Calculate (fundamentals.py reports both) |
| Altman Z-score in the distress zone AND negative free cash flow (non-financial companies only) | Calculate (Gate 5) |
| Loss-making with under 12 months of cash runway and no committed funding | Cash flow statement, liquidity section of MD&A |
| You cannot explain in two sentences how the company makes money and why customers choose it | Your own notes |
| Too illiquid to exit your position within a few trading days without moving the price | Average daily traded value. Check SGX small caps carefully |
| Ownership structure you cannot underwrite, for example a VIE where you own a contractual claim rather than the operating assets, unless the discount fully prices that risk | Prospectus, 10-K / 20-F risk factors |

---

## Gate 1: Understand the business

Answer each in writing. If an answer needs more than three sentences, you do not understand it yet.

- What does it sell, to whom, and why do they buy it instead of the alternative?
- Revenue mix by segment, geography and customer type.
- Which segment makes the profit? Use segment operating income, not segment revenue.
- Revenue type: recurring (subscription, contracted), usage-based, transactional, one-off (hardware, projects, licences). Recurring revenue deserves a higher multiple because it is more predictable.
- Pricing power: has it raised prices faster than inflation without losing volume? 2021 to 2023 is a good test window. Gross margin that held through that period is evidence.
- Customer concentration: US filings must disclose any single customer at 10% or more of revenue. Is concentration rising?
- Supplier concentration and single points of failure (one foundry, one licence, one platform).
- Unit economics: cost to acquire a customer, cost to serve, retention, lifetime value.
- Capital intensity: capex as % of revenue. Asset-light businesses compound with less reinvestment.
- Cyclicality: how did revenue and margins behave in 2008 to 2009, 2020 and 2022?
- Industry life cycle: emerging, growth, mature or declining.
- What would make this product unnecessary in 10 years? Who is spending money to take this profit pool?

---

## Gate 2: Competitive moat and industry structure

### Moat sources

| Moat type | What it looks like | How to verify with numbers |
|---|---|---|
| Intangibles (brand, patents, licences, regulatory approvals) | Premium pricing, protected markets | Gross margin above peers for 5+ years. Patent expiry schedule |
| Switching costs | Painful, costly or risky for customers to leave | Gross revenue retention, contract length, churn |
| Network effects | Product improves as more users join | User growth with flat or falling acquisition cost, rising market share |
| Cost advantage and scale | Lowest-cost producer | Operating margin above peers at similar prices, position on the industry cost curve |
| Efficient scale | Market only supports one or a few players | Stable shares, few new entrants, high returns that are not competed away |

Helmer's 7 Powers adds three more worth checking: counter-positioning (incumbents cannot copy without hurting themselves), cornered resource (exclusive access to talent, IP or inputs) and process power (hard-to-copy operational know-how).

### Moat tests

- ROIC above WACC for most of the last 10 years. The size and persistence of that spread is the best single number for moat.
- Gross margin stable or rising through a full cycle.
- Market share stable or rising.
- Price increases that stick.
- Moat direction: widening, stable or narrowing. A narrowing moat on a high multiple is the most dangerous combination in this framework.

### Porter's five forces

| Force | Favourable when | Unfavourable when |
|---|---|---|
| Rivalry | Few rational players, differentiated products | Many players, commodity product, high fixed costs, price wars |
| Threat of new entrants | High capital needs, regulation, scale, brand | Low barriers, cheap capital chasing the space |
| Substitutes | No close substitute | Cheaper or better alternatives emerging |
| Buyer power | Fragmented customers, high switching costs | Few large customers, easy to switch |
| Supplier power | Many suppliers, commodity inputs | One critical supplier, scarce inputs |

---

## Gate 3: Stronger, not just bigger

This is the centre of the framework. Size is not the goal. Per-share value and business quality are.

### Revenue growth quality

- Growth over 1, 3, 5 and 10 years. CAGR = (End value / Start value)^(1 / years) - 1.
- Direction of growth, the second derivative. 30% after 50% is a 20-point deceleration. Find the reason before you buy: tough comparison, saturation, share loss, price cuts or macro.
- Last 8 quarters of year-on-year growth. A steady slide is a trend. A one-quarter dip may be a comparison effect.
- Two-year stacked growth removes comparison distortion: (1 + growth year 1) × (1 + growth year 2) - 1.
- Organic vs acquired growth. Strip out acquisitions. Bought growth costs capital and is not the same as earned growth.
- Price vs volume. Growth from price alone while volume falls means demand is weakening.
- Constant-currency (FX-neutral) growth, to separate business performance from currency moves.
- Guidance vs actual results over the last 3 to 5 years.

### Earnings and margin quality

- EPS growth vs revenue growth. EPS growing faster means operating leverage (good) or buybacks, a lower tax rate or one-offs (check which).
- Gross margin trend over 5 to 10 years.
- Operating margin trend over 5 to 10 years.
- Incremental operating margin = change in operating income / change in revenue. Above the current margin means operating leverage.

### Per-share growth

- Revenue per share, EPS, FCF per share, book value per share (for financials), dividend per share.
- Diluted share count over 5 years. Rising more than about 2% a year is meaningful dilution (convention).
- Stock-based compensation as % of revenue. Above about 10% is heavy for a mature company (convention).

### Returns on growth

- Incremental ROIC = change in NOPAT / change in invested capital, measured over 3 to 5 years. Growth above WACC creates value. Growth below WACC destroys it, even when revenue rises.
- Reinvestment rate = (net capex + change in working capital + acquisitions) / NOPAT.
- Fundamental growth equation: sustainable growth = reinvestment rate × ROIC.

### Stronger vs bigger test

| Metric | Getting stronger | Just bigger | Weakening |
|---|---|---|---|
| Gross margin | Rising | Flat | Falling |
| Operating margin | Rising | Flat | Falling |
| ROIC | Rising | Flat | Falling |
| FCF per share growth vs revenue growth | Faster | Similar | Slower |
| Diluted share count | Falling | Flat | Rising |
| Customer retention (NRR, churn) | Improving | Flat | Worsening |
| Market share | Gaining | Flat | Losing |
| Debt used to fund growth | None | Some | Heavy |

Five or more in the "getting stronger" column is a pass. Three or more in "weakening" is a fail.

### Rule of 40 (software and high-growth companies)

Revenue growth % + FCF margin % should be 40 or higher. Some analysts use EBITDA margin instead of FCF margin. State which one you use.

---

## Gate 4: Profitability and returns

| Metric | Formula | What good looks like (convention, compare to sector) |
|---|---|---|
| Gross margin | (Revenue - COGS) / Revenue | Stable or rising, above peers |
| Operating margin | EBIT / Revenue | Stable or rising, above peers |
| Net margin | Net income / Revenue | Check for one-offs and tax effects |
| EBITDA margin | EBITDA / Revenue | Ignores capex. Never use alone for capital-heavy companies |
| FCF margin | FCF / Revenue | Above 15% is strong for most non-financials |
| ROE | Net income / average shareholders' equity | Above 15%, but check how much comes from leverage |
| ROA | Net income / average total assets | Around 1% or more is solid for banks |
| ROIC | NOPAT / invested capital | Above 15% excellent, above 10% good, below WACC destroys value |
| ROCE | EBIT / (total assets - current liabilities) | Above cost of capital, rising |
| CROIC | FCF / invested capital | Confirms ROIC with cash |

Definitions:
- NOPAT = EBIT × (1 - tax rate).
- Invested capital = total debt + total equity - excess cash. Equivalent operating view: net working capital + net fixed assets + operating intangibles.
- FCF = cash from operations - capital expenditure.

### DuPont decomposition

ROE = (Net income / Revenue) × (Revenue / Total assets) × (Total assets / Equity)

ROE built on margin and asset turnover is higher quality than ROE built on the equity multiplier (leverage). Heavy buybacks can push equity close to zero or negative, which makes ROE meaningless. Use ROIC in those cases.

---

## Gate 5: Financial strength

### Leverage and liquidity

| Metric | Formula | Convention (non-financials) |
|---|---|---|
| Net debt / EBITDA | (Total debt - cash) / EBITDA | Below 1x low, 1x to 3x moderate, above 3x elevated |
| Debt / equity | Total debt / shareholders' equity | Compare to sector |
| Interest coverage | EBIT / interest expense | Above 8x strong, 4x to 8x adequate, 1.5x to 4x weak, below 1.5x danger |
| Current ratio | Current assets / current liabilities | Above 1.5 comfortable, below 1 needs a reason |
| Quick ratio | (Cash + marketable securities + receivables) / current liabilities | Above 1 comfortable |
| Cash runway (loss makers) | (Cash + short-term investments) / quarterly cash burn | At least 8 quarters, ideally more |

Some businesses run below a current ratio of 1 safely because customers pay before suppliers are paid (many retailers and subscription businesses). Check the cash conversion cycle before penalising it.

### Debt structure

- Maturity schedule: debt due in the next 24 months vs cash plus expected FCF.
- Refinancing cost: what happens to interest expense if maturing debt rolls at today's rates?
- Fixed vs floating mix.
- Covenants and how close the company is to them.
- Credit rating and outlook. Investment grade is BBB- (S&P, Fitch) or Baa3 (Moody's) and above. A negative outlook often leads the equity.

### Off-balance-sheet and hidden obligations

- Lease commitments, including signed leases that have not started yet.
- Purchase obligations and take-or-pay contracts.
- Guarantees and contingent liabilities.
- Pension and post-retirement deficits.
- Legal liabilities not yet provisioned.

### Dividend safety

- FCF payout ratio = dividends / FCF. Above 80% leaves little margin (convention, REITs and utilities differ).
- Dividend cover = EPS / dividend per share.
- History of cuts, and whether debt funds the dividend.

### Altman Z-score (distress, non-financial companies)

Original model for public manufacturers:

Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E

- A = working capital / total assets
- B = retained earnings / total assets
- C = EBIT / total assets
- D = market value of equity / total liabilities
- E = sales / total assets

Zones: above 2.99 safe, 1.81 to 2.99 grey, below 1.81 distress.

Z'' model for non-manufacturers and service companies:

Z'' = 6.56A + 3.26B + 6.72C + 1.05D, where D = book value of equity / total liabilities.

Zones: above 2.60 safe, 1.10 to 2.60 grey, below 1.10 distress.

Do not use either model on banks, insurers or REITs.

### Piotroski F-score (0 to 9, one point per test passed)

| # | Test | Point if |
|---|---|---|
| 1 | Return on assets | Net income / beginning total assets is positive |
| 2 | Operating cash flow | Positive |
| 3 | Change in ROA | Higher than last year |
| 4 | Accruals | Operating cash flow greater than net income |
| 5 | Leverage | Long-term debt / average total assets lower than last year |
| 6 | Liquidity | Current ratio higher than last year |
| 7 | Dilution | No new common shares issued in the last year |
| 8 | Gross margin | Higher than last year |
| 9 | Asset turnover | Sales / beginning total assets higher than last year |

8 to 9 strong, 3 to 7 middle, 0 to 2 weak.

---

## Gate 6: Earnings quality and accounting

Cash does not lie. Accruals can. This gate checks whether reported profit is real.

### Cash conversion

- Cash from operations / net income above 1 over a multi-year period (convention).
- FCF / net income. Persistently below 0.8 needs an explanation (convention, growth capex is a valid one).
- Simple accruals ratio = (net income - cash from operations) / average total assets. Higher means lower quality. A rising trend or a ratio well above peers is a warning.

### Working capital

- DSO (days sales outstanding) = accounts receivable / revenue × 365
- DIO (days inventory outstanding) = inventory / COGS × 365
- DPO (days payables outstanding) = accounts payable / COGS × 365
- Cash conversion cycle = DSO + DIO - DPO

Warnings:
- Receivables growing faster than revenue: sales pulled forward or looser credit terms.
- Inventory growing faster than sales: demand miss, future write-downs.
- Payables stretched hard: cash flow flattered by delaying suppliers.
- Supplier finance programmes or receivables factoring. US companies must disclose supplier finance programmes under ASU 2022-04. These can hide working capital stress.

### Capitalisation and depreciation

- Rising capitalised software, capitalised interest or capitalised customer acquisition costs push expense off the income statement.
- Extending asset useful lives lowers depreciation and lifts earnings without any change in the business. Hyperscaler server lives are the live example in 2025 to 2026.
- Capex well below depreciation for years can mean underinvestment. Capex far above depreciation means depreciation will rise later and pressure margins.

### Adjusted numbers

- Gap between GAAP and non-GAAP earnings. A widening gap is a warning.
- "One-time" restructuring charges that appear every year are operating costs.
- Stock-based compensation is a real cost. Track FCF minus SBC.

### Balance sheet quality

- Goodwill and intangibles as % of total assets. High levels plus frequent acquisitions mean serial-acquirer risk and impairment risk.
- Impairment history.
- Related-party transactions.
- Revenue recognition changes, bill-and-hold arrangements, large unbilled receivables.
- Effective tax rate far below peers or dependent on one jurisdiction.
- Deferred revenue trend for subscription businesses. Deferred revenue slowing before revenue slows is an early signal.

### Beneish M-score (earnings manipulation screen)

M = -4.84 + 0.920 DSRI + 0.528 GMI + 0.404 AQI + 0.892 SGI + 0.115 DEPI - 0.172 SGAI + 4.679 TATA - 0.327 LVGI

| Variable | Definition |
|---|---|
| DSRI | (Receivables / Sales) this year ÷ (Receivables / Sales) last year |
| GMI | Gross margin last year ÷ gross margin this year |
| AQI | [1 - (Current assets + PP&E + securities) / Total assets] this year ÷ same ratio last year |
| SGI | Sales this year ÷ sales last year |
| DEPI | Depreciation rate last year ÷ depreciation rate this year, where rate = depreciation / (depreciation + PP&E) |
| SGAI | (SG&A / Sales) this year ÷ (SG&A / Sales) last year |
| LVGI | [(Current liabilities + long-term debt) / Total assets] this year ÷ same ratio last year |
| TATA | (Income from continuing operations - cash from operations) / total assets |

Above -1.78 flags a likely manipulator in the 8-variable model. Some analysts use -2.22 as a stricter cutoff. It is a screen, not proof. A fast-growing honest company can score high on SGI alone, so the kill switch uses the growth-neutral score: recompute M with SGI set to 1. If that stays above -1.78, stop. If only the raw score is above the line, explain it in the report and check accruals (TATA) and receivables (DSRI) by hand.

---

## Gate 7: Management and governance

### Track record

- Compare guidance with actual results for the last 3 to 5 years. Consistent misses or constant re-basing is a credibility problem.
- Did they deliver on the targets set at investor days?

### Capital allocation report card

| Use of cash | Good | Bad |
|---|---|---|
| Reinvestment | High incremental ROIC | Growth below cost of capital |
| Acquisitions | Earned their cost of capital, no later write-downs | Overpaid, later impaired, used to buy growth |
| Buybacks | Bought when undervalued, share count actually fell net of SBC | Bought at peak prices, share count still rising |
| Dividends | Covered by FCF, growing with earnings | Funded with debt, cut later |
| Debt | Used for value-creating projects at sensible leverage | Borrowed to fund buybacks at peak valuations |

### Alignment

- Insider ownership: meaningful personal stake relative to their wealth.
- Insider transactions: open-market buys are a stronger signal than sales, especially cluster buys by several insiders. Sales are noisy because of 10b5-1 plans, tax and diversification. US insiders file Form 4 within 2 business days. SG director and substantial shareholder dealings appear on SGXNet.
- Compensation (US proxy statement, DEF 14A): pay tied to ROIC, FCF per share or relative total shareholder return is better aligned. Pay tied only to revenue or adjusted EPS can be gamed.

### Governance

- Dual-class shares that remove voting rights from outside shareholders.
- Board independence, combined CEO and chair, staggered boards, poison pills.
- Related-party dealings with the founder or controlling family.
- For S-REITs: sponsor strength, pipeline of assets, management fee structure (fees in units vs cash, fees on acquisitions that reward growth over yield).

### Communication

- Candour about bad news.
- Consistent KPIs over time. A company that stops reporting a metric is usually telling you the metric got worse.
- Answers analysts' hard questions directly on earnings calls.

### People

- Key person risk and succession plan.
- Turnover in senior finance roles.
- Employee reviews and hiring trends.

---

## Gate 8: Valuation

A great business at the wrong price is a bad investment. Always check price against at least three independent methods.

### 8.1 Multiples

| Multiple | Formula | Best used for | Watch out for |
|---|---|---|---|
| Trailing P/E | Price / EPS (last 12 months) | Stable, profitable companies | One-offs, cyclical peaks |
| Forward P/E | Price / next 12 months consensus EPS | Growth companies | Estimates can be wrong. If forward P/E is far above trailing, earnings are expected to fall. Find out why |
| PEG | P/E / EPS growth rate (%) | Comparing growth companies | Below 1 cheap, 1 to 2 fair, above 2 rich (convention). Use 3 to 5 year growth |
| EV / EBITDA | Enterprise value / EBITDA | Comparing companies with different debt levels | Ignores capex |
| EV / EBIT | Enterprise value / EBIT | Capex-heavy companies | Better than EV/EBITDA when depreciation is real |
| EV / Sales | Enterprise value / revenue | Loss-making or early-stage companies | Says nothing about margins |
| EV / Gross profit | Enterprise value / gross profit | Software and marketplaces | Ignores operating costs |
| P / FCF | Market cap / FCF | Cash-generative businesses | Capex timing swings it |
| FCF yield | FCF / market cap | Comparing with bond yields | Subtract SBC for a cleaner number |
| Earnings yield | EPS / price, or EBIT / EV | Comparing with the 10-year Treasury | EBIT / EV is the Greenblatt version |
| P / B, P / TBV | Price / book value per share, or tangible book | Banks, insurers, asset-heavy firms | Meaningless for asset-light companies |
| Dividend yield | Dividend per share / price | Income stocks | A very high yield often prices in a cut |
| Shareholder yield | Dividend yield + net buyback yield | Mature companies | Buybacks offset by SBC do not count |

Enterprise value = market cap + total debt + preferred stock + minority interest - cash and equivalents.

### 8.2 Relative valuation

- Against its own 5 and 10-year median multiples.
- Against true peers with similar business models, growth and margins.
- Against the market (S&P 500 or STI forward P/E).
- Against bonds: earnings yield or FCF yield minus the 10-year government bond yield.
- A discount to history only means something if the business is as good as it was. Check Gates 3 and 9 before calling it cheap.

### 8.3 Intrinsic value

Discounted cash flow (DCF), step by step:

1. Forecast unlevered FCF for 5 to 10 years: EBIT × (1 - tax rate) + depreciation and amortisation - capex - change in net working capital.
2. Discount rate: WACC = (E / (D + E)) × Re + (D / (D + E)) × Rd × (1 - tax rate).
3. Cost of equity by CAPM: Re = risk-free rate + beta × equity risk premium.
4. Terminal value (Gordon growth): TV = FCF in final year × (1 + g) / (WACC - g). Keep g at or below long-run nominal GDP growth. 2% to 3% is a conservative range (convention). Exit-multiple method is the alternative. Run both.
5. Discount each cash flow: PV = FCF in year t / (1 + WACC)^t.
6. Equity value = enterprise value - net debt - minority interest - preferred stock. Divide by diluted shares.
7. Sensitivity table: WACC plus and minus 1 point, terminal growth plus and minus 0.5 points.
8. Sanity check: if terminal value is more than about 75% of total value, the answer is mostly assumption (convention).

Reverse DCF:
- Solve for the growth rate that justifies today's price.
- Compare that implied growth with the company's history, its industry growth and its market size. If the price needs growth the company has never delivered, you are paying for a hope.

Other methods:
- Dividend discount model for stable payers: Price = next year's dividend / (required return - dividend growth).
- Sum of the parts for conglomerates and multi-segment groups.
- Net asset value (NAV) for REITs, property developers and resource companies.
- Residual income for banks: value = book value + present value of (ROE - cost of equity) × book value.
- Justified P/B for banks = (ROE - g) / (cost of equity - g).
- Graham number = square root of (22.5 × EPS × book value per share). A rough ceiling for defensive, asset-backed companies. Not useful for growth companies.

### 8.4 Expected return math

Expected annual return is approximately:

FCF yield (or shareholder yield) + growth in FCF per share + annualised change in valuation multiple

Annualised multiple change = (exit multiple / entry multiple)^(1 / years) - 1.

Worked example: 4% FCF yield, 8% FCF per share growth, multiple contracts from 25x to 20x over 5 years. (20 / 25)^(1/5) - 1 = -4.4% a year. Expected return is about 4% + 8% - 4.4% = 7.6% a year.

This is an approximation. The terms are added, not compounded, so treat it as a quick estimate.

### 8.5 The hurdle

The expected return must clear two bars:
1. Risk-free: SGD T-bills or Singapore Savings Bonds for SGD money, US Treasury bills or notes for USD money.
2. A broad index ETF. A single stock carries more risk than the index. If the expected return does not beat the index by a clear margin, own the index.

### 8.6 Scenario analysis

| Scenario | Revenue growth | Operating margin | Exit multiple | Value per share | Probability |
|---|---|---|---|---|---|
| Bull | | | | | |
| Base | | | | | |
| Bear | | | | | |

Probability-weighted value = sum of (value × probability). Probabilities must add to 100%.

Upside to base case vs downside to bear case should be at least 2 to 1, ideally 3 to 1 (convention).

### 8.7 Margin of safety

Buy below your estimate of intrinsic value. Common practice is a 20% to 30% discount for stable, predictable businesses and 40% or more for uncertain ones (convention). The less predictable the cash flows, the bigger the discount you need.

### 8.8 Cyclical companies

P/E is lowest at the earnings peak and highest at the trough. Buying a cyclical on a low P/E at peak earnings is one of the most expensive mistakes in investing. Use normalised earnings: average margin across a full cycle × current revenue. Semis, energy, materials, autos, airlines, shipping, homebuilders and memory chips all need this treatment.

### 8.9 Sector-specific metrics

| Sector | Key metrics |
|---|---|
| Banks | P/B and P/TBV vs ROE, net interest margin (NIM), CET1 ratio vs regulatory minimum plus buffers and peers, NPL ratio, credit cost in basis points, cost-to-income ratio, loan-to-deposit ratio, fee income share |
| S-REITs | Distribution yield, price / NAV, aggregate leverage (MAS cap 50%), interest coverage ratio (MAS minimum 1.5x, managers must disclose plans if below 1.8x), all-in cost of debt, % of debt fixed, weighted average debt maturity, WALE, occupancy, rental reversion, tenant concentration, NPI margin, sponsor pipeline. REITs must distribute at least 90% of taxable income to keep tax transparency. Check whether distributions are propped up by one-off divestment gains or capital distributions |
| US REITs | FFO and AFFO per share, P/FFO, net debt / EBITDA, same-store NOI growth, occupancy, lease expiry profile |
| Insurers | Combined ratio (below 100% means underwriting profit for P&C), solvency or capital ratio, P/B, P/embedded value, value of new business, reserve development |
| Software and SaaS | ARR growth, net revenue retention (above 120% excellent, below 100% means the base shrinks, convention), gross revenue retention (above 90% good for enterprise, convention), Rule of 40, CAC payback, magic number (above 0.75 generally efficient, convention), EV / ARR, RPO growth |
| Semiconductors | Book-to-bill, customer inventory days, utilisation, cycle position, capex intensity, customer concentration |
| Energy and resources | Breakeven commodity price, reserve life, position on the cost curve, normalised earnings at mid-cycle prices, P / NAV |
| Utilities | Rate base growth, allowed ROE, regulatory relationship, capex plan funding |
| Consumer and retail | Same-store sales split into traffic and ticket, inventory turns, sales per square foot, e-commerce mix, gross margin vs promotions |
| Platforms and internet | DAU / MAU, engagement time, ARPU, take rate, GMV growth |
| Industrials | Backlog, book-to-bill, organic growth, incremental margins, aftermarket revenue share |
| Pharma | Patent cliff schedule, pipeline, revenue concentration in top drugs |
| Biotech | Cash runway, risk-adjusted pipeline value (rNPV), trial readout dates, dilution history |

---

## Gate 9: Is something quietly breaking?

A company can look fine on the headline numbers while the base erodes. These signals usually show up one to four quarters before the headline numbers turn. Two or more firing in consecutive quarters means the thesis needs re-underwriting.

### Customers

| Signal | Where to find it | What it means |
|---|---|---|
| Net revenue retention falling | Earnings releases, investor decks | Existing customers spending less |
| Gross retention falling, churn rising | Same | Customers leaving |
| Customer count flat while revenue grows on price | Segment KPIs | Growth depends on price, not demand |
| Engagement falling (DAU/MAU, hours per member, usage) | KPIs, third-party data | Product losing relevance |
| Rising customer concentration | 10-K customer disclosure | Growing dependence on a few buyers |
| Deferred revenue, RPO or backlog growing slower than revenue | Balance sheet, notes | Future revenue slowing |
| Book-to-bill below 1 for several quarters | Industrials, semis | Orders not replacing shipments |

### Margins

| Signal | What it means |
|---|---|
| Gross margin falling while revenue rises | Discounting, worse mix or input costs |
| Sales and marketing rising as % of revenue to hold growth | Customer acquisition getting more expensive |
| Longer payment terms, more promotions | Buying revenue |
| Core segment profit falling while total revenue grows | Bigger but weaker |

### Cash

| Signal | What it means |
|---|---|
| FCF falling while earnings rise | Earnings quality deteriorating |
| Capex rising faster than operating cash flow | Self-funding capacity shrinking |
| DSO rising, inventory rising faster than sales | Working capital stress |
| Debt rising to fund dividends or buybacks | Shareholder returns not covered by the business |

### Disclosure

| Signal | What it means |
|---|---|
| Company stops reporting a KPI or redefines segments | The metric turned bad |
| "Adjusted" definitions change | Moving the goalposts |
| Guidance withdrawn, widened, or shifted to longer-term targets | Low visibility |
| Consensus EPS revisions trending down for 2+ quarters | The street is losing confidence |
| More hedging and fewer numbers on earnings calls | Management is less sure |

### People

| Signal | What it means |
|---|---|
| CFO or senior finance departure | Possible disagreement over numbers |
| Auditor change | Possible accounting dispute |
| Cluster insider selling outside 10b5-1 plans | Insiders reducing exposure |
| Layoffs in core product teams, hiring freeze, falling employee ratings | Internal stress |

### Competition and market signals

| Signal | What it means |
|---|---|
| Market share loss in third-party data | Competitors winning |
| New entrant pricing well below incumbent | Price war risk |
| Credit spreads or CDS widening before the stock reacts | Bond market sees risk first |
| Rating outlook moved to negative | Downgrade risk |
| Short interest rising | Informed sellers building positions |
| Stock falls on good news | Distribution, holders using strength to exit |
| Stock underperforming its own sector for months | Company-specific problem |

---

## Gate 10: Technical analysis

Fundamentals decide what to buy. Technicals help decide when to buy and where you are wrong. Never let a chart override Gates 0 to 9.

### 10.1 Trend

- Price vs 50-day and 200-day simple moving averages. Price above a rising 200-day is a long-term uptrend.
- Golden cross: 50-day crosses above 200-day. Death cross: 50-day crosses below 200-day. Both lag price.
- Uptrend: higher highs and higher lows. Downtrend: lower highs and lower lows.
- Weinstein stage analysis using the 30-week moving average (about 150 trading days):

| Stage | Price action | 30-week MA | Action for long-term buyers |
|---|---|---|---|
| 1 Basing | Sideways after a decline | Flattening | Watch, start building late in the stage |
| 2 Advancing | Higher highs, above the MA | Rising | Preferred buy zone, especially on pullbacks |
| 3 Topping | Choppy, failing at highs | Flattening | Tighten risk, do not add |
| 4 Declining | Lower lows, below the MA | Falling | Avoid. Wait for a new Stage 1 |

- ADX (14): above 25 means a trending market, below 20 means weak or no trend.
- Multi-timeframe check: weekly chart sets the trend, daily chart sets the entry.

### 10.2 Momentum

- RSI (14) = 100 - 100 / (1 + RS), where RS = average gain / average loss over 14 periods (Wilder smoothing). Above 70 overbought, below 30 oversold. In strong uptrends RSI tends to hold a 40 to 80 range, in downtrends a 20 to 60 range. Divergence between price and RSI is a warning.
- MACD (12, 26, 9): MACD line = 12-period EMA - 26-period EMA. Signal line = 9-period EMA of the MACD line. Histogram = MACD - signal. Watch crossovers, the zero line and divergences.
- Stochastic (14, 3, 3): above 80 overbought, below 20 oversold. Best in ranging markets.
- Rate of change: % change over N periods.
- Relative strength line: stock price / index price (and / sector ETF price). A rising line means the stock is leading. Not the same thing as RSI.

### 10.3 Volatility

- ATR (14): average of the true range over 14 periods. True range = the largest of (high - low), absolute value of (high - previous close), absolute value of (low - previous close). Stops are often set 2 to 3 ATR below entry (convention).
- Bollinger Bands (20, 2): 20-period SMA plus and minus 2 standard deviations. A squeeze (narrow bands) often comes before a big move.
- Beta: sensitivity to the market. Above 1 moves more than the index.
- Historical vs implied volatility. IV rank = (current IV - 52-week low IV) / (52-week high IV - 52-week low IV) × 100.

### 10.4 Volume

- Breakouts should come on volume well above average. Many traders look for at least 40% to 50% above the 50-day average (convention).
- Up days on heavier volume than down days means accumulation.
- On-balance volume (OBV): running total that adds volume on up days and subtracts it on down days. Rising OBV with flat price can lead a breakout.
- Accumulation / distribution line.
- VWAP and anchored VWAP. Anchor to the last earnings date or a major low to see the average cost of recent buyers.
- Volume profile: high-volume nodes act as support and resistance. Price moves quickly through low-volume nodes.

### 10.5 Support and resistance toolkit

| Method | How it works |
|---|---|
| Swing highs and lows | Prior turning points where buyers or sellers stepped in |
| Moving average clusters | 20, 50, 100 and 200-day averages bunched together |
| Volume shelves | Price levels where heavy volume traded |
| Fibonacci retracements | 23.6%, 38.2%, 50%, 61.8% and 78.6% of the major swing. 50% is not a Fibonacci ratio but traders watch it. Extensions at 127.2% and 161.8% |
| Classic pivot points | Pivot P = (High + Low + Close) / 3. R1 = 2P - Low. S1 = 2P - High. R2 = P + (High - Low). S2 = P - (High - Low). R3 = High + 2(P - Low). S3 = Low - 2(High - P) |
| Round numbers and big option strikes | Psychological levels and strikes with heavy open interest |
| Gaps | Earnings gaps often get retested |
| Prior breakout level | Old resistance often becomes new support |
| Trendlines and channels | Need at least three touches to be meaningful |

Rules:
- Support is a zone, not a single price.
- Three or more methods pointing to the same zone makes it strong. One method alone is weak.
- A daily close below the zone on above-average volume means the support broke.
- After a break, old support often becomes resistance on the retest.

### 10.6 Chart patterns

- Bullish: cup with handle, flat base, ascending triangle, bull flag, double bottom, inverse head and shoulders, breakout from a long base.
- Bearish: head and shoulders top, double top, descending triangle, breakdown from a rising wedge, failed breakout.
- Patterns confirm on a close beyond the trigger level with volume. Before that, they are possibilities.

### 10.7 Market context

- Index trend: S&P 500 and STI vs their 200-day averages.
- Breadth: % of index members above their 200-day averages. A rising index with falling breadth is narrow and fragile.
- VIX level and direction.
- Sector leadership: is the stock's sector leading or lagging?

### 10.8 Technical pass criteria for a long-term buy

- Not in Stage 4.
- Either above a rising 200-day average, or in a clear base with a defined support zone and an improving relative strength line.
- Entry near a confluence support zone with a stop below it, so risk per share is known before you buy.

---

## Gate 11: Sentiment and positioning

- Earnings estimate revisions: direction matters more than level. Rising estimates support the price. Falling estimates erode it.
- Earnings surprise history: beats, misses and size of surprise over 8 quarters.
- Post-earnings drift: stocks tend to keep drifting in the direction of a large earnings surprise for weeks.
- Analyst ratings distribution: when nearly everyone rates it Buy, upgrades can no longer push it higher. Wide dispersion in price targets means high uncertainty.
- Short interest as % of float: above 10% elevated, above 20% high (convention). Days to cover = short interest / average daily volume. High short interest can mean informed bears or squeeze potential. Find out which.
- Institutional ownership changes from 13F filings, due 45 days after each quarter end. These are stale by the time you see them.
- Options market: put/call ratio, skew (puts priced richer than calls signals fear), implied vs historical volatility, unusual activity.
- Media and retail sentiment: euphoria near tops, despair near bottoms. Use as a contrarian check, not a signal on its own.

---

## Gate 12: Macro and market regime

| Factor | What to check | Why it matters |
|---|---|---|
| Interest rates | 10-year government yield, real yield (10-year TIPS), central bank path (CME FedWatch), 2s10s curve | Higher real yields compress valuations of long-duration growth stocks |
| Equity risk premium proxy | Index forward earnings yield - 10-year yield | Near zero means little reward for owning stocks over bonds |
| Inflation | CPI, PCE | Drives rates and margins |
| Growth | GDP, PMI (above 50 expansion, below 50 contraction) | Drives cyclical earnings |
| Labour | Payrolls, unemployment, jobless claims | Leads consumer spending |
| Credit | High-yield spreads (OAS) | Widening spreads often lead equity weakness |
| Currency | USD index, SGD/USD | Affects multinationals' reported earnings and your SGD returns |
| Commodities | Oil, copper | Input costs and inflation |

Typical sector pattern across the business cycle (a tendency, not a rule):
- Early cycle: financials, consumer discretionary, industrials, small caps.
- Mid cycle: technology, industrials.
- Late cycle: energy, materials, consumer staples.
- Recession: consumer staples, utilities, healthcare.

Singapore specifics:
- MAS manages monetary policy through the SGD exchange rate (S$NEER), not an interest rate.
- SORA drives SGD floating borrowing costs for S-REITs and banks.
- SGS bond yields and T-bill yields set the SGD risk-free hurdle.

---

## Gate 13: Risk register

Rate each risk by likelihood (low, medium, high) and impact (low, medium, high).

| Risk | Likelihood | Impact | Notes |
|---|---|---|---|
| Business model or demand | | | |
| Competitive | | | |
| Technological disruption | | | |
| Regulatory and legal | | | |
| Financial leverage and refinancing | | | |
| Currency | | | |
| Geopolitical and supply chain | | | |
| Concentration (customer, supplier, product, geography) | | | |
| Key person | | | |
| ESG and reputational | | | |
| Valuation (multiple compression) | | | |
| Liquidity of the stock | | | |
| Tail risk (fraud, war, pandemic, single-event wipeout) | | | |

Three exercises before every buy:
1. Pre-mortem: assume the stock is down 50% in two years. Write the most likely reasons.
2. Steelman the bear case in five bullet points. If you cannot write it, you do not understand the stock yet.
3. Drawdown check: what was the stock's largest historical drawdown and how long did recovery take? Can you hold through a repeat without selling at the bottom?

---

## Gate 14: Catalysts and calendar

List every date that can move the stock in your holding window:

- Next earnings date and the one after.
- Investor day, product launches, trial readouts.
- Regulatory rulings, court dates, antitrust decisions.
- Index inclusion or exclusion.
- Spin-offs, mergers, asset sales.
- Buyback authorisations, dividend declarations and ex-dividend dates.
- IPO lockup expiries.
- Major debt maturities.
- Patent expiries and large contract renewals.
- Macro dates: FOMC, CPI, payrolls, MAS policy statements.

Without a catalyst, a cheap stock can stay cheap for years. Long-term holders do not need one, but catalysts help set timing and position size.

---

## Gate 15: Portfolio fit, sizing and entry

### Fit

- Correlation and factor overlap with existing holdings. Three AI-capex names are one bet, not three.
- Sector, country and currency exposure after adding the position.
- Time horizon: money needed within 3 to 5 years should not depend on single stocks (convention).
- Liquidity needs: can you hold through a 30% to 50% drawdown without being forced to sell?

### Position sizing

- Concentration limits (convention): 5% to 10% per stock at cost for a diversified portfolio. Concentrated investors go to 15% to 20% for top ideas and accept the volatility that comes with it.
- Risk-based sizing: shares = (portfolio value × risk per position %) / (entry price - stop price). Risk per position of 0.5% to 2% is common (convention).
- Kelly criterion: f = p - (1 - p) / b, where p = probability of a win and b = average win / average loss. Full Kelly is too aggressive because your inputs are estimates. Use half or quarter Kelly at most.

### Tax and structure (Singapore resident individual)

- No capital gains tax for individuals in general, unless IRAS treats your trading as a business, in which case gains can be taxed as income.
- US dividends: 30% withholding tax. Singapore has no income tax treaty with the US.
- US estate tax: non-resident aliens face US estate tax on US-situs assets (including US-listed shares) above a US$60,000 exemption.
- Ireland-domiciled UCITS ETFs that hold US stocks suffer 15% withholding at fund level and are generally not US-situs assets.
- SGX dividends under the one-tier system are tax-exempt in the hands of shareholders.
- Confirm current rules with IRAS and a tax professional before acting on large positions.

### Entry method A: direct purchase

- Limit orders at or just above a confluence support zone.
- Scale in, for example in thirds: first third at the first support zone, second on a successful retest or a confirmed breakout, third after the next earnings report confirms the thesis.
- Avoid full size right before binary events (earnings, FOMC, court rulings).
- Set the stop or the thesis-break price before the order goes in.

### Entry method B: cash-secured put

- Only sell puts on companies that passed Gates 0 to 9, at a strike where you would be happy to own the shares.
- Place the strike at or below a confluence support zone.
- Check for an earnings date before expiry. Selling through earnings collects more premium for a reason.
- Higher IV rank means more premium. Find out why IV is high before treating it as free money.
- Liquidity: tight bid-ask spread and decent open interest at your strike.
- Breakeven = strike - premium.
- Annualised yield on collateral = (premium / strike) × (365 / days to expiry).
- Delta is a rough market-implied estimate of the chance the option finishes in the money. It is an approximation, not a true probability.
- Worked example: $200 strike, $4.00 premium, 30 days to expiry. Breakeven $196. Annualised yield = (4 / 200) × (365 / 30) = 24.3%.
- Downside is the same as owning the stock, cushioned only by the premium. Maximum loss = strike - premium per share if the stock goes to zero.
- Assignment plan: if assigned, re-run Gate 9. If it still passes, hold or sell covered calls above your cost basis. If it fails, exit.

---

## Scorecard and rating

Score each category from 1 (worst) to 5 (best). Weights add to 100.

| # | Category | Weight | 5 looks like | 3 looks like | 1 looks like |
|---|---|---|---|---|---|
| 1 | Valuation | 15 | 30%+ below intrinsic value, FCF yield above the 10-year yield, multiple below history with an equal or better business | Near fair value, multiples near history | Priced for perfection, reverse DCF needs growth far above history |
| 2 | Growth prospects | 12 | Durable double-digit per-share growth, steady or accelerating | Mid-single-digit, stable | Shrinking, or decelerating fast without explanation |
| 3 | Profitability | 10 | ROIC above 20%, margins rising | ROIC a few points above WACC, margins flat | ROIC below WACC, margins falling |
| 4 | Financial strength | 12 | Net cash or below 1x net debt/EBITDA, coverage above 8x, F-score 8 to 9 | 1x to 3x, coverage 4x to 8x | Above 3x with a refinancing wall, coverage below 2x |
| 5 | Competitive moat | 12 | Wide and widening, ROIC above WACC for 10 years | Narrow or stable | None, or eroding |
| 6 | Management quality | 8 | Strong capital allocation record, high ownership, aligned pay | Mixed record | Value-destroying deals, heavy dilution, misaligned pay |
| 7 | Industry outlook | 8 | Growing market, rational competition | Mature and stable | Declining or being disrupted |
| 8 | Earnings quality and hidden breaks | 10 | Operating cash flow above net income, clean accounting, KPIs improving | Minor flags | Several Gate 9 signals firing |
| 9 | Risk factors (higher score = lower risk) | 8 | Few risks, manageable, diversified | Moderate | Concentrated, binary or existential |
| 10 | Technical trend | 5 | Stage 2, above a rising 200-day, RS line rising, at support | Basing or neutral | Stage 4, below a falling 200-day |
| | Total | 100 | | | |

Weighted score = sum of (weight × score) / 100. The result runs from 1.00 to 5.00.

### Rating map

| Weighted score | Rating |
|---|---|
| 4.20 to 5.00 | Strong Buy |
| 3.60 to 4.19 | Buy |
| 2.80 to 3.59 | Hold |
| 2.20 to 2.79 | Reduce |
| Below 2.20 | Sell |

### Overrides (apply after scoring)

1. Any Gate 0 kill switch: Sell or avoid, whatever the score.
2. Valuation scored 1 or 2: rating capped at Hold for new money. This blocks the great company at an expensive price.
3. Average of Moat and Profitability at 2 or below: rating capped at Hold. This blocks the bad company at a good price.
4. Earnings quality scored 1: rating capped at Reduce.
5. Expected return (Gate 8.4) below the index hurdle (Gate 8.5): rating capped at Hold.
6. Technical scored 1 (Stage 4): the rating stands, but delay or stage the entry until a base forms.

How to read the ratings:
- For new money, Hold means do not start a position.
- For an existing position, Reduce means trim and Sell means exit.

### Worked scoring example

Scores: Valuation 4, Growth 4, Profitability 5, Financial strength 4, Moat 5, Management 4, Industry 4, Earnings quality 4, Risk 3, Technical 3.

(15×4 + 12×4 + 10×5 + 12×4 + 12×5 + 8×4 + 8×4 + 10×4 + 8×3 + 5×3) / 100 = 409 / 100 = 4.09

Rating: Buy. No override applies. Raise Financial strength to 5 and the score becomes 4.21, which crosses into Strong Buy. One category point can move the rating, so be honest with every score.

---

## Sell discipline

Write the sell criteria before you buy.

Sell or trim when:
- The thesis is broken. The specific reason you bought is no longer true.
- A Gate 0 kill switch triggers.
- Price exceeds your bull-case value, or expected return falls below the hurdle.
- A clearly better risk-adjusted opportunity needs the capital.
- The position has grown beyond your size limit.
- Two or more Gate 9 signals fire in consecutive quarters and management cannot explain them.

Do not sell because:
- The price fell but the thesis holds and valuation improved. Re-underwrite and consider adding.
- You want to get back to breakeven. That is anchoring.
- One noisy quarter that does not change the long-term picture.

---

## Behavioural traps

- Anchoring to your purchase price or the past high.
- Confirmation bias. Read the bear case first, not last.
- Value traps. Cheap and getting cheaper because the fundamentals keep deteriorating.
- Catching a falling knife. Buying in Stage 4 with no base.
- Story stocks. A narrative without numbers.
- Recency bias. Assuming the last year repeats forever.
- Overconfidence after wins, revenge trades after losses.
- Sunk cost. Holding because of time or money already spent on the idea.
- Familiarity bias. Owning what you use instead of what is mispriced.
- Confusing a great company with a great stock.
- Treating adjusted EBITDA as cash.

---

## Data sources

US filings and data:
- SEC EDGAR: 10-K (annual), 10-Q (quarterly), 8-K (material events), DEF 14A (proxy, executive pay), Form 4 (insider trades), 13F (institutional holdings).
- Earnings call transcripts and investor presentations on company IR sites.
- FRED for macro data, US Treasury for the yield curve, CME FedWatch for rate expectations.

Singapore:
- SGXNet for announcements, results, director and substantial shareholder dealings.
- Company annual reports and results presentations.
- MAS for SORA, monetary policy statements and REIT rules.
- MAS / SGS website for SGS bond and T-bill yields.

Screeners and platforms:
- Morningstar, Koyfin, TIKR, Finviz, TradingView, stockanalysis.com, Macrotrends, GuruFocus.
- IBKR for options chains, IV and fundamentals. POEMS for SGX execution.

Rule: trace every number that drives the decision back to the original filing.

---

## Quick checklist

Gate 0
- [ ] No kill switch triggered

Is it a good business getting stronger?
- [ ] I can explain how it makes money in two sentences
- [ ] Moat identified and verified with numbers
- [ ] ROIC above WACC for most of the last 10 years
- [ ] Margins stable or rising
- [ ] Per-share growth, not just total growth
- [ ] Share count flat or falling net of SBC
- [ ] Growth deceleration explained, if any
- [ ] Balance sheet passes (net debt/EBITDA, coverage, maturities)
- [ ] Altman Z and Piotroski F-score acceptable
- [ ] Operating cash flow at or above net income over time
- [ ] Beneish M-score below -1.78 (growth-neutral)
- [ ] Management capital allocation record is good
- [ ] Insiders aligned

Is the price fair?
- [ ] Below own 5 and 10-year median multiples, or premium justified
- [ ] Fair vs true peers
- [ ] DCF and reverse DCF done, implied growth is achievable
- [ ] FCF yield vs 10-year yield checked
- [ ] Expected return beats the index hurdle
- [ ] Upside / downside at least 2 to 1
- [ ] Margin of safety present
- [ ] Cyclical earnings normalised, if relevant

Is something quietly breaking?
- [ ] Retention, churn and engagement stable or improving
- [ ] Deferred revenue, RPO or backlog keeping pace with revenue
- [ ] No KPI dropped or redefined
- [ ] Estimate revisions not trending down
- [ ] No CFO or auditor exit
- [ ] Credit signals calm

Timing and fit
- [ ] Not in Stage 4
- [ ] Entry at a confluence support zone with a known stop
- [ ] No binary event before full size is in
- [ ] Position size within limits
- [ ] Correlation with existing holdings checked
- [ ] Sell criteria written down

---

## Ticker analysis template

Copy this block for each company.

```
Ticker:
Date of analysis:
Price at analysis:
Analyst (me) confidence: low / medium / high

GATE 0 KILL SWITCHES
Any triggered? (Y/N, which):

BUSINESS IN TWO SENTENCES

MOAT
Type:
Evidence (numbers):
Direction: widening / stable / narrowing

STRONGER VS BIGGER (5 and 10-year trend)
Revenue CAGR:
Latest 8 quarters YoY growth:
Gross margin trend:
Operating margin trend:
ROIC trend:
FCF per share CAGR:
Diluted share count change:
SBC % of revenue:
Verdict: stronger / just bigger / weakening

PROFITABILITY
ROIC vs WACC:
ROE (DuPont split):
FCF margin:

FINANCIAL STRENGTH
Net debt / EBITDA:
Interest coverage:
Debt due in 24 months vs cash + FCF:
Altman Z:
Piotroski F:

EARNINGS QUALITY
CFO / net income (3-year average):
Accruals ratio:
DSO / DIO trend:
GAAP vs non-GAAP gap:
Beneish M:

MANAGEMENT
Capital allocation grade:
Insider ownership and recent trades:
Pay metrics:

VALUATION
Trailing P/E | 5-year median:
Forward P/E:
EV / EBIT:
FCF yield vs 10-year yield:
PEG:
DCF value (base):
Reverse DCF implied growth:
Bull / base / bear values and probabilities:
Probability-weighted value:
Expected annual return:
Beats index hurdle? (Y/N):

QUIET BREAKAGE SIGNALS FIRING
List:

TECHNICALS
Stage (1 to 4):
Price vs 50 / 200-day:
RSI / MACD read:
Support zones (S1, S2, S3) and methods agreeing:
Resistance zones:

SENTIMENT
Estimate revision direction:
Short interest % float:

MACRO SENSITIVITY

TOP 5 RISKS

BEAR CASE IN 5 BULLETS

CATALYSTS AND DATES

SCORECARD
Valuation (15):
Growth (12):
Profitability (10):
Financial strength (12):
Moat (12):
Management (8):
Industry (8):
Earnings quality (10):
Risk (8):
Technical (5):
Weighted score:
Overrides applied:
FINAL RATING:

ENTRY PLAN
Method (direct / CSP):
Entry zone:
Position size:
Stop or thesis-break price:

SELL CRITERIA (written before buying)
```

---

Not financial advice. This framework improves the odds of a good decision. It cannot guarantee one. Thresholds marked (convention) are practitioner rules of thumb, and every number should be checked against the source filing before money moves.
