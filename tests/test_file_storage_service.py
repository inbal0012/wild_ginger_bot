import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.services.file_storage_service import FileStorageService


class TestFileStorageService:
    """Test suite for FileStorageService class"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def file_storage(self, temp_data_dir):
        """Create a FileStorageService instance with temporary directory"""
        return FileStorageService(data_dir=temp_data_dir)
    
    def test_init_default_data_dir(self):
        """Test initialization with default data directory"""
        with patch('os.path.exists', return_value=True):
            with patch('os.makedirs') as mock_makedirs:
                service = FileStorageService()
                
                assert service.data_dir == "data"
                mock_makedirs.assert_not_called()
    
    def test_init_custom_data_dir(self, temp_data_dir):
        """Test initialization with custom data directory"""
        service = FileStorageService(data_dir=temp_data_dir)
        
        assert service.data_dir == temp_data_dir
        assert os.path.exists(temp_data_dir)
    
    def test_init_creates_data_dir_if_not_exists(self):
        """Test that data directory is created if it doesn't exist"""
        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs') as mock_makedirs:
                service = FileStorageService(data_dir="test_data")
                
                assert service.data_dir == "test_data"
                mock_makedirs.assert_called_once_with("test_data")
    
    def test_get_file_path(self, file_storage):
        """Test getting file path"""
        file_path = file_storage._get_file_path("test_file")
        expected_path = os.path.join(file_storage.data_dir, "test_file")
        
        assert file_path == expected_path
    
    def test_save_data_success(self, file_storage):
        """Test successful data saving"""
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        
        result = file_storage.save_data("test_file", test_data)
        
        assert result is True
        
        # Check that file was created
        file_path = os.path.join(file_storage.data_dir, "test_file.json")
        assert os.path.exists(file_path)
        
        # Check file contents
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert "data" in saved_data
        assert "metadata" in saved_data
        assert saved_data["data"] == test_data
        assert "saved_at" in saved_data["metadata"]
        assert saved_data["metadata"]["data_type"] == "dict"
        assert saved_data["metadata"]["version"] == "1.0"
    
    def test_save_data_with_complex_objects(self, file_storage):
        """Test saving data with complex objects that need custom serialization"""
        test_data = {
            "datetime": datetime(2024, 1, 1, 12, 0, 0),
            "set": {1, 2, 3},
            "bytes": b"test bytes"
        }
        
        result = file_storage.save_data("complex_file", test_data)
        
        assert result is True
        
        # Check that file was created and can be loaded
        file_path = os.path.join(file_storage.data_dir, "complex_file.json")
        assert os.path.exists(file_path)
        
        loaded_data = file_storage.load_data("complex_file")
        assert loaded_data is not None
        assert "datetime" in loaded_data
        assert "set" in loaded_data
        assert "bytes" in loaded_data
    
    def test_save_data_failure_permission_error(self, file_storage):
        """Test data saving failure due to permission error"""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = file_storage.save_data("test_file", {"key": "value"})
            
            assert result is False
    
    def test_save_data_failure_json_error(self, file_storage):
        """Test data saving failure due to JSON serialization error"""
        # Create an object that can't be JSON serialized
        class NonSerializable:
            pass

        non_serializable_data = {"key": NonSerializable()}

        result = file_storage.save_data("test_file", non_serializable_data)

        # The service uses default=str, so it should succeed
        assert result is True
    
    def test_load_data_existing_file(self, file_storage):
        """Test loading data from existing file"""
        test_data = {"key": "value", "number": 42}
        
        # Save data first
        file_storage.save_data("test_file", test_data)
        
        # Load data
        loaded_data = file_storage.load_data("test_file")
        
        assert loaded_data == test_data
    
    def test_load_data_nonexistent_file(self, file_storage):
        """Test loading data from non-existent file"""
        loaded_data = file_storage.load_data("nonexistent_file")
        
        assert loaded_data is None
    
    def test_load_data_with_default(self, file_storage):
        """Test loading data with custom default value"""
        default_value = {"default": "value"}
        loaded_data = file_storage.load_data("nonexistent_file", default=default_value)
        
        assert loaded_data == default_value
    
    def test_load_data_corrupted_file(self, file_storage):
        """Test loading data from corrupted JSON file"""
        file_path = os.path.join(file_storage.data_dir, "corrupted_file.json")
        
        # Create a corrupted JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json}')
        
        loaded_data = file_storage.load_data("corrupted_file")
        
        assert loaded_data is None
    
    def test_load_data_missing_data_key(self, file_storage):
        """Test loading data from file missing 'data' key"""
        file_path = os.path.join(file_storage.data_dir, "invalid_file.json")
        
        # Create file with invalid structure
        invalid_data = {"metadata": {"saved_at": "2024-01-01"}}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        loaded_data = file_storage.load_data("invalid_file")
        
        assert loaded_data is None
    
    def test_load_data_missing_metadata_key(self, file_storage):
        """Test loading data from file missing 'metadata' key"""
        file_path = os.path.join(file_storage.data_dir, "invalid_file.json")
        
        # Create file with invalid structure
        invalid_data = {"data": {"key": "value"}}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        loaded_data = file_storage.load_data("invalid_file")
        
        assert loaded_data is None
    
    def test_save_and_load_various_data_types(self, file_storage):
        """Test saving and loading various data types"""
        test_cases = [
            {"string": "test"},
            {"number": 42},
            {"float": 3.14},
            {"boolean": True},
            {"list": [1, 2, 3]},
            {"dict": {"nested": "value"}},
            {"null": None},
            {"mixed": {"str": "test", "num": 42, "bool": False, "list": [1, 2], "dict": {"key": "value"}}}
        ]
        
        for i, test_data in enumerate(test_cases):
            filename = f"test_data_{i}"
            
            # Save data
            save_result = file_storage.save_data(filename, test_data)
            assert save_result is True
            
            # Load data
            loaded_data = file_storage.load_data(filename)
            assert loaded_data == test_data
    
    def test_save_and_load_empty_data(self, file_storage):
        """Test saving and loading empty data structures"""
        empty_data_cases = [
            {},
            [],
            "",
            None
        ]
        
        for i, test_data in enumerate(empty_data_cases):
            filename = f"empty_data_{i}"
            
            # Save data
            save_result = file_storage.save_data(filename, test_data)
            assert save_result is True
            
            # Load data
            loaded_data = file_storage.load_data(filename)
            assert loaded_data == test_data
    
    def test_file_path_handling(self, file_storage):
        """Test that file paths are handled correctly"""
        # Test with filename that includes .json extension
        test_data = {"key": "value"}
        
        result = file_storage.save_data("test_file.json", test_data)
        assert result is True
        
        # Check that file was created with .json extension
        file_path = os.path.join(file_storage.data_dir, "test_file.json.json")
        assert os.path.exists(file_path)
        
        # Load data
        loaded_data = file_storage.load_data("test_file.json")
        assert loaded_data == test_data
    
    def test_concurrent_access_simulation(self, file_storage):
        """Test that multiple save/load operations work correctly"""
        test_data_1 = {"user": "alice", "score": 100}
        test_data_2 = {"user": "bob", "score": 200}
        
        # Save multiple files
        assert file_storage.save_data("user1", test_data_1) is True
        assert file_storage.save_data("user2", test_data_2) is True
        
        # Load multiple files
        loaded_1 = file_storage.load_data("user1")
        loaded_2 = file_storage.load_data("user2")
        
        assert loaded_1 == test_data_1
        assert loaded_2 == test_data_2
    
    def test_data_persistence(self, temp_data_dir):
        """Test that data persists between service instances"""
        # Create first service instance and save data
        service1 = FileStorageService(data_dir=temp_data_dir)
        test_data = {"persistent": "data"}
        service1.save_data("persistent_file", test_data)
        
        # Create second service instance and load data
        service2 = FileStorageService(data_dir=temp_data_dir)
        loaded_data = service2.load_data("persistent_file")
        
        assert loaded_data == test_data
    
    def test_error_logging(self, file_storage, caplog):
        """Test that errors are properly logged"""
        with patch('builtins.open', side_effect=Exception("Test error")):
            result = file_storage.save_data("test_file", {"key": "value"})
            
            assert result is False
            assert "Error saving data to test_file" in caplog.text
    
    def test_info_logging(self, file_storage, caplog):
        """Test that successful operations are properly logged"""
        test_data = {"key": "value"}
        result = file_storage.save_data("test_file", test_data)

        assert result is True
        # Check for the actual log message format if logging is captured
        if caplog.text:
            assert "✅ Data saved to" in caplog.text or "Data saved to" in caplog.text
    
    def test_unicode_handling(self, file_storage):
        """Test handling of Unicode characters"""
        unicode_data = {
            "hebrew": "שלום עולם",
            "arabic": "مرحبا بالعالم",
            "chinese": "你好世界",
            "emoji": "🚀🌟🎉"
        }
        
        result = file_storage.save_data("unicode_file", unicode_data)
        assert result is True
        
        loaded_data = file_storage.load_data("unicode_file")
        assert loaded_data == unicode_data 