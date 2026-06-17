import io
from typing import BinaryIO

import boto3
from botocore.client import Config

from app.core.config import settings


class S3Storage:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.S3_BUCKET

    def upload_file(self, key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> str:
        self.client.upload_fileobj(data, self.bucket, key, ExtraArgs={"ContentType": content_type})
        return f"{settings.S3_ENDPOINT_URL}/{self.bucket}/{key}"

    def upload_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        return self.upload_file(key, io.BytesIO(content), content_type)

    def download_bytes(self, key: str) -> bytes:
        buffer = io.BytesIO()
        self.client.download_fileobj(self.bucket, key, buffer)
        return buffer.getvalue()
