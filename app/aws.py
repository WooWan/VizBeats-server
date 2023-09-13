import boto3
import os, io
from botocore.exceptions import NoCredentialsError
import mimetypes
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = "vizbeats"


def get_content_type(filename):
    format = filename.split(".")[-1]
    if format == "mp3":
        return "audio/mpeg"
    elif format == "m4a":
        return "audio/mp4"
    else:
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type


def upload_file_to_s3(file_object, filename, folder):
    s3 = boto3.client(
        "s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY
    )

    try:
        if hasattr(file_object, "file"):
            contents = file_object.file.read()
        else:
            # 유튜브로 업로드 했을 경우
            contents = file_object.read()

        temp_file = io.BytesIO()
        temp_file.write(contents)

        temp_file.seek(0)

        content_type = get_content_type(filename)
        print(content_type)
        s3.upload_fileobj(
            temp_file,
            "vizbeats",
            f"{folder}/{filename}",
            ExtraArgs={"ContentType": content_type},
        )
        temp_file.close()
    except FileNotFoundError:
        return {"error": "File not found"}
    except NoCredentialsError:
        return {"error": "Credentials not available"}

    return {"message": "File uploaded successfully"}
