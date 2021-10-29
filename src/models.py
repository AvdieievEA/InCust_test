from sqlalchemy import Boolean, Column, Integer, String

from .database import Base, engine


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    title = Column(String(250))
    description = Column(String(1000))
    photo_id = Column(String(100))
    creator_id = Column(Integer)
    message_id = Column(Integer)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    show_reply_markup = Column(Boolean)


Base.metadata.create_all(engine)
