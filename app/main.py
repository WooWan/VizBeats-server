from typing import Annotated, Optional
from fastapi import (
    FastAPI,
    BackgroundTasks,
    UploadFile,
    Depends,
    Form,
    HTTPException,
    Request,
)
import shutil, os, hashlib
from . import config, crud
from . import models
from .aws import upload_file_to_s3
from .database import engine, SessionLocal
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Union

from .models import Music
from .schemas import MusicCreate, MusicUpdate
import demucs.separate
from fastapi.encoders import jsonable_encoder
from .ytdl import (
    download_from_url,
    perform_search,
    download_image_from_url,
)

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
    music: Music,
    title: str,
    audio_path: Path,
    db: Session = Depends(get_db),
):
    path = Path("separated")
    model = "htdemucs_6s"

    demucs.separate.main(["--mp3", "--mp3-preset=2", "-n", model, str(audio_path)])

    vocals_path = Path(path, model, title, "vocals.mp3")
    drums_path = Path(path, model, title, "drums.mp3")
    piano_path = Path(path, model, title, "piano.mp3")
    guitar_path = Path(path, model, title, "guitar.mp3")
    bass_path = Path(path, model, title, "bass.mp3")
    other_path = Path(path, model, title, "other.mp3")

    with vocals_path.open("rb") as file:
        upload_file_to_s3(file, "vocals.mp3", title)

    with drums_path.open("rb") as file:
        upload_file_to_s3(file, "drums.mp3", title)

    with piano_path.open("rb") as file:
        upload_file_to_s3(file, "piano.mp3", title)

    with bass_path.open("rb") as file:
        upload_file_to_s3(file, "bass.mp3", title)

    with guitar_path.open("rb") as file:
        upload_file_to_s3(file, "guitar.mp3", title)

    with other_path.open("rb") as file:
        upload_file_to_s3(file, "other.mp3", title)
    #
    updated_music = {
        "bassUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{title}/bass.mp3",
        "guitarUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{title}/other.mp3",
        "drumUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{title}/drums.mp3",
        "pianoUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{title}/piano.mp3",
        "vocalUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{title}/vocals.mp3",
        "otherUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{title}/other.mp3",
    }
    music_update_schema = MusicUpdate(**updated_music)
    crud.update_music(db, music_update_schema, music.id)

    if path.exists() and path.is_dir():
        shutil.rmtree(path)

    if audio_path.exists() and audio_path.is_file():
        os.remove(audio_path)


@app.get("/youtube-search")
def youtube_search(query, limit):
    try:
        response = jsonable_encoder(perform_search(query, limit))
        return response
    except Exception as e:
        raise HTTPException(status_code=429, detail="Exceed api usage limitation")


def generate_user_id(ip_address: str):
    md5 = hashlib.md5()
    md5.update((ip_address + os.getenv("IP_ADDRESS_SALT")).encode("utf-8"))
    return md5.hexdigest()


@app.post("/music-separation")
async def music_separation(
    background_tasks: BackgroundTasks,
    request: Request,
    title: Annotated[str, Form(...)],
    artist: Annotated[str, Form(...)],
    videoId: Optional[str] = Form(None),
    albumCover: Union[str, UploadFile] = Form(...),
    audio: UploadFile | None = None,
    db: Session = Depends(get_db),
):
    ip_address = request.client.host or "127.0.0.1"
    user_id = generate_user_id(ip_address)
    user = crud.get_user_by_id(db, user_id)

    if user is None:
        user = models.User(id=user_id, name="anonymous")
        db.add(user)
        db.commit()
        db.refresh(user)

    download_path = "app/separated"

    # if there is no audio, create youtube url
    if audio is None:
        file_format = "m4a"
        filename = f"{title}.{file_format}"
        audio_path = Path(download_path, filename)
        Path(download_path).mkdir(parents=True, exist_ok=True)

        youtube_url = f"https://www.youtube.com/watch?v={videoId}"
        download_from_url(youtube_url, download_path, filename)

        with audio_path.open("rb") as file:
            upload_file_to_s3(file, filename, title)

    else:
        filename, ext = os.path.splitext(audio.filename)
        file_format = ext.split(".")[-1]
        audio_path = Path(download_path, f"{title}.{file_format}")

        with audio_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

    with audio_path.open("rb") as file:
        upload_file_to_s3(file, f"{title}.{file_format}", title)

    if hasattr(albumCover, "filename"):
        upload_file_to_s3(albumCover.file, "albums.png", title)
    else:
        file = download_image_from_url(albumCover)
        upload_file_to_s3(file, "albums.png", title)

    albumCoverUrl = (
        f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{title}/albums.png"
    )

    music = {
        "title": title,
        "artist": artist,
        "albumCover": albumCoverUrl,
        "musicUrl": f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{title}/{title}.{file_format}",
        "userId": user.id,
    }

    music_create_schema = MusicCreate(**music)
    created_music = crud.create_music(db=db, music=music_create_schema)

    background_tasks.add_task(
        process_music_separation,
        created_music,
        title,
        audio_path,
        db,
    )

    return {"filename"}
