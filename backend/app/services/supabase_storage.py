from supabase import create_client, Client
from fastapi import HTTPException
import os
import logging
import mimetypes

logger = logging.getLogger(__name__)

# Read env vars at module level (cheap — just os.getenv, no network call)
_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Lazy singleton — created on first actual use, not at import time
_supabase_client: Client | None = None


def _get_client() -> Client:
    """
    Return the Supabase storage client, creating it on first call.
    Raises HTTP 503 if credentials are missing so the error is surfaced
    cleanly to the caller rather than crashing the process at import time.
    """
    global _supabase_client
    if _supabase_client is None:
        if not _SUPABASE_URL or not _SUPABASE_SERVICE_KEY:
            raise HTTPException(
                status_code=503,
                detail="Supabase storage is not configured on the server (missing SUPABASE_URL or SUPABASE_SERVICE_KEY)"
            )
        _supabase_client = create_client(_SUPABASE_URL, _SUPABASE_SERVICE_KEY)
    return _supabase_client


class SupabaseStorageService:
    """Service class to handle file uploads and downloads using Supabase Storage."""

    @staticmethod
    def upload_file(file_content: bytes, file_name: str, bucket_name: str = "question-papers") -> str:
        """
        Upload a file to Supabase Storage.

        Returns:
            The public URL of the uploaded file.
        """
        client = _get_client()
        try:
            client.storage.from_(bucket_name).upload(
                file_name,
                file_content,
                file_options={
                    "content-type": mimetypes.guess_type(file_name)[0] or "application/octet-stream"
                },
            )
            return client.storage.from_(bucket_name).get_public_url(file_name)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {e}")
            raise

    @staticmethod
    def download_file(file_path: str, bucket_name: str = "question-papers") -> bytes:
        """Download a file from Supabase Storage."""
        client = _get_client()
        try:
            return client.storage.from_(bucket_name).download(file_path)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error downloading file from Supabase: {e}")
            raise

    @staticmethod
    def delete_file(file_path: str, bucket_name: str = "question-papers") -> bool:
        """Delete a file from Supabase Storage. Returns True on success."""
        client = _get_client()
        try:
            client.storage.from_(bucket_name).remove([file_path])
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {e}")
            return False

    @staticmethod
    def list_files(bucket_name: str = "question-papers", prefix: str = "") -> list:
        """List files in a Supabase Storage bucket."""
        client = _get_client()
        try:
            return client.storage.from_(bucket_name).list(prefix)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing files from Supabase: {e}")
            return []

    @staticmethod
    def get_file_info(file_path: str, bucket_name: str = "question-papers") -> dict:
        """Get metadata information about a file in Supabase Storage."""
        client = _get_client()
        try:
            public_url = client.storage.from_(bucket_name).get_public_url(file_path)
            return {"exists": True, "public_url": public_url, "file_name": file_path}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting file info from Supabase: {e}")
            return {"exists": False, "error": str(e)}
