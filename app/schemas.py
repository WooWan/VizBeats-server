from pydantic import BaseModel
from fastapi import File, UploadFile


class MusicCreate(BaseModel):
    userId: str
    title: str
    artist: str
    albumCover: str
    musicUrl: str


class MusicUpdate(BaseModel):
    bassUrl: str
    guitarUrl: str
    drumUrl: str
    pianoUrl: str
    vocalUrl: str
    otherUrl: str


class MusicData(BaseModel):
    audio: UploadFile = File(...)
    title: str
    artist: str
    albumCover: str


class User(BaseModel):
    id: str
    name: str
    email: str
    emailVerified: str
