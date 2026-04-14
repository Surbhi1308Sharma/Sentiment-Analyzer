# Sentiment Analyzer Tasks

## Phase 1: Environment & Orchestration
- [x] Initialize Python Virtual Environment: `python -m venv sentiment_env`
- [x] Activate Virtual Environment and install dependencies: `pip install -r requirements.txt`
- [x] Add user-agent inside `.env` file (API tokens are bypassed).
- [x] Implement setup and teardown inside `PipelineAgent` (`pipeline.py`), parsing CLI args.

## Phase 2: ScraperAgent Implementation (`scraper.py`)
- [x] Implement fetching from `mastodon.social` public endpoints via `requests`.
- [x] Implement fetching from `public.api.bsky.app` public endpoints via `requests`.
- [x] Parse HTML from Mastodon into raw `text` using `beautifulsoup4`.
- [x] Combine data into a single uniform Pandas DataFrame matching expected schema.

## Phase 3: SentimentAgent Implementation (`sentiment.py`)
- [x] Setup `vaderSentiment` initialization.
- [x] Iterate through DataFrame or use `.apply()` to assign `sentiment_label` and `compound_score`.
- [x] Handle empty `full_text` inputs gracefully.
- [x] Return a copy of the modified `DataFrame`.

## Phase 4: PersistenceAgent Implementation (`storage.py`)
- [x] Convert `created_utc` from timestamp to proper datetime format (ISO 8601).
- [x] Implement CSV saving with `mode="a"`.
- [x] Implement SQLite database append (`if_exists="append"`).
- [x] Deal with row deduplication by `url` before saving.

## Phase 5: Error Handling and Pipeline Logging
- [x] Add `pipeline.py` level `try-except` blocks.
- [x] Ensure `sys.exit(1)` triggers upon error to signal external scheduler.
- [x] Add explicit logging for scraped rows, persisted rows, execution time, and any warnings.

## Phase 6: Scheduling & Dashboard integration
- [x] Schedule Task on Windows Task Scheduler to run `pipeline.py` every 6 hours via system Python path.
- [x] Hook up Power BI / Tableau to generated `sentiment_data.csv` or `sentiment.db`.
- [x] Create missing charts specified in AGENTS.md (Line, Bar, Scatter, Word Cloud).
