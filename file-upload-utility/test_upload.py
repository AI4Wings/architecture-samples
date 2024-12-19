from pathlib import Path
from unittest.mock import MagicMock
import sys

# Mock the bytedtos module before importing FileUploader
class MockBytedtosClient:
    def __init__(self, *args, **kwargs):
        self.uploaded_files = []

    def put_object(self, remote_key, file_obj):
        self.uploaded_files.append(remote_key)
        print(f"Mock: Uploaded file to {remote_key}")
        return True

mock_module = MagicMock()
mock_module.Client = MockBytedtosClient
sys.modules['bytedtos'] = mock_module

# Import FileUploader after setting up mock
from main import FileUploader

def setup_test_environment():
    """Create test directory structure and files."""
    base_dir = Path("大字模式")
    test_path = base_dir / "Oppo A5" / "链路1-10次"
    test_path.mkdir(parents=True, exist_ok=True)

    # Create test files
    (test_path / "采集1.png").touch()
    (test_path / "采集2.png").touch()
    return base_dir

def test_upload():
    """Test the FileUploader functionality."""
    # Create test environment
    base_dir = setup_test_environment()

    # Initialize uploader
    uploader = FileUploader(
        bucket_name="test-bucket",
        ak="test-ak",
        sub_domain="test.endpoint.com"
    )

    print("\nTesting directory upload with correct structure:")
    result = uploader.upload_directory(str(base_dir))
    print(f"Directory upload result: {result}")

    # Test with invalid root directory
    print("\nTesting directory upload with invalid root directory:")
    invalid_dir = Path("invalid_root")
    invalid_dir.mkdir(exist_ok=True)
    result = uploader.upload_directory(str(invalid_dir))
    print(f"Invalid directory upload result: {result}")

    # Print uploaded files to verify structure
    client = uploader.get_client()
    print("\nUploaded files:")
    for remote_key in client.uploaded_files:
        print(f"- {remote_key}")

if __name__ == "__main__":
    test_upload()
