from typing import List, Dict, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from datetime import datetime, timedelta
import joblib
import os
from models.search_model import SearchHistory, AutocompleteSuggestions
from utils.content_filter import ContentFilter
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

class PredictionService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.content_filter = ContentFilter()
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 3), min_df=2)
        self.knn_model = NearestNeighbors(n_neighbors=5, metric='cosine')
        self.model_path = 'models/search_predictor.joblib'
        self.load_or_train_model()

    def load_or_train_model(self):
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            self.train_model()

    def load_model(self):
        model_data = joblib.load(self.model_path)
        self.vectorizer = model_data['vectorizer']
        self.knn_model = model_data['knn']

    def train_model(self):
        # Get historical searches from last 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        historical_searches = self.db_session.query(SearchHistory.query_text)\
            .filter(SearchHistory.timestamp >= cutoff_date)\
            .all()
        
        search_texts = [search[0] for search in historical_searches]
        if not search_texts:
            return
            
        # Transform search texts to TF-IDF features
        features = self.vectorizer.fit_transform(search_texts)
        
        # Train KNN model
        self.knn_model.fit(features)
        
        # Save model
        model_data = {
            'vectorizer': self.vectorizer,
            'knn': self.knn_model
        }
        joblib.dump(model_data, self.model_path)

    def get_autocomplete_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        if not partial_query:
            return []

        # Get cached suggestions first
        cached_suggestions = self.db_session.query(AutocompleteSuggestions.suggestion)\
            .filter(AutocompleteSuggestions.partial_query == partial_query)\
            .order_by(desc(AutocompleteSuggestions.frequency))\
            .limit(limit)\
            .all()

        if cached_suggestions:
            return [sugg[0] for sugg in cached_suggestions]

        # Generate new suggestions using the model
        try:
            partial_vector = self.vectorizer.transform([partial_query])
            distances, indices = self.knn_model.kneighbors(partial_vector)
            
            # Get similar queries from training data
            similar_queries = self.vectorizer.get_feature_names_out()[indices[0]]
            
            # Filter suggestions
            filtered_suggestions = []
            for suggestion in similar_queries:
                if suggestion.startswith(partial_query) and \
                   not self.content_filter.is_inappropriate(suggestion):
                    filtered_suggestions.append(suggestion)
                    
                    # Cache the suggestion
                    new_suggestion = AutocompleteSuggestions(
                        partial_query=partial_query,
                        suggestion=suggestion,
                        frequency=1
                    )
                    self.db_session.add(new_suggestion)
            
            self.db_session.commit()
            return filtered_suggestions[:limit]
            
        except Exception as e:
            print(f"Error generating suggestions: {str(e)}")
            return []

    def update_model(self, new_search_text: str):
        try:
            # Add new search to history
            new_search = SearchHistory(query_text=new_search_text)
            self.db_session.add(new_search)
            self.db_session.commit()

            # Retrain model if enough new data
            search_count = self.db_session.query(func.count(SearchHistory.id))\
                .filter(SearchHistory.timestamp >= datetime.now() - timedelta(hours=1))\
                .scalar()
                
            if search_count >= 100:  # Retrain after 100 new searches
                self.train_model()
                
        except Exception as e:
            print(f"Error updating model: {str(e)}")
            self.db_session.rollback()

    def remove_suggestion(self, suggestion: str):
        try:
            self.db_session.query(AutocompleteSuggestions)\
                .filter(AutocompleteSuggestions.suggestion == suggestion)\
                .delete()
            self.db_session.commit()
        except Exception as e:
            print(f"Error removing suggestion: {str(e)}")
            self.db_session.rollback()
