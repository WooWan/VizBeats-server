from pydantic import BaseModel
from fastapi import File, UploadFile


class MusicCreate(BaseModel):
    title: str
    artist: str
    albumCover: str
    musicUrl: str
    bassUrl: str
    guitarUrl: str
    drumUrl: str
    pianoUrl: str
    vocalUrl: str


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
