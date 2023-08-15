import boto3
import os, io
from botocore.exceptions import NoCredentialsError
import mimetypes

ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = "vizbeats"


def upload_file_to_s3(file_object, filename, folder):
    s3 = boto3.client(
        "s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY
    )

    try:
        if hasattr(file_object, "file"):
            contents = file_object.file.read()
        else:
            contents = file_object.read()

        mime_type, _ = mimetypes.guess_type(filename)
        temp_file = io.BytesIO()
        temp_file.write(contents)
        temp_file.seek(0)
        s3.upload_fileobj(
            temp_file,
            "vizbeats",
            f"{folder}/{filename}",
            ExtraArgs={
                "ContentType": mime_type,
                "ContentDisposition": "inline",
            },
        )
        temp_file.close()
    except FileNotFoundError:
        return {"error": "File not found"}
    except NoCredentialsError:
        return {"error": "Credentials not available"}

    return {"message": "File uploaded successfully"}
