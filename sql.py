import threading
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from config import Config

# Determine DB URL from ENV or default sqlite local file
SQL_DB = Config.SQL_DB or "sqlite:///bot.db"

# if using sqlite, avoid check_same_thread issues
connect_args = {}
if SQL_DB.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(SQL_DB, connect_args=connect_args, echo=False)
BASE = declarative_base()
SESSION_FACTORY = sessionmaker(bind=engine, autoflush=False)
SESSION = scoped_session(SESSION_FACTORY)
INSERTION_LOCK = threading.RLock()

class Users(BASE):
    __tablename__ = "bot_users"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String)

    def __init__(self, id, user_name=None):
        self.id = id
        self.user_name = user_name

# create tables
BASE.metadata.create_all(engine)

def add_user(id, user_name=None):
    with INSERTION_LOCK:
        session = SESSION()
        try:
            msg = session.query(Users).get(id)
            if not msg:
                usr = Users(id, user_name)
                session.add(usr)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

def remove_user(id):
    with INSERTION_LOCK:
        session = SESSION()
        try:
            msg = session.query(Users).get(id)
            if msg:
                session.delete(msg)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

def count_users():
    session = SESSION()
    try:
        return session.query(Users).count()
    finally:
        session.close()

def user_list():
    session = SESSION()
    try:
        rows = session.query(Users.id).order_by(Users.id).all()
        return [r[0] for r in rows]
    finally:
        session.close()