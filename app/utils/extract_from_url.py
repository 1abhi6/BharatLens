from urllib.parse import urlparse


def extract_bucket_and_key(s3_url: str) -> tuple:
    """
    Extract bucket and key from S3 URL.
    Supports URLs like:
    - https://bucket-name.s3.region.amazonaws.com/path/to/object
    - https://s3.region.amazonaws.com/bucket-name/path/to/object

    Returns:
      (bucket, key)
    """
    parsed_url = urlparse(s3_url)
    hostname = parsed_url.hostname
    path = parsed_url.path.lstrip("/")

    # Case 1: bucket in subdomain
    # e.g. my-bucket.s3.region.amazonaws.com
    if hostname and hostname.endswith(".amazonaws.com"):
        parts = hostname.split(".")
        if len(parts) > 3 and parts[1] == "s3":
            bucket = parts[0]
            key = path
            return bucket, key

        # Case 2: s3.region.amazonaws.com/bucket-name/path
        elif hostname.startswith("s3"):
            bucket_end = path.find("/")
            if bucket_end == -1:
                bucket = path
                key = ""
            else:
                bucket = path[:bucket_end]
                key = path[bucket_end + 1 :]
            return bucket, key

    raise ValueError("Unsupported S3 URL format")


