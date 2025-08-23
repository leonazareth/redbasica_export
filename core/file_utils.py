"""
File utilities and security functions for the Flexible Sewerage DXF Export Plugin.

This module provides secure file operations, path validation, and permission checking
to prevent security issues and provide clear error messages.
"""

import os
import stat
import tempfile
from pathlib import Path
from typing import Tuple, Optional, List

try:
    from .exceptions import FilePermissionError, ExportError
except ImportError:
    from exceptions import FilePermissionError, ExportError


class FileSecurityValidator:
    """Validates file operations for security and accessibility."""
    
    @staticmethod
    def validate_output_path(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate output file path for security and accessibility.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path).resolve()
            
            # Check for directory traversal attempts
            if '..' in str(path) or str(path).startswith('/'):
                return False, "Path contains directory traversal sequences"
            
            # Check if path is absolute and reasonable
            if not path.is_absolute():
                return False, "Path must be absolute"
            
            # Check directory exists
            if not path.parent.exists():
                return False, f"Directory does not exist: {path.parent}"
            
            # Check directory is writable
            if not os.access(path.parent, os.W_OK):
                return False, f"No write permission to directory: {path.parent}"
            
            # If file exists, check if it's writable
            if path.exists():
                if not os.access(path, os.W_OK):
                    return False, f"File exists but is not writable: {path}"
                
                # Check if file is locked by another process
                try:
                    with open(path, 'a'):
                        pass
                except IOError:
                    return False, f"File is locked by another process: {path}"
            
            return True, None
            
        except Exception as e:
            return False, f"Path validation error: {e}"
    
    @staticmethod
    def validate_template_path(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate template file path for security and accessibility.
        
        Args:
            file_path: Template file path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path).resolve()
            
            # Check file exists
            if not path.exists():
                return False, f"Template file does not exist: {path}"
            
            # Check file is readable
            if not os.access(path, os.R_OK):
                return False, f"Template file is not readable: {path}"
            
            # Check file size (prevent extremely large files)
            file_size = path.stat().st_size
            if file_size == 0:
                return False, f"Template file is empty: {path}"
            
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                return False, f"Template file is too large ({file_size / 1024 / 1024:.1f}MB > {max_size / 1024 / 1024}MB)"
            
            # Check file extension
            if path.suffix.lower() != '.dxf':
                return False, f"Template file must have .dxf extension, got: {path.suffix}"
            
            return True, None
            
        except Exception as e:
            return False, f"Template validation error: {e}"
    
    @staticmethod
    def create_secure_temp_file(suffix: str = '.dxf') -> Tuple[str, Optional[str]]:
        """
        Create a secure temporary file for DXF operations.
        
        Args:
            suffix: File suffix/extension
            
        Returns:
            Tuple of (temp_file_path, error_message)
        """
        try:
            # Create temporary file with secure permissions
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix='redbasica_export_')
            os.close(fd)  # Close file descriptor, we just need the path
            
            # Set secure permissions (owner read/write only)
            os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)
            
            return temp_path, None
            
        except Exception as e:
            return "", f"Failed to create temporary file: {e}"
    
    @staticmethod
    def cleanup_temp_file(file_path: str) -> bool:
        """
        Safely cleanup temporary file.
        
        Args:
            file_path: Path to temporary file
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception:
            return False


class PathValidator:
    """Validates and normalizes file paths."""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        Normalize file path for consistent handling.
        
        Args:
            path: File path to normalize
            
        Returns:
            Normalized path string
        """
        return str(Path(path).resolve())
    
    @staticmethod
    def ensure_dxf_extension(path: str) -> str:
        """
        Ensure file path has .dxf extension.
        
        Args:
            path: File path
            
        Returns:
            Path with .dxf extension
        """
        path_obj = Path(path)
        if path_obj.suffix.lower() != '.dxf':
            return str(path_obj.with_suffix('.dxf'))
        return path
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        Create a safe filename by removing/replacing problematic characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename string
        """
        # Remove or replace problematic characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in '.-_':
                safe_chars.append(char)
            elif char in ' /\\':
                safe_chars.append('_')
        
        safe_name = ''.join(safe_chars)
        
        # Ensure it's not empty and doesn't start with dot
        if not safe_name or safe_name.startswith('.'):
            safe_name = 'export_' + safe_name
        
        return safe_name
    
    @staticmethod
    def validate_path_length(path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate path length for filesystem compatibility.
        
        Args:
            path: File path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Windows has a 260 character limit for full paths
        max_path_length = 260
        
        if len(path) > max_path_length:
            return False, f"Path too long ({len(path)} > {max_path_length} characters)"
        
        # Check individual component lengths
        path_obj = Path(path)
        for part in path_obj.parts:
            if len(part) > 255:  # Most filesystems limit to 255 chars per component
                return False, f"Path component too long: '{part}' ({len(part)} > 255 characters)"
        
        return True, None


class FileOperationHelper:
    """Helper class for safe file operations."""
    
    @staticmethod
    def check_disk_space(path: str, required_mb: int = 10) -> Tuple[bool, Optional[str]]:
        """
        Check available disk space at target location.
        
        Args:
            path: Target file path
            required_mb: Required space in megabytes
            
        Returns:
            Tuple of (sufficient_space, error_message)
        """
        try:
            path_obj = Path(path)
            target_dir = path_obj.parent if path_obj.parent.exists() else path_obj
            
            # Get disk usage statistics
            statvfs = os.statvfs(target_dir)
            available_bytes = statvfs.f_frsize * statvfs.f_bavail
            available_mb = available_bytes / (1024 * 1024)
            
            if available_mb < required_mb:
                return False, f"Insufficient disk space: {available_mb:.1f}MB available, {required_mb}MB required"
            
            return True, None
            
        except Exception as e:
            # If we can't check disk space, assume it's okay but warn
            return True, f"Could not check disk space: {e}"
    
    @staticmethod
    def backup_existing_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Create backup of existing file before overwriting.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Tuple of (backup_created, backup_path_or_error)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return True, "No existing file to backup"
            
            # Create backup with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = path.with_name(f"{path.stem}_backup_{timestamp}{path.suffix}")
            
            # Copy file to backup location
            import shutil
            shutil.copy2(path, backup_path)
            
            return True, str(backup_path)
            
        except Exception as e:
            return False, f"Failed to create backup: {e}"
    
    @staticmethod
    def verify_file_integrity(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Perform basic file integrity check.
        
        Args:
            file_path: Path to file to verify
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False, "File does not exist"
            
            # Check file size
            file_size = path.stat().st_size
            if file_size == 0:
                return False, "File is empty"
            
            # Try to read first few bytes to ensure file is accessible
            with open(path, 'rb') as f:
                header = f.read(100)
                if not header:
                    return False, "File appears to be empty or unreadable"
            
            return True, None
            
        except Exception as e:
            return False, f"File integrity check failed: {e}"


def check_file_permissions(file_path: str, operation: str = "write") -> None:
    """
    Check file permissions and raise appropriate exception if insufficient.
    
    Args:
        file_path: Path to check
        operation: Type of operation (read, write, create)
        
    Raises:
        FilePermissionError: If permissions are insufficient
    """
    validator = FileSecurityValidator()
    
    if operation == "write" or operation == "create":
        is_valid, error = validator.validate_output_path(file_path)
    elif operation == "read":
        is_valid, error = validator.validate_template_path(file_path)
    else:
        raise ValueError(f"Unknown operation type: {operation}")
    
    if not is_valid:
        raise FilePermissionError(file_path, operation)


def validate_and_prepare_output_path(output_path: str) -> str:
    """
    Validate and prepare output path for DXF export.
    
    Args:
        output_path: Requested output path
        
    Returns:
        Validated and normalized output path
        
    Raises:
        FilePermissionError: If path is invalid or inaccessible
        ExportError: If path preparation fails
    """
    try:
        # Normalize path
        normalized_path = PathValidator.normalize_path(output_path)
        
        # Ensure .dxf extension
        dxf_path = PathValidator.ensure_dxf_extension(normalized_path)
        
        # Validate path length
        length_valid, length_error = PathValidator.validate_path_length(dxf_path)
        if not length_valid:
            raise ExportError(f"Path validation failed: {length_error}")
        
        # Check security and permissions
        check_file_permissions(dxf_path, "write")
        
        # Check disk space
        space_valid, space_error = FileOperationHelper.check_disk_space(dxf_path)
        if not space_valid:
            raise ExportError(f"Disk space check failed: {space_error}")
        
        return dxf_path
        
    except FilePermissionError:
        raise  # Re-raise permission errors as-is
    except Exception as e:
        raise ExportError(f"Failed to prepare output path: {e}")


def create_backup_if_exists(file_path: str) -> Optional[str]:
    """
    Create backup of existing file if it exists.
    
    Args:
        file_path: Path to potentially existing file
        
    Returns:
        Path to backup file if created, None if no backup needed
        
    Raises:
        ExportError: If backup creation fails
    """
    try:
        backup_created, backup_info = FileOperationHelper.backup_existing_file(file_path)
        
        if not backup_created:
            raise ExportError(f"Backup creation failed: {backup_info}")
        
        # Return backup path if a backup was actually created
        if backup_info and backup_info != "No existing file to backup":
            return backup_info
        
        return None
        
    except Exception as e:
        raise ExportError(f"Backup operation failed: {e}")