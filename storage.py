"""
PersistenceAgent

Role: Data Storage
Responsibility: Saves the enriched DataFrame to disk (CSV) and/or SQLite for dashboard consumption.
"""
import os
import pandas as pd
import sqlite3
import re

STOP_WORDS = {
    "the", "and", "to", "of", "a", "in", "is", "that", "for", "it", "with", "as", "was",
    "on", "are", "by", "be", "this", "an", "at", "from", "which", "not", "but", "or",
    "have", "we", "they", "you", "all", "what", "there", "can", "if", "would", "about",
    "has", "will", "so", "up", "out", "more", "their", "who", "when", "some", "them",
    "my", "do", "like", "just", "how"
}

class PersistenceAgent:
    def __init__(self, csv_filepath: str = "sentiment_data.csv", db_filepath: str = "sentiment.db"):
        self.csv_filepath = csv_filepath
        self.db_filepath = db_filepath
        self.words_csv_filepath = "sentiment_words.csv"

    def _extract_words(self, text):
        words = re.findall(r'\b[a-zA-Z]{3,}\b', str(text).lower())
        return [w for w in words if w not in STOP_WORDS]

    def save(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0

        # Convert created_utc to proper datetime ISO 8601 strings
        df['created_utc'] = pd.to_datetime(df['created_utc'], errors='coerce').dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        with sqlite3.connect(self.db_filepath) as conn:
            # Check for existing URLs to avoid duplicate entries across pipeline runs
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
            if cursor.fetchone():
                existing_urls = pd.read_sql("SELECT url FROM posts", conn)['url'].tolist()
            else:
                existing_urls = []
            
            # Deduplicate incoming batch and exclude existing records
            df_unique = df.drop_duplicates(subset=['url'])
            df_new = df_unique[~df_unique['url'].isin(existing_urls)]

            if df_new.empty:
                return 0

            # Append to SQLite
            df_new.to_sql("posts", conn, if_exists="append", index=False)

            # --- TOKENIZATION FOR TABLEAU WORD CLOUDS ---
            if 'full_text' in df_new.columns:
                df_words = df_new[['url', 'created_utc', 'sentiment_label', 'full_text']].copy()
                df_words['word'] = df_words['full_text'].apply(self._extract_words)
                df_words = df_words.drop(columns=['full_text']).explode('word')
                df_words = df_words.dropna(subset=['word'])

                if not df_words.empty:
                    # Save to DB
                    df_words.to_sql("word_occurrences", conn, if_exists="append", index=False)
                    
                    # Save to CSV
                    words_file_exists = os.path.isfile(self.words_csv_filepath)
                    df_words.to_csv(self.words_csv_filepath, mode='a', index=False, header=not words_file_exists)

        # Append to CSV
        file_exists = os.path.isfile(self.csv_filepath)
        df_new.to_csv(self.csv_filepath, mode='a', index=False, header=not file_exists)
        
        return len(df_new)
