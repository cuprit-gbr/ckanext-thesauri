from sqlalchemy import create_engine, Column, Integer, String, Index
from sqlalchemy.ext.declarative import declarative_base
from ckan.model.meta import metadata

Base = declarative_base(metadata=metadata)

class ThesaurusWord(Base):
    __tablename__ = 'thesaurus_words'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(250), unique=True, nullable=False, index=True)

Index('ix_thesaurus_words_word', ThesaurusWord.word)
