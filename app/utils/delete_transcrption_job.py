from botocore.exceptions import ClientError


def delete_job_if_exists(transcribe, job_name):
    try:
        transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        print(f"Deleted previous job: {job_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] in ["NotFoundException", "BadRequestException"]:
            print("No existing job found to delete.")
        else:
            raise
