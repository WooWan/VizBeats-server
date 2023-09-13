from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import uuid


class User(Base):
    __tablename__ = "User"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    musics = relationship("Music", back_populates="user")


# sda
class Music(Base):
    __tablename__ = "Music"

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
    otherUrl = Column(String)

    userId = Column(String, ForeignKey("User.id"), name="user_id")
    user = relationship("User", back_populates="musics")
