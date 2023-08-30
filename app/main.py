from typing import Annotated
from fastapi import FastAPI, BackgroundTasks, File, UploadFile, Depends, Form
import shutil, os
from . import config, crud
from . import models
from .aws import upload_file_to_s3
from .database import engine, SessionLocal
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Union
from .schemas import MusicCreate
import demucs.separate

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


@app.get("/")
def read_root():
    return {"status": "healthy"}


@app.get("/demucs")
def separate_musics():
    return {"hello changwan"}


@app.get("/users")
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)


def process_music_separation(
    folder: str,
    audio: File(...),
    db: Session = Depends(get_db),
):
    separator_path = Path("app/separated")
    temp_file = separator_path / f"{folder}.mp3"

    separator_path.mkdir(exist_ok=True)

    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    path = "separated"
    model = "htdemucs_6s"

    demucs.separate.main(["--mp3", "-n", model, str(temp_file)])

    vocals_path = Path(path, model, folder, "vocals.mp3")
    drums_path = Path(path, model, folder, "drums.mp3")
    piano_path = Path(path, model, folder, "piano.mp3")
    guitar_path = Path(path, model, folder, "guitar.mp3")
    bass_path = Path(path, model, folder, "bass.mp3")
    other_path = Path(path, model, folder, "other.mp3")

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

    with guitar_path.open("rb") as file:
        upload_file_to_s3(file, "guitar.mp3", folder)

    with other_path.open("rb") as file:
        upload_file_to_s3(file, "other.mp3", folder)

    separated = Path("separated")

    music = {
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

    if separated.exists() and separated.is_dir():
        shutil.rmtree(separated)


@app.post("/music-separation")
async def music_separation(
    background_tasks: BackgroundTasks,
    title: Annotated[str, Form(...)],
    artist: Annotated[str, Form(...)],
    albumCover: Union[str, UploadFile] = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    folder, _ = os.path.splitext(audio.filename)

    background_tasks.add_task(
        process_music_separation,
        folder,
        audio,
        db,
    )

    upload_file_to_s3(audio, "audio.mp3", folder)

    albumCoverUrl = albumCover

    if hasattr(albumCover, "filename"):
        upload_file_to_s3(albumCover, "albums.png", folder)
        albumCoverUrl = (
            f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/albums.png"
        )

    music = {
        "title": title,
        "artist": artist,
        "albumCover": albumCoverUrl,
        "musicUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{folder}/audio.mp3",
        "userId": "clkza1yhr0000958swtsmyztm",
    }
    music_create_schema = MusicCreate(**music)
    crud.create_music(db=db, music=music_create_schema)

    return {"filename"}
