"""
SentimentAgent

Role: NLP Processing
Responsibility: Accepts a DataFrame from ScraperAgent and annotates each row with a sentiment label and compound score using VADER.
"""
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class SentimentAgent:
    def __init__(self):
        # Initialize VADER analyzer
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()
        
        def calculate_sentiment(text):
            if pd.isna(text) or not str(text).strip():
                return pd.Series([None, 0.0])
                
            score = self.analyzer.polarity_scores(str(text))['compound']
            
            if score >= 0.05:
                label = "Positive"
            elif score <= -0.05:
                label = "Negative"
            else:
                label = "Neutral"
                
            return pd.Series([label, score])
            
        if not df_copy.empty and 'full_text' in df_copy.columns:
            df_copy[['sentiment_label', 'compound_score']] = df_copy['full_text'].apply(calculate_sentiment)
        else:
            df_copy['sentiment_label'] = None
            df_copy['compound_score'] = 0.0
            
        return df_copy
