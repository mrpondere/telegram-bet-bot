import os

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


Base = declarative_base()


class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    start_date = Column(DateTime)
    team1 = Column(String(50))
    team2 = Column(String(50))
    score1 = Column(Integer)
    score2 = Column(Integer)


class Ranking(Base):
    __tablename__ = 'ranking'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer)
    wins = Column(Integer, default=0)
    total = Column(Integer, default=0)


class Bet(Base):
    __tablename__ = 'bets'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer)
    match = Column(Integer)
    bet = Column(String(50))


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer)
    telegram = Column(String)
    notify = Column(Integer)

schema = os.environ.get('betBOTSchema')
engine = create_engine(schema)
Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()


def get_session():
    return session


def get_matches():
    return session.query(Match)


def get_bets():
    return session.query(Bet)


def get_ranking():
    return session.query(Ranking)


def get_users():
    return session.query(User)


def add(to_add):
    try:
        session.add(to_add)
        session.commit()
        return 1
    except Exception:
        return 0


def update():
    session.commit()


def delete(model, _filter):
    session.query(model).filter(_filter).delete()
    session.commit()
