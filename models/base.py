from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

from config.config import Config

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Create engine and session factory
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                       autoflush=False,
                                       bind=engine))

# Create declarative base
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    """Initialize database and create all tables"""
    # Import models here to ensure they are known to SQLAlchemy
    from models.search_model import SearchHistory, AutocompleteSuggestions, UserFeedback
    Base.metadata.create_all(bind=engine)

def shutdown_session(exception=None):
    """Remove database session at end of request"""
    db_session.remove()
