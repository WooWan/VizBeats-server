# get Posts
from sqlalchemy.orm import Session

import models
import schemas


def get_posts(db: Session):
    return db.query(models.Post).all()