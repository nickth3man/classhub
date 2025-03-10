"""
Assignment Manager for the Academic Organizer application.

This module handles assignment creation, tracking, and grading.
"""

import logging
from datetime import datetime, timedelta
import uuid


class AssignmentManager:
    """
    Assignment Manager for the Academic Organizer application.
    
    This class is responsible for:
    - Creating, retrieving, updating, and deleting assignments
    - Tracking assignment deadlines
    - Managing assignment grades and feedback
    - Organizing assignments by course
    - Generating reports on assignment progress and grades
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
    
    # Assignment type constants
    TYPE_HOMEWORK = "homework"
    TYPE_QUIZ = "quiz"
    TYPE_EXAM = "exam"
    TYPE_PROJECT = "project"
    TYPE_PAPER = "paper"
    TYPE_PRESENTATION = "presentation"
    TYPE_DISCUSSION = "discussion"
    TYPE_LAB = "lab"
    TYPE_OTHER = "other"
    
    def __init__(self, db_manager):
        """
        Initialize the assignment manager.
        
        Args:
            db_manager: The database manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
    
    # --------------------------- #
    # Assignment CRUD Operations #
    # --------------------------- #
    
    def create_assignment(self, title, course_id=None, due_date=None, description=None,
                         assignment_type=None, priority=None, status=None, max_score=None,
                         weight=None, submission_type=None, instructions=None,
                         estimated_time=None, notes=None):
        """
        Create a new assignment.
        
        Args:
            title (str): Assignment title
            course_id (int, optional): Associated course ID
            due_date (str, optional): Due date in ISO format
            description (str, optional): Assignment description
            assignment_type (str, optional): Type of assignment
            priority (str, optional): Priority level
            status (str, optional): Current status
            max_score (float, optional): Maximum possible score
            weight (float, optional): Weight in course grade
            submission_type (str, optional): Type of submission required
            instructions (str, optional): Detailed instructions
            estimated_time (int, optional): Estimated time to complete (minutes)
            notes (str, optional): Additional notes
            
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
                
            if not assignment_type:
                assignment_type = self.TYPE_HOMEWORK
                
            # Validate status
            valid_statuses = [
                self.STATUS_NOT_STARTED, self.STATUS_IN_PROGRESS, 
                self.STATUS_COMPLETED, self.STATUS_SUBMITTED,
                self.STATUS_GRADED, self.STATUS_LATE
            ]
            
            if status not in valid_statuses:
                self.logger.warning(f"Invalid status: {status}, using default")
                status = self.STATUS_NOT_STARTED
                
            # Validate priority
            valid_priorities = [
                self.PRIORITY_LOW, self.PRIORITY_MEDIUM,
                self.PRIORITY_HIGH, self.PRIORITY_URGENT
            ]
            
            if priority not in valid_priorities:
                self.logger.warning(f"Invalid priority: {priority}, using default")
                priority = self.PRIORITY_MEDIUM
                
            # Validate assignment type
            valid_types = [
                self.TYPE_HOMEWORK, self.TYPE_QUIZ, self.TYPE_EXAM,
                self.TYPE_PROJECT, self.TYPE_PAPER, self.TYPE_PRESENTATION,
                self.TYPE_DISCUSSION, self.TYPE_LAB, self.TYPE_OTHER
            ]
            
            if assignment_type not in valid_types:
                self.logger.warning(f"Invalid assignment type: {assignment_type}, using default")
                assignment_type = self.TYPE_HOMEWORK
                
            # Parse due date
            parsed_due_date = None
            if due_date:
                try:
                    if isinstance(due_date, str):
                        parsed_due_date = datetime.fromisoformat(due_date)
                    elif isinstance(due_date, datetime):
                        parsed_due_date = due_date
                except ValueError:
                    self.logger.error(f"Invalid due date format: {due_date}")
                    parsed_due_date = None
                    
            # Generate a unique external ID for integration with other systems
            external_id = str(uuid.uuid4())
                
            # Insert assignment into database
            query = """
            INSERT INTO assignments (
                title, course_id, due_date, description,
                assignment_type, priority, status, max_score,
                weight, submission_type, instructions,
                estimated_time, notes, external_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                title, course_id, parsed_due_date, description,
                assignment_type, priority, status, max_score,
                weight, submission_type, instructions,
                estimated_time, notes, external_id
            )
            
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
            SELECT a.*, c.name as course_name, c.code as course_code
            FROM assignments a
            LEFT JOIN courses c ON a.course_id = c.id
            WHERE a.id = ?
            """
            params = (assignment_id,)
            
            result = self.db_manager.execute_query(query, params)
            
            if result:
                assignment_data = result[0]
                
                # Get linked files
                file_query = """
                SELECT * FROM files
                WHERE assignment_id = ?
                """
                file_params = (assignment_id,)
                
                files = self.db_manager.execute_query(file_query, file_params)
                assignment_data['files'] = files
                
                return assignment_data
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting assignment: {e}", exc_info=True)
            return None
    
    def get_all_assignments(self, course_id=None, status=None, assignment_type=None, 
                          due_before=None, due_after=None, sort_by=None, sort_order='asc'):
        """
        Get all assignments, with optional filtering.
        
        Args:
            course_id (int, optional): Filter by course ID
            status (str, optional): Filter by status
            assignment_type (str, optional): Filter by assignment type
            due_before (str, optional): Filter by due date before this date
            due_after (str, optional): Filter by due date after this date
            sort_by (str, optional): Field to sort by
            sort_order (str, optional): Sort order (asc/desc)
            
        Returns:
            list: List of assignment dictionaries
        """
        try:
            # Build query with conditional filters
            query_parts = [
                "SELECT a.*, c.name as course_name, c.code as course_code",
                "FROM assignments a",
                "LEFT JOIN courses c ON a.course_id = c.id",
                "WHERE 1=1"  # Base condition to simplify adding AND clauses
            ]
            params = []
            
            if course_id is not None:
                query_parts.append("AND a.course_id = ?")
                params.append(course_id)
                
            if status is not None:
                query_parts.append("AND a.status = ?")
                params.append(status)
                
            if assignment_type is not None:
                query_parts.append("AND a.assignment_type = ?")
                params.append(assignment_type)
                
            if due_before is not None:
                # Parse date
                try:
                    if isinstance(due_before, str):
                        due_before_date = datetime.fromisoformat(due_before)
                    elif isinstance(due_before, datetime):
                        due_before_date = due_before
                    else:
                        due_before_date = due_before
                        
                    query_parts.append("AND a.due_date <= ?")
                    params.append(due_before_date)
                except (ValueError, TypeError):
                    self.logger.error(f"Invalid due_before date format: {due_before}")
                    
            if due_after is not None:
                # Parse date
                try:
                    if isinstance(due_after, str):
                        due_after_date = datetime.fromisoformat(due_after)
                    elif isinstance(due_after, datetime):
                        due_after_date = due_after
                    else:
                        due_after_date = due_after
                        
                    query_parts.append("AND a.due_date >= ?")
                    params.append(due_after_date)
                except (ValueError, TypeError):
                    self.logger.error(f"Invalid due_after date format: {due_after}")
                    
            # Add sorting
            if sort_by:
                # Map front-end field names to database columns if needed
                field_map = {
                    'title': 'a.title',
                    'course': 'c.name',
                    'due_date': 'a.due_date',
                    'status': 'a.status',
                    'priority': 'a.priority',
                    'created_at': 'a.created_at',
                    'updated_at': 'a.updated_at'
                }
                
                db_field = field_map.get(sort_by, f"a.{sort_by}")
                query_parts.append(f"ORDER BY {db_field} {sort_order.upper()}")
            else:
                # Default sort by due date
                query_parts.append("ORDER BY a.due_date")
                
            # Combine query parts
            query = " ".join(query_parts)
            
            # Execute query
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            # Get files for each assignment
            for assignment in results:
                file_query = """
                SELECT * FROM files
                WHERE assignment_id = ?
                """
                file_params = (assignment['id'],)
                
                files = self.db_manager.execute_query(file_query, file_params)
                assignment['files'] = files
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting assignments: {e}", exc_info=True)
            return []
    
    def update_assignment(self, assignment_id, **kwargs):
        """
        Update an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get allowed fields
            allowed_fields = [
                'title', 'course_id', 'due_date', 'description',
                'assignment_type', 'priority', 'status', 'max_score',
                'weight', 'submission_type', 'instructions',
                'estimated_time', 'notes', 'is_favorite', 'actual_score',
                'completed_date', 'submission_date', 'feedback'
            ]
            
            # Filter kwargs to only include allowed fields
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                self.logger.warning("No valid fields provided for update")
                return False
                
            # Special handling for date fields
            for date_field in ['due_date', 'completed_date', 'submission_date']:
                if date_field in update_fields:
                    date_value = update_fields[date_field]
                    if date_value is not None:
                        try:
                            if isinstance(date_value, str):
                                datetime.fromisoformat(date_value)  # Validate format
                            elif isinstance(date_value, datetime):
                                update_fields[date_field] = date_value.isoformat()
                        except ValueError:
                            self.logger.error(f"Invalid {date_field} format: {date_value}")
                            del update_fields[date_field]
                
            # Special handling for status - set to LATE if past due date and not completed
            if 'status' in update_fields and update_fields['status'] not in [
                self.STATUS_COMPLETED, self.STATUS_SUBMITTED, self.STATUS_GRADED
            ]:
                # Check if we need to update the due date
                if 'due_date' in update_fields:
                    due_date = update_fields['due_date']
                else:
                    # Get current due date
                    assignment = self.get_assignment(assignment_id)
                    due_date = assignment.get('due_date') if assignment else None
                    
                if due_date:
                    # Parse due date if needed
                    if isinstance(due_date, str):
                        due_date = datetime.fromisoformat(due_date)
                        
                    # Check if past due
                    if due_date < datetime.now():
                        update_fields['status'] = self.STATUS_LATE
                        
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            
            query = f"UPDATE assignments SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (assignment_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
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
            # Begin a transaction to delete related records
            conn = self.db_manager.get_connection()
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # Update files to remove assignment reference
                file_query = "UPDATE files SET assignment_id = NULL WHERE assignment_id = ?"
                conn.execute(file_query, (assignment_id,))
                
                # Delete the assignment
                assignment_query = "DELETE FROM assignments WHERE id = ?"
                conn.execute(assignment_query, (assignment_id,))
                
                # Commit the transaction
                conn.commit()
                
                return True
                
            except Exception as e:
                # Roll back transaction on error
                conn.rollback()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error deleting assignment: {e}", exc_info=True)
            return False
    
    # --------------------------- #
    # Assignment Status & Grades #
    # --------------------------- #
    
    def mark_as_completed(self, assignment_id, completion_date=None):
        """
        Mark an assignment as completed.
        
        Args:
            assignment_id (int): The assignment ID
            completion_date (str, optional): Completion date in ISO format
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Set completion date to now if not provided
            if completion_date is None:
                completion_date = datetime.now().isoformat()
                
            # Update assignment status
            update_data = {
                'status': self.STATUS_COMPLETED,
                'completed_date': completion_date
            }
            
            return self.update_assignment(assignment_id, **update_data)
            
        except Exception as e:
            self.logger.error(f"Error marking assignment as completed: {e}", exc_info=True)
            return False
    
    def mark_as_submitted(self, assignment_id, submission_date=None):
        """
        Mark an assignment as submitted.
        
        Args:
            assignment_id (int): The assignment ID
            submission_date (str, optional): Submission date in ISO format
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Set submission date to now if not provided
            if submission_date is None:
                submission_date = datetime.now().isoformat()
                
            # Update assignment status
            update_data = {
                'status': self.STATUS_SUBMITTED,
                'submission_date': submission_date
            }
            
            return self.update_assignment(assignment_id, **update_data)
            
        except Exception as e:
            self.logger.error(f"Error marking assignment as submitted: {e}", exc_info=True)
            return False
    
    def record_grade(self, assignment_id, actual_score, feedback=None):
        """
        Record a grade for an assignment.
        
        Args:
            assignment_id (int): The assignment ID
            actual_score (float): The actual score received
            feedback (str, optional): Feedback on the assignment
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get assignment to check max score
            assignment = self.get_assignment(assignment_id)
            if not assignment:
                self.logger.error(f"Assignment not found: {assignment_id}")
                return False
                
            max_score = assignment.get('max_score')
            
            # Validate score
            if max_score is not None and actual_score > max_score:
                self.logger.warning(f"Score {actual_score} exceeds max score {max_score}")
                
            # Update assignment with grade
            update_data = {
                'actual_score': actual_score,
                'status': self.STATUS_GRADED
            }
            
            if feedback:
                update_data['feedback'] = feedback
                
            return self.update_assignment(assignment_id, **update_data)
            
        except Exception as e:
            self.logger.error(f"Error recording grade: {e}", exc_info=True)
            return False
    
    # --------------------------- #
    # Assignment Reports & Stats #
    # --------------------------- #
    
    def get_overdue_assignments(self):
        """
        Get all overdue assignments.
        
        Returns:
            list: List of overdue assignment dictionaries
        """
        try:
            now = datetime.now().isoformat()
            
            query = """
            SELECT a.*, c.name as course_name, c.code as course_code
            FROM assignments a
            LEFT JOIN courses c ON a.course_id = c.id
            WHERE a.due_date < ?
            AND a.status NOT IN (?, ?, ?)
            ORDER BY a.due_date
            """
            params = (
                now,
                self.STATUS_COMPLETED,
                self.STATUS_SUBMITTED,
                self.STATUS_GRADED
            )
            
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error getting overdue assignments: {e}", exc_info=True)
            return []
    
    def get_upcoming_assignments(self, days=7):
        """
        Get assignments due in the upcoming days.
        
        Args:
            days (int, optional): Number of days ahead to check
            
        Returns:
            list: List of upcoming assignment dictionaries
        """
        try:
            now = datetime.now()
            future_date = (now + timedelta(days=days)).isoformat()
            
            query = """
            SELECT a.*, c.name as course_name, c.code as course_code
            FROM assignments a
            LEFT JOIN courses c ON a.course_id = c.id
            WHERE a.due_date BETWEEN ? AND ?
            AND a.status NOT IN (?, ?, ?)
            ORDER BY a.due_date
            """
            params = (
                now.isoformat(),
                future_date,
                self.STATUS_COMPLETED,
                self.STATUS_SUBMITTED,
                self.STATUS_GRADED
            )
            
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming assignments: {e}", exc_info=True)
            return []
    
    def get_assignments_by_priority(self, priority=None):
        """
        Get assignments grouped by priority.
        
        Args:
            priority (str, optional): Specific priority to get, or None for all
            
        Returns:
            dict: Dictionary of assignments by priority
        """
        try:
            result = {}
            
            if priority:
                # Get assignments for specific priority
                query = """
                SELECT a.*, c.name as course_name, c.code as course_code
                FROM assignments a
                LEFT JOIN courses c ON a.course_id = c.id
                WHERE a.priority = ?
                AND a.status NOT IN (?, ?, ?)
                ORDER BY a.due_date
                """
                params = (
                    priority,
                    self.STATUS_COMPLETED,
                    self.STATUS_SUBMITTED,
                    self.STATUS_GRADED
                )
                
                assignments = self.db_manager.execute_query(query, params)
                result[priority] = assignments
            else:
                # Get all priorities
                priorities = [
                    self.PRIORITY_URGENT,
                    self.PRIORITY_HIGH,
                    self.PRIORITY_MEDIUM,
                    self.PRIORITY_LOW
                ]
                
                for p in priorities:
                    query = """
                    SELECT a.*, c.name as course_name, c.code as course_code
                    FROM assignments a
                    LEFT JOIN courses c ON a.course_id = c.id
                    WHERE a.priority = ?
                    AND a.status NOT IN (?, ?, ?)
                    ORDER BY a.due_date
                    """
                    params = (
                        p,
                        self.STATUS_COMPLETED,
                        self.STATUS_SUBMITTED,
                        self.STATUS_GRADED
                    )
                    
                    assignments = self.db_manager.execute_query(query, params)
                    result[p] = assignments
                    
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting assignments by priority: {e}", exc_info=True)
            return {}
    
    def get_assignment_completion_stats(self, course_id=None):
        """
        Get assignment completion statistics.
        
        Args:
            course_id (int, optional): Filter by course ID
            
        Returns:
            dict: Statistics about assignment completion
        """
        try:
            # Build base query
            base_query = """
            SELECT COUNT(*) as count FROM assignments
            WHERE 1=1
            """
            
            params = []
            
            # Add course filter if provided
            if course_id is not None:
                base_query += " AND course_id = ?"
                params.append(course_id)
                
            # Total assignments
            total_query = base_query
            total_result = self.db_manager.execute_query(total_query, tuple(params) if params else None)
            total_count = total_result[0]['count'] if total_result else 0
            
            # Statuses to count
            statuses = {
                'not_started': self.STATUS_NOT_STARTED,
                'in_progress': self.STATUS_IN_PROGRESS,
                'completed': self.STATUS_COMPLETED,
                'submitted': self.STATUS_SUBMITTED,
                'graded': self.STATUS_GRADED,
                'late': self.STATUS_LATE
            }
            
            status_counts = {}
            
            for key, status in statuses.items():
                status_query = base_query + " AND status = ?"
                status_params = params + [status]
                
                status_result = self.db_manager.execute_query(
                    status_query, 
                    tuple(status_params)
                )
                
                status_counts[key] = status_result[0]['count'] if status_result else 0
                
            # Create stats dictionary
            stats = {
                'total': total_count,
                'status_counts': status_counts
            }
            
            # Calculate percentages
            if total_count > 0:
                stats['status_percentages'] = {
                    key: round((count / total_count) * 100, 2)
                    for key, count in status_counts.items()
                }
                
                # Overall completion percentage
                completed_count = sum([
                    status_counts.get('completed', 0),
                    status_counts.get('submitted', 0),
                    status_counts.get('graded', 0)
                ])
                
                stats['completion_percentage'] = round((completed_count / total_count) * 100, 2)
            else:
                stats['status_percentages'] = {key: 0 for key in status_counts.keys()}
                stats['completion_percentage'] = 0
                
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting assignment stats: {e}", exc_info=True)
            return {
                'total': 0,
                'status_counts': {},
                'status_percentages': {},
                'completion_percentage': 0
            }
    
    def get_grade_summary(self, course_id=None):
        """
        Get a summary of grades for assignments.
        
        Args:
            course_id (int, optional): Filter by course ID
            
        Returns:
            dict: Grade summary information
        """
        try:
            # Build query with conditional filters
            query_parts = [
                "SELECT a.*, c.name as course_name, c.code as course_code",
                "FROM assignments a",
                "LEFT JOIN courses c ON a.course_id = c.id",
                "WHERE a.status = ?",
                "AND a.actual_score IS NOT NULL"
            ]
            params = [self.STATUS_GRADED]
            
            if course_id is not None:
                query_parts.append("AND a.course_id = ?")
                params.append(course_id)
                
            query = " ".join(query_parts)
            
            # Execute query to get graded assignments
            graded_assignments = self.db_manager.execute_query(query, tuple(params))
            
            if not graded_assignments:
                return {
                    'total_assignments': 0,
                    'graded_assignments': 0,
                    'average_score': 0,
                    'weighted_average': 0,
                    'assignments': []
                }
                
            # Calculate summary statistics
            total_score = 0
            total_max_score = 0
            total_weighted_score = 0
            total_weight = 0
            
            for assignment in graded_assignments:
                actual_score = assignment.get('actual_score')
                max_score = assignment.get('max_score')
                weight = assignment.get('weight')
                
                if actual_score is not None:
                    if max_score is not None and max_score > 0:
                        assignment['percentage'] = round((actual_score / max_score) * 100, 2)
                        total_score += actual_score
                        total_max_score += max_score
                        
                        if weight is not None and weight > 0:
                            total_weighted_score += (actual_score / max_score) * weight
                            total_weight += weight
                    else:
                        assignment['percentage'] = None
                        
            # Calculate averages
            average_score = total_score / len(graded_assignments) if graded_assignments else 0
            average_percentage = (total_score / total_max_score) * 100 if total_max_score > 0 else 0
            weighted_average = (total_weighted_score / total_weight) * 100 if total_weight > 0 else 0
            
            return {
                'total_assignments': len(graded_assignments),
                'graded_assignments': len(graded_assignments),
                'average_score': round(average_score, 2),
                'average_percentage': round(average_percentage, 2),
                'weighted_average': round(weighted_average, 2),
                'assignments': graded_assignments
            }
            
        except Exception as e:
            self.logger.error(f"Error getting grade summary: {e}", exc_info=True)
            return {
                'total_assignments': 0,
                'graded_assignments': 0,
                'average_score': 0,
                'average_percentage': 0,
                'weighted_average': 0,
                'assignments': []
            }
    
    # --------------------------- #
    # Helper Methods            #
    # --------------------------- #
    
    def get_assignment_statuses(self):
        """
        Get a list of all assignment statuses.
        
        Returns:
            list: List of status strings
        """
        return [
            self.STATUS_NOT_STARTED, self.STATUS_IN_PROGRESS,
            self.STATUS_COMPLETED, self.STATUS_SUBMITTED,
            self.STATUS_GRADED, self.STATUS_LATE
        ]
    
    def get_assignment_priorities(self):
        """
        Get a list of all assignment priorities.
        
        Returns:
            list: List of priority strings
        """
        return [
            self.PRIORITY_LOW, self.PRIORITY_MEDIUM,
            self.PRIORITY_HIGH, self.PRIORITY_URGENT
        ]
    
    def get_assignment_types(self):
        """
        Get a list of all assignment types.
        
        Returns:
            list: List of assignment type strings
        """
        return [
            self.TYPE_HOMEWORK, self.TYPE_QUIZ, self.TYPE_EXAM,
            self.TYPE_PROJECT, self.TYPE_PAPER, self.TYPE_PRESENTATION,
            self.TYPE_DISCUSSION, self.TYPE_LAB, self.TYPE_OTHER
        ]
    
    def update_assignment_statuses(self):
        """
        Update assignment statuses based on due dates.
        
        Returns:
            int: Number of assignments updated
        """
        try:
            now = datetime.now()
            
            # Find assignments that are now late
            query = """
            UPDATE assignments
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE due_date < ?
            AND status IN (?, ?)
            """
            
            params = (
                self.STATUS_LATE,
                now.isoformat(),
                self.STATUS_NOT_STARTED,
                self.STATUS_IN_PROGRESS
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            
            return rows_affected
            
        except Exception as e:
            self.logger.error(f"Error updating assignment statuses: {e}", exc_info=True)
            return 0
    
    def format_assignment_list(self, assignments, include_details=False):
        """
        Format a list of assignments into a human-readable string.
        
        Args:
            assignments (list): List of assignment dictionaries
            include_details (bool, optional): Whether to include more details
            
        Returns:
            str: Formatted assignment list
        """
        try:
            if not assignments:
                return "No assignments found"
                
            lines = []
            
            for assignment in assignments:
                title = assignment.get('title', '')
                course_name = assignment.get('course_name', '')
                due_date = assignment.get('due_date', '')
                status = assignment.get('status', '')
                priority = assignment.get('priority', '')
                
                # Format due date
                formatted_due_date = ""
                if due_date:
                    try:
                        if isinstance(due_date, str):
                            due_date_obj = datetime.fromisoformat(due_date)
                        else:
                            due_date_obj = due_date
                            
                        formatted_due_date = due_date_obj.strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        formatted_due_date = str(due_date)
                
                # Basic assignment line
                assignment_line = f"{title}"
                if course_name:
                    assignment_line += f" ({course_name})"
                lines.append(assignment_line)
                
                # Add due date and status
                info_line = ""
                if formatted_due_date:
                    info_line += f"Due: {formatted_due_date}"
                if status:
                    if info_line:
                        info_line += " | "
                    info_line += f"Status: {status.replace('_', ' ').title()}"
                if priority:
                    if info_line:
                        info_line += " | "
                    info_line += f"Priority: {priority.title()}"
                    
                if info_line:
                    lines.append(f"  {info_line}")
                    
                # Additional details if requested
                if include_details:
                    if assignment.get('description'):
                        lines.append(f"  Description: {assignment['description']}")
                        
                    if assignment.get('assignment_type'):
                        lines.append(f"  Type: {assignment['assignment_type'].replace('_', ' ').title()}")
                        
                    if assignment.get('max_score') is not None:
                        lines.append(f"  Max Score: {assignment['max_score']}")
                        
                    if assignment.get('actual_score') is not None:
                        lines.append(f"  Score: {assignment['actual_score']}")
                        
                    if assignment.get('weight') is not None:
                        lines.append(f"  Weight: {assignment['weight']}%")
                        
                    if assignment.get('estimated_time') is not None:
                        minutes = assignment['estimated_time']
                        hours = minutes // 60
                        remaining_minutes = minutes % 60
                        
                        if hours > 0:
                            time_str = f"{hours} hr"
                            if remaining_minutes > 0:
                                time_str += f" {remaining_minutes} min"
                        else:
                            time_str = f"{minutes} min"
                            
                        lines.append(f"  Estimated Time: {time_str}")
                        
                    if assignment.get('feedback'):
                        lines.append(f"  Feedback: {assignment['feedback']}")
                        
                    # Add files if available
                    if assignment.get('files'):
                        files = assignment['files']
                        if files:
                            lines.append("  Files:")
                            for file in files:
                                filename = file.get('original_filename', '')
                                lines.append(f"    - {filename}")
                    
                # Add a blank line between assignments
                lines.append("")
                
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Error formatting assignment list: {e}", exc_info=True)
            return "Error formatting assignments"