"""
Assignment Tracker for the Academic Organizer application.

This module handles assignment creation, tracking, deadline management,
and progress tracking for academic assignments.
"""

import logging
from datetime import datetime, timedelta
import re
import json
from pathlib import Path
import uuid


class AssignmentTracker:
    """
    Assignment Tracker for the Academic Organizer application.
    
    This class is responsible for:
    - Assignment creation, retrieval, update, and deletion
    - Deadline tracking and notification management
    - Progress and status tracking
    - Priority management
    - Related file association
    """
    
    # Assignment status constants
    STATUS_NOT_STARTED = "not_started"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_SUBMITTED = "submitted"
    STATUS_GRADED = "graded"
    STATUS_LATE = "late"
    
    # Assignment priority constants
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    
    def __init__(self, db_manager):
        """
        Initialize the assignment tracker.
        
        Args:
            db_manager: The database manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
    
    # --------------------------- #
    # Assignment CRUD Operations  #
    # --------------------------- #
    
    def create_assignment(self, title, course_id=None, description=None, 
                         due_date=None, priority=None, status=None, 
                         weight=None, max_score=None):
        """
        Create a new assignment.
        
        Args:
            title (str): The assignment title
            course_id (int, optional): The associated course ID
            description (str, optional): Detailed description of the assignment
            due_date (str, optional): Due date in ISO format (YYYY-MM-DD HH:MM:SS)
            priority (str, optional): Assignment priority (low, medium, high, urgent)
            status (str, optional): Assignment status (defaults to not_started)
            weight (float, optional): Weight of the assignment in course grade (percent)
            max_score (float, optional): Maximum possible score
            
        Returns:
            int: The ID of the created assignment, or None if creation failed
        """
        try:
            # Validate required fields
            if not title:
                self.logger.error("Assignment title is required")
                return None
                
            # Set default values if not provided
            if not status:
                status = self.STATUS_NOT_STARTED
                
            if not priority:
                priority = self.PRIORITY_MEDIUM
                
            # Validate priority
            if priority not in [self.PRIORITY_LOW, self.PRIORITY_MEDIUM, 
                               self.PRIORITY_HIGH, self.PRIORITY_URGENT]:
                self.logger.warning(f"Invalid priority: {priority}, using medium")
                priority = self.PRIORITY_MEDIUM
                
            # Validate status
            if status not in [self.STATUS_NOT_STARTED, self.STATUS_IN_PROGRESS, 
                             self.STATUS_COMPLETED, self.STATUS_SUBMITTED, 
                             self.STATUS_GRADED, self.STATUS_LATE]:
                self.logger.warning(f"Invalid status: {status}, using not_started")
                status = self.STATUS_NOT_STARTED
                
            # Parse due date if provided
            parsed_due_date = None
            if due_date:
                try:
                    parsed_due_date = datetime.fromisoformat(due_date)
                except ValueError:
                    self.logger.warning(f"Invalid due date format: {due_date}, should be YYYY-MM-DD HH:MM:SS")
                    
            # Insert assignment into database
            query = """
            INSERT INTO assignments (title, course_id, description, due_date, 
                                    priority, status, weight, max_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (title, course_id, description, parsed_due_date, 
                     priority, status, weight, max_score)
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            assignment_id = cursor.lastrowid
            self.logger.info(f"Assignment created with ID: {assignment_id}")
            
            return assignment_id
            
        except Exception as e:
            self.logger.error(f"Error creating assignment: {e}", exc_info=True)
            self.db_manager.get_connection().rollback()
            return None
    
    def get_assignment(self, assignment_id):
        """
        Get an assignment by ID.
        
        Args:
            assignment_id (int): The assignment ID
            
        Returns:
            dict: The assignment data, or None if not found
        """
        try:
            query = """
            SELECT a.*, c.name as course_name
            FROM assignments a
            LEFT JOIN courses c ON a.course_id = c.id
            WHERE a.id = ?
            """
            params = (assignment_id,)
            
            result = self.db_manager.execute_query(query, params)
            if result:
                # Get subtasks for this assignment
                assignment = result[0]
                assignment['subtasks'] = self.get_subtasks(assignment_id)
                return assignment
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting assignment: {e}", exc_info=True)
            return None
    
    def get_all_assignments(self, course_id=None, status=None, priority=None, 
                           due_before=None, due_after=None):
        """
        Get all assignments, with optional filtering.
        
        Args:
            course_id (int, optional): Filter by course ID
            status (str, optional): Filter by status
            priority (str, optional): Filter by priority
            due_before (str, optional): Filter for assignments due before this date
            due_after (str, optional): Filter for assignments due after this date
            
        Returns:
            list: List of assignment dictionaries
        """
        try:
            # Build query with conditional filters
            query_parts = [
                "SELECT a.*, c.name as course_name",
                "FROM assignments a",
                "LEFT JOIN courses c ON a.course_id = c.id",
                "WHERE 1=1"  # Base condition to simplify adding AND clauses
            ]
            params = []
            
            if course_id is not None:
                query_parts.append("AND a.course_id = ?")
                params.append(course_id)
                
            if status:
                query_parts.append("AND a.status = ?")
                params.append(status)
                
            if priority:
                query_parts.append("AND a.priority = ?")
                params.append(priority)
                
            if due_before:
                try:
                    parsed_date = datetime.fromisoformat(due_before)
                    query_parts.append("AND a.due_date < ?")
                    params.append(parsed_date)
                except ValueError:
                    self.logger.warning(f"Invalid due_before date format: {due_before}")
                    
            if due_after:
                try:
                    parsed_date = datetime.fromisoformat(due_after)
                    query_parts.append("AND a.due_date > ?")
                    params.append(parsed_date)
                except ValueError:
                    self.logger.warning(f"Invalid due_after date format: {due_after}")
                    
            query_parts.append("ORDER BY a.due_date, a.priority DESC")
            
            # Combine query parts
            query = " ".join(query_parts)
            
            # Execute query
            assignments = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            # Get subtasks for each assignment
            for assignment in assignments:
                assignment['subtasks'] = self.get_subtasks(assignment['id'])
                
            return assignments
            
        except Exception as e:
            self.logger.error(f"Error getting assignments: {e}", exc_info=True)
            return []
    
    def update_assignment(self, assignment_id, **kwargs):
        """
        Update an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            **kwargs: Fields to update (title, course_id, description, due_date,
                      priority, status, weight, max_score, actual_score)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get allowed fields
            allowed_fields = ['title', 'course_id', 'description', 'due_date', 
                             'priority', 'status', 'weight', 'max_score', 'actual_score']
            
            # Filter kwargs to only include allowed fields
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                self.logger.warning("No valid fields provided for update")
                return False
                
            # Validate priority if provided
            if 'priority' in update_fields:
                priority = update_fields['priority']
                if priority not in [self.PRIORITY_LOW, self.PRIORITY_MEDIUM, 
                                  self.PRIORITY_HIGH, self.PRIORITY_URGENT]:
                    self.logger.warning(f"Invalid priority: {priority}, using medium")
                    update_fields['priority'] = self.PRIORITY_MEDIUM
                    
            # Validate status if provided
            if 'status' in update_fields:
                status = update_fields['status']
                if status not in [self.STATUS_NOT_STARTED, self.STATUS_IN_PROGRESS, 
                                 self.STATUS_COMPLETED, self.STATUS_SUBMITTED, 
                                 self.STATUS_GRADED, self.STATUS_LATE]:
                    self.logger.warning(f"Invalid status: {status}, using not_started")
                    update_fields['status'] = self.STATUS_NOT_STARTED
                    
            # Parse due date if provided
            if 'due_date' in update_fields and update_fields['due_date']:
                try:
                    update_fields['due_date'] = datetime.fromisoformat(update_fields['due_date'])
                except ValueError:
                    self.logger.warning(f"Invalid due date format, should be YYYY-MM-DD HH:MM:SS")
                    del update_fields['due_date']
            
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            
            query = f"UPDATE assignments SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (assignment_id,)
            
            # Execute update
            rows_affected = self.db_manager.execute_update(query, params)
            
            # If status was updated to completed, update completion date
            if 'status' in update_fields and update_fields['status'] == self.STATUS_COMPLETED:
                completion_query = "UPDATE assignments SET completed_at = CURRENT_TIMESTAMP WHERE id = ?"
                completion_params = (assignment_id,)
                self.db_manager.execute_update(completion_query, completion_params)
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating assignment: {e}", exc_info=True)
            return False
    
    def delete_assignment(self, assignment_id):
        """
        Delete an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # First delete related subtasks
            self.delete_all_subtasks(assignment_id)
            
            # Then delete the assignment itself
            query = "DELETE FROM assignments WHERE id = ?"
            params = (assignment_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting assignment: {e}", exc_info=True)
            return False
    
    # --------------------------- #
    # Subtask Management         #
    # --------------------------- #
    
    def add_subtask(self, assignment_id, title, description=None, 
                   due_date=None, status=None, order=None):
        """
        Add a subtask to an assignment.
        
        Args:
            assignment_id (int): The parent assignment ID
            title (str): The subtask title
            description (str, optional): Subtask description
            due_date (str, optional): Due date in ISO format (YYYY-MM-DD HH:MM:SS)
            status (str, optional): Subtask status (defaults to not_started)
            order (int, optional): Display order of the subtask
            
        Returns:
            int: The ID of the created subtask, or None if creation failed
        """
        try:
            # Validate required fields
            if not title:
                self.logger.error("Subtask title is required")
                return None
                
            # Verify parent assignment exists
            parent_query = "SELECT id FROM assignments WHERE id = ?"
            parent_params = (assignment_id,)
            parent_result = self.db_manager.execute_query(parent_query, parent_params)
            
            if not parent_result:
                self.logger.error(f"Parent assignment not found: {assignment_id}")
                return None
                
            # Set default values if not provided
            if not status:
                status = self.STATUS_NOT_STARTED
                
            # Validate status
            if status not in [self.STATUS_NOT_STARTED, self.STATUS_IN_PROGRESS, 
                             self.STATUS_COMPLETED]:
                self.logger.warning(f"Invalid status: {status}, using not_started")
                status = self.STATUS_NOT_STARTED
                
            # Parse due date if provided
            parsed_due_date = None
            if due_date:
                try:
                    parsed_due_date = datetime.fromisoformat(due_date)
                except ValueError:
                    self.logger.warning(f"Invalid due date format: {due_date}")
                    
            # If order not specified, place at end
            if order is None:
                order_query = """
                SELECT COALESCE(MAX("order"), 0) + 1 as next_order
                FROM subtasks
                WHERE assignment_id = ?
                """
                order_params = (assignment_id,)
                order_result = self.db_manager.execute_query(order_query, order_params)
                order = order_result[0]['next_order'] if order_result else 1
                
            # Insert subtask into database
            query = """
            INSERT INTO subtasks (assignment_id, title, description, due_date, status, "order")
            VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (assignment_id, title, description, parsed_due_date, status, order)
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            subtask_id = cursor.lastrowid
            self.logger.info(f"Subtask created with ID: {subtask_id}")
            
            # Update assignment's subtask count and status
            self._update_assignment_subtask_stats(assignment_id)
            
            return subtask_id
            
        except Exception as e:
            self.logger.error(f"Error creating subtask: {e}", exc_info=True)
            self.db_manager.get_connection().rollback()
            return None
    
    def get_subtasks(self, assignment_id):
        """
        Get all subtasks for an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            
        Returns:
            list: List of subtask dictionaries
        """
        try:
            query = """
            SELECT * FROM subtasks
            WHERE assignment_id = ?
            ORDER BY "order"
            """
            params = (assignment_id,)
            
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error getting subtasks: {e}", exc_info=True)
            return []
    
    def update_subtask(self, subtask_id, **kwargs):
        """
        Update a subtask.
        
        Args:
            subtask_id (int): The subtask ID
            **kwargs: Fields to update (title, description, due_date, status, order)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get allowed fields
            allowed_fields = ['title', 'description', 'due_date', 'status', 'order']
            
            # Filter kwargs to only include allowed fields
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                self.logger.warning("No valid fields provided for update")
                return False
                
            # Validate status if provided
            if 'status' in update_fields:
                status = update_fields['status']
                if status not in [self.STATUS_NOT_STARTED, self.STATUS_IN_PROGRESS, 
                                 self.STATUS_COMPLETED]:
                    self.logger.warning(f"Invalid status: {status}, using not_started")
                    update_fields['status'] = self.STATUS_NOT_STARTED
                    
            # Parse due date if provided
            if 'due_date' in update_fields and update_fields['due_date']:
                try:
                    update_fields['due_date'] = datetime.fromisoformat(update_fields['due_date'])
                except ValueError:
                    self.logger.warning(f"Invalid due date format, should be YYYY-MM-DD HH:MM:SS")
                    del update_fields['due_date']
            
            # Get the assignment_id for this subtask
            query_assignment = "SELECT assignment_id FROM subtasks WHERE id = ?"
            params_assignment = (subtask_id,)
            result_assignment = self.db_manager.execute_query(query_assignment, params_assignment)
            
            if not result_assignment:
                self.logger.error(f"Subtask not found: {subtask_id}")
                return False
                
            assignment_id = result_assignment[0]['assignment_id']
            
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            
            query = f"UPDATE subtasks SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (subtask_id,)
            
            # Execute update
            rows_affected = self.db_manager.execute_update(query, params)
            
            # Update assignment's subtask stats
            self._update_assignment_subtask_stats(assignment_id)
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating subtask: {e}", exc_info=True)
            return False
    
    def delete_subtask(self, subtask_id):
        """
        Delete a subtask.
        
        Args:
            subtask_id (int): The subtask ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Get the assignment_id for this subtask
            query_assignment = "SELECT assignment_id FROM subtasks WHERE id = ?"
            params_assignment = (subtask_id,)
            result_assignment = self.db_manager.execute_query(query_assignment, params_assignment)
            
            if not result_assignment:
                self.logger.error(f"Subtask not found: {subtask_id}")
                return False
                
            assignment_id = result_assignment[0]['assignment_id']
            
            # Delete the subtask
            query = "DELETE FROM subtasks WHERE id = ?"
            params = (subtask_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            
            # Update assignment's subtask stats
            self._update_assignment_subtask_stats(assignment_id)
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting subtask: {e}", exc_info=True)
            return False
    
    def delete_all_subtasks(self, assignment_id):
        """
        Delete all subtasks for an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            query = "DELETE FROM subtasks WHERE assignment_id = ?"
            params = (assignment_id,)
            
            self.db_manager.execute_update(query, params)
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting subtasks: {e}", exc_info=True)
            return False
    
    # --------------------------- #
    # Deadline Management        #
    # --------------------------- #
    
    def get_upcoming_deadlines(self, days=7, course_id=None):
        """
        Get assignments with deadlines coming up in the specified number of days.
        
        Args:
            days (int, optional): Number of days to look ahead (default: 7)
            course_id (int, optional): Filter by course ID
            
        Returns:
            list: List of upcoming assignment dictionaries
        """
        try:
            # Calculate date range
            now = datetime.now()
            end_date = now + timedelta(days=days)
            
            # Build query
            query_parts = [
                "SELECT a.*, c.name as course_name",
                "FROM assignments a",
                "LEFT JOIN courses c ON a.course_id = c.id",
                "WHERE a.due_date BETWEEN ? AND ?",
                "AND a.status NOT IN (?, ?, ?)"  # Exclude completed, submitted, graded
            ]
            params = [now, end_date, self.STATUS_COMPLETED, self.STATUS_SUBMITTED, self.STATUS_GRADED]
            
            if course_id is not None:
                query_parts.append("AND a.course_id = ?")
                params.append(course_id)
                
            query_parts.append("ORDER BY a.due_date, a.priority DESC")
            
            # Combine query parts
            query = " ".join(query_parts)
            
            return self.db_manager.execute_query(query, tuple(params))
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming deadlines: {e}", exc_info=True)
            return []
    
    def get_overdue_assignments(self, course_id=None):
        """
        Get assignments that are past their due date and not completed.
        
        Args:
            course_id (int, optional): Filter by course ID
            
        Returns:
            list: List of overdue assignment dictionaries
        """
        try:
            # Build query
            query_parts = [
                "SELECT a.*, c.name as course_name",
                "FROM assignments a",
                "LEFT JOIN courses c ON a.course_id = c.id",
                "WHERE a.due_date < CURRENT_TIMESTAMP",
                "AND a.status NOT IN (?, ?, ?)"  # Exclude completed, submitted, graded
            ]
            params = [self.STATUS_COMPLETED, self.STATUS_SUBMITTED, self.STATUS_GRADED]
            
            if course_id is not None:
                query_parts.append("AND a.course_id = ?")
                params.append(course_id)
                
            query_parts.append("ORDER BY a.due_date, a.priority DESC")
            
            # Combine query parts
            query = " ".join(query_parts)
            
            return self.db_manager.execute_query(query, tuple(params))
            
        except Exception as e:
            self.logger.error(f"Error getting overdue assignments: {e}", exc_info=True)
            return []
    
    def mark_late_assignments(self):
        """
        Automatically mark assignments as late if they're past due.
        
        Returns:
            int: Number of assignments marked as late
        """
        try:
            query = """
            UPDATE assignments
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE due_date < CURRENT_TIMESTAMP
            AND status NOT IN (?, ?, ?, ?)
            """
            params = (self.STATUS_LATE, self.STATUS_COMPLETED, self.STATUS_SUBMITTED, 
                     self.STATUS_GRADED, self.STATUS_LATE)
            
            return self.db_manager.execute_update(query, params)
            
        except Exception as e:
            self.logger.error(f"Error marking late assignments: {e}", exc_info=True)
            return 0
    
    # --------------------------- #
    # Progress and Statistics    #
    # --------------------------- #
    
    def calculate_completion_percentage(self, assignment_id):
        """
        Calculate completion percentage based on subtasks.
        
        Args:
            assignment_id (int): The assignment ID
            
        Returns:
            float: Completion percentage (0-100)
        """
        try:
            # Get all subtasks for the assignment
            subtasks = self.get_subtasks(assignment_id)
            
            if not subtasks:
                # If no subtasks, check assignment status
                query = "SELECT status FROM assignments WHERE id = ?"
                params = (assignment_id,)
                result = self.db_manager.execute_query(query, params)
                
                if not result:
                    return 0
                    
                status = result[0]['status']
                if status == self.STATUS_COMPLETED or status == self.STATUS_GRADED:
                    return 100
                elif status == self.STATUS_SUBMITTED:
                    return 90
                elif status == self.STATUS_IN_PROGRESS:
                    return 50
                else:
                    return 0
            
            # Count completed subtasks
            completed = sum(1 for task in subtasks if task['status'] == self.STATUS_COMPLETED)
            in_progress = sum(1 for task in subtasks if task['status'] == self.STATUS_IN_PROGRESS)
            
            # Calculate percentage
            total = len(subtasks)
            completed_percentage = (completed / total) * 100
            in_progress_percentage = (in_progress / total) * 25  # Count in_progress as 25% complete
            
            return min(100, completed_percentage + in_progress_percentage)
            
        except Exception as e:
            self.logger.error(f"Error calculating completion percentage: {e}", exc_info=True)
            return 0
    
    def get_assignment_statistics(self, course_id=None):
        """
        Get statistical information about assignments.
        
        Args:
            course_id (int, optional): Filter by course ID
            
        Returns:
            dict: Assignment statistics
        """
        try:
            # Base query parts
            base_query = """
            SELECT COUNT(*) as count
            FROM assignments
            WHERE 1=1
            """
            params = []
            
            if course_id is not None:
                base_query += " AND course_id = ?"
                params.append(course_id)
                
            # Build and execute various statistic queries
            
            # Total assignments
            total_query = base_query
            total_result = self.db_manager.execute_query(total_query, tuple(params) if params else None)
            total = total_result[0]['count'] if total_result else 0
            
            # Completed assignments
            completed_query = base_query + f" AND status IN (?, ?, ?)"
            completed_params = tuple(params) + (self.STATUS_COMPLETED, self.STATUS_SUBMITTED, self.STATUS_GRADED)
            completed_result = self.db_manager.execute_query(completed_query, completed_params)
            completed = completed_result[0]['count'] if completed_result else 0
            
            # In progress assignments
            in_progress_query = base_query + f" AND status = ?"
            in_progress_params = tuple(params) + (self.STATUS_IN_PROGRESS,)
            in_progress_result = self.db_manager.execute_query(in_progress_query, in_progress_params)
            in_progress = in_progress_result[0]['count'] if in_progress_result else 0
            
            # Not started assignments
            not_started_query = base_query + f" AND status = ?"
            not_started_params = tuple(params) + (self.STATUS_NOT_STARTED,)
            not_started_result = self.db_manager.execute_query(not_started_query, not_started_params)
            not_started = not_started_result[0]['count'] if not_started_result else 0
            
            # Late assignments
            late_query = base_query + f" AND status = ?"
            late_params = tuple(params) + (self.STATUS_LATE,)
            late_result = self.db_manager.execute_query(late_query, late_params)
            late = late_result[0]['count'] if late_result else 0
            
            # Urgent assignments
            urgent_query = base_query + f" AND priority = ? AND status NOT IN (?, ?, ?)"
            urgent_params = tuple(params) + (self.PRIORITY_URGENT, self.STATUS_COMPLETED, 
                                            self.STATUS_SUBMITTED, self.STATUS_GRADED)
            urgent_result = self.db_manager.execute_query(urgent_query, urgent_params)
            urgent = urgent_result[0]['count'] if urgent_result else 0
            
            # Compile statistics
            stats = {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "not_started": not_started,
                "late": late,
                "urgent": urgent,
                "completion_rate": (completed / total * 100) if total > 0 else 0
            }
            
            # Add course-specific info if relevant
            if course_id is not None:
                course_query = "SELECT name FROM courses WHERE id = ?"
                course_params = (course_id,)
                course_result = self.db_manager.execute_query(course_query, course_params)
                if course_result:
                    stats['course_name'] = course_result[0]['name']
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting assignment statistics: {e}", exc_info=True)
            return {"total": 0, "completed": 0, "in_progress": 0, 
                   "not_started": 0, "late": 0, "urgent": 0, "completion_rate": 0}
    
    # --------------------------- #
    # Helper Methods             #
    # --------------------------- #
    
    def _update_assignment_subtask_stats(self, assignment_id):
        """
        Update an assignment's status based on its subtasks.
        
        Args:
            assignment_id (int): The assignment ID
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get subtasks for the assignment
            subtasks = self.get_subtasks(assignment_id)
            
            if not subtasks:
                return True  # No subtasks to update from
                
            # Calculate subtask statistics
            total = len(subtasks)
            completed = sum(1 for task in subtasks if task['status'] == self.STATUS_COMPLETED)
            in_progress = sum(1 for task in subtasks if task['status'] == self.STATUS_IN_PROGRESS)
            
            # Update assignment stats in the database
            query = """
            UPDATE assignments
            SET subtask_count = ?, 
                completed_subtasks = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            params = (total, completed, assignment_id)
            
            self.db_manager.execute_update(query, params)
            
            # Update assignment status based on subtasks
            if completed == total and total > 0:
                # All subtasks complete - mark assignment as completed
                self.update_assignment(assignment_id, status=self.STATUS_COMPLETED)
            elif in_progress > 0 or completed > 0:
                # Some subtasks in progress or complete - mark assignment as in progress
                self.update_assignment(assignment_id, status=self.STATUS_IN_PROGRESS)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating assignment subtask stats: {e}", exc_info=True)
            return False
    
    def associate_file_with_assignment(self, assignment_id, material_id):
        """
        Associate a file with an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            material_id (int): The material ID
            
        Returns:
            bool: True if association successful, False otherwise
        """
        try:
            # Check if assignment exists
            assignment_query = "SELECT id FROM assignments WHERE id = ?"
            assignment_params = (assignment_id,)
            assignment_result = self.db_manager.execute_query(assignment_query, assignment_params)
            
            if not assignment_result:
                self.logger.error(f"Assignment not found: {assignment_id}")
                return False
                
            # Check if material exists
            material_query = "SELECT id FROM materials WHERE id = ?"
            material_params = (material_id,)
            material_result = self.db_manager.execute_query(material_query, material_params)
            
            if not material_result:
                self.logger.error(f"Material not found: {material_id}")
                return False
                
            # Check if association already exists
            existing_query = """
            SELECT * FROM assignment_materials 
            WHERE assignment_id = ? AND material_id = ?
            """
            existing_params = (assignment_id, material_id)
            existing_result = self.db_manager.execute_query(existing_query, existing_params)
            
            if existing_result:
                self.logger.info(f"Association already exists")
                return True
                
            # Create the association
            query = """
            INSERT INTO assignment_materials (assignment_id, material_id)
            VALUES (?, ?)
            """
            params = (assignment_id, material_id)
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            self.logger.info(f"File associated with assignment: {assignment_id} -> {material_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error associating file with assignment: {e}", exc_info=True)
            self.db_manager.get_connection().rollback()
            return False
    
    def remove_file_association(self, assignment_id, material_id):
        """
        Remove a file association from an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            material_id (int): The material ID
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        try:
            query = """
            DELETE FROM assignment_materials 
            WHERE assignment_id = ? AND material_id = ?
            """
            params = (assignment_id, material_id)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error removing file association: {e}", exc_info=True)
            return False
    
    def get_associated_files(self, assignment_id):
        """
        Get all files associated with an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            
        Returns:
            list: List of material dictionaries
        """
        try:
            query = """
            SELECT m.*
            FROM materials m
            JOIN assignment_materials am ON m.id = am.material_id
            WHERE am.assignment_id = ?
            ORDER BY m.title
            """
            params = (assignment_id,)
            
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error getting associated files: {e}", exc_info=True)
            return []