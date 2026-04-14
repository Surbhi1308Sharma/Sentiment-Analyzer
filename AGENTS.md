# AGENTS.md — Sentiment Analyzer

This document describes the agents, roles, and responsibilities within the Sentiment Analyzer project. It is intended for AI coding assistants (e.g., Claude, Copilot, Cursor) and human contributors to understand how work is divided across the pipeline.

---

## Project Overview

The Sentiment Analyzer is a data pipeline that:
1. Scrapes posts from Reddit on trending topics
2. Runs NLP-based sentiment analysis using VADER
3. Persists results to a CSV / SQLite database
4. Feeds a Power BI / Tableau dashboard for trend visualization

---

## Agent Definitions

### 1. `ScraperAgent`

**File:** `scraper.py`  
**Role:** Data Collection  
**Responsibility:** Connects to the Reddit API via PRAW and fetches posts based on a search topic.

**Inputs:**
- `topic` (str) — Search keyword or phrase (e.g., `"artificial intelligence"`)
- `subreddit` (str) — Target subreddit, defaults to `"all"`
- `limit` (int) — Number of posts to fetch, defaults to `200`

**Outputs:**
- `pandas.DataFrame` with columns: `title`, `text`, `score`, `created_utc`, `num_comments`, `url`

**Key Rules:**
- Must read credentials from `.env` — never hardcode API keys
- Must handle `429 Rate Limit` errors with exponential backoff (`time.sleep`)
- Must combine `title + text` into `full_text` for downstream analysis
- Must not crash on posts with empty `selftext` (link posts)

**Error Handling:**
| Error | Cause | Fix |
|---|---|---|
| `OAuthException` | Wrong credentials | Re-check `.env` values |
| `ResponseException 429` | Rate limited | Add `time.sleep(2)` between requests |
| Empty `text` field | Link-only posts | Default to empty string, not `None` |

---

### 2. `SentimentAgent`

**File:** `sentiment.py`  
**Role:** NLP Processing  
**Responsibility:** Accepts a DataFrame from `ScraperAgent` and annotates each row with a sentiment label and compound score using VADER.

**Inputs:**
- `pandas.DataFrame` with a `full_text` column

**Outputs:**
- Same DataFrame with two new columns:
  - `sentiment_label` — `"Positive"`, `"Neutral"`, or `"Negative"`
  - `compound_score` — Float between `-1.0` and `+1.0`

**Scoring Thresholds (VADER standard):**
| Compound Score | Label |
|---|---|
| `>= 0.05` | Positive |
| `<= -0.05` | Negative |
| Between | Neutral |

**Key Rules:**
- Must skip rows where `full_text` is `None` or empty — return `(None, 0.0)`
- Must use VADER (not TextBlob) — VADER handles slang, caps, and punctuation better for social media
- Must not modify the original DataFrame in place — return a copy

**Known Limitations:**
- VADER cannot detect sarcasm
- Mixed-language posts may score inaccurately
- Very short posts (< 5 words) may produce unreliable scores

---

### 3. `PersistenceAgent`

**File:** `storage.py`  
**Role:** Data Storage  
**Responsibility:** Saves the enriched DataFrame to disk (CSV) and/or SQLite for dashboard consumption.

**Inputs:**
- Enriched `pandas.DataFrame` from `SentimentAgent`

**Outputs:**
- Appended rows in `sentiment_data.csv`
- Appended rows in `sentiment.db` (SQLite table: `posts`)

**Key Rules:**
- Must use `if_exists="append"` when writing to SQLite — **never `"replace"`**, which deletes historical data
- Must deduplicate rows by `url` before appending to avoid double-counting on reruns
- Must ensure `created_utc` is stored as a proper datetime string (ISO 8601), not a Unix timestamp

**Error Handling:**
| Error | Cause | Fix |
|---|---|---|
| `OperationalError: table locked` | Another process writing | Retry with backoff |
| Duplicate rows | Script ran twice | Deduplicate on `url` before insert |
| Dates as integers | Forgot `pd.to_datetime()` | Convert before saving |

---

### 4. `PipelineAgent`

