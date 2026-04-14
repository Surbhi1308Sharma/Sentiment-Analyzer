"""
PipelineAgent

Role: Orchestration
Responsibility: Coordinates ScraperAgent -> SentimentAgent -> PersistenceAgent in sequence.
"""
import argparse
import sys
import logging
from scraper import ScraperAgent
from sentiment import SentimentAgent
from storage import PersistenceAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    import time
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description="Sentiment Analyzer Pipeline")
    parser.add_argument("--topic", type=str, required=True, help="Search keyword or phrase")
    parser.add_argument("--limit", type=int, default=200, help="Number of posts to fetch")
    args = parser.parse_args()

    logging.info(f"Starting execution for topic: '{args.topic}' with limit {args.limit}")
    
    try:
        scraper = ScraperAgent()
        df = scraper.scrape(topic=args.topic, limit=args.limit)
        
        logging.info(f"Scraped {len(df)} posts successfully.")
        
        if df.empty:
            logging.warning("No posts DataFrame returned from scraper. Exiting cleanly.")
            sys.exit(0)
            
        sentiment_agent = SentimentAgent()
        enriched_df = sentiment_agent.analyze(df)
        
        logging.info("Sentiment analysis completed.")
        
        storage_agent = PersistenceAgent()
        saved_count = storage_agent.save(enriched_df)
        logging.info(f"Persisted {saved_count} new unique posts to DB and CSV.")
        
        end_time = time.time()
        exec_time = end_time - start_time
        logging.info(f"Pipeline finished successfully in {exec_time:.2f} seconds.")
        print(f"\nPipeline successfully finished in {exec_time:.2f} seconds. {saved_count} rows added.")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
