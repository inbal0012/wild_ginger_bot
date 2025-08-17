"""
FileStorageService - Simple file-based storage for bot data persistence.
Handles saving and retrieving data to/from JSON files for development and testing.
"""

import json
import os
from typing import Any, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FileStorageService:
    """
    Simple file-based storage service for bot data persistence.
    Used for development and testing before implementing database storage.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the file storage service.
        
        Args:
            data_dir: Directory to store data files (default: "data")
        """
        self.data_dir = data_dir
        self._ensure_data_dir()
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Created data directory: {self.data_dir}")
    
    def _get_file_path(self, filename: str) -> str:
        """Get full file path for a given filename."""
        return os.path.join(self.data_dir, filename)
    
    def save_data(self, filename: str, data: Any) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            filename: Name of the file (without .json extension)
            data: Data to save (must be JSON serializable)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_file_path(f"{filename}.json")
            
            # Add metadata
            save_data = {
                "data": data,
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "data_type": type(data).__name__,
                    "version": "1.0"
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ Data saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving data to {filename}: {e}")
            return False
    
    def load_data(self, filename: str, default: Any = None) -> Any:
        """
        Load data from a JSON file.
        
        Args:
            filename: Name of the file (without .json extension)
            default: Default value to return if file doesn't exist or is invalid
            
        Returns:
            Loaded data or default value
        """
        try:
            file_path = self._get_file_path(f"{filename}.json")
            
            if not os.path.exists(file_path):
                logger.info(f"📁 No existing data file found: {file_path}")
                return default
            
            with open(file_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # expect a list of dicts
            if "data" not in save_data:
                logger.error(f"❌ {filename} Data not found in file: {save_data}")
                return default
            if "metadata" not in save_data:
                logger.error(f"❌ {filename} Metadata not found in file: {save_data}")
                return default
            return save_data["data"]
            
            
            # Extract the actual data
            
            data = save_data.get("data", default)
            metadata = save_data.get("metadata", {})
            
            logger.info(f"✅ Data loaded from {file_path} (saved: {metadata.get('saved_at', 'unknown')})")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error loading data from {filename}: {e}")
            return default
    
    def delete_data(self, filename: str) -> bool:
        """
        Delete a data file.
        
        Args:
            filename: Name of the file (without .json extension)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_file_path(f"{filename}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Deleted data file: {file_path}")
                return True
            else:
                logger.info(f"📁 File not found: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting data file {filename}: {e}")
            return False
    
    def list_data_files(self) -> list:
        """
        List all data files in the data directory.
        
        Returns:
            List of filenames (without .json extension)
        """
        try:
            files = []
            for file in os.listdir(self.data_dir):
                if file.endswith('.json'):
                    files.append(file[:-5])  # Remove .json extension
            return files
        except Exception as e:
            logger.error(f"❌ Error listing data files: {e}")
            return []
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a data file.
        
        Args:
            filename: Name of the file (without .json extension)
            
        Returns:
            Dictionary with file info or None if not found
        """
        try:
            file_path = self._get_file_path(f"{filename}.json")
            
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                "filename": filename,
                "file_path": file_path,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting file info for {filename}: {e}")
            return None
    
    def backup_data(self, filename: str, backup_suffix: str = None) -> bool:
        """
        Create a backup of a data file.
        
        Args:
            filename: Name of the file to backup (without .json extension)
            backup_suffix: Optional suffix for backup filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_file_path(f"{filename}.json")
            
            if not os.path.exists(file_path):
                logger.warning(f"📁 File not found for backup: {file_path}")
                return False
            
            if backup_suffix is None:
                backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            backup_filename = f"{filename}_backup_{backup_suffix}"
            backup_path = self._get_file_path(f"{backup_filename}.json")
            
            # Copy the file
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            logger.info(f"💾 Backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating backup for {filename}: {e}")
            return False 