**File:** `pipeline.py`  
**Role:** Orchestration  
**Responsibility:** Coordinates `ScraperAgent → SentimentAgent → PersistenceAgent` in sequence. This is the main entry point for scheduled runs.

**Inputs:**
- `topic` (str) — Passed from CLI or config file
- `limit` (int) — Optional, defaults to `200`

**Usage:**
```bash
python pipeline.py --topic "climate change" --limit 300
```

**Flow:**
```
pipeline.py
  └── ScraperAgent.scrape(topic, limit)
        └── SentimentAgent.analyze(df)
              └── PersistenceAgent.save(df)
```

**Key Rules:**
- Must log start time, row count scraped, and row count saved
- Must exit cleanly (non-zero exit code) on any agent failure
- Must not silently swallow exceptions — all errors must be printed or logged

---

### 5. `SchedulerAgent`

**Tool:** OS-level scheduler (cron / Task Scheduler)  
**Role:** Automation  
**Responsibility:** Triggers `pipeline.py` on a recurring schedule to keep the dataset fresh for the dashboard.

**Recommended Schedule:** Every 6 hours

**Cron (Mac/Linux):**
```bash
0 */6 * * * /path/to/sentiment_env/bin/python /path/to/pipeline.py --topic "AI" --limit 200
```

**Windows Task Scheduler:**
- Program: `C:\path\to\sentiment_env\Scripts\python.exe`
- Arguments: `C:\path\to\pipeline.py --topic "AI" --limit 200`

**Key Rules:**
- Must use the virtual environment's Python binary — not system Python
- Logs should be redirected to a file:  
  `>> /path/to/logs/pipeline.log 2>&1`

---

### 6. `DashboardAgent`

**Tool:** Power BI / Tableau  
**Role:** Visualization  
**Responsibility:** Reads `sentiment_data.csv` or `sentiment.db` and displays sentiment trends over time.

**Required Charts:**
| Chart | X-Axis | Y-Axis / Metric |
|---|---|---|
| Line Chart | `created_utc` (Date) | `AVG(compound_score)` |
| Bar Chart | `sentiment_label` | Count of posts |
| Scatter Plot | `compound_score` | `score` (upvotes) |
| Word Cloud | — | Most frequent words in `full_text` |

**Key Rules:**
- `created_utc` must be set as a **Date** type in Power BI / Tableau — not string or number
- Refresh the data source after every pipeline run
- Filter out rows where `sentiment_label` is `None` (empty posts)

---

## Inter-Agent Data Contract

```
ScraperAgent  →  DataFrame(title, text, score, created_utc, num_comments, url, full_text)
                        ↓
SentimentAgent →  + sentiment_label, compound_score
                        ↓
PersistenceAgent → sentiment_data.csv / sentiment.db (posts table)
                        ↓
DashboardAgent  →  Visual charts in Power BI / Tableau
```

---

## Environment & Configuration

| Variable | Description |
|---|---|
| `REDDIT_CLIENT_ID` | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | Reddit app client secret |
| `REDDIT_USER_AGENT` | Unique identifier string for your app |

Store in `.env`. Load with `python-dotenv`. **Never commit `.env` to version control.**

---

## File Structure

```
sentiment-analyzer/
├── .env                   ← API credentials (gitignored)
├── .gitignore
├── AGENTS.md              ← This file
├── pipeline.py            ← PipelineAgent (entry point)
├── scraper.py             ← ScraperAgent
├── sentiment.py           ← SentimentAgent
├── storage.py             ← PersistenceAgent
├── sentiment_data.csv     ← Output for dashboard
├── sentiment.db           ← SQLite database (optional)
├── logs/
│   └── pipeline.log       ← Scheduled run logs
└── requirements.txt
```

---

## Running the Project

```bash
# 1. Activate virtual environment
source sentiment_env/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up .env with Reddit credentials

# 4. Run the full pipeline
python pipeline.py --topic "electric vehicles" --limit 200

# 5. Open sentiment_data.csv in Power BI / Tableau
```

---

## Contributing

- Each agent must be independently testable
- New agents must be documented in this file with: Role, Inputs, Outputs, Key Rules, and Error Handling
- All API credentials must go through `.env` — no exceptions
