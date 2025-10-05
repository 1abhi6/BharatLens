import boto3
import time
import requests
from app.core.config import settings
from app.utils import delete_job_if_exists

def transcribe_file(job_name, s3_uri, media_format="mp3"):
    transcribe = boto3.client(
        "transcribe",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION,
    )

    delete_job_if_exists(transcribe, job_name)
    print(f"Starting new transcription job: {job_name}")

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": s3_uri},
        MediaFormat=media_format,
        IdentifyLanguage=True,
        # Optionally restrict to expected languages
        LanguageOptions=["en-IN", "hi-IN"],
    )

    # Poll until job is done
    while True:
        job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        status = job["TranscriptionJob"]["TranscriptionJobStatus"]
        if status in ["COMPLETED", "FAILED"]:
            break
        print("Waiting for job to complete...")
        time.sleep(5)

    if status == "COMPLETED":
        transcript_url = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        transcript_json = requests.get(transcript_url).json()
        print(
            "\nTranscript:\n",
            transcript_json["results"]["transcripts"][0]["transcript"],
        )
        print(
            "Languages detected:",
            transcript_json.get("results", {}).get("language_codes", []),
        )
        return transcript_json
    else:
        raise Exception(
            "Transcription failed: " + job["TranscriptionJob"]["FailureReason"]
        )

