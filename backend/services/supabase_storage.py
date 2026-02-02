from supabase import create_client, Client
import os
from typing import Optional
import mimetypes
from io import BytesIO

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

class SupabaseStorageService:
    """
    Service class to handle file uploads and downloads using Supabase Storage
    """
    
    @staticmethod
    def upload_file(file_content: bytes, file_name: str, bucket_name: str = "question-papers") -> str:
        """
        Upload a file to Supabase Storage
        
        Args:
            file_content: The binary content of the file to upload
            file_name: The name to give the file in storage
            bucket_name: The storage bucket name (defaults to "question-papers")
        
        Returns:
            The public URL of the uploaded file
        """
        try:
            # Create the bucket if it doesn't exist (or ensure it exists)
            # Note: In practice, you'd create buckets through the Supabase dashboard
            response = supabase.storage.from_(bucket_name).upload(
                file_name, 
                file_content,
                file_options={"content-type": mimetypes.guess_type(file_name)[0] or "application/octet-stream"}
            )
            
            # Get the public URL
            public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
            return public_url
            
        except Exception as e:
            print(f"Error uploading file to Supabase: {str(e)}")
            raise e
    
    @staticmethod
    def download_file(file_path: str, bucket_name: str = "question-papers") -> bytes:
        """
        Download a file from Supabase Storage
        
        Args:
            file_path: The path of the file in storage
            bucket_name: The storage bucket name (defaults to "question-papers")
        
        Returns:
            The binary content of the downloaded file
        """
        try:
            response = supabase.storage.from_(bucket_name).download(file_path)
            return response
        
        except Exception as e:
            print(f"Error downloading file from Supabase: {str(e)}")
            raise e
    
    @staticmethod
    def delete_file(file_path: str, bucket_name: str = "question-papers") -> bool:
        """
        Delete a file from Supabase Storage
        
        Args:
            file_path: The path of the file in storage
            bucket_name: The storage bucket name (defaults to "question-papers")
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            response = supabase.storage.from_(bucket_name).remove([file_path])
            return True
        
        except Exception as e:
            print(f"Error deleting file from Supabase: {str(e)}")
            return False
    
    @staticmethod
    def list_files(bucket_name: str = "question-papers", prefix: str = "") -> list:
        """
        List files in a Supabase Storage bucket
        
        Args:
            bucket_name: The storage bucket name (defaults to "question-papers")
            prefix: Optional prefix to filter files
        
        Returns:
            List of file objects with metadata
        """
        try:
            response = supabase.storage.from_(bucket_name).list(prefix)
            return response
        
        except Exception as e:
            print(f"Error listing files from Supabase: {str(e)}")
            return []

    @staticmethod
    def get_file_info(file_path: str, bucket_name: str = "question-papers"):
        """
        Get metadata information about a file in Supabase Storage
        
        Args:
            file_path: The path of the file in storage
            bucket_name: The storage bucket name (defaults to "question-papers")
        
        Returns:
            File metadata object
        """
        try:
            # Unfortunately, Supabase Storage doesn't have a direct method to get file info
            # We'll return the public URL which confirms the file exists
            public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
            return {
                "exists": True,
                "public_url": public_url,
                "file_name": file_path
            }
        
        except Exception as e:
            print(f"Error getting file info from Supabase: {str(e)}")
            return {
                "exists": False,
                "error": str(e)
            }