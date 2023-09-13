from http.client import HTTPException

from sqlalchemy.orm import Session
from . import schemas, models
from .models import Music


def create_music(db: Session, music: schemas.MusicCreate):
    db_music = models.Music(**music.model_dump(), userId="clkza4nyv0001958szh0fn7y4")
    db.add(db_music)
    db.commit()
    db.refresh(db_music)
    return db_music


def update_music(db: Session, music_update: schemas.MusicUpdate, music_id):
    find_music = db.query(Music).filter(Music.id == music_id).first()

    if find_music is None:
        raise HTTPException(status_code=404, detail="Music not found")

        # Update the record with new data
    for var, value in music_update.model_dump().items():
        setattr(find_music, var, value)

    # Commit the changes and refresh the object
    db.commit()
    db.refresh(find_music)

    return find_music


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()
