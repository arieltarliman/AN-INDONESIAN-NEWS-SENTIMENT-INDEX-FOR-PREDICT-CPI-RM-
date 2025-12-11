# Dataset README

This folder contains all raw, intermediate, and final processed data files utilized in the construction and evaluation of the Indonesia News Sentiment of Inflation (INSEI) index.

## 1. News Article Data (Text Corpus)

The news articles covering Indonesian inflation sentiment were sourced via a multi-step process:

| Data Component | Source | Details |
| :--- | :--- | :--- |
| **Initial URLs** | **GDELT 2.0 GKG via BigQuery** | Queries targeted five Indonesian news domains (*bisnis.com*, *liputan6.com*, *cnnindonesia.com*, *tempo.co*, and *detik.com*) for articles related to economic themes and inflation between January 2017 and December 2025,. |
| **Article Content** | **Custom Web Scraper using Trafilatura** | The body text of the articles was extracted from the filtered URLs. |
| **Sentiment Labels** | **Gemini 2.5 Flash API** (Teacher Model) | The final 8,992 cleaned articles were labeled by the LLM, acting as a macroeconomic analyst, to establish the gold standard sentiment corpus,. |

## 2. Official Inflation Data (CPI Rate)

The ground truth time series used for nowcasting and validation is the Month-to-Month (M-to-M) Consumer Price Index (CPI) rate for Indonesia.

| Data Component | Source | Details |
| :--- | :--- | :--- |
| **CPI Rate (M-to-M)** | **Badan Pusat Statistik (BPS) (Statistics Indonesia)** | The data covers the period necessary for the INSEI project (2017 to 2025), and the specific table is available online at: [https://www.bps.go.id/id/statistics-table/2/MSMy/inflasi-bulanan-m-to-m-.html] (Information not in sources). |

The final CPI time series used for forecasting models is loaded from `M-to-M CPI Rate Indonesia 2017-2025 Clean.xlsx`.
