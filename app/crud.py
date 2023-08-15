from sqlalchemy.orm import Session
from . import schemas, models


def create_music(db: Session, music: schemas.MusicCreate):
    db_music = models.Music(**music.dict(), userId="clkza1yhr0000958swtsmyztm")
    db.add(db_music)
    db.commit()
    db.refresh(db_music)
    return db_music


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()
