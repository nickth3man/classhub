"""
File Manager for the Academic Organizer application.

This module handles file storage, retrieval, and organization.
"""

import logging
import os
import shutil
import hashlib
import mimetypes
import uuid
from datetime import datetime
from pathlib import Path


class FileManager:
    """
    File Manager for the Academic Organizer application.
    
    This class is responsible for:
    - Uploading and storing files
    - Retrieving files
    - Organizing files by course and assignment
    - Tracking file metadata
    - File versioning
    """
    
    # File category constants
    CATEGORY_ASSIGNMENT = "assignment"
    CATEGORY_LECTURE = "lecture"
    CATEGORY_NOTE = "note"
    CATEGORY_SYLLABUS = "syllabus"
    CATEGORY_REFERENCE = "reference"
    CATEGORY_OTHER = "other"
    
    def __init__(self, db_manager, base_storage_path=None):
        """
        Initialize the file manager.
        
        Args:
            db_manager: The database manager instance
            base_storage_path (str, optional): Base path for file storage
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
        
        # Set base storage path - default to user's documents folder if not provided
        if base_storage_path is None:
            # Try to use user's documents folder as default
            try:
                import appdirs
                base_storage_path = os.path.join(
                    appdirs.user_data_dir("AcademicOrganizer", "AcademicOrganizer"),
                    "files"
                )
            except ImportError:
                # If appdirs is not available, use a relative path
                base_storage_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/files"))
                
        self.base_storage_path = base_storage_path
        
        # Ensure the storage directory exists
        os.makedirs(self.base_storage_path, exist_ok=True)
        
        # Create basic file directories
        self.init_storage_structure()
    
    def init_storage_structure(self):
        """
        Initialize the file storage directory structure.
        
        Creates the necessary directories for file organization.
        """
        try:
            # Create basic directory structure
            directories = [
                os.path.join(self.base_storage_path, self.CATEGORY_ASSIGNMENT),
                os.path.join(self.base_storage_path, self.CATEGORY_LECTURE),
                os.path.join(self.base_storage_path, self.CATEGORY_NOTE),
                os.path.join(self.base_storage_path, self.CATEGORY_SYLLABUS),
                os.path.join(self.base_storage_path, self.CATEGORY_REFERENCE),
                os.path.join(self.base_storage_path, self.CATEGORY_OTHER),
                os.path.join(self.base_storage_path, "temp")
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                
            self.logger.info("File storage structure initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing storage structure: {e}", exc_info=True)
    
    # --------------------------- #
    # File Management Operations #
    # --------------------------- #
    
    def save_file(self, file_path, original_filename, category=None, course_id=None, 
                assignment_id=None, description=None, tags=None, version=1):
        """
        Save a file to the system and database.
        
        Args:
            file_path (str): Path to the file to be saved
            original_filename (str): Original name of the file
            category (str, optional): File category
            course_id (int, optional): Associated course ID
            assignment_id (int, optional): Associated assignment ID
            description (str, optional): File description
            tags (list, optional): List of tags
            version (int, optional): File version number
            
        Returns:
            int: The ID of the saved file record, or None if saving failed
        """
        try:
            # Validate file existence
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return None
                
            # Default category if not provided
            if not category:
                category = self.CATEGORY_OTHER
                
            # Validate category
            valid_categories = [
                self.CATEGORY_ASSIGNMENT, self.CATEGORY_LECTURE, 
                self.CATEGORY_NOTE, self.CATEGORY_SYLLABUS,
                self.CATEGORY_REFERENCE, self.CATEGORY_OTHER
            ]
            
            if category not in valid_categories:
                self.logger.warning(f"Invalid category: {category}, using default")
                category = self.CATEGORY_OTHER
                
            # Generate a unique filename to avoid collisions
            file_extension = os.path.splitext(original_filename)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Create storage path based on category and optional course
            if course_id:
                storage_dir = os.path.join(self.base_storage_path, category, f"course_{course_id}")
            else:
                storage_dir = os.path.join(self.base_storage_path, category)
                
            # Create directory if it doesn't exist
            os.makedirs(storage_dir, exist_ok=True)
            
            # Full path for the stored file
            stored_file_path = os.path.join(storage_dir, unique_filename)
            
            # Calculate file hash for integrity checking
            file_hash = self.calculate_file_hash(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Determine file mime type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
                
            # Copy the file to storage
            shutil.copy2(file_path, stored_file_path)
            
            # Convert tags to string if provided
            tags_str = None
            if tags:
                if isinstance(tags, list):
                    tags_str = ','.join(tags)
                else:
                    tags_str = str(tags)
                    
            # Generate relative path for database storage
            relative_path = os.path.relpath(stored_file_path, self.base_storage_path)
            
            # Insert file record into database
            query = """
            INSERT INTO files (
                filename, original_filename, file_path, file_size, file_type,
                file_hash, category, course_id, assignment_id,
                description, tags, version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                unique_filename, original_filename, relative_path, file_size, mime_type,
                file_hash, category, course_id, assignment_id,
                description, tags_str, version
            )
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            file_id = cursor.lastrowid
            self.logger.info(f"File saved with ID: {file_id}")
            
            return file_id
            
        except Exception as e:
            self.logger.error(f"Error saving file: {e}", exc_info=True)
            
            # Cleanup if needed
            if 'stored_file_path' in locals() and os.path.exists(stored_file_path):
                try:
                    os.remove(stored_file_path)
                except Exception:
                    pass
                    
            self.db_manager.get_connection().rollback()
            return None
    
    def get_file(self, file_id):
        """
        Get a file by ID.
        
        Args:
            file_id (int): The file ID
            
        Returns:
            dict: The file data including its actual path, or None if not found
        """
        try:
            query = """
            SELECT f.*, c.name as course_name, a.title as assignment_title
            FROM files f
            LEFT JOIN courses c ON f.course_id = c.id
            LEFT JOIN assignments a ON f.assignment_id = a.id
            WHERE f.id = ?
            """
            params = (file_id,)
            
            result = self.db_manager.execute_query(query, params)
            
            if result:
                file_data = result[0]
                
                # Add full path for file access
                relative_path = file_data.get('file_path')
                if relative_path:
                    file_data['full_path'] = os.path.join(self.base_storage_path, relative_path)
                    
                return file_data
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting file: {e}", exc_info=True)
            return None
    
    def get_all_files(self, category=None, course_id=None, assignment_id=None, 
                    search_term=None, sort_by=None, sort_order='asc'):
        """
        Get all files with optional filtering.
        
        Args:
            category (str, optional): Filter by category
            course_id (int, optional): Filter by course ID
            assignment_id (int, optional): Filter by assignment ID
            search_term (str, optional): Search term to filter by filename or description
            sort_by (str, optional): Field to sort by
            sort_order (str, optional): Sort order (asc/desc)
            
        Returns:
            list: List of file dictionaries
        """
        try:
            # Build query with conditional filters
            query_parts = [
                "SELECT f.*, c.name as course_name, a.title as assignment_title",
                "FROM files f",
                "LEFT JOIN courses c ON f.course_id = c.id",
                "LEFT JOIN assignments a ON f.assignment_id = a.id",
                "WHERE 1=1"  # Base condition to simplify adding AND clauses
            ]
            params = []
            
            if category is not None:
                query_parts.append("AND f.category = ?")
                params.append(category)
                
            if course_id is not None:
                query_parts.append("AND f.course_id = ?")
                params.append(course_id)
                
            if assignment_id is not None:
                query_parts.append("AND f.assignment_id = ?")
                params.append(assignment_id)
                
            if search_term is not None:
                query_parts.append("AND (f.original_filename LIKE ? OR f.description LIKE ?)")
                search_pattern = f"%{search_term}%"
                params.append(search_pattern)
                params.append(search_pattern)
                
            # Add sorting
            if sort_by:
                # Map front-end field names to database columns if needed
                field_map = {
                    'filename': 'f.original_filename',
                    'size': 'f.file_size',
                    'date': 'f.created_at',
                    'type': 'f.file_type',
                    'category': 'f.category',
                    'course': 'c.name',
                    'assignment': 'a.title'
                }
                
                db_field = field_map.get(sort_by, f"f.{sort_by}")
                query_parts.append(f"ORDER BY {db_field} {sort_order.upper()}")
            else:
                # Default sort by created_at
                query_parts.append("ORDER BY f.created_at DESC")
                
            # Combine query parts
            query = " ".join(query_parts)
            
            # Execute query
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            # Add full paths for file access
            for file_data in results:
                relative_path = file_data.get('file_path')
                if relative_path:
                    file_data['full_path'] = os.path.join(self.base_storage_path, relative_path)
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting files: {e}", exc_info=True)
            return []
    
    def update_file_metadata(self, file_id, **kwargs):
        """
        Update file metadata.
        
        Args:
            file_id (int): The file ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get allowed fields
            allowed_fields = [
                'original_filename', 'category', 'course_id', 'assignment_id',
                'description', 'tags', 'is_favorite'
            ]
            
            # Filter kwargs to only include allowed fields
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                self.logger.warning("No valid fields provided for update")
                return False
                
            # Special handling for tags field
            if 'tags' in update_fields:
                tags = update_fields['tags']
                if isinstance(tags, list):
                    update_fields['tags'] = ','.join(tags)
                
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            
            query = f"UPDATE files SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (file_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating file metadata: {e}", exc_info=True)
            return False
    
    def delete_file(self, file_id):
        """
        Delete a file.
        
        Args:
            file_id (int): The file ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Get file info first
            file_data = self.get_file(file_id)
            if not file_data:
                self.logger.error(f"File not found: {file_id}")
                return False
                
            # Get file path
            full_path = file_data.get('full_path')
            if not full_path or not os.path.exists(full_path):
                self.logger.warning(f"File path not found: {full_path}")
                # Still delete the database record even if file is missing
            else:
                # Delete the actual file
                os.remove(full_path)
                
            # Delete the file record
            query = "DELETE FROM files WHERE id = ?"
            params = (file_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting file: {e}", exc_info=True)
            return False
    
    # --------------------------- #
    # File Operations            #
    # --------------------------- #
    
    def open_file(self, file_id):
        """
        Prepare a file for opening.
        
        Args:
            file_id (int): The file ID
            
        Returns:
            str: The full path to the file, or None if error
        """
        try:
            file_data = self.get_file(file_id)
            if not file_data:
                self.logger.error(f"File not found: {file_id}")
                return None
                
            full_path = file_data.get('full_path')
            if not full_path or not os.path.exists(full_path):
                self.logger.error(f"File path not found: {full_path}")
                return None
                
            # Update last accessed timestamp
            self.update_file_metadata(file_id, last_accessed=datetime.now().isoformat())
            
            return full_path
            
        except Exception as e:
            self.logger.error(f"Error opening file: {e}", exc_info=True)
            return None
    
    def save_new_version(self, file_id, new_file_path):
        """
        Save a new version of an existing file.
        
        Args:
            file_id (int): The existing file ID
            new_file_path (str): Path to the new version
            
        Returns:
            int: The ID of the new file version, or None if saving failed
        """
        try:
            # Get existing file info
            existing_file = self.get_file(file_id)
            if not existing_file:
                self.logger.error(f"Original file not found: {file_id}")
                return None
                
            # Calculate next version number
            current_version = existing_file.get('version', 1)
            next_version = current_version + 1
            
            # Save the new version
            return self.save_file(
                file_path=new_file_path,
                original_filename=existing_file.get('original_filename'),
                category=existing_file.get('category'),
                course_id=existing_file.get('course_id'),
                assignment_id=existing_file.get('assignment_id'),
                description=existing_file.get('description'),
                tags=existing_file.get('tags'),
                version=next_version
            )
            
        except Exception as e:
            self.logger.error(f"Error saving new file version: {e}", exc_info=True)
            return None
    
    def get_file_versions(self, original_filename, course_id=None, assignment_id=None):
        """
        Get all versions of a file.
        
        Args:
            original_filename (str): Original filename
            course_id (int, optional): Course ID to narrow search
            assignment_id (int, optional): Assignment ID to narrow search
            
        Returns:
            list: List of file versions sorted by version number
        """
        try:
            # Build query with conditional filters
            query_parts = [
                "SELECT f.*",
                "FROM files f",
                "WHERE f.original_filename = ?"
            ]
            params = [original_filename]
            
            if course_id is not None:
                query_parts.append("AND f.course_id = ?")
                params.append(course_id)
                
            if assignment_id is not None:
                query_parts.append("AND f.assignment_id = ?")
                params.append(assignment_id)
                
            # Sort by version
            query_parts.append("ORDER BY f.version")
            
            # Combine query parts
            query = " ".join(query_parts)
            
            # Execute query
            results = self.db_manager.execute_query(query, tuple(params))
            
            # Add full paths for file access
            for file_data in results:
                relative_path = file_data.get('file_path')
                if relative_path:
                    file_data['full_path'] = os.path.join(self.base_storage_path, relative_path)
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting file versions: {e}", exc_info=True)
            return []
    
    def import_file(self, source_path, category=None, course_id=None, assignment_id=None, 
                  description=None, tags=None):
        """
        Import an external file into the system.
        
        Args:
            source_path (str): Path to the source file
            category (str, optional): File category
            course_id (int, optional): Associated course ID
            assignment_id (int, optional): Associated assignment ID
            description (str, optional): File description
            tags (list, optional): List of tags
            
        Returns:
            int: The ID of the imported file, or None if import failed
        """
        try:
            if not os.path.exists(source_path):
                self.logger.error(f"Source file not found: {source_path}")
                return None
                
            # Get original filename from path
            original_filename = os.path.basename(source_path)
            
            # Save the file
            return self.save_file(
                file_path=source_path,
                original_filename=original_filename,
                category=category,
                course_id=course_id,
                assignment_id=assignment_id,
                description=description,
                tags=tags
            )
            
        except Exception as e:
            self.logger.error(f"Error importing file: {e}", exc_info=True)
            return None
    
    def export_file(self, file_id, target_path):
        """
        Export a file to an external location.
        
        Args:
            file_id (int): The file ID
            target_path (str): Target path to export to
            
        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            # Get file info
            file_data = self.get_file(file_id)
            if not file_data:
                self.logger.error(f"File not found: {file_id}")
                return False
                
            # Get file path
            source_path = file_data.get('full_path')
            if not source_path or not os.path.exists(source_path):
                self.logger.error(f"File path not found: {source_path}")
                return False
                
            # Check if target is a directory
            if os.path.isdir(target_path):
                # Use original filename in the target directory
                original_filename = file_data.get('original_filename')
                target_file = os.path.join(target_path, original_filename)
            else:
                # Use the target path as is
                target_file = target_path
                
            # Copy the file
            shutil.copy2(source_path, target_file)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting file: {e}", exc_info=True)
            return False
    
    # --------------------------- #
    # File Analysis & Reporting  #
    # --------------------------- #
    
    def get_files_by_course(self):
        """
        Get files organized by course.
        
        Returns:
            dict: Dictionary with course IDs as keys and file lists as values
        """
        try:
            # Get all files
            query = """
            SELECT f.*, c.name as course_name, c.code as course_code
            FROM files f
            LEFT JOIN courses c ON f.course_id = c.id
            WHERE f.course_id IS NOT NULL
            ORDER BY c.name, f.original_filename
            """
            
            results = self.db_manager.execute_query(query)
            
            # Organize by course
            files_by_course = {}
            
            for file_data in results:
                course_id = file_data.get('course_id')
                
                if course_id not in files_by_course:
                    files_by_course[course_id] = {
                        'course_name': file_data.get('course_name'),
                        'course_code': file_data.get('course_code'),
                        'files': []
                    }
                    
                # Add full path for file access
                relative_path = file_data.get('file_path')
                if relative_path:
                    file_data['full_path'] = os.path.join(self.base_storage_path, relative_path)
                    
                files_by_course[course_id]['files'].append(file_data)
                
            return files_by_course
            
        except Exception as e:
            self.logger.error(f"Error getting files by course: {e}", exc_info=True)
            return {}
    
    def get_storage_stats(self):
        """
        Get storage statistics.
        
        Returns:
            dict: Statistics about file storage
        """
        try:
            # Get total file count and size
            count_query = "SELECT COUNT(*) as count, SUM(file_size) as total_size FROM files"
            count_result = self.db_manager.execute_query(count_query)
            
            total_count = count_result[0]['count'] if count_result else 0
            total_size = count_result[0]['total_size'] if count_result else 0
            
            # Get counts by category
            category_query = """
            SELECT category, COUNT(*) as count, SUM(file_size) as total_size
            FROM files
            GROUP BY category
            """
            category_results = self.db_manager.execute_query(category_query)
            
            # Get counts by file type (group similar types)
            type_query = """
            SELECT 
                CASE
                    WHEN file_type LIKE 'image/%' THEN 'Images'
                    WHEN file_type LIKE 'application/pdf' THEN 'PDFs'
                    WHEN file_type LIKE 'text/%' THEN 'Text'
                    WHEN file_type LIKE 'application/msword' THEN 'Documents'
                    WHEN file_type LIKE 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 'Documents'
                    WHEN file_type LIKE 'application/vnd.ms-excel' THEN 'Spreadsheets'
                    WHEN file_type LIKE 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' THEN 'Spreadsheets'
                    WHEN file_type LIKE 'application/vnd.ms-powerpoint' THEN 'Presentations'
                    WHEN file_type LIKE 'application/vnd.openxmlformats-officedocument.presentationml.presentation' THEN 'Presentations'
                    ELSE 'Other'
                END as file_group,
                COUNT(*) as count,
                SUM(file_size) as total_size
            FROM files
            GROUP BY file_group
            """
            type_results = self.db_manager.execute_query(type_query)
            
            # Format sizes to human-readable
            stats = {
                'total_files': total_count,
                'total_size': total_size,
                'total_size_formatted': self.format_file_size(total_size),
                'by_category': {},
                'by_type': {}
            }
            
            # Process category results
            for category in category_results:
                cat_name = category['category']
                cat_count = category['count']
                cat_size = category['total_size'] or 0
                
                stats['by_category'][cat_name] = {
                    'count': cat_count,
                    'size': cat_size,
                    'size_formatted': self.format_file_size(cat_size)
                }
                
            # Process type results
            for file_type in type_results:
                type_name = file_type['file_group']
                type_count = file_type['count']
                type_size = file_type['total_size'] or 0
                
                stats['by_type'][type_name] = {
                    'count': type_count,
                    'size': type_size,
                    'size_formatted': self.format_file_size(type_size)
                }
                
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}", exc_info=True)
            return {
                'total_files': 0,
                'total_size': 0,
                'total_size_formatted': '0 B',
                'by_category': {},
                'by_type': {}
            }
    
    def search_file_contents(self, search_term, file_type=None):
        """
        Search for files containing the given text (limited to text-based files).
        
        Args:
            search_term (str): Text to search for
            file_type (str, optional): Limit search to specific file type
            
        Returns:
            list: List of matching files
        """
        try:
            # Get files that could contain searchable text
            query_parts = [
                "SELECT * FROM files",
                "WHERE file_type LIKE 'text/%'",  # Text files
                "OR file_type = 'application/pdf'"  # PDFs
            ]
            params = []
            
            if file_type:
                query_parts.append("AND file_type LIKE ?")
                params.append(f"%{file_type}%")
                
            query = " ".join(query_parts)
            
            # Execute query
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            # Check each file for the search term
            matching_files = []
            
            for file_data in results:
                relative_path = file_data.get('file_path')
                if not relative_path:
                    continue
                    
                full_path = os.path.join(self.base_storage_path, relative_path)
                if not os.path.exists(full_path):
                    continue
                    
                # Simple text search for text files
                # Note: This is a basic implementation. For real-world use,
                # you'd want to use libraries like PyPDF2 for PDFs, etc.
                try:
                    file_type = file_data.get('file_type', '')
                    
                    if file_type.startswith('text/'):
                        # For text files
                        with open(full_path, 'r', errors='ignore') as f:
                            content = f.read()
                            if search_term.lower() in content.lower():
                                file_data['full_path'] = full_path
                                matching_files.append(file_data)
                except:
                    # Skip files that can't be read
                    continue
                    
            return matching_files
            
        except Exception as e:
            self.logger.error(f"Error searching file contents: {e}", exc_info=True)
            return []
    
    # --------------------------- #
    # Helper Methods            #
    # --------------------------- #
    
    def calculate_file_hash(self, file_path):
        """
        Calculate MD5 hash of a file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: Hexadecimal hash string
        """
        try:
            hash_md5 = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
                    
            return hash_md5.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating file hash: {e}", exc_info=True)
            return None
    
    def format_file_size(self, size_bytes):
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes (int): Size in bytes
            
        Returns:
            str: Formatted size string
        """
        if size_bytes is None:
            return "0 B"
            
        # Convert to float to handle division
        size = float(size_bytes)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0 or unit == 'TB':
                break
            size /= 1024.0
            
        return f"{size:.2f} {unit}"
    
    def get_file_categories(self):
        """
        Get a list of all file categories.
        
        Returns:
            list: List of category strings
        """
        return [
            self.CATEGORY_ASSIGNMENT, self.CATEGORY_LECTURE, 
            self.CATEGORY_NOTE, self.CATEGORY_SYLLABUS,
            self.CATEGORY_REFERENCE, self.CATEGORY_OTHER
        ]
    
    def get_file_icon(self, file_type):
        """
        Get appropriate icon name for a file type.
        
        Args:
            file_type (str): MIME type of the file
            
        Returns:
            str: Icon name/class
        """
        if not file_type:
            return "file"
            
        file_type = file_type.lower()
        
        if file_type.startswith("image/"):
            return "image"
        elif file_type == "application/pdf":
            return "file-pdf"
        elif file_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            return "file-word"
        elif file_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            return "file-excel"
        elif file_type in ["application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]:
            return "file-powerpoint"
        elif file_type.startswith("text/"):
            return "file-text"
        elif file_type.startswith("video/"):
            return "file-video"
        elif file_type.startswith("audio/"):
            return "file-audio"
        elif file_type == "application/zip" or file_type == "application/x-rar-compressed":
            return "file-archive"
        elif file_type.startswith("application/"):
            return "file-code"
        else:
            return "file"
            
    def clean_temp_files(self):
        """
        Clean up temporary files.
        
        Returns:
            int: Number of files removed
        """
        try:
            temp_dir = os.path.join(self.base_storage_path, "temp")
            if not os.path.exists(temp_dir):
                return 0
                
            count = 0
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        # Check if file is older than 24 hours
                        file_time = os.path.getmtime(file_path)
                        if (datetime.now().timestamp() - file_time) > (24 * 3600):
                            os.remove(file_path)
                            count += 1
                    except:
                        continue
                        
            return count
            
        except Exception as e:
            self.logger.error(f"Error cleaning temp files: {e}", exc_info=True)
            return 0