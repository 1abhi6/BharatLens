import io
import asyncio
from urllib.parse import urlparse

import httpx
import docx
from PyPDF2 import PdfReader
import boto3
from app.utils import extract_bucket_and_key
from app.core.config import settings


async def extract_text_from_s3_docs(s3_url: str) -> str:
    """
    Async extraction of text from PDF or DOCX documents stored in S3.
    - Text PDFs: parsed with PyPDF2.
    - DOCX: parsed with python-docx.
    - Skips images.
    - Falls back to Textract for scanned PDFs.
    """
    parsed_url = urlparse(s3_url)

    # --- Async download from S3 ---
    async with httpx.AsyncClient() as client:
        resp = await client.get(s3_url)
        resp.raise_for_status()
        file_bytes = resp.content

    # --- PDF Handling ---
    if parsed_url.path.lower().endswith(".pdf"):

        def parse_pdf():
            """Synchronous PDF text extraction using PyPDF2."""
            text = ""
            try:
                pdf_reader = PdfReader(io.BytesIO(file_bytes))
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip() if text else None
            except Exception as e:
                print(f"[PDF Parsing Error] {e}")
                return None

        # Run sync PDF parser in a separate thread
        text = await asyncio.to_thread(parse_pdf)
        if text:
            return text

        # Fallback to Textract for scanned or unparseable PDFs
        bucket, document = extract_bucket_and_key(s3_url)
        textract = boto3.client(
            "textract",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION,
        )

        def textract_sync():
            return textract.detect_document_text(
                Document={"S3Object": {"Bucket": bucket, "Name": document}}
            )

        response = await asyncio.to_thread(textract_sync)
        lines = [
            item["Text"]
            for item in response.get("Blocks", [])
            if item["BlockType"] == "LINE"
        ]
        return "\n".join(lines)

    # --- DOCX Handling ---
    elif parsed_url.path.lower().endswith(".docx"):

        def parse_docx():
            """Synchronous DOCX text extraction using python-docx."""
            text = ""
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                for para in doc.paragraphs:
                    if para.text.strip():
                        text += para.text + "\n"
                return text.strip()
            except Exception as e:
                print(f"[DOCX Parsing Error] {e}")
                return ""

        return await asyncio.to_thread(parse_docx)

    else:
        raise ValueError(f"Unsupported document type: {parsed_url.path}")
