"""
Adaptive File Organizer for the Academic Organizer application.

This module handles file organization, import, categorization, and content extraction
for academic materials and documents.
"""

import logging
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
import mimetypes


class AdaptiveFileOrganizer:
    """
    Adaptive File Organizer for the Academic Organizer application.
    
    This class is responsible for:
    - Organizing files by course, type, and semantic content
    - Importing files into the application storage
    - Automatically categorizing and tagging files
    - Extracting content for search functionality
    - Generating metadata for files
    """
    
    def __init__(self, db_manager):
        """
        Initialize the file organizer.
        
        Args:
            db_manager: The database manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
        self.base_storage_dir = Path.home() / ".academic_organizer" / "materials"
        self.base_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize supported file types and their extensions
        self.file_type_extensions = {
            "document": [".doc", ".docx", ".pdf", ".txt", ".rtf", ".odt"],
            "spreadsheet": [".xls", ".xlsx", ".csv", ".ods"],
            "presentation": [".ppt", ".pptx", ".odp"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
            "code": [".py", ".java", ".cpp", ".c", ".h", ".js", ".html", ".css", ".php", ".rb"],
            "data": [".json", ".xml", ".yaml", ".sql", ".db"],
            "archive": [".zip", ".rar", ".tar", ".gz", ".7z"],
            "media": [".mp3", ".mp4", ".wav", ".avi", ".mov"]
        }
        
        # Set up mime type detection
        mimetypes.init()
    
    # ------------------------------ #
    # File organization and storage  #
    # ------------------------------ #
    
    def import_file(self, file_path, course_id=None, title=None, tags=None):
        """
        Import a file into the application's storage and database.
        
        Args:
            file_path (str or Path): Path to the file to import
            course_id (int, optional): The course ID to associate with the file
            title (str, optional): The title for the material (defaults to filename)
            tags (str, optional): Comma-separated tags for the material
            
        Returns:
            int: The ID of the imported material, or None if import failed
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists() or not source_path.is_file():
                self.logger.error(f"File does not exist: {file_path}")
                return None
                
            # Generate title from filename if not provided
            if not title:
                title = source_path.stem
                
            # Determine file type
            file_type = self.determine_file_type(source_path)
            
            # Create a storage path based on course and file type
            storage_dir = self._get_storage_dir(course_id, file_type)
            
            # Generate a unique filename to avoid collisions
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            target_path = storage_dir / new_filename
            
            # Copy the file to storage
            shutil.copy2(source_path, target_path)
            
            # Extract text content for search indexing
            content_text = self.extract_text_content(target_path)
            
            # Store file information in database
            material_id = self._store_material_in_db(
                course_id=course_id,
                title=title,
                file_path=str(target_path),
                file_type=file_type,
                tags=tags,
                content_text=content_text
            )
            
            self.logger.info(f"File imported successfully: {target_path}")
            return material_id
            
        except Exception as e:
            self.logger.error(f"Error importing file: {e}", exc_info=True)
            return None
    
    def move_file(self, material_id, new_course_id=None):
        """
        Move a file to a different course's storage directory.
        
        Args:
            material_id (int): The ID of the material to move
            new_course_id (int, optional): The new course ID (None for uncategorized)
            
        Returns:
            bool: True if move successful, False otherwise
        """
        try:
            # Get the material from the database
            query = "SELECT * FROM materials WHERE id = ?"
            params = (material_id,)
            result = self.db_manager.execute_query(query, params)
            
            if not result:
                self.logger.error(f"Material not found: {material_id}")
                return False
                
            material = result[0]
            old_path = Path(material['file_path'])
            
            if not old_path.exists():
                self.logger.error(f"Material file not found: {old_path}")
                return False
                
            # Determine new storage directory
            new_storage_dir = self._get_storage_dir(new_course_id, material['file_type'])
            new_path = new_storage_dir / old_path.name
            
            # Move the file
            shutil.move(old_path, new_path)
            
            # Update the database
            update_query = """
            UPDATE materials 
            SET course_id = ?, file_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            update_params = (new_course_id, str(new_path), material_id)
            
            self.db_manager.execute_update(update_query, update_params)
            
            self.logger.info(f"File moved successfully: {old_path} -> {new_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving file: {e}", exc_info=True)
            return False
    
    def update_file_metadata(self, material_id, title=None, tags=None):
        """
        Update metadata for a file.
        
        Args:
            material_id (int): The ID of the material to update
            title (str, optional): The new title
            tags (str, optional): The new tags
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            update_fields = {}
            if title is not None:
                update_fields['title'] = title
            if tags is not None:
                update_fields['tags'] = tags
                
            if not update_fields:
                self.logger.warning("No fields provided for update")
                return False
                
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            
            query = f"UPDATE materials SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (material_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating file metadata: {e}", exc_info=True)
            return False
    
    def delete_file(self, material_id):
        """
        Delete a file from storage and database.
        
        Args:
            material_id (int): The ID of the material to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Get the material from the database
            query = "SELECT * FROM materials WHERE id = ?"
            params = (material_id,)
            result = self.db_manager.execute_query(query, params)
            
            if not result:
                self.logger.error(f"Material not found: {material_id}")
                return False
                
            material = result[0]
            file_path = Path(material['file_path'])
            
            # Delete from filesystem if exists
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                
            # Delete from database
            delete_query = "DELETE FROM materials WHERE id = ?"
            delete_params = (material_id,)
            
            rows_affected = self.db_manager.execute_update(delete_query, delete_params)
            
            self.logger.info(f"File deleted successfully: {file_path}")
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting file: {e}", exc_info=True)
            return False
    
    # ------------------------------ #
    # File retrieval and search      #
    # ------------------------------ #
    
    def get_file(self, material_id):
        """
        Get file information by material ID.
        
        Args:
            material_id (int): The ID of the material
            
        Returns:
            dict: The material data, or None if not found
        """
        try:
            query = """
            SELECT m.*, c.name as course_name
            FROM materials m
            LEFT JOIN courses c ON m.course_id = c.id
            WHERE m.id = ?
            """
            params = (material_id,)
            
            result = self.db_manager.execute_query(query, params)
            if result:
                return result[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting file: {e}", exc_info=True)
            return None
    
    def get_course_files(self, course_id, file_type=None):
        """
        Get all files for a course, optionally filtered by type.
        
        Args:
            course_id (int): The course ID
            file_type (str, optional): The file type to filter by
            
        Returns:
            list: List of material dictionaries
        """
        try:
            if file_type:
                query = """
                SELECT * FROM materials
                WHERE course_id = ? AND file_type = ?
                ORDER BY title
                """
                params = (course_id, file_type)
            else:
                query = """
                SELECT * FROM materials
                WHERE course_id = ?
                ORDER BY title
                """
                params = (course_id,)
                
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error getting course files: {e}", exc_info=True)
            return []
    
    def search_files(self, search_term, course_id=None):
        """
        Search for files by content or metadata.
        
        Args:
            search_term (str): The search term
            course_id (int, optional): Course ID to restrict search
            
        Returns:
            list: List of matching material dictionaries
        """
        try:
            # Use the virtual FTS table for full-text search
            base_query = """
            SELECT m.*, c.name as course_name, rank
            FROM materials m
            JOIN (
                SELECT rowid, rank
                FROM fts_materials
                WHERE fts_materials MATCH ?
            ) AS fts ON m.id = fts.rowid
            LEFT JOIN courses c ON m.course_id = c.id
            """
            
            if course_id is not None:
                query = base_query + " WHERE m.course_id = ? ORDER BY rank"
                params = (search_term, course_id)
            else:
                query = base_query + " ORDER BY rank"
                params = (search_term,)
                
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error searching files: {e}", exc_info=True)
            return []
    
    # ------------------------------ #
    # File analysis and processing   #
    # ------------------------------ #
    
    def determine_file_type(self, file_path):
        """
        Determine the type of a file based on its extension.
        
        Args:
            file_path (str or Path): Path to the file
            
        Returns:
            str: The determined file type
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Check if extension matches any known file type
        for file_type, extensions in self.file_type_extensions.items():
            if extension in extensions:
                return file_type
                
        # Use mime type as fallback
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type:
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('text/'):
                return 'document'
            elif mime_type.startswith('video/'):
                return 'media'
            elif mime_type.startswith('audio/'):
                return 'media'
                
        # Default if no match found
        return 'other'
    
    def extract_text_content(self, file_path):
        """
        Extract text content from a file for indexing.
        
        This is a placeholder for a more advanced implementation that would
        use appropriate libraries for each file type (e.g., PyPDF2 for PDFs,
        python-docx for Word documents).
        
        Args:
            file_path (str or Path): Path to the file
            
        Returns:
            str: Extracted text content, or empty string if extraction failed
        """
        path = Path(file_path)
        file_type = self.determine_file_type(path)
        
        # For simple text files, just read the content
        if file_type == 'document' and path.suffix.lower() in ['.txt', '.md']:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Error reading text file: {e}", exc_info=True)
                return ""
                
        # For PDF files, use PyPDF2 to extract text
        if file_type == 'document' and path.suffix.lower() == '.pdf':
            text = ""
            try:
                import PyPDF2
                with open(path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return text
            except Exception as e:
                self.logger.error(f"Error reading PDF: {e}", exc_info=True)
                return ""
                
        # For other file types, return placeholder
        # TODO: Implement proper content extraction for different file types
        return f"Content extraction not implemented for {path.suffix} files"
    
    def suggest_tags(self, file_path):
        """
        Suggest tags for a file based on its content and metadata.
        
        This is a placeholder for a more advanced implementation that would
        use NLP techniques to analyze file content and suggest relevant tags.
        
        Args:
            file_path (str or Path): Path to the file
            
        Returns:
            list: Suggested tags
        """
        # TODO: Implement intelligent tag suggestion
        # For now, just return some placeholder tags based on file type
        file_type = self.determine_file_type(file_path)
        
        if file_type == 'document':
            return ['reading', 'notes']
        elif file_type == 'presentation':
            return ['slides', 'lecture']
        elif file_type == 'spreadsheet':
            return ['data', 'analysis']
        elif file_type == 'image':
            return ['visual', 'diagram']
        elif file_type == 'code':
            return ['code', 'programming']
        else:
            return []
    
    # ------------------------------ #
    # Helper methods                 #
    # ------------------------------ #
    
    def _get_storage_dir(self, course_id, file_type):
        """
        Get the storage directory for a file based on course and type.
        
        Args:
            course_id (int or None): The course ID, or None for uncategorized
            file_type (str): The file type
            
        Returns:
            Path: The storage directory path
        """
        if course_id:
            # Get course code or name for the directory
            query = "SELECT code, name FROM courses WHERE id = ?"
            params = (course_id,)
            result = self.db_manager.execute_query(query, params)
            
            if result:
                course = result[0]
                course_code = course.get('code') or course.get('name')
                # Sanitize for filesystem
                course_dir = re.sub(r'[^\w\-\.]', '_', course_code)
                return self.base_storage_dir / course_dir / file_type
            
        # If no course ID or course not found, use uncategorized
        return self.base_storage_dir / "uncategorized" / file_type
    
    def _store_material_in_db(self, course_id, title, file_path, file_type, tags=None, content_text=None):
        """
        Store material information in the database.
        
        Args:
            course_id (int or None): The course ID, or None for uncategorized
            title (str): The material title
            file_path (str): Path where the file is stored
            file_type (str): The file type
            tags (str, optional): Comma-separated tags
            content_text (str, optional): Extracted text content for search
            
        Returns:
            int: The ID of the stored material, or None if storage failed
        """
        try:
            query = """
            INSERT INTO materials (course_id, title, file_path, file_type, tags, content_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (course_id, title, file_path, file_type, tags, content_text)
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            material_id = cursor.lastrowid
            return material_id
            
        except Exception as e:
            self.logger.error(f"Error storing material in database: {e}", exc_info=True)
            self.db_manager.get_connection().rollback()
            return None
    
    def get_storage_statistics(self):
        """
        Get statistical information about stored files.
        
        Returns:
            dict: Storage statistics
        """
        try:
            # Get total number of files
            query_count = "SELECT COUNT(*) as total_files FROM materials"
            result_count = self.db_manager.execute_query(query_count)
            
            # Get files by type
            query_type = """
            SELECT file_type, COUNT(*) as file_count 
            FROM materials 
            GROUP BY file_type
            """
            result_type = self.db_manager.execute_query(query_type)
            
            # Get files by course
            query_course = """
            SELECT c.name as course_name, COUNT(m.id) as file_count
            FROM courses c
            LEFT JOIN materials m ON c.id = m.course_id
            GROUP BY c.id
            ORDER BY file_count DESC
            """
            result_course = self.db_manager.execute_query(query_course)
            
            # Calculate total storage used (this would be more accurate with actual file sizes)
            query_storage = "SELECT COUNT(*) as total_files FROM materials"
            result_storage = self.db_manager.execute_query(query_storage)
            
            # Compile statistics
            statistics = {
                "total_files": result_count[0]['total_files'] if result_count else 0,
                "files_by_type": result_type,
                "files_by_course": result_course,
                "estimated_storage": f"{result_storage[0]['total_files'] * 1.5} MB (estimated)" if result_storage else "0 MB"
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Error getting storage statistics: {e}", exc_info=True)
            return {"total_files": 0, "files_by_type": [], "files_by_course": [], "estimated_storage": "0 MB"}