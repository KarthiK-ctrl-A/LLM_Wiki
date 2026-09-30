# Property & Casualty Insurance — Source Corpus Manifest

**Domain:** Property & Casualty (P&C) Insurance  
**Purpose:** Starter corpus for a Database-Driven LLM Wiki / RAG wiki project.  
**Suggested corpus size:** Start with 35–40 sources below, then trim or expand to 50–100 later.  
**Best storage format:** Save each source as `.pdf`, `.md`, or `.txt` inside `data/sources/property_casualty_insurance/`.

## Why this domain works well for an LLM Wiki

Property & Casualty insurance has many naturally connected concepts: underwriting, premiums, claims, loss ratio, reinsurance, homeowners insurance, auto liability, flood insurance, cyber insurance, catastrophe risk, deductibles, actual cash value, replacement cost, market share, profitability, regulation, and consumer protection. These repeated entities and terms make it a strong domain for semantic search and wiki page generation.

## Recommended folder structure

```text
llm_wiki/
└── data/
    └── sources/
        └── property_casualty_insurance/
            ├── naic/
            ├── fema_nfip/
            ├── triple_i/
            ├── regulators/
            └── reinsurance/
```

## Download approach

For direct PDFs, open the link in your browser and save the file, or use:

```bash
curl -L "PDF_URL_HERE" -o "filename.pdf"
```

For HTML pages, open the page and either:

```bash
# Option 1: Save as HTML
curl -L "PAGE_URL_HERE" -o "filename.html"

# Option 2: Convert to Markdown using pandoc if installed
pandoc "filename.html" -t markdown -o "filename.md"
```

For pages with a visible **Download Resource** or **Download PDF** button, open the page and click the download button.

---

# Source List

## A. NAIC — Industry, Market, Profitability, Regulation

| # | Title | Source | Type | Why useful for wiki | Link / Download |
|---:|---|---|---|---|---|
| 1 | U.S. Property & Casualty and Title Insurance Industries — 2024 Full Year Results | NAIC | PDF | Industry-level P&C financial results, underwriting results, surplus, trends | https://content.naic.org/sites/default/files/2024-annual-property-casualty-and-title-insurance-industries-analysis-report.pdf |
| 2 | Property & Casualty Insurance Industry — 2021 | NAIC | PDF | Historical P&C industry analysis useful for trend comparison | https://content.naic.org/sites/default/files/industry-analysis-report-2021-property-casualty.pdf |
| 3 | Property & Casualty Insurance Industry — 2020 | NAIC | PDF | Earlier P&C market snapshot and financial analysis | https://content.naic.org/sites/default/files/industry-analysis-report-2020-property-casualty.pdf |
| 4 | 2024 Year-End Snapshot | NAIC | PDF | Snapshot of insurance industry financial metrics | https://content.naic.org/sites/default/files/2024-year-end-snapshot.pdf |
| 5 | 2024 Market Share Reports for Property/Casualty Groups and Companies | NAIC | PDF | Market concentration, top writers, premium by group/company | https://content.naic.org/sites/default/files/publication-msr-pb-property-casualty.pdf |
| 6 | Property and Casualty Insurance Industry — 2025 Top 25 Groups and Companies by Countrywide Premium | NAIC | PDF | Market-share and competitive landscape data | https://content.naic.org/sites/default/files/research-actuarial-property-casualty-market-share.pdf |
| 7 | 2022/2023 Auto Insurance Database Report | NAIC | PDF | Auto premiums, losses, claims, state-level statistics | https://content.naic.org/sites/default/files/publication-aut-pb-auto-insurance-database.pdf |
| 8 | 2023 Auto Insurance Database Average Premium Supplement | NAIC | PDF | Auto insurance average premium/expenditure supplement | https://content.naic.org/sites/default/files/aut-db_1.pdf |
| 9 | 2022 Auto Insurance Database Average Premium Supplement | NAIC | PDF | Auto premium trend data | https://content.naic.org/sites/default/files/aut-db.pdf |
| 10 | 2022 Homeowners Report | NAIC | PDF | Homeowners premium and exposure data by state and policy form | https://content.naic.org/sites/default/files/publication-hmr-zu-homeowners-report.pdf |
| 11 | Report on Profitability by Line by State in 2023 | NAIC | PDF | Profitability by insurance line and state | https://content.naic.org/sites/default/files/publication-pbl-pb-profitability-line-state.pdf |
| 12 | 2023 Competition Database Report | NAIC | PDF | Competition and market concentration metrics | https://content.naic.org/sites/default/files/publication-cdr-im-competition-database-report.pdf |
| 13 | Statistical Handbook | NAIC | PDF | Structural and performance measures across insurance markets | https://content.naic.org/sites/default/files/publications-sta-zu-statistical-handbook.pdf |
| 14 | A Consumer’s Guide to Home Insurance | NAIC | PDF | Consumer-level explanation of homeowners insurance coverages | https://content.naic.org/sites/default/files/publication-hoi-pp-consumer-homeowners.pdf |
| 15 | Use of Credit Reports / Scoring in Underwriting | NAIC | PDF | Insurance scoring, underwriting, and regulatory treatment | https://content.naic.org/sites/default/files/model-law-chart-mc-20-use-of-credit-reports-scoring-in-underwriting.pdf |
| 16 | Homeowners Market Data Call — Proposed Revisions Summary | NAIC | PDF | Homeowners market data collection, regulation, and availability issues | https://content.naic.org/sites/default/files/inline-files/Homeowners%20Market%20Data%20Call%20%28C%29%20Task%20Force%20-%20Proposed%20Revisions%20Summary_Exposure.pdf |
| 17 | Insurance Industry Snapshots and Analysis Reports | NAIC | HTML | Landing page for P&C and insurance industry reports | https://content.naic.org/industry/insurance-industry-snapshots-analysis-reports |
| 18 | Research and Statistical Reports | NAIC | HTML | Catalog of NAIC reports: auto, homeowners, profitability, market share | https://content.naic.org/newsroom_statistical_reports.htm |
| 19 | InsData | NAIC | HTML | Data and reports on U.S. insurance industry | https://content.naic.org/industry/insdata |
| 20 | Model Laws | NAIC | HTML | Regulatory model laws and guidelines | https://content.naic.org/model-laws |

