from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ARRAY, Float
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=False)
    age_limit = Column(String(10))
    author_origin = Column(String(50), nullable=False)
    keywords = Column(ARRAY(String))
    description = Column(String)
    url = Column(String(255), nullable=False)
    rating = Column(Float)

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    preferred_genres = Column(ARRAY(String))
    preferred_authors = Column(ARRAY(String))
    age_limit = Column(String(10))
    author_origin_preference = Column(String(50))
    search_history = Column(JSONB)