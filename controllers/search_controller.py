from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemy
from datetime import datetime

from models.search_model import SearchHistory, AutocompleteSuggestions, UserFeedback
from services.prediction_service import PredictionService
from utils.content_filter import ContentFilter
from utils.database import db_session

search_bp = Blueprint('search', __name__)
prediction_service = PredictionService()
content_filter = ContentFilter()

@search_bp.route('/api/search/autocomplete', methods=['GET'])
def get_autocomplete_suggestions():
    """Get autocomplete suggestions for partial search query"""
    try:
        query = request.args.get('q', '')
        if not query or len(query.strip()) < 2:
            return jsonify({'suggestions': []})

        # Get predictions from ML model
        raw_suggestions = prediction_service.get_suggestions(query)
        
        # Filter suggestions for inappropriate content
        filtered_suggestions = [
            sugg for sugg in raw_suggestions 
            if not content_filter.is_inappropriate(sugg)
        ]

        # Log the search query
        search_history = SearchHistory(
            query=query,
            timestamp=datetime.utcnow()
        )
        db_session.add(search_history)
        db_session.commit()

        return jsonify({
            'suggestions': filtered_suggestions[:10],
            'search_id': search_history.id
        })

    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@search_bp.route('/api/search/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback for autocomplete suggestions"""
    try:
        data = request.get_json()
        search_id = data.get('search_id')
        suggestion = data.get('suggestion')
        is_inappropriate = data.get('is_inappropriate', False)
        
        if not all([search_id, suggestion]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Store user feedback
        feedback = UserFeedback(
            search_id=search_id,
            suggestion=suggestion,
            is_inappropriate=is_inappropriate,
            timestamp=datetime.utcnow()
        )
        db_session.add(feedback)

        # If marked inappropriate, add to content filter
        if is_inappropriate:
            content_filter.add_inappropriate_term(suggestion)
            
            # Remove from autocomplete suggestions
            AutocompleteSuggestions.query.filter_by(
                suggestion=suggestion
            ).delete()

        db_session.commit()
        return jsonify({'status': 'success'})

    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@search_bp.route('/api/search/popular', methods=['GET'])
def get_popular_searches():
    """Get most popular search queries"""
    try:
        limit = int(request.args.get('limit', 10))
        
        popular = SearchHistory.query\
            .with_entities(
                SearchHistory.query,
                db.func.count(SearchHistory.id).label('count')
            )\
            .group_by(SearchHistory.query)\
            .order_by(db.text('count DESC'))\
            .limit(limit)\
            .all()

        return jsonify({
            'popular_searches': [
                {'query': p.query, 'count': p.count}
                for p in popular
            ]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@search_bp.teardown_request
def remove_session(exc=None):
    """Remove database session at the end of each request"""
    db_session.remove()
