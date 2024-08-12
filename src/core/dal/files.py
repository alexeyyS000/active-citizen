from infrastructure.minio.client import BaseBucketClient


class FilesBucketClient(BaseBucketClient):
    class Config:
        bucket_name = "files"
