"""
DEPRECATED (Fix Phase A).

Cloud storage is no longer used. Papers are stored on the local filesystem
via app.core.local_storage. Any import of this module should be removed.
"""


class SupabaseStorageService:
    @staticmethod
    def upload_file(*args, **kwargs):
        raise RuntimeError(
            "Supabase storage is removed. Use app.core.local_storage.save_upload instead."
        )

    @staticmethod
    def download_file(*args, **kwargs):
        raise RuntimeError(
            "Supabase storage is removed. Use app.core.local_storage.read_upload instead."
        )

    @staticmethod
    def delete_file(*args, **kwargs):
        raise RuntimeError(
            "Supabase storage is removed. Use app.core.local_storage.delete_upload instead."
        )
