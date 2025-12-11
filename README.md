# An Indonesian News Sentiment Index for CPI Nowcasting (INSEI)

This project establishes a reproducible framework for native-language sentiment analysis in emerging market inflation nowcasting, aiming to overcome the latency of official CPI reports and the methodological flaw of relying on English translation,,. The outcome is the **Indonesia News Sentiment of Inflation (INSEI)** index, validated as a leading indicator of Indonesia's monthly CPI rate.

## 1. Research Methodology Overview

The creation of the INSEI index involved four main stages: Data Acquisition and Filtering, Text Preprocessing and Label Generation, Multi-Model Training and Alignment, and finally, Index Construction and Forecasting.

| Stage | Goal | Key Tool / Output |
| :--- | :--- | :--- |
| **Data Acquisition** | Collect inflation-relevant news URLs. | GDELTS 2.0 GKG via BigQuery, targeting 5 Indonesian news domains. |
| **Filtering** | Filter headlines based on semantic relevance. | **SentenceTransformer (MiniLM-L12-v2)** using a cosine similarity threshold of **0.7** against 40 "golden slugs",. |
| **Labeling** | Generate gold standard sentiment labels. | **Gemini 2.5 Flash API** acting as a macroeconomic analyst. |
| **Modeling** | Distill knowledge into efficient models. | Fine-tuning three transformer models (**mDeBERTa, IndoLEM, IndoBERT**). |
| **Index Construction** | Create the lagged, scaled INSEI time series. | Expanding Window Z-score, 3-month MA, and **optimal 2-month lag**. |
| **Forecasting** | Evaluate predictive utility against CPI. | Hybrid models (VAR, Ridge, LSTM) vs. univariate baselines,. |

## 2. Data and Corpus Statistics

### Data Acquisition and Preprocessing
The initial query on GDELTS retrieved 380,167 URLs from five targeted Indonesian domains (bisnis.com, liputan6.com, cnnindonesia.com, tempo.co, detik.com). After semantic filtering and scraping, the process yielded a final curated corpus of **8,992 articles** covering the period from **January 2017 to October 2025**,,.

The corpus underwent rigorous domain-specific cleaning, including Unicode normalization and boilerplate removal,. To fit the models, article text content was capped at **3,000 characters**,.

### Gold Standard Sentiment Distribution
The corpus was labeled by Gemini 2.5 Flash (the Teacher model) using the three classes: Inflation, Deflation, and Neutral.

| Label | Count | Proportion |
| :--- | :--- | :--- |
| **Neutral** | 4,443 | **49.46%** |
| **Inflation** | 3,221 | 35.68% |
| **Deflation** | 1,328 | 14.86% |
| **Total** | 8,992 | 100.00% |

The dominance of the **Neutral** class and the low volume of the **Deflation** class created a class imbalance challenge addressed through a weighted cross-entropy loss function during training,.

### Teacher Labeling Challenges
The automated labeling process relied on the Gemini 2.5 Flash API, which frequently encountered **429 RESOURCE\_EXHAUSTED** errors (quota limits), requiring complex handling including API key switching and mandatory delays of 6 seconds between batches to complete the labeling job,,.

## 3. Model Training and Index Construction (INSEI)

### Model Distillation
Three transformer architectures were fine-tuned as "student" models to mimic the Gemini Teacher's classification logic:
1.  **mDeBERTa-v3-base** (Multilingual)
2.  **IndoLEM/IndoBERT-base-uncased** (Indonesian)
3.  **IndoBERT-base-p2** (Indonesian)

In the fidelity evaluation against the unseen test set, **mDeBERTa-v3-base** demonstrated the strongest teacher-student alignment, achieving the highest Cohen’s Kappa ($\approx 0.51$),. However, **IndoLEM** often showed superior performance on specific metrics, achieving the highest recall (0.71) for the problematic minority **Deflation** class. All three student models exhibited an extremely high correlation ($\approx 0.97 - 0.99$) with the Gemini Teacher index, confirming the successful transfer of the underlying sentiment signal,.

### INSEI Index Construction
The INSEI index aggregates the model's soft probability scores ($P$) monthly to create the raw net inflationary pressure score ($S_{i,t}$):
$$S_{i,t} = P(\text{Inflation})_{i,t} - P(\text{Deflation})_{i,t}$$
The aggregate monthly index is the mean of these scores,.

The raw index then underwent three final transformations,:
1.  **Normalization:** Expanding Window Z-score Standardization to ensure stationarity.
2.  **Smoothing:** 3-month Moving Average to reduce high-frequency noise.
3.  **Lagging:** Application of the statistically optimal **2-month lag**, confirmed by Granger Causality tests (P < 0.05).

The final index is scaled to a diffusion style baseline of 50:
$$\text{INSEI}_{\text{final}, t} = 50 + (10 \times \text{INSEI}_{\text{norm}, t-2})$$

## 4. Forecasting and Evaluation

The predictive utility was evaluated over a 22-month forecast horizon (Jan 2024 – Oct 2025), comparing a univariate Autoregressive (AR) baseline against Hybrid models that included the INSEI signal.

### Key Forecasting Findings
*   **Best Model:** The **Vector Autoregression (VAR) Hybrid** model using the mDeBERTa sentiment index achieved the lowest RMSE of **0.4962**, representing a modest 1% error reduction over the AR-only baseline, validating that the sentiment index contributes valuable predictive signal,,.
*   **Structural Value:** The predictive coupling between INSEI and CPI strengthens significantly during periods of macroeconomic shocks, validating the index as an **early warning mechanism** for events like the COVID-19 onset and fuel subsidy adjustments.
*   **Model Failure:** The LSTM network, a deep learning architecture, performed poorly, as the **limited training window of 82 months** was insufficient, causing the model to overfit noise and *increase* prediction error when sentiment features were added,.

## 6. Future Work

Future work must **implement sliding window inference** for context preservation and expand the limited 82-month training period and news source diversity,. Hybrid models incorporating **hierarchical attention** should enhance forecasting of sustained **deflationary cycles** and extreme **inflationary spikes**.

---
## Authors and Availability

| Author | Contribution |
| :--- | :--- |
| **Arieldhipta Tarliman** | Conceptualization, Methodology, Software, Formal Analysis, Investigation, Visualization, Writing. |
| **Justin Hartanto Widjaja** | Conceptualization, Data Curation, Investigation, Writing. |
|**Noviyanti Tri Maretta Sagala** | Supervision. |
|**Henry Lucky** | Supervision. |
|**Rilo Chandra Pradana** | Supervision. |

**Source Code and Data:** The source code and data details are available at [https://github.com/arieltarliman](https://github.com/arieltarliman).
