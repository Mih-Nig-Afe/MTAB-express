import asyncio
import boto3
from botocore.exceptions import ClientError
from app.config import settings

def _get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name="auto" # typical for Cloudflare R2 or standard AWS
    )

async def upload_file(key: str, data: bytes, content_type: str = "application/pdf") -> str:
    """Uploads a file to S3/R2 and returns the public URL."""
    if not settings.s3_endpoint_url:
        # Graceful degradation if S3 not configured
        return f"https://example.com/placeholder/{key}"
        
    s3_client = _get_s3_client()
    
    def _upload():
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
            ACL='public-read' # Assuming public read, or bucket policy allows it
        )
        
    await asyncio.to_thread(_upload)
    
    # Construct public URL
    base_url = settings.s3_public_base_url.rstrip("/")
    return f"{base_url}/{key}"

async def generate_signed_url(key: str, expires_in: int = 3600) -> str:
    """Generates a pre-signed download URL."""
    if not settings.s3_endpoint_url:
        return f"https://example.com/placeholder/{key}?signed=true"

    s3_client = _get_s3_client()
    
    def _generate():
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.s3_bucket_name, 'Key': key},
            ExpiresIn=expires_in
        )
        
    return await asyncio.to_thread(_generate)
