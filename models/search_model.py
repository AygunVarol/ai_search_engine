from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from models.base import Base

class SearchHistory(Base):
    __tablename__ = 'search_history'

    id = Column(Integer, primary_key=True)
    query = Column(String(255), nullable=False)
    user_id = Column(String(100))  # Optional user ID if logged in
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    result_count = Column(Integer)
    
    feedback = relationship("UserFeedback", back_populates="search")
    suggestions = relationship("AutocompleteSuggestion", back_populates="search")

    def __repr__(self):
        return f"<SearchHistory(query='{self.query}', timestamp='{self.timestamp}')>"

class AutocompleteSuggestion(Base):
    __tablename__ = 'autocomplete_suggestions'

    id = Column(Integer, primary_key=True)
    search_id = Column(Integer, ForeignKey('search_history.id'))
    suggestion = Column(String(255), nullable=False)
    confidence_score = Column(Float)
    is_filtered = Column(Integer, default=0)  # 0=not filtered, 1=filtered
    filter_reason = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    search = relationship("SearchHistory", back_populates="suggestions")

    def __repr__(self):
        return f"<AutocompleteSuggestion(suggestion='{self.suggestion}', confidence={self.confidence_score})>"

class UserFeedback(Base):
    __tablename__ = 'user_feedback'

    id = Column(Integer, primary_key=True)
    search_id = Column(Integer, ForeignKey('search_history.id'))
    feedback_type = Column(String(50), nullable=False)  # positive/negative/report
    comment = Column(Text)
    user_id = Column(String(100))  # Optional user ID if logged in
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    is_reviewed = Column(Integer, default=0)  # 0=not reviewed, 1=reviewed
    review_notes = Column(Text)
    review_timestamp = Column(DateTime)

    search = relationship("SearchHistory", back_populates="feedback")

    def __repr__(self):
        return f"<UserFeedback(type='{self.feedback_type}', search_id={self.search_id})>"
