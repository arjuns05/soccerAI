from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.sql import func 
from sqlalchemy.dialects.postgresql import ARRAY 
from app.db import Base

class Match(Base):
    __tablename__ = "matches"
    id = Column(String, primary_key = True) #this is the match id 
    home_team = Column(String, nullable = False)
    away_team = Column(String, nullable = False)
    competition = Column(String, nullable = True) #can be of null value
    kickoff_ts = Column(DateTime(timezone = True), nullable = True)
    status = Column(String, nullable = False, default = "scheduled") #status is scheduled, live, or finished 
    final_home_goals = Column(Integer, nullable = True)
    final_away_goals = Column(Integer, nullable = True)
    created_at = Column(DateTime(timezone = True), server_default = func.now())

class MatchEvent(Base):
    __tablename__ = "match_events"
    id = Column(Integer, primary_key = True, autoincrement = True)
    match_id = Column(String, ForeignKey("matches.id"), index =True, nullable = False)
    ts = Column(DateTime(timezone = True), nullable = False)
    minute = Column(Integer, nullable = True)
    event_type = Column(String, nullable = False) #kickoff/shot/goal/foul/corner/etc.
    team = Column (String, nullable = True)
    player = Column(String, nullable = True)
    payload = Column(JSON, nullable = False, default = {})
    created_at = Column(DateTime(timezone = True), server_default=func.now())

Index("ix_match_events_match_ts", MatchEvent.match_id, MatchEvent.ts)

class PlayerEvent(Base):
    __tablename__ = "player_events"
    id = Column(Integer, primary_key = True, autoincrement = True)
    match_id = Column(String, index = True, nullable = False)
    ts = Column(DateTime(timezone = True), nullable = False)
    player = Column(String, nullable = False)
    team = Column(String, nullable = True)
    stat_type = Column(String, nullable = False) #xg, pass, tackle, shot, etc
    value = Column(Float, nullable = False, default = 0.0)
    payload = Column(JSON, nullable = False, default = {})
    created_at = Column(DateTime(timezone = True), server_default = func.now())

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key = True, autoincrement = True)
    match_id = Column(String, index = True, nullable = False)
    ts = Column(DateTime(timezone = True), nullable = False)
    model_version = Column(String, nullable = False)
    p_home_win = Column(Float, nullable = False)
    p_draw = Column(Float, nullable = False)
    p_away_win = Column(Float, nullable = False)
    features = Column(JSON, nullable = False, default = {})
    explanation = Column(Text, nullable = True)

class RagDoc(Base):
    '''
    this is a vector store without using pgvector 
    store embeddings as a float and do cosine in python at the time of the query

    '''
    __tablename__ = "rag_docs"
    id = Column(Integer, primary_key= True, autoincrement = True)
    doc_type = Column(String, nullable = False) #historical_match, etc. 
    match_id = Column(String, nullable = True)
    text = Column(Text, nullable = False)
    meta = Column(JSON, nullable = False, default = {})
    embedding = Column(ARRAY(Float), nullable = True) #length depends on the model (above)
    created_at = Column(DateTime(timezone = True), server_default=func.now())
