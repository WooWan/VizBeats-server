from spleeter.separator import Separator
import config
import shutil
from pathlib import Path
import models
from database import engine, SessionLocal
from fastapi import FastAPI, File, UploadFile, Form


models.Base.metadata.create_all(bind=engine)
app = FastAPI()
config.setup_cors(app)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/music-separation")
async def music_separation(audio: UploadFile = File(...), artist: str = Form(...), title: str = Form(...)):
    temp_file = Path(f"temp_{audio.filename}")
    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    # Separate the audio using the temporary file
    separator = Separator('spleeter:5stems')
    separator.separate_to_file(str(temp_file), 'separator', codec="mp3", bitrate="256k")
    return {"filename": audio.filename}