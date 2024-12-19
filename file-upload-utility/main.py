import os
from pathlib import Path
from typing import Optional
import bytedtos

class FileUploader:
    """A class to handle file uploads using bytedtos client."""

    def __init__(self, bucket_name: str, ak: str, sub_domain: str):
        """Initialize the FileUploader.

        Args:
            bucket_name (str): The name of the bucket
            ak (str): Access key
            sub_domain (str): Endpoint subdomain
        """
        self.BUCKET_NAME = bucket_name
        self.AK = ak
        self.SUB_DOMAIN = sub_domain

    def get_client(self):
        """Get bytedtos client instance with specified configuration.

        Returns:
            bytedtos.Client: Configured client instance
        """
        client = bytedtos.Client(
            self.BUCKET_NAME,
            self.AK,
            endpoint=self.SUB_DOMAIN,
            timeout=120,
            connect_timeout=120,
        )
        return client

    def upload_file(self, local_path: str, root_dir: str) -> bool:
        """Upload a local file maintaining the directory structure.

        Args:
            local_path (str): Path to the local file
            root_dir (str): Root directory path for relative path calculation

        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            file_path = Path(local_path)
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return False

            # Use root_dir as base for relative path
            relative_path = str(file_path.relative_to(Path(root_dir)))
            remote_key = relative_path

            client = self.get_client()
            with open(str(file_path), 'rb') as f:
                client.put_object(remote_key, f)

            print(f"Successfully uploaded {file_path} to {remote_key}")
            return True

        except Exception as e:
            print(f"Failed to upload file: {e}")
            return False

    def upload_directory(self, root_dir: str) -> bool:
        """Upload all files in a directory maintaining the structure.

        Args:
            root_dir (str): Path to the root directory (must be named '大字模式')

        Returns:
            bool: True if all uploads successful, False if any failed
        """
        try:
            dir_path = Path(root_dir)
            if not dir_path.is_dir():
                print(f"Directory not found: {dir_path}")
                return False
            if dir_path.name != "大字模式":
                print(f"Invalid root directory. Expected '大字模式', got '{dir_path.name}'")
                return False

            success = True
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    if not self.upload_file(str(file_path), str(dir_path)):
                        success = False

            return success

        except Exception as e:
            print(f"Failed to process directory: {e}")
            return False
