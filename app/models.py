from sqlalchemy import Column, String, ForeignKey,DateTime, Integer
from sqlalchemy.orm import relationship
from .database import Base
import uuid

class Account(Base):
    __tablename__ = 'Account'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column(String, ForeignKey('User.id'), nullable=False)
    type = Column(String)
    provider = Column(String)
    providerAccountId = Column(String)
    refresh_token = Column(String)
    access_token = Column(String)
    expires_at = Column(Integer)
    token_type = Column(String)
    scope = Column(String)
    id_token = Column(String)
    session_state = Column(String)
    oauth_token_secret = Column(String)
    oauth_token = Column(String)
    user = relationship('User', back_populates='accounts')

class Session(Base):
    __tablename__ = 'Session'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sessionToken = Column(String, unique=True)
    userId = Column(String, ForeignKey('User.id'), nullable=False)
    expires = Column(DateTime)
    user = relationship('User', back_populates='sessions')


class User(Base):
    __tablename__ = 'User'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    email = Column(String, unique=True)
    emailVerified = Column(DateTime)
    image = Column(String)
    accounts = relationship('Account', back_populates='user')
    sessions = relationship('Session', back_populates='user')
    musics = relationship('Music', back_populates='user')

class Music(Base):
    __tablename__ = 'Music'

    id = Column(String, primary_key=True, default=uuid.uuid4().hex)
    title = Column(String)
    artist = Column(String)
    albumCover = Column(String)
    musicUrl = Column(String)
    bassUrl = Column(String)
    guitarUrl = Column(String)
    drumUrl = Column(String)
    pianoUrl = Column(String)
    vocalUrl = Column(String)

    userId = Column(String, ForeignKey('User.id'), name="user_id")
    user = relationship('User', back_populates='musics')