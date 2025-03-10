"""
Search Processor for the Academic Organizer application.

This module provides unified search functionality across all entities
(assignments, courses, materials, etc.) in the application.
"""

import logging
import re
from datetime import datetime
import json
from collections import defaultdict


class SearchProcessor:
    """
    Search Processor for the Academic Organizer application.
    
    This class is responsible for:
    - Unified search across all entities (assignments, courses, materials)
    - Advanced search with filters and query parsing
    - Relevance ranking of search results
    - Query suggestions and search history management
    """
    
    # Search entity types
    ENTITY_ASSIGNMENT = "assignment"
    ENTITY_COURSE = "course"
    ENTITY_MATERIAL = "material"
    ENTITY_TERM = "term"
    
    # Search result score thresholds
    SCORE_EXACT_MATCH = 100
    SCORE_HIGH_RELEVANCE = 75
    SCORE_MEDIUM_RELEVANCE = 50
    SCORE_LOW_RELEVANCE = 25
    
    def __init__(self, db_manager):
        """
        Initialize the search processor.
        
        Args:
            db_manager: The database manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
        self.search_history = []
        
    # --------------------------- #
    # Main Search Functions      #
    # --------------------------- #
    
    def search(self, query, entity_types=None, filters=None, limit=20):
        """
        Perform a unified search across specified entity types.
        
        Args:
            query (str): The search query
            entity_types (list, optional): List of entity types to search 
                (defaults to all entity types)
            filters (dict, optional): Additional filters for search
            limit (int, optional): Maximum number of results to return
            
        Returns:
            dict: Dictionary with search results by entity type and metadata
        """
        try:
            if not query:
                return {"results": {}, "total_count": 0, "query": ""}
                
            # Clean and normalize the query
            cleaned_query = self._clean_query(query)
            
            # Add to search history
            self._add_to_history(cleaned_query)
            
            # Determine which entity types to search
            if not entity_types:
                entity_types = [
                    self.ENTITY_ASSIGNMENT,
                    self.ENTITY_COURSE,
                    self.ENTITY_MATERIAL
                ]
                
            # Initialize results container
            results = {}
            total_count = 0
            
            # Search each entity type
            for entity_type in entity_types:
                if entity_type == self.ENTITY_ASSIGNMENT:
                    entity_results = self._search_assignments(cleaned_query, filters, limit)
                elif entity_type == self.ENTITY_COURSE:
                    entity_results = self._search_courses(cleaned_query, filters, limit)
                elif entity_type == self.ENTITY_MATERIAL:
                    entity_results = self._search_materials(cleaned_query, filters, limit)
                elif entity_type == self.ENTITY_TERM:
                    entity_results = self._search_terms(cleaned_query, filters, limit)
                else:
                    self.logger.warning(f"Unknown entity type: {entity_type}")
                    continue
                    
                results[entity_type] = entity_results
                total_count += len(entity_results)
                
            # Return complete search results
            return {
                "results": results,
                "total_count": total_count,
                "query": cleaned_query
            }
            
        except Exception as e:
            self.logger.error(f"Error performing search: {e}", exc_info=True)
            return {"results": {}, "total_count": 0, "query": query, "error": str(e)}
    
    def advanced_search(self, params):
        """
        Perform an advanced search with complex filtering.
        
        Args:
            params (dict): Advanced search parameters including:
                - query: The search query
                - entity_types: List of entity types to search
                - course_id: Filter by course ID
                - term_id: Filter by term ID
                - date_range: Dictionary with start_date and end_date
                - status: Filter by status (for assignments)
                - priority: Filter by priority (for assignments)
                - file_type: Filter by file type (for materials)
                - sort_by: Field to sort results by
                - sort_order: Sort order (asc/desc)
                - limit: Maximum number of results
                - offset: Offset for pagination
            
        Returns:
            dict: Dictionary with search results and metadata
        """
        try:
            # Extract and validate parameters
            query = params.get('query', '')
            entity_types = params.get('entity_types')
            
            # Build filters from params
            filters = {}
            
            if 'course_id' in params:
                filters['course_id'] = params['course_id']
                
            if 'term_id' in params:
                filters['term_id'] = params['term_id']
                
            if 'date_range' in params:
                filters['date_range'] = params['date_range']
                
            if 'status' in params:
                filters['status'] = params['status']
                
            if 'priority' in params:
                filters['priority'] = params['priority']
                
            if 'file_type' in params:
                filters['file_type'] = params['file_type']
                
            # Sort parameters
            sort_by = params.get('sort_by')
            sort_order = params.get('sort_order', 'desc')
            
            if sort_by:
                filters['sort'] = {
                    'field': sort_by,
                    'order': sort_order
                }
                
            # Pagination parameters
            limit = params.get('limit', 20)
            offset = params.get('offset', 0)
            
            # Perform base search
            search_results = self.search(query, entity_types, filters, limit)
            
            # Apply additional processing for advanced search
            # (could include additional filtering, post-processing, etc.)
            
            # Add pagination metadata
            search_results['pagination'] = {
                'limit': limit,
                'offset': offset,
                'has_more': False  # This would need to be calculated based on total results
            }
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error performing advanced search: {e}", exc_info=True)
            return {"results": {}, "total_count": 0, "query": params.get('query', ''), "error": str(e)}
    
    def get_search_suggestions(self, partial_query, limit=5):
        """
        Get search suggestions based on partial query.
        
        Args:
            partial_query (str): The partial search query
            limit (int, optional): Maximum number of suggestions to return
            
        Returns:
            list: List of search suggestions
        """
        try:
            if not partial_query or len(partial_query) < 2:
                return []
                
            # Clean the partial query
            cleaned_partial = self._clean_query(partial_query)
            
            # Get suggestions from various sources
            
            # 1. From search history
            history_suggestions = [
                item for item in self.search_history 
                if item.lower().startswith(cleaned_partial.lower())
            ]
            
            # 2. From common entity fields
            # Courses
            course_query = """
            SELECT name FROM courses
            WHERE name LIKE ? 
            LIMIT ?
            """
            course_params = (f"{cleaned_partial}%", limit)
            course_results = self.db_manager.execute_query(course_query, course_params)
            course_suggestions = [result['name'] for result in course_results]
            
            # Assignments
            assignment_query = """
            SELECT title FROM assignments
            WHERE title LIKE ? 
            LIMIT ?
            """
            assignment_params = (f"{cleaned_partial}%", limit)
            assignment_results = self.db_manager.execute_query(assignment_query, assignment_params)
            assignment_suggestions = [result['title'] for result in assignment_results]
            
            # Materials
            material_query = """
            SELECT title FROM materials
            WHERE title LIKE ? 
            LIMIT ?
            """
            material_params = (f"{cleaned_partial}%", limit)
            material_results = self.db_manager.execute_query(material_query, material_params)
            material_suggestions = [result['title'] for result in material_results]
            
            # Combine and deduplicate suggestions
            all_suggestions = []
            all_suggestions.extend(history_suggestions)
            all_suggestions.extend(course_suggestions)
            all_suggestions.extend(assignment_suggestions)
            all_suggestions.extend(material_suggestions)
            
            # Remove duplicates while preserving order
            unique_suggestions = []
            for suggestion in all_suggestions:
                if suggestion not in unique_suggestions:
                    unique_suggestions.append(suggestion)
                    
            return unique_suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting search suggestions: {e}", exc_info=True)
            return []
    
    def get_recent_searches(self, limit=10):
        """
        Get recent search queries.
        
        Args:
            limit (int, optional): Maximum number of recent searches to return
            
        Returns:
            list: List of recent search queries
        """
        # Return most recent searches first (up to limit)
        return self.search_history[-limit:][::-1]
    
    # --------------------------- #
    # Entity-Specific Search     #
    # --------------------------- #
    
    def _search_assignments(self, query, filters=None, limit=20):
        """
        Search for assignments.
        
        Args:
            query (str): The search query
            filters (dict, optional): Additional filters
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of matching assignment dictionaries with relevance scores
        """
        try:
            # Build base query parts
            if query:
                # Use FTS for text search if query is provided
                base_query_parts = [
                    "SELECT a.*, c.name as course_name, rank",
                    "FROM assignments a",
                    "JOIN courses c ON a.course_id = c.id",
                    "JOIN (SELECT rowid, rank FROM fts_assignments WHERE fts_assignments MATCH ?) AS fts ON a.id = fts.rowid",
                    "WHERE 1=1"
                ]
                params = [query]
            else:
                # Just use regular selection if no query
                base_query_parts = [
                    "SELECT a.*, c.name as course_name",
                    "FROM assignments a",
                    "JOIN courses c ON a.course_id = c.id",
                    "WHERE 1=1"
                ]
                params = []
                
            # Apply filters if provided
            if filters:
                if 'course_id' in filters:
                    base_query_parts.append("AND a.course_id = ?")
                    params.append(filters['course_id'])
                    
                if 'status' in filters:
                    base_query_parts.append("AND a.status = ?")
                    params.append(filters['status'])
                    
                if 'priority' in filters:
                    base_query_parts.append("AND a.priority = ?")
                    params.append(filters['priority'])
                    
                if 'date_range' in filters:
                    date_range = filters['date_range']
                    if 'start_date' in date_range:
                        base_query_parts.append("AND a.due_date >= ?")
                        params.append(date_range['start_date'])
                    if 'end_date' in date_range:
                        base_query_parts.append("AND a.due_date <= ?")
                        params.append(date_range['end_date'])
                        
            # Apply sorting if specified
            if filters and 'sort' in filters:
                sort = filters['sort']
                sort_field = sort.get('field', 'due_date')
                sort_order = sort.get('order', 'desc').upper()
                
                # Map front-end field names to database columns if needed
                field_map = {
                    'title': 'a.title',
                    'due_date': 'a.due_date',
                    'priority': 'a.priority',
                    'status': 'a.status',
                    'course': 'c.name'
                }
                
                db_field = field_map.get(sort_field, sort_field)
                base_query_parts.append(f"ORDER BY {db_field} {sort_order}")
            else:
                # Default sorting: by relevance if search query provided, otherwise by due date
                if query:
                    base_query_parts.append("ORDER BY rank")
                else:
                    base_query_parts.append("ORDER BY a.due_date")
                    
            # Apply limit
            base_query_parts.append("LIMIT ?")
            params.append(limit)
            
            # Build and execute final query
            final_query = " ".join(base_query_parts)
            results = self.db_manager.execute_query(final_query, tuple(params))
            
            # Post-process results to add entity type and adjust format
            for result in results:
                result['entity_type'] = self.ENTITY_ASSIGNMENT
                result['display_name'] = result['title']
                result['display_date'] = result['due_date']
                
                # Calculate relevance score if not from FTS
                if query and 'rank' in result:
                    # SQLite FTS rank is inverted (lower is better)
                    # Convert to a 0-100 score where higher is better
                    base_score = 100 - min(result['rank'] * 10, 90)
                    
                    # Exact title match bonus
                    if query.lower() == result['title'].lower():
                        base_score = self.SCORE_EXACT_MATCH
                        
                    result['relevance_score'] = base_score
                else:
                    result['relevance_score'] = self.SCORE_MEDIUM_RELEVANCE
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching assignments: {e}", exc_info=True)
            return []
    
    def _search_courses(self, query, filters=None, limit=20):
        """
        Search for courses.
        
        Args:
            query (str): The search query
            filters (dict, optional): Additional filters
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of matching course dictionaries with relevance scores
        """
        try:
            # Build base query parts
            if query:
                # Use FTS for text search if query is provided
                base_query_parts = [
                    "SELECT c.*, t.name as term_name, rank",
                    "FROM courses c",
                    "LEFT JOIN terms t ON c.term_id = t.id",
                    "JOIN (SELECT rowid, rank FROM fts_courses WHERE fts_courses MATCH ?) AS fts ON c.id = fts.rowid",
                    "WHERE 1=1"
                ]
                params = [query]
            else:
                # Just use regular selection if no query
                base_query_parts = [
                    "SELECT c.*, t.name as term_name",
                    "FROM courses c",
                    "LEFT JOIN terms t ON c.term_id = t.id",
                    "WHERE 1=1"
                ]
                params = []
                
            # Apply filters if provided
            if filters:
                if 'term_id' in filters:
                    base_query_parts.append("AND c.term_id = ?")
                    params.append(filters['term_id'])
                    
                if 'is_active' in filters:
                    base_query_parts.append("AND c.is_active = ?")
                    params.append(filters['is_active'])
                    
            # Apply sorting if specified
            if filters and 'sort' in filters:
                sort = filters['sort']
                sort_field = sort.get('field', 'name')
                sort_order = sort.get('order', 'asc').upper()
                
                # Map front-end field names to database columns if needed
                field_map = {
                    'name': 'c.name',
                    'code': 'c.code',
                    'instructor': 'c.instructor',
                    'term': 't.name'
                }
                
                db_field = field_map.get(sort_field, sort_field)
                base_query_parts.append(f"ORDER BY {db_field} {sort_order}")
            else:
                # Default sorting: by relevance if search query provided, otherwise by name
                if query:
                    base_query_parts.append("ORDER BY rank")
                else:
                    base_query_parts.append("ORDER BY c.name")
                    
            # Apply limit
            base_query_parts.append("LIMIT ?")
            params.append(limit)
            
            # Build and execute final query
            final_query = " ".join(base_query_parts)
            results = self.db_manager.execute_query(final_query, tuple(params))
            
            # Post-process results to add entity type and adjust format
            for result in results:
                result['entity_type'] = self.ENTITY_COURSE
                result['display_name'] = result['name']
                
                # Include code in display name if available
                if result['code']:
                    result['display_name'] = f"{result['code']} - {result['name']}"
                    
                result['display_date'] = None
                
                # Calculate relevance score if not from FTS
                if query and 'rank' in result:
                    # SQLite FTS rank is inverted (lower is better)
                    # Convert to a 0-100 score where higher is better
                    base_score = 100 - min(result['rank'] * 10, 90)
                    
                    # Exact name match bonus
                    if query.lower() == result['name'].lower():
                        base_score = self.SCORE_EXACT_MATCH
                    # Exact code match bonus
                    elif result['code'] and query.lower() == result['code'].lower():
                        base_score = self.SCORE_EXACT_MATCH
                        
                    result['relevance_score'] = base_score
                else:
                    result['relevance_score'] = self.SCORE_MEDIUM_RELEVANCE
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching courses: {e}", exc_info=True)
            return []
    
    def _search_materials(self, query, filters=None, limit=20):
        """
        Search for materials/files.
        
        Args:
            query (str): The search query
            filters (dict, optional): Additional filters
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of matching material dictionaries with relevance scores
        """
        try:
            # Build base query parts
            if query:
                # Use FTS for text search if query is provided
                base_query_parts = [
                    "SELECT m.*, c.name as course_name, rank",
                    "FROM materials m",
                    "LEFT JOIN courses c ON m.course_id = c.id",
                    "JOIN (SELECT rowid, rank FROM fts_materials WHERE fts_materials MATCH ?) AS fts ON m.id = fts.rowid",
                    "WHERE 1=1"
                ]
                params = [query]
            else:
                # Just use regular selection if no query
                base_query_parts = [
                    "SELECT m.*, c.name as course_name",
                    "FROM materials m",
                    "LEFT JOIN courses c ON m.course_id = c.id",
                    "WHERE 1=1"
                ]
                params = []
                
            # Apply filters if provided
            if filters:
                if 'course_id' in filters:
                    base_query_parts.append("AND m.course_id = ?")
                    params.append(filters['course_id'])
                    
                if 'file_type' in filters:
                    base_query_parts.append("AND m.file_type = ?")
                    params.append(filters['file_type'])
                    
            # Apply sorting if specified
            if filters and 'sort' in filters:
                sort = filters['sort']
                sort_field = sort.get('field', 'title')
                sort_order = sort.get('order', 'asc').upper()
                
                # Map front-end field names to database columns if needed
                field_map = {
                    'title': 'm.title',
                    'file_type': 'm.file_type',
                    'uploaded': 'm.created_at',
                    'course': 'c.name'
                }
                
                db_field = field_map.get(sort_field, sort_field)
                base_query_parts.append(f"ORDER BY {db_field} {sort_order}")
            else:
                # Default sorting: by relevance if search query provided, otherwise by title
                if query:
                    base_query_parts.append("ORDER BY rank")
                else:
                    base_query_parts.append("ORDER BY m.title")
                    
            # Apply limit
            base_query_parts.append("LIMIT ?")
            params.append(limit)
            
            # Build and execute final query
            final_query = " ".join(base_query_parts)
            results = self.db_manager.execute_query(final_query, tuple(params))
            
            # Post-process results to add entity type and adjust format
            for result in results:
                result['entity_type'] = self.ENTITY_MATERIAL
                result['display_name'] = result['title']
                result['display_date'] = result['created_at']
                
                # Calculate relevance score if not from FTS
                if query and 'rank' in result:
                    # SQLite FTS rank is inverted (lower is better)
                    # Convert to a 0-100 score where higher is better
                    base_score = 100 - min(result['rank'] * 10, 90)
                    
                    # Exact title match bonus
                    if query.lower() == result['title'].lower():
                        base_score = self.SCORE_EXACT_MATCH
                        
                    # Content match (should be weighted lower than title match)
                    # This is already factored into the FTS ranking
                    
                    result['relevance_score'] = base_score
                else:
                    result['relevance_score'] = self.SCORE_MEDIUM_RELEVANCE
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching materials: {e}", exc_info=True)
            return []
    
    def _search_terms(self, query, filters=None, limit=20):
        """
        Search for academic terms.
        
        Args:
            query (str): The search query
            filters (dict, optional): Additional filters
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of matching term dictionaries with relevance scores
        """
        try:
            # Build query
            query_parts = [
                "SELECT * FROM terms",
                "WHERE name LIKE ?"
            ]
            
            # Add additional filters
            params = [f"%{query}%"]
            
            if filters:
                # Example filter: current term only
                if 'is_current' in filters:
                    query_parts.append("AND is_current = ?")
                    params.append(filters['is_current'])
                    
                # Date range filter
                if 'date_range' in filters:
                    date_range = filters['date_range']
                    if 'start_date' in date_range:
                        query_parts.append("AND end_date >= ?")
                        params.append(date_range['start_date'])
                    if 'end_date' in date_range:
                        query_parts.append("AND start_date <= ?")
                        params.append(date_range['end_date'])
            
            # Add ordering
            query_parts.append("ORDER BY start_date DESC")
            
            # Add limit
            query_parts.append("LIMIT ?")
            params.append(limit)
            
            # Execute query
            final_query = " ".join(query_parts)
            results = self.db_manager.execute_query(final_query, tuple(params))
            
            # Post-process results
            for result in results:
                result['entity_type'] = self.ENTITY_TERM
                result['display_name'] = result['name']
                result['display_date'] = result['start_date']
                
                # Calculate relevance score
                if query:
                    if query.lower() == result['name'].lower():
                        result['relevance_score'] = self.SCORE_EXACT_MATCH
                    elif query.lower() in result['name'].lower():
                        result['relevance_score'] = self.SCORE_HIGH_RELEVANCE
                    else:
                        result['relevance_score'] = self.SCORE_MEDIUM_RELEVANCE
                else:
                    result['relevance_score'] = self.SCORE_MEDIUM_RELEVANCE
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching terms: {e}", exc_info=True)
            return []
    
    # --------------------------- #
    # Helper Methods             #
    # --------------------------- #
    
    def _clean_query(self, query):
        """
        Clean and normalize a search query.
        
        Args:
            query (str): The original query
            
        Returns:
            str: The cleaned query
        """
        if not query:
            return ""
            
        # Trim whitespace
        cleaned = query.strip()
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove special characters that might interfere with search
        # but keep spaces and alphanumeric characters
        cleaned = re.sub(r'[^\w\s]', '', cleaned)
        
        return cleaned
    
    def _add_to_history(self, query):
        """
        Add a query to the search history.
        
        Args:
            query (str): The search query
        """
        if not query:
            return
            
        # Remove the query if it already exists to avoid duplicates
        if query in self.search_history:
            self.search_history.remove(query)
            
        # Add to the end of the list (most recent)
        self.search_history.append(query)
        
        # Limit history size
        max_history = 50
        if len(self.search_history) > max_history:
            self.search_history = self.search_history[-max_history:]
            
    def parse_search_query(self, query_string):
        """
        Parse a search query to extract filters and keywords.
        
        This supports advanced query syntax like:
            course:CS101 status:in_progress due:next_week important
        
        Args:
            query_string (str): The complete search query string
            
        Returns:
            dict: Dictionary with parsed keywords and filters
        """
        try:
            if not query_string:
                return {"keywords": "", "filters": {}}
                
            # Define recognized filters and their regex patterns
            filter_patterns = {
                "course": r'course:([^\s]+)',
                "status": r'status:([^\s]+)',
                "priority": r'priority:([^\s]+)',
                "due": r'due:([^\s]+)',
                "type": r'type:([^\s]+)',
                "term": r'term:([^\s]+)'
            }
            
            filters = {}
            
            # Extract filters
            for filter_name, pattern in filter_patterns.items():
                matches = re.findall(pattern, query_string)
                if matches:
                    filters[filter_name] = matches[0]
                    # Remove matched filter from query string
                    query_string = re.sub(pattern, '', query_string)
            
            # Whatever remains is the keyword query
            keywords = self._clean_query(query_string)
            
            return {
                "keywords": keywords,
                "filters": filters
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing search query: {e}", exc_info=True)
            return {"keywords": query_string, "filters": {}}