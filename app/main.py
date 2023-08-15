from spleeter.separator import Separator
from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Depends, Form
import shutil, os
from . import config, crud
from . import models
from .aws import upload_file_to_s3
from .database import engine, SessionLocal
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Union
from .schemas import MusicCreate

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
config.setup_cors(app)

BUCKET_NAME = "vizbeats"


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/users")
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)


@app.post("/music-separation")
async def music_separation(
    title: Annotated[str, Form(...)],
    artist: Annotated[str, Form(...)],
    albumCover: Union[str, UploadFile] = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    folder, _ = os.path.splitext(audio.filename)
    separator_path = Path("separator", folder)
    temp_file = separator_path / "audio.mp3"

    separator_path.mkdir(exist_ok=True)
    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    # Separate the audio using the temporary file
    separator = Separator("spleeter:5stems")
    separator.separate_to_file(
        str(temp_file), f"separator/{folder}", codec="mp3", bitrate="256k"
    )

    # #path
    drums_path = Path("separator", folder, "audio", "drums.mp3")
    piano_path = Path("separator", folder, "audio", "piano.mp3")
    vocals_path = Path("separator", folder, "audio", "vocals.mp3")
    other_path = Path("separator", folder, "audio", "other.mp3")
    bass_path = Path("separator", folder, "audio", "bass.mp3")

    with temp_file.open("rb") as file:
        upload_file_to_s3(file, "audio.mp3", folder)

    with vocals_path.open("rb") as file:
        upload_file_to_s3(file, "vocals.mp3", folder)

    with drums_path.open("rb") as file:
        upload_file_to_s3(file, "drums.mp3", folder)

    with piano_path.open("rb") as file:
        upload_file_to_s3(file, "piano.mp3", folder)

    with bass_path.open("rb") as file:
        upload_file_to_s3(file, "bass.mp3", folder)

    with other_path.open("rb") as file:
        upload_file_to_s3(file, "other.mp3", folder)

    albumCoverUrl = albumCover
    if hasattr(albumCover, "filename"):
        upload_file_to_s3(albumCover, "albums.png", folder)
        albumCoverUrl = (
            f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/albums.png"
        )

    print("cover", albumCoverUrl)
    music = {
        "title": title,
        "artist": artist,
        "albumCover": albumCoverUrl,
        "musicUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/audio.mp3",
        "bassUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/bass.mp3",
        "guitarUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/other.mp3",
        "drumUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/drums.mp3",
        "pianoUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/piano.mp3",
        "vocalUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/vocals.mp3",
        "userId": "clkza1yhr0000958swtsmyztm",
    }
    music_create_schema = MusicCreate(**music)
    crud.create_music(db=db, music=music_create_schema)
    return {"filename"}


@app.put("/music-separation")
async def music_separation(
    title: Annotated[str, Form(...)],
    artist: Annotated[str, Form(...)],
    albumCover: Union[str, UploadFile] = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    print("hello", type(albumCover))
    if hasattr(albumCover, "filename"):
        print("upload")
    else:
        print("string")
