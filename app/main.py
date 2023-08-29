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
import demucs.separate
from fastapi.encoders import jsonable_encoder
from .ytdl import download_from_url, webm_to_mp3, perform_search

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


#
@app.post("/music-separation")
async def music_separation(
    title: Annotated[str, Form(...)],
    artist: Annotated[str, Form(...)],
    albumCover: Union[str, UploadFile] = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    folder, _ = os.path.splitext(audio.filename)
    separator_path = Path("separated", folder)
    temp_file = separator_path / "audio.mp3"
    audio_name = "audio"

    separator_path.mkdir(exist_ok=True)

    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    demucs.separate.main(["--mp3", "-n", "htdemucs_6s", str(temp_file)])
    path = "separated"
    model = "htdemucs_6s"

    # #path
    vocals_path = Path(path, model, audio_name, "vocals.mp3")
    drums_path = Path(path, model, audio_name, "drums.mp3")
    piano_path = Path(path, model, audio_name, "piano.mp3")
    guitar_path = Path(path, model, audio_name, "guitar.mp3")
    bass_path = Path(path, model, audio_name, "bass.mp3")
    # other_path = Path(path, folder, "audio", "other.mp3")

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


@app.post("/youtube-search")
def youtube_search(query):
    response = jsonable_encoder(perform_search(query))
    return response

@app.post("/youtoube-download")
def youtube_download(url, title):
    base_path = '/'
    webm_path = base_path + title + '.webm'
    mp3_path = base_path + title + '.mp3'
    download_from_url(url, webm_path)
    webm_to_mp3(webm_path, mp3_path)
    return {"youtube download"}



