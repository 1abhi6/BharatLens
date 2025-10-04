import boto3
from app.utils import extract_bucket_and_key
from app.core.config import settings


def extract_text_from_s3_image(image_s3_url):
    # Get bucket and name
    res = extract_bucket_and_key(image_s3_url)
    bucket = res[0]
    document = res[1]

    # Initialize Textract client
    textract = boto3.client(
        "textract",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION,
    )

    response = textract.detect_document_text(
        Document={"S3Object": {"Bucket": bucket, "Name": document}}
    )

    # Extract lines of text
    text = []
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            text.append(item["Text"])
    return "\n".join(text)