## B. FEMA / NFIP — Flood Insurance, Claims, Manuals

| # | Title | Source | Type | Why useful for wiki | Link / Download |
|---:|---|---|---|---|---|
| 21 | October 2025 NFIP Flood Insurance Manual | FEMA | PDF | Flood underwriting, rating, servicing, and policy guidance | https://www.fema.gov/sites/default/files/documents/fema_rsl_national-flood-insurance-manual_06032025.pdf |
| 22 | Current Flood Insurance Manuals | FEMA | HTML | Current NFIP manual landing page | https://www.fema.gov/flood-insurance/work-with-nfip/manuals/current |
| 23 | Flood Insurance Manuals and Handbooks | FEMA | HTML | Manual and handbook index | https://www.fema.gov/flood-insurance/work-with-nfip/manuals |
| 24 | June 2023 NFIP Claims Manual | FEMA | PDF | Claims lifecycle, adjuster guidance, claim handling | https://www.fema.gov/sites/default/files/documents/fema_nfip-claims-manual_062023.pdf |
| 25 | NFIP Claims Handbook | FloodSmart / FEMA | PDF | Policyholder claims process and recovery guidance | https://agents.floodsmart.gov/sites/default/files/media/document/2025-07/fema-nfip-claims-handbook-08-2024.pdf |
| 26 | Flood Insurance Manual — Current Editions | FloodSmart / FEMA | HTML | Agent/insurer manual download page | https://agents.floodsmart.gov/manuals |
| 27 | Flood Insurance Manual — Effective April 1, 2020 | FEMA | HTML | Historical manual useful for policy/rating changes | https://www.fema.gov/flood-insurance/work-with-nfip/manuals/april-2020 |
| 28 | Flood Insurance Manuals Archive: 2005–2021 | FEMA | HTML | Older flood manual archive for versioned corpus | https://www.fema.gov/flood-insurance/work-with-nfip/manuals/archive |

## C. Insurance Information Institute / Triple-I — Market, Homeowners, Cyber, Auto Liability

