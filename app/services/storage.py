import boto3
import uuid
from app.core.config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION,
)


def upload_file_to_s3(file_bytes: bytes, filename: str, content_type: str) -> str:
    key = f"uploads/{uuid.uuid4()}-{filename}"
    s3_client.put_object(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"
