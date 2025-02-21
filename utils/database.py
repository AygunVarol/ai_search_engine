from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator

from config.config import DatabaseConfig
from models.base import Base

class Database:
    def __init__(self):
        self.engine = create_engine(
            DatabaseConfig.DATABASE_URI,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600
        )
        
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        self.Session = scoped_session(self.session_factory)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
        
    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(self.engine)
        
    @contextmanager
    def session_scope(self) -> Generator:
        """Provide a transactional scope around a series of operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def dispose_engine(self):
        """Dispose of the database engine"""
        self.engine.dispose()

# Global database instance
db = Database()