| # | Title | Source | Type | Why useful for wiki | Link / Download |
|---:|---|---|---|---|---|
| 29 | Insurance Handbook | Triple-I | PDF | Broad insurance glossary and product explanations | https://www.iii.org/sites/default/files/docs/pdf/Insurance_Handbook_20103.pdf |
| 30 | 2020 Insurance Fact Book | Triple-I | PDF | Industry statistics, emerging risks, homeowners high-risk market | https://www.iii.org/sites/default/files/docs/pdf/insurance_factbook_2020.pdf |
| 31 | Homebuyers Insurance Handbook | Triple-I | PDF | Homeowners insurance basics, covered and excluded perils | https://www.iii.org/sites/default/files/docs/pdf/2023_triple-i_homeowners_insurance_handbook.pdf |
| 32 | HO-3 Sample Homeowners Policy — Special Form | Triple-I / ISO sample | PDF | Policy language, definitions, coverage structure | https://www.iii.org/sites/default/files/docs/pdf/HO3_sample.pdf |
| 33 | Homeowners Insurance: Understanding, Attitudes and Shopping Practices | Triple-I | PDF | Consumer understanding of coverage, flood confusion, shopping behavior | https://www.iii.org/sites/default/files/docs/pdf/pulse-wp-020217-final.pdf |
| 34 | What Homeowners, Renters and Drivers Know — and Ought to Know | Triple-I | PDF | Consumer knowledge of deductibles, replacement cost, ACV, ALE | https://www.iii.org/sites/default/files/docs/pdf/pulse-wp-112415-8-final.pdf |
| 35 | Am I Covered? | Triple-I | PDF | Consumer-focused coverage explanation | https://www.iii.org/sites/default/files/docs/pdf/AmICovered.pdf |
| 36 | Homeowners Perception of Weather Risks | Triple-I | PDF | Weather risk awareness, flood risk, homeowners insurance gaps | https://www.iii.org/sites/default/files/docs/pdf/2023_q2_ho_perception_of_weather_risks.pdf |
| 37 | Trends and Insights: Homeowners Insurance Rates | Triple-I | PDF | Premium affordability, replacement costs, catastrophe pricing | https://www.iii.org/sites/default/files/docs/pdf/triple-i_trends_and_insights_homeowners_insurance_rates_07092024.pdf |
| 38 | Trends and Insights: Homeowners Insurance | Triple-I | PDF | Homeowners line performance and P&C premium contribution | https://www.iii.org/sites/default/files/docs/pdf/triple-i_trends_and_insights_homeowners_insurance_12152025.pdf |
| 39 | Short-Term Rentals and Homeowners Insurance | Triple-I | PDF | Commercial-use exclusions, personal vs commercial insurance | https://www.iii.org/sites/default/files/docs/pdf/short-term_rentals_and_homeowners_insurance_outlook_03092026.pdf |
| 40 | Impact of Increasing Inflation on Personal and Commercial Auto Liability Insurance | Triple-I | PDF | Loss development, inflation, auto liability trends | https://www.iii.org/sites/default/files/docs/pdf/triple-i_auto_inflation_trends_2023.pdf |
| 41 | Social Inflation and Loss Development | Triple-I | PDF | Social inflation, commercial auto liability, casualty claims | https://www.iii.org/sites/default/files/docs/pdf/social_inflation_loss_development_wp_02082022.pdf |
| 42 | Cyber Insurance: State of the Risk | Triple-I | PDF | Cyber insurance market, coverage, reinsurance support | https://www.iii.org/sites/default/files/docs/pdf/triple-i_state_of_the_risk_cyber_02062024.pdf |
| 43 | Cyber: State of the Risk | Triple-I | PDF | Earlier cyber insurance market and claims context | https://www.iii.org/sites/default/files/docs/pdf/triple-i_state_of_the_risk_cyber_10142021.pdf |
| 44 | Small Business and Cyber Insurance | Triple-I | PDF | SMB cyber risk, coverage demand, claims costs | https://www.iii.org/sites/default/files/docs/pdf/cyber_risk_wp_103017.pdf |
| 45 | Smaller Doesn’t Mean Safer | Triple-I | PDF | SMB cyber risk and cyber insurance adoption | https://www.iii.org/sites/default/files/docs/pdf/small_business_cyber_wp_102319.pdf |
| 46 | Small Business, Big Risk | Triple-I | PDF | Lack of cyber insurance among small businesses | https://www.iii.org/sites/default/files/docs/pdf/small_business_big_risk_101218.pdf |
| 47 | Addressing the Personal Cyber Protection Gap | Triple-I | PDF | Personal cyber coverage and homeowners-related cyber protection | https://www.iii.org/sites/default/files/docs/pdf/personal_cyber_protection_gap_03252025.pdf |
| 48 | Helping Consumers Understand the Value of Cyber Insurance | Triple-I | PDF | Consumer cyber coverage awareness | https://www.iii.org/sites/default/files/docs/pdf/cyber_survey_092718.pdf |
| 49 | Consumer Indifference Is Still a Challenge for Personal Cyber | Triple-I | PDF | Personal cyber coverage awareness and adoption | https://www.iii.org/sites/default/files/docs/pdf/consumers_wp_030920.pdf |
| 50 | Cyber Risk Infographic | Triple-I | PDF | Short visual source for cyber risk terms and market stats | https://www.iii.org/sites/default/files/docs/pdf/cyber_risk_infographic_102616_4.pdf |

