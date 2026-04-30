import os
import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ["S3_BUCKET"]

s3 = boto3.client("s3", region_name=AWS_REGION)


def upload_file_to_s3(fileobj, object_key: str, content_type: str = "application/octet-stream") -> None:
    s3.upload_fileobj(
        Fileobj=fileobj,
        Bucket=S3_BUCKET,
        Key=object_key,
        ExtraArgs={"ContentType": content_type},
    )


def list_uploaded_files(prefix: str = "data/"):
    paginator = s3.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            files.append({
                "key": obj["Key"],
                "name": clean_original_name(obj["Key"]),
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })
    return files

def clean_original_name(key: str) -> str:
    filename = key.split("/")[-1]
    if "_" in filename:
        possible_uuid, original = filename.split("_", 1)
        if len(possible_uuid) == 32:
            return original
    return filename

def delete_file_from_s3(key: str):
    s3.delete_object(
        Bucket=S3_BUCKET,
        Key=key
    )