## D. State Regulators and Consumer Guides

| # | Title | Source | Type | Why useful for wiki | Link / Download |
|---:|---|---|---|---|---|
| 51 | Commercial Insurance Guide | California Department of Insurance | PDF | Commercial property and casualty explanations | https://www.insurance.ca.gov/01-consumers/105-type/95-guides/09-comm/upload/Commercial-Insurance-Updated-090623.pdf |
| 52 | Glossary of Insurance Terms | California Department of Insurance | HTML | Definitions: liability, property damage, binder, premium, quote | https://www.insurance.ca.gov/01-consumers/105-type/95-guides/20-Glossary/ |
| 53 | Homeowners Insurance | North Carolina Department of Insurance | HTML | Homeowners coverage overview | https://www.ncdoi.gov/consumers/homeowners-insurance |
| 54 | Basic Homeowners Insurance | North Carolina Department of Insurance | HTML | Coverage sections, excluded perils, liability coverages | https://www.ncdoi.gov/consumers/homeowners-insurance/basic-homeowners-insurance |
| 55 | Actual Cash Value vs Replacement Cost Value | North Carolina Department of Insurance | HTML | Key claims valuation concept | https://www.ncdoi.gov/consumers/homeowners-insurance/actual-cash-value-vs-replacement-cost-value |
| 56 | Dwelling Policies | North Carolina Department of Insurance | HTML | Dwelling fire policies, rental/vacant/seasonal homes | https://www.ncdoi.gov/consumers/homeowners-insurance/dwelling-policies |
| 57 | Windstorm and Hail | North Carolina Department of Insurance | HTML | Coastal risk, wind/hail coverage, residual market | https://www.ncdoi.gov/consumers/homeowners-insurance/windstorm-and-hail |
| 58 | Changes to Rating of Automobile Insurance Policies Effective July 1, 2025 | North Carolina Department of Insurance | HTML | Auto liability limits and underinsured motorist changes | https://www.ncdoi.gov/changes-rating-automobile-insurance-policies-effective-july-1-2025 |
| 59 | Safe Driver Incentive Plan | North Carolina Department of Insurance | HTML | Auto rating, points, at-fault accidents, experience period | https://www.ncdoi.gov/consumers/auto-and-vehicle-insurance/safe-driver-incentive-plan |
| 60 | Department of Insurance Brochures and Publications | North Carolina Department of Insurance | HTML | Publication landing page for auto/homeowners/business docs | https://www.ncdoi.gov/documents-publications |

## E. Reinsurance and Risk Transfer

| # | Title | Source | Type | Why useful for wiki | Link / Download |
|---:|---|---|---|---|---|
| 61 | What Is Reinsurance? | Reinsurance Association of America | HTML | Reinsurance basics and insurer risk transfer | https://www.reinsurance.org/RAA/RAA/About-the-RAA/what-is-reinsurance.aspx |
| 62 | Purposes of Reinsurance | Reinsurance Association of America | HTML | Capacity, catastrophe protection, stabilization, limiting liability | https://www.reinsurance.org/RAA/RAA/About-the-RAA/Fundamentals/Purposes%20of%20Reinsurance.aspx |
| 63 | Reinsurance Definition, Types, and How It Works | Investopedia | HTML | Simple explainer for reinsurance concepts | https://www.investopedia.com/terms/r/reinsurance.asp |

---

# Suggested first 25 files to download

If you want a smaller first corpus, start with these because they cover the domain end-to-end:

1. NAIC 2024 Annual P&C and Title Industry Analysis Report
2. NAIC 2024 Market Share Reports for P&C Groups and Companies
3. NAIC 2022/2023 Auto Insurance Database Report
4. NAIC 2022 Homeowners Report
5. NAIC Report on Profitability by Line by State in 2023
6. NAIC Consumer’s Guide to Home Insurance
7. NAIC Use of Credit Reports / Scoring in Underwriting
8. FEMA October 2025 NFIP Flood Insurance Manual
9. FEMA June 2023 NFIP Claims Manual
10. FEMA NFIP Claims Handbook
11. Triple-I Insurance Handbook
12. Triple-I 2020 Insurance Fact Book
13. Triple-I Homebuyers Insurance Handbook
14. Triple-I HO-3 Sample Homeowners Policy
15. Triple-I Homeowners Insurance Rates
16. Triple-I Homeowners Insurance Trends and Insights
17. Triple-I Short-Term Rentals and Homeowners Insurance
18. Triple-I Social Inflation and Loss Development
19. Triple-I Impact of Inflation on Auto Liability Insurance
20. Triple-I Cyber Insurance: State of the Risk 2024
21. California DOI Commercial Insurance Guide
22. California DOI Glossary of Insurance Terms
23. NC DOI Basic Homeowners Insurance
24. NC DOI Actual Cash Value vs Replacement Cost Value
25. RAA What Is Reinsurance?

---

# Suggested wiki pages your LLM can generate from this corpus

Use your LLM provider to generate pages like these:

- Property and Casualty Insurance
- Homeowners Insurance
- Auto Liability Insurance
- Commercial Property Insurance
- Commercial Casualty Insurance
- Flood Insurance
- NFIP
- Claims Handling
- Underwriting
- Premium
- Deductible
- Actual Cash Value
- Replacement Cost Value
- Loss Ratio
- Combined Ratio
- Reinsurance
- Catastrophe Risk
- Social Inflation
- Insurance Scoring
- Market Share
- Profitability by Line
- Cyber Insurance
- Short-Term Rental Insurance
- Windstorm and Hail Coverage
- Residual Markets
- Consumer Insurance Regulation

---

# Simple downloader script template

Create a file called `download_pdfs.py` and add only the direct PDF URLs you want to download.

```python
import os
import requests
from urllib.parse import urlparse

OUTPUT_DIR = "data/sources/property_casualty_insurance/pdfs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

pdf_urls = [
    "https://content.naic.org/sites/default/files/2024-annual-property-casualty-and-title-insurance-industries-analysis-report.pdf",
    "https://content.naic.org/sites/default/files/publication-msr-pb-property-casualty.pdf",
    "https://content.naic.org/sites/default/files/publication-aut-pb-auto-insurance-database.pdf",
    "https://content.naic.org/sites/default/files/publication-hmr-zu-homeowners-report.pdf",
    "https://www.fema.gov/sites/default/files/documents/fema_rsl_national-flood-insurance-manual_06032025.pdf",
    "https://www.fema.gov/sites/default/files/documents/fema_nfip-claims-manual_062023.pdf",
    "https://www.iii.org/sites/default/files/docs/pdf/Insurance_Handbook_20103.pdf",
    "https://www.iii.org/sites/default/files/docs/pdf/2023_triple-i_homeowners_insurance_handbook.pdf",
    "https://www.iii.org/sites/default/files/docs/pdf/triple-i_state_of_the_risk_cyber_02062024.pdf",
    "https://www.insurance.ca.gov/01-consumers/105-type/95-guides/09-comm/upload/Commercial-Insurance-Updated-090623.pdf"
]

for url in pdf_urls:
    filename = os.path.basename(urlparse(url).path)
    output_path = os.path.join(OUTPUT_DIR, filename)

    print(f"Downloading: {filename}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    with open(output_path, "wb") as file:
        file.write(response.content)

print("Done.")
```

Install dependency:

```bash
pip install requests
```

Run:

```bash
python download_pdfs.py
```

---

# Notes for ingestion into your LLM Wiki

For each source, store metadata like:

```json
{
  "source_id": "naic_2024_pc_analysis",
  "title": "U.S. Property & Casualty and Title Insurance Industries — 2024 Full Year Results",
  "source_type": "pdf",
  "publisher": "NAIC",
  "url": "https://content.naic.org/sites/default/files/2024-annual-property-casualty-and-title-insurance-industries-analysis-report.pdf",
  "domain": "property_casualty_insurance",
  "topics": ["property casualty", "industry analysis", "underwriting", "surplus", "profitability"]
}
```

Recommended chunking:

```text
chunk_size: 700–1200 tokens
chunk_overlap: 100–150 tokens
embedding_prefix: search_document:
query_prefix: search_query:
```

