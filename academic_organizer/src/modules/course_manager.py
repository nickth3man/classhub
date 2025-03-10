"""
Course Manager for the Academic Organizer application.

This module handles course-related operations for the application.
"""

import logging
import json
from datetime import datetime, timedelta, time
import uuid
import calendar


class CourseManager:
    """
    Course Manager for the Academic Organizer application.
    
    This class is responsible for:
    - Creation, retrieval, update, and deletion of courses
    - Managing course schedules and meeting times
    - Tracking course progress and grades
    - Organizing courses by semester/term
    - Calculating GPA and credit totals
    """
    
    # Course status constants
    STATUS_PLANNED = "planned"
    STATUS_CURRENT = "current"
    STATUS_COMPLETED = "completed"
    STATUS_DROPPED = "dropped"
    STATUS_ARCHIVED = "archived"
    
    # Course type constants
    TYPE_LECTURE = "lecture"
    TYPE_LAB = "lab"
    TYPE_SEMINAR = "seminar"
    TYPE_STUDIO = "studio"
    TYPE_ONLINE = "online"
    TYPE_HYBRID = "hybrid"
    TYPE_INDEPENDENT = "independent"
    TYPE_OTHER = "other"
    
    # Grade constants
    GRADE_A_PLUS = "A+"
    GRADE_A = "A"
    GRADE_A_MINUS = "A-"
    GRADE_B_PLUS = "B+"
    GRADE_B = "B"
    GRADE_B_MINUS = "B-"
    GRADE_C_PLUS = "C+"
    GRADE_C = "C"
    GRADE_C_MINUS = "C-"
    GRADE_D_PLUS = "D+"
    GRADE_D = "D"
    GRADE_D_MINUS = "D-"
    GRADE_F = "F"
    GRADE_P = "P"  # Pass
    GRADE_NP = "NP"  # No Pass
    GRADE_I = "I"  # Incomplete
    GRADE_W = "W"  # Withdrawn
    GRADE_IP = "IP"  # In Progress
    
    def __init__(self, db_manager):
        """
        Initialize the course manager.
        
        Args:
            db_manager: The database manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
    
    # --------------------------- #
    # Course CRUD Operations     #
    # --------------------------- #
    
    def create_course(self, name, code, credits=None, term_id=None, instructor=None,
                    description=None, location=None, course_type=None, status=None, 
                    syllabus_url=None, website_url=None, start_date=None, end_date=None,
                    color=None, notes=None):
        """
        Create a new course.
        
        Args:
            name (str): Course name
            code (str): Course code/number
            credits (float, optional): Credit hours
            term_id (int, optional): The term/semester ID
            instructor (str, optional): Instructor name
            description (str, optional): Course description
            location (str, optional): Course location (classroom, building)
            course_type (str, optional): Type of course
            status (str, optional): Current status
            syllabus_url (str, optional): URL to syllabus
            website_url (str, optional): URL to course website
            start_date (str, optional): Start date in ISO format
            end_date (str, optional): End date in ISO format
            color (str, optional): Color code for UI representation
            notes (str, optional): Additional notes
            
        Returns:
            int: The ID of the created course, or None if creation failed
        """
        try:
            # Validate required fields
            if not name:
                self.logger.error("Course name is required")
                return None
                
            if not code:
                self.logger.error("Course code is required")
                return None
                
            # Set default values if not provided
            if not status:
                status = self.STATUS_PLANNED
                
            if not course_type:
                course_type = self.TYPE_LECTURE
                
            # Validate status
            valid_statuses = [
                self.STATUS_PLANNED, self.STATUS_CURRENT, 
                self.STATUS_COMPLETED, self.STATUS_DROPPED,
                self.STATUS_ARCHIVED
            ]
            
            if status not in valid_statuses:
                self.logger.warning(f"Invalid status: {status}, using default")
                status = self.STATUS_PLANNED
                
            # Validate course type
            valid_types = [
                self.TYPE_LECTURE, self.TYPE_LAB, self.TYPE_SEMINAR,
                self.TYPE_STUDIO, self.TYPE_ONLINE, self.TYPE_HYBRID,
                self.TYPE_INDEPENDENT, self.TYPE_OTHER
            ]
            
            if course_type not in valid_types:
                self.logger.warning(f"Invalid course type: {course_type}, using default")
                course_type = self.TYPE_LECTURE
                
            # Parse dates
            parsed_start_date = None
            if start_date:
                try:
                    if isinstance(start_date, str):
                        parsed_start_date = datetime.fromisoformat(start_date)
                    elif isinstance(start_date, datetime):
                        parsed_start_date = start_date
                except ValueError:
                    self.logger.error(f"Invalid start date format: {start_date}")
                    parsed_start_date = None
                    
            parsed_end_date = None
            if end_date:
                try:
                    if isinstance(end_date, str):
                        parsed_end_date = datetime.fromisoformat(end_date)
                    elif isinstance(end_date, datetime):
                        parsed_end_date = end_date
                except ValueError:
                    self.logger.error(f"Invalid end date format: {end_date}")
                    parsed_end_date = None
                    
            # Generate a unique external ID for integration with other systems
            external_id = str(uuid.uuid4())
                
            # Insert course into database
            query = """
            INSERT INTO courses (
                name, code, credits, term_id, instructor,
                description, location, course_type, status,
                syllabus_url, website_url, start_date, end_date,
                color, notes, external_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                name, code, credits, term_id, instructor,
                description, location, course_type, status,
                syllabus_url, website_url, parsed_start_date, parsed_end_date,
                color, notes, external_id
            )
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            course_id = cursor.lastrowid
            self.logger.info(f"Course created with ID: {course_id}")
            
            return course_id
            
        except Exception as e:
            self.logger.error(f"Error creating course: {e}", exc_info=True)
            self.db_manager.get_connection().rollback()
            return None
    
    def get_course(self, course_id):
        """
        Get a course by ID.
        
        Args:
            course_id (int): The course ID
            
        Returns:
            dict: The course data, or None if not found
        """
        try:
            query = """
            SELECT c.*, t.name as term_name
            FROM courses c
            LEFT JOIN terms t ON c.term_id = t.id
            WHERE c.id = ?
            """
            params = (course_id,)
            
            result = self.db_manager.execute_query(query, params)
            
            if result:
                course_data = result[0]
                
                # Get schedule data
                course_data['schedule'] = self.get_course_schedule(course_id)
                
                return course_data
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting course: {e}", exc_info=True)
            return None
    
    def get_all_courses(self, term_id=None, status=None, course_type=None, 
                      active_only=False, sort_by=None, sort_order='asc'):
        """
        Get all courses, with optional filtering.
        
        Args:
            term_id (int, optional): Filter by term ID
            status (str, optional): Filter by status
            course_type (str, optional): Filter by course type
            active_only (bool, optional): If True, only returns current courses
            sort_by (str, optional): Field to sort by
            sort_order (str, optional): Sort order (asc/desc)
            
        Returns:
            list: List of course dictionaries
        """
        try:
            # Build query with conditional filters
            query_parts = [
                "SELECT c.*, t.name as term_name",
                "FROM courses c",
                "LEFT JOIN terms t ON c.term_id = t.id",
                "WHERE 1=1"  # Base condition to simplify adding AND clauses
            ]
            params = []
            
            if term_id is not None:
                query_parts.append("AND c.term_id = ?")
                params.append(term_id)
                
            if status is not None:
                query_parts.append("AND c.status = ?")
                params.append(status)
                
            if course_type is not None:
                query_parts.append("AND c.course_type = ?")
                params.append(course_type)
                
            if active_only:
                query_parts.append("AND c.status = ?")
                params.append(self.STATUS_CURRENT)
                
            # Add sorting
            if sort_by:
                # Map front-end field names to database columns if needed
                field_map = {
                    'name': 'c.name',
                    'code': 'c.code',
                    'credits': 'c.credits',
                    'instructor': 'c.instructor',
                    'status': 'c.status',
                    'term': 't.name',
                    'created_at': 'c.created_at',
                    'updated_at': 'c.updated_at'
                }
                
                db_field = field_map.get(sort_by, f"c.{sort_by}")
                query_parts.append(f"ORDER BY {db_field} {sort_order.upper()}")
            else:
                # Default sort by name
                query_parts.append("ORDER BY c.name")
                
            # Combine query parts
            query = " ".join(query_parts)
            
            # Execute query
            results = self.db_manager.execute_query(query, tuple(params) if params else None)
            
            # Get schedules for each course
            for course in results:
                course['schedule'] = self.get_course_schedule(course['id'])
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting courses: {e}", exc_info=True)
            return []
    
    def update_course(self, course_id, **kwargs):
        """
        Update a course.
        
        Args:
            course_id (int): The course ID
            **kwargs: Fields to update (name, code, credits, etc.)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get allowed fields
            allowed_fields = [
                'name', 'code', 'credits', 'term_id', 'instructor',
                'description', 'location', 'course_type', 'status',
                'syllabus_url', 'website_url', 'start_date', 'end_date',
                'color', 'notes', 'final_grade', 'is_favorite'
            ]
            
            # Filter kwargs to only include allowed fields
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                self.logger.warning("No valid fields provided for update")
                return False
                
            # Special handling for date fields
            for date_field in ['start_date', 'end_date']:
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
                
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            
            query = f"UPDATE courses SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (course_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating course: {e}", exc_info=True)
            return False
    
    def delete_course(self, course_id):
        """
        Delete a course.
        
        Args:
            course_id (int): The course ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Begin a transaction to delete related records
            conn = self.db_manager.get_connection()
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # Update files to remove course reference
                file_query = "UPDATE files SET course_id = NULL WHERE course_id = ?"
                conn.execute(file_query, (course_id,))
                
                # Update assignments to remove course reference
                assignment_query = "UPDATE assignments SET course_id = NULL WHERE course_id = ?"
                conn.execute(assignment_query, (course_id,))
                
                # Delete course schedule entries
                schedule_query = "DELETE FROM course_schedule WHERE course_id = ?"
                conn.execute(schedule_query, (course_id,))
                
                # Delete the course
                course_query = "DELETE FROM courses WHERE id = ?"
                conn.execute(course_query, (course_id,))
                
                # Commit the transaction
                conn.commit()
                
                return True
                
            except Exception as e:
                # Roll back transaction on error
                conn.rollback()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error deleting course: {e}", exc_info=True)
            return False
    
    # --------------------------- #
    # Course Schedule Management #
    # --------------------------- #
    
    def add_course_schedule(self, course_id, day_of_week, start_time, end_time, 
                          location=None, is_recurring=True, specific_date=None,
                          notes=None):
        """
        Add a scheduled meeting time for a course.
        
        Args:
            course_id (int): The course ID
            day_of_week (int): Day of week (0=Monday, 6=Sunday)
            start_time (str): Start time in 24-hour format (HH:MM)
            end_time (str): End time in 24-hour format (HH:MM)
            location (str, optional): Location for this specific meeting
            is_recurring (bool, optional): Whether this is a recurring meeting
            specific_date (str, optional): Specific date for non-recurring meetings
            notes (str, optional): Additional notes for this meeting
            
        Returns:
            int: The ID of the created schedule entry, or None if creation failed
        """
        try:
            # Validate required fields
            if course_id is None:
                self.logger.error("Course ID is required")
                return None
                
            if day_of_week is None and specific_date is None:
                self.logger.error("Either day_of_week or specific_date is required")
                return None
                
            if not start_time or not end_time:
                self.logger.error("Start time and end time are required")
                return None
                
            # Validate day of week
            if day_of_week is not None and (day_of_week < 0 or day_of_week > 6):
                self.logger.error(f"Invalid day of week: {day_of_week}")
                return None
                
            # Parse times
            try:
                if isinstance(start_time, str):
                    # Parse time string (HH:MM)
                    hour, minute = map(int, start_time.split(':'))
                    parsed_start_time = time(hour, minute)
                elif isinstance(start_time, time):
                    parsed_start_time = start_time
                else:
                    self.logger.error(f"Invalid start time format: {start_time}")
                    return None
            except (ValueError, TypeError):
                self.logger.error(f"Invalid start time format: {start_time}")
                return None
                
            try:
                if isinstance(end_time, str):
                    # Parse time string (HH:MM)
                    hour, minute = map(int, end_time.split(':'))
                    parsed_end_time = time(hour, minute)
                elif isinstance(end_time, time):
                    parsed_end_time = end_time
                else:
                    self.logger.error(f"Invalid end time format: {end_time}")
                    return None
            except (ValueError, TypeError):
                self.logger.error(f"Invalid end time format: {end_time}")
                return None
                
            # Parse specific date if provided
            parsed_specific_date = None
            if specific_date:
                try:
                    if isinstance(specific_date, str):
                        parsed_specific_date = datetime.fromisoformat(specific_date).date()
                    elif isinstance(specific_date, datetime):
                        parsed_specific_date = specific_date.date()
                except ValueError:
                    self.logger.error(f"Invalid specific date format: {specific_date}")
                    return None
                    
            # Insert schedule into database
            query = """
            INSERT INTO course_schedule (
                course_id, day_of_week, start_time, end_time,
                location, is_recurring, specific_date, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                course_id, day_of_week, parsed_start_time, parsed_end_time,
                location, is_recurring, parsed_specific_date, notes
            )
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            schedule_id = cursor.lastrowid
            self.logger.info(f"Course schedule added with ID: {schedule_id}")
            
            return schedule_id
            
        except Exception as e:
            self.logger.error(f"Error adding course schedule: {e}", exc_info=True)
            self.db_manager.get_connection().rollback()
            return None
    
    def get_course_schedule(self, course_id):
        """
        Get all scheduled meeting times for a course.
        
        Args:
            course_id (int): The course ID
            
        Returns:
            list: List of schedule dictionaries
        """
        try:
            query = """
            SELECT *
            FROM course_schedule
            WHERE course_id = ?
            ORDER BY day_of_week, start_time
            """
            params = (course_id,)
            
            results = self.db_manager.execute_query(query, params)
            
            # Format day of week as string for display
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            for schedule in results:
                if schedule.get('day_of_week') is not None:
                    day_index = schedule['day_of_week']
                    if 0 <= day_index <= 6:
                        schedule['day_name'] = days[day_index]
                    else:
                        schedule['day_name'] = "Unknown"
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting course schedule: {e}", exc_info=True)
            return []
    
    def update_course_schedule(self, schedule_id, **kwargs):
        """
        Update a course schedule entry.
        
        Args:
            schedule_id (int): The schedule entry ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get allowed fields
            allowed_fields = [
                'day_of_week', 'start_time', 'end_time', 'location',
                'is_recurring', 'specific_date', 'notes'
            ]
            
            # Filter kwargs to only include allowed fields
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                self.logger.warning("No valid fields provided for update")
                return False
                
            # Special handling for time fields
            for time_field in ['start_time', 'end_time']:
                if time_field in update_fields:
                    time_value = update_fields[time_field]
                    if time_value is not None:
                        try:
                            if isinstance(time_value, str):
                                # Parse time string (HH:MM)
                                hour, minute = map(int, time_value.split(':'))
                                parsed_time = time(hour, minute)
                                update_fields[time_field] = parsed_time
                            elif not isinstance(time_value, time):
                                # Invalid type
                                self.logger.error(f"Invalid {time_field} format: {time_value}")
                                del update_fields[time_field]
                        except (ValueError, TypeError):
                            self.logger.error(f"Invalid {time_field} format: {time_value}")
                            del update_fields[time_field]
                
            # Special handling for specific_date
            if 'specific_date' in update_fields:
                date_value = update_fields['specific_date']
                if date_value is not None:
                    try:
                        if isinstance(date_value, str):
                            parsed_date = datetime.fromisoformat(date_value).date()
                            update_fields['specific_date'] = parsed_date
                        elif isinstance(date_value, datetime):
                            update_fields['specific_date'] = date_value.date()
                        elif not isinstance(date_value, date):
                            # Invalid type
                            self.logger.error(f"Invalid specific_date format: {date_value}")
                            del update_fields['specific_date']
                    except ValueError:
                        self.logger.error(f"Invalid specific_date format: {date_value}")
                        del update_fields['specific_date']
                
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            
            query = f"UPDATE course_schedule SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (schedule_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating course schedule: {e}", exc_info=True)
            return False
    
    def delete_course_schedule(self, schedule_id):
        """
        Delete a course schedule entry.
        
        Args:
            schedule_id (int): The schedule entry ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            query = "DELETE FROM course_schedule WHERE id = ?"
            params = (schedule_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting course schedule: {e}", exc_info=True)
            return False
    
    def get_weekly_schedule(self, term_id=None, date=None):
        """
        Get the weekly schedule for all courses.
        
        Args:
            term_id (int, optional): Filter by term ID
            date (str, optional): Reference date to determine the current week
            
        Returns:
            dict: Weekly schedule organized by day and time
        """
        try:
            # Get all active courses
            courses = self.get_all_courses(term_id=term_id, active_only=True)
            
            # Initialize weekly schedule
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekly_schedule = {day: [] for day in days}
            
            # Process each course
            for course in courses:
                course_id = course['id']
                course_schedule = self.get_course_schedule(course_id)
                
                for schedule in course_schedule:
                    # Skip non-recurring events if we're getting a generic weekly schedule
                    if not schedule.get('is_recurring', True):
                        continue
                        
                    day_of_week = schedule.get('day_of_week')
                    
                    # Skip if day_of_week is invalid
                    if day_of_week is None or day_of_week < 0 or day_of_week > 6:
                        continue
                        
                    day_name = days[day_of_week]
                    
                    # Format times
                    start_time = schedule.get('start_time')
                    end_time = schedule.get('end_time')
                    
                    if isinstance(start_time, str):
                        # Already a string
                        formatted_start = start_time
                    elif isinstance(start_time, time):
                        formatted_start = start_time.strftime("%H:%M")
                    else:
                        formatted_start = "Unknown"
                        
                    if isinstance(end_time, str):
                        # Already a string
                        formatted_end = end_time
                    elif isinstance(end_time, time):
                        formatted_end = end_time.strftime("%H:%M")
                    else:
                        formatted_end = "Unknown"
                        
                    # Create event entry
                    event = {
                        'course_id': course_id,
                        'course_name': course['name'],
                        'course_code': course['code'],
                        'start_time': formatted_start,
                        'end_time': formatted_end,
                        'location': schedule.get('location') or course.get('location'),
                        'color': course.get('color'),
                        'schedule_id': schedule['id']
                    }
                    
                    weekly_schedule[day_name].append(event)
                    
            # Sort events by start time for each day
            for day in days:
                weekly_schedule[day].sort(key=lambda x: x['start_time'])
                
            return weekly_schedule
            
        except Exception as e:
            self.logger.error(f"Error getting weekly schedule: {e}", exc_info=True)
            return {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    
    def get_daily_schedule(self, date=None):
        """
        Get the schedule for a specific day.
        
        Args:
            date (str, optional): The date to get schedule for (defaults to today)
            
        Returns:
            list: List of scheduled events for the day
        """
        try:
            # Parse date
            if date is None:
                target_date = datetime.now().date()
            elif isinstance(date, str):
                target_date = datetime.fromisoformat(date).date()
            elif isinstance(date, datetime):
                target_date = date.date()
            else:
                target_date = date
                
            # Get day of week (0 = Monday, 6 = Sunday)
            day_of_week = target_date.weekday()
            
            # Get all active courses
            courses = self.get_all_courses(active_only=True)
            
            daily_events = []
            
            # Process each course
            for course in courses:
                course_id = course['id']
                course_schedule = self.get_course_schedule(course_id)
                
                for schedule in course_schedule:
                    # Include if:
                    # 1. It's a recurring event on this day of week, or
                    # 2. It's a specific event on this exact date
                    is_recurring = schedule.get('is_recurring', True)
                    schedule_day = schedule.get('day_of_week')
                    specific_date = schedule.get('specific_date')
                    
                    is_matching_day = (is_recurring and schedule_day == day_of_week)
                    is_matching_date = False
                    
                    if specific_date:
                        # Compare to the target date
                        if isinstance(specific_date, str):
                            specific_date = datetime.fromisoformat(specific_date).date()
                        elif isinstance(specific_date, datetime):
                            specific_date = specific_date.date()
                            
                        is_matching_date = (specific_date == target_date)
                        
                    if is_matching_day or is_matching_date:
                        # Format times
                        start_time = schedule.get('start_time')
                        end_time = schedule.get('end_time')
                        
                        if isinstance(start_time, str):
                            # Already a string
                            formatted_start = start_time
                        elif isinstance(start_time, time):
                            formatted_start = start_time.strftime("%H:%M")
                        else:
                            formatted_start = "Unknown"
                            
                        if isinstance(end_time, str):
                            # Already a string
                            formatted_end = end_time
                        elif isinstance(end_time, time):
                            formatted_end = end_time.strftime("%H:%M")
                        else:
                            formatted_end = "Unknown"
                            
                        # Create event entry
                        event = {
                            'course_id': course_id,
                            'course_name': course['name'],
                            'course_code': course['code'],
                            'start_time': formatted_start,
                            'end_time': formatted_end,
                            'location': schedule.get('location') or course.get('location'),
                            'color': course.get('color'),
                            'schedule_id': schedule['id'],
                            'notes': schedule.get('notes'),
                            'is_recurring': is_recurring
                        }
                        
                        daily_events.append(event)
                        
            # Sort events by start time
            daily_events.sort(key=lambda x: x['start_time'])
            
            return daily_events
            
        except Exception as e:
            self.logger.error(f"Error getting daily schedule: {e}", exc_info=True)
            return []
    
    # --------------------------- #
    # Term/Semester Management   #
    # --------------------------- #
    
    def create_term(self, name, start_date=None, end_date=None, is_current=False):
        """
        Create a new term/semester.
        
        Args:
            name (str): Term name
            start_date (str, optional): Start date in ISO format
            end_date (str, optional): End date in ISO format
            is_current (bool, optional): Whether this is the current term
            
        Returns:
            int: The ID of the created term, or None if creation failed
        """
        try:
            # Validate required fields
            if not name:
                self.logger.error("Term name is required")
                return None
                
            # Parse dates
            parsed_start_date = None
            if start_date:
                try:
                    if isinstance(start_date, str):
                        parsed_start_date = datetime.fromisoformat(start_date)
                    elif isinstance(start_date, datetime):
                        parsed_start_date = start_date
                except ValueError:
                    self.logger.error(f"Invalid start date format: {start_date}")
                    parsed_start_date = None
                    
            parsed_end_date = None
            if end_date:
                try:
                    if isinstance(end_date, str):
                        parsed_end_date = datetime.fromisoformat(end_date)
                    elif isinstance(end_date, datetime):
                        parsed_end_date = end_date
                except ValueError:
                    self.logger.error(f"Invalid end date format: {end_date}")
                    parsed_end_date = None
                    
            # If this is set as current, unset any existing current term
            if is_current:
                update_query = "UPDATE terms SET is_current = 0"
                self.db_manager.execute_update(update_query)
                
            # Insert term into database
            query = """
            INSERT INTO terms (
                name, start_date, end_date, is_current
            )
            VALUES (?, ?, ?, ?)
            """
            params = (name, parsed_start_date, parsed_end_date, is_current)
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            term_id = cursor.lastrowid
            self.logger.info(f"Term created with ID: {term_id}")
            
            return term_id
            
        except Exception as e:
            self.logger.error(f"Error creating term: {e}", exc_info=True)
            self.db_manager.get_connection().rollback()
            return None
    
    def get_term(self, term_id):
        """
        Get a term by ID.
        
        Args:
            term_id (int): The term ID
            
        Returns:
            dict: The term data, or None if not found
        """
        try:
            query = "SELECT * FROM terms WHERE id = ?"
            params = (term_id,)
            
            result = self.db_manager.execute_query(query, params)
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting term: {e}", exc_info=True)
            return None
    
    def get_all_terms(self, include_current_indicator=False):
        """
        Get all terms.
        
        Args:
            include_current_indicator (bool, optional): Include indication of the current term
            
        Returns:
            list: List of term dictionaries
        """
        try:
            query = "SELECT * FROM terms ORDER BY start_date DESC"
            terms = self.db_manager.execute_query(query)
            
            if include_current_indicator:
                current_term = self.get_current_term()
                
                if current_term:
                    for term in terms:
                        term['is_current'] = (term['id'] == current_term['id'])
                        
            return terms
            
        except Exception as e:
            self.logger.error(f"Error getting terms: {e}", exc_info=True)
            return []
    
    def get_current_term(self):
        """
        Get the current term.
        
        Returns:
            dict: The current term data, or None if not found
        """
        try:
            # Try to get term marked as current
            query = "SELECT * FROM terms WHERE is_current = 1"
            result = self.db_manager.execute_query(query)
            
            if result:
                return result[0]
                
            # If no term is marked as current, try to find one that encompasses today's date
            today = datetime.now().date().isoformat()
            
            date_query = """
            SELECT * FROM terms
            WHERE start_date <= ? AND end_date >= ?
            ORDER BY start_date DESC
            LIMIT 1
            """
            params = (today, today)
            
            date_result = self.db_manager.execute_query(date_query, params)
            
            if date_result:
                return date_result[0]
                
            # If still no term found, return the most recent one
            recent_query = """
            SELECT * FROM terms
            ORDER BY start_date DESC
            LIMIT 1
            """
            
            recent_result = self.db_manager.execute_query(recent_query)
            return recent_result[0] if recent_result else None
            
        except Exception as e:
            self.logger.error(f"Error getting current term: {e}", exc_info=True)
            return None
    
    def update_term(self, term_id, **kwargs):
        """
        Update a term.
        
        Args:
            term_id (int): The term ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get allowed fields
            allowed_fields = ['name', 'start_date', 'end_date', 'is_current']
            
            # Filter kwargs to only include allowed fields
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                self.logger.warning("No valid fields provided for update")
                return False
                
            # Special handling for date fields
            for date_field in ['start_date', 'end_date']:
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
                
            # If setting as current, unset any existing current term
            if update_fields.get('is_current'):
                update_query = "UPDATE terms SET is_current = 0"
                self.db_manager.execute_update(update_query)
                
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            
            query = f"UPDATE terms SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (term_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating term: {e}", exc_info=True)
            return False
    
    def delete_term(self, term_id):
        """
        Delete a term.
        
        Args:
            term_id (int): The term ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Check if any courses are associated with this term
            check_query = "SELECT COUNT(*) as count FROM courses WHERE term_id = ?"
            check_params = (term_id,)
            
            check_result = self.db_manager.execute_query(check_query, check_params)
            
            if check_result and check_result[0]['count'] > 0:
                self.logger.warning(f"Cannot delete term: {term_id} as it has associated courses")
                return False
                
            # Delete the term
            query = "DELETE FROM terms WHERE id = ?"
            params = (term_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting term: {e}", exc_info=True)
            return False
    
    # --------------------------- #
    # Grade and GPA Calculation  #
    # --------------------------- #
    
    # --------------------------- #
    # Syllabus Parsing           #
    # --------------------------- #
    
    def _store_syllabus(self, syllabus_path, course_code):
        """
        Store a syllabus file in the application's storage directory.
        
        Args:
            syllabus_path (str): Path to the syllabus file
            course_code (str): Course code for naming the file
            
        Returns:
            str: Path to the stored syllabus file, or None if storage failed
        """
        try:
            import shutil
            from pathlib import Path
            from datetime import datetime
            
            # Create a unique filename based on course code and timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{course_code.replace(' ', '_')}_{timestamp}.pdf"
            
            # Determine storage directory
            storage_dir = Path("data/syllabi")
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Destination path
            dest_path = storage_dir / filename
            
            # Copy the file
            shutil.copy2(syllabus_path, dest_path)
            
            self.logger.info(f"Syllabus stored at: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            self.logger.error(f"Error storing syllabus: {e}", exc_info=True)
            return None
    
    def _delete_syllabus(self, syllabus_path):
        """
        Delete a syllabus file.
        
        Args:
            syllabus_path (str): Path to the syllabus file
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            from pathlib import Path
            
            path = Path(syllabus_path)
            if path.exists() and path.is_file():
                path.unlink()
                self.logger.info(f"Syllabus deleted: {syllabus_path}")
                return True
            else:
                self.logger.warning(f"Syllabus not found: {syllabus_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting syllabus: {e}", exc_info=True)
            return False
    
    def parse_syllabus(self, syllabus_path):
        """
        Parse a syllabus file to extract course information.
        
        Args:
            syllabus_path (str): Path to the syllabus file
            
        Returns:
            dict: Extracted information from the syllabus
        """
        try:
            import re
            import PyPDF2
            from pathlib import Path
            
            path = Path(syllabus_path)
            if not path.exists() or not path.is_file():
                self.logger.error(f"Syllabus file not found: {syllabus_path}")
                return None
                
            # Check file extension
            if path.suffix.lower() != '.pdf':
                self.logger.error(f"Unsupported file format: {path.suffix}")
                return {"error": "Only PDF files are supported for syllabus parsing"}
                
            # Extract text from PDF
            text = ""
            try:
                with open(path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                self.logger.error(f"Error reading PDF: {e}", exc_info=True)
                return {"error": f"Error reading PDF: {str(e)}"}
                
            # Parse the extracted text
            result = {
                "course_name": None,
                "course_code": None,
                "instructor": None,
                "semester": None,
                "office_hours": None,
                "textbooks": [],
                "assignments": [],
                "schedule": []
            }
            
            # Extract course code and name
            course_pattern = re.compile(r'([A-Z]{2,4}\s*\d{3,4}[A-Z]?)(?:\s*[-:]\s*|\s+)([^\\n]+)', re.IGNORECASE)
            course_match = course_pattern.search(text)
            if course_match:
                result["course_code"] = course_match.group(1).strip()
                result["course_name"] = course_match.group(2).strip()
                
            # Extract instructor
            instructor_pattern = re.compile(r'(?:instructor|professor|teacher)s?(?:\s*[:]\s*|\s+)((?:Dr|Prof|Professor|Mr|Ms|Mrs)?\.?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE)
            instructor_match = instructor_pattern.search(text)
            if instructor_match:
                result["instructor"] = instructor_match.group(1).strip()
                
            # Extract semester
            semester_pattern = re.compile(r'(?:semester|term|quarter)(?:\s*[:]\s*|\s+)((?:Spring|Fall|Summer|Winter)\s+\d{4})', re.IGNORECASE)
            semester_match = semester_pattern.search(text)
            if semester_match:
                result["semester"] = semester_match.group(1).strip()
                
            # Extract office hours
            office_hours_pattern = re.compile(r'(?:office\s+hours)(?:\s*[:]\s*|\s+)([^\\n]+)', re.IGNORECASE)
            office_hours_match = office_hours_pattern.search(text)
            if office_hours_match:
                result["office_hours"] = office_hours_match.group(1).strip()
                
            # Extract assignments
            assignment_pattern = re.compile(r'(?:assignment|homework|project|paper|exam|quiz)(?:\s*\d+)?(?:\s*[:]\s*|\s+)([^\\n]+)(?:\s+Due(?:\s*[:]\s*|\s+)([^\\n]+))?', re.IGNORECASE)
            for match in assignment_pattern.finditer(text):
                assignment = {
                    "title": match.group(1).strip(),
                    "due_date": match.group(2).strip() if match.group(2) else None
                }
                result["assignments"].append(assignment)
                
            # Extract textbooks
            textbook_pattern = re.compile(r'(?:textbook|book|reading)(?:\s*[:]\s*|\s+)([^\\n]+)', re.IGNORECASE)
            for match in textbook_pattern.finditer(text):
                result["textbooks"].append(match.group(1).strip())
                
            # Extract schedule items
            schedule_pattern = re.compile(r'(?:week|session|class)\s+(\d+)(?:\s*[:]\s*|\s+)([^\\n]+)', re.IGNORECASE)
            for match in schedule_pattern.finditer(text):
                schedule_item = {
                    "week": match.group(1).strip(),
                    "topic": match.group(2).strip()
                }
                result["schedule"].append(schedule_item)
                
            self.logger.info(f"Syllabus parsed successfully: {syllabus_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing syllabus: {e}", exc_info=True)
            return {"error": str(e)}
    
    def update_course_from_syllabus(self, course_id, syllabus_path):
        """
        Update course information based on parsed syllabus data.
        
        Args:
            course_id (int): The course ID
            syllabus_path (str): Path to the syllabus file
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Parse the syllabus
            syllabus_data = self.parse_syllabus(syllabus_path)
            if not syllabus_data or "error" in syllabus_data:
                self.logger.error(f"Failed to parse syllabus: {syllabus_data.get('error', 'Unknown error')}")
                return False
                
            # Store the syllabus file
            course = self.get_course(course_id)
            if not course:
                self.logger.error(f"Course not found: {course_id}")
                return False
                
            course_code = syllabus_data.get("course_code") or course.get("code")
            stored_path = self._store_syllabus(syllabus_path, course_code)
            if not stored_path:
                self.logger.error("Failed to store syllabus file")
                return False
                
            # Update course with syllabus data
            update_data = {
                "syllabus_path": stored_path
            }
            
            # Update course name if available
            if syllabus_data.get("course_name"):
                update_data["name"] = syllabus_data["course_name"]
                
            # Update course code if available
            if syllabus_data.get("course_code"):
                update_data["code"] = syllabus_data["course_code"]
                
            # Update semester if available
            if syllabus_data.get("semester"):
                update_data["semester"] = syllabus_data["semester"]
                
            # Update instructor if available
            if syllabus_data.get("instructor"):
                # Check if instructor exists
                instructor_id = None
                instructors = self.search_instructors(syllabus_data["instructor"])
                
                if instructors:
                    # Use existing instructor
                    instructor_id = instructors[0]["id"]
                else:
                    # Create new instructor
                    instructor_id = self.create_instructor(
                        name=syllabus_data["instructor"],
                        office_hours=syllabus_data.get("office_hours")
                    )
                    
                if instructor_id:
                    update_data["instructor_id"] = instructor_id
                    
            # Update the course
            success = self.update_course(course_id, **update_data)
            
            # Add assignments from syllabus
            if success and syllabus_data.get("assignments"):
                for assignment in syllabus_data["assignments"]:
                    # TODO: Implement assignment creation when assignment module is ready
                    self.logger.info(f"Assignment found in syllabus: {assignment['title']}")
                    
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating course from syllabus: {e}", exc_info=True)
            return False
    
    def search_instructors(self, name_query):
        """
        Search for instructors by name.
        
        Args:
            name_query (str): Name to search for
            
        Returns:
            list: List of matching instructors
        """
        try:
            query = """
            SELECT *
            FROM instructors
            WHERE name LIKE ?
            ORDER BY name
            """
            params = (f"%{name_query}%",)
            
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error searching instructors: {e}", exc_info=True)
            return []
    
    def create_instructor(self, name, email=None, phone=None, office_location=None, office_hours=None):
        """
        Create a new instructor.
        
        Args:
            name (str): Instructor name
            email (str, optional): Email address
            phone (str, optional): Phone number
            office_location (str, optional): Office location
            office_hours (str, optional): Office hours
            
        Returns:
            int: The ID of the created instructor, or None if creation failed
        """
        try:
            # Validate required fields
            if not name:
                self.logger.error("Instructor name is required")
                return None
                
            # Insert instructor into database
            query = """
            INSERT INTO instructors (
                name, email, phone, office_location, office_hours
            )
            VALUES (?, ?, ?, ?, ?)
            """
            params = (name, email, phone, office_location, office_hours)
            
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(query, params)
            self.db_manager.get_connection().commit()
            
            instructor_id = cursor.lastrowid
            self.logger.info(f"Instructor created with ID: {instructor_id}")
            
            return instructor_id
            
        except Exception as e:
            self.logger.error(f"Error creating instructor: {e}", exc_info=True)
            self.db_manager.get_connection().rollback()
            return None
    
    def get_instructor(self, instructor_id):
        """
        Get an instructor by ID.
        
        Args:
            instructor_id (int): The instructor ID
            
        Returns:
            dict: The instructor data, or None if not found
        """
        try:
            query = "SELECT * FROM instructors WHERE id = ?"
            params = (instructor_id,)
            
            result = self.db_manager.execute_query(query, params)
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting instructor: {e}", exc_info=True)
            return None
    
    def update_instructor(self, instructor_id, **kwargs):
        """
        Update an instructor.
        
        Args:
            instructor_id (int): The instructor ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get allowed fields
            allowed_fields = ['name', 'email', 'phone', 'office_location', 'office_hours']
            
            # Filter kwargs to only include allowed fields
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                self.logger.warning("No valid fields provided for update")
                return False
                
            # Build update query
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            
            query = f"UPDATE instructors SET {set_clause} WHERE id = ?"
            params = tuple(update_fields.values()) + (instructor_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating instructor: {e}", exc_info=True)
            return False
    
    def delete_instructor(self, instructor_id):
        """
        Delete an instructor.
        
        Args:
            instructor_id (int): The instructor ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Check if any courses are associated with this instructor
            check_query = "SELECT COUNT(*) as count FROM courses WHERE instructor_id = ?"
            check_params = (instructor_id,)
            
            check_result = self.db_manager.execute_query(check_query, check_params)
            
            if check_result and check_result[0]['count'] > 0:
                self.logger.warning(f"Cannot delete instructor: {instructor_id} as they have associated courses")
                return False
                
            # Delete the instructor
            query = "DELETE FROM instructors WHERE id = ?"
            params = (instructor_id,)
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting instructor: {e}", exc_info=True)
            return False
    
    def set_course_grade(self, course_id, grade):
        """
        Set the final grade for a course.
        
        Args:
            course_id (int): The course ID
            grade (str): The grade (letter or number)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Validate grade
            valid_grades = [
                self.GRADE_A_PLUS, self.GRADE_A, self.GRADE_A_MINUS,
                self.GRADE_B_PLUS, self.GRADE_B, self.GRADE_B_MINUS,
                self.GRADE_C_PLUS, self.GRADE_C, self.GRADE_C_MINUS,
                self.GRADE_D_PLUS, self.GRADE_D, self.GRADE_D_MINUS,
                self.GRADE_F, self.GRADE_P, self.GRADE_NP,
                self.GRADE_I, self.GRADE_W, self.GRADE_IP
            ]
            
            # Check if grade is a valid letter grade
            if grade not in valid_grades:
                # Check if it's a numeric grade
                try:
                    numeric_grade = float(grade)
                    if 0 <= numeric_grade <= 100:
                        # Convert numeric grade to letter grade
                        grade = self.convert_numeric_to_letter_grade(numeric_grade)
                    else:
                        self.logger.error(f"Invalid numeric grade: {grade}")
                        return False
                except (ValueError, TypeError):
                    self.logger.error(f"Invalid grade: {grade}")
                    return False
                    
            # Update course with grade and set status to completed
            update_data = {
                'final_grade': grade,
                'status': self.STATUS_COMPLETED
            }
            
            return self.update_course(course_id, **update_data)
            
        except Exception as e:
            self.logger.error(f"Error setting course grade: {e}", exc_info=True)
            return False
    
    def calculate_term_gpa(self, term_id=None):
        """
        Calculate GPA for a specific term or the current term.
        
        Args:
            term_id (int, optional): The term ID, or None for current term
            
        Returns:
            dict: Term GPA information
        """
        try:
            # Get term
            term = None
            if term_id is None:
                term = self.get_current_term()
                if term:
                    term_id = term['id']
            else:
                term = self.get_term(term_id)
                
            if not term:
                self.logger.error("No term found")
                return {
                    'success': False,
                    'error': 'No term found'
                }
                
            # Get all courses for the term with grades
            query = """
            SELECT c.id, c.name, c.code, c.credits, c.final_grade
            FROM courses c
            WHERE c.term_id = ?
            AND c.final_grade IS NOT NULL
            AND c.final_grade != ''
            """
            params = (term_id,)
            
            courses = self.db_manager.execute_query(query, params)
            
            # Calculate GPA
            total_grade_points = 0
            total_credits = 0
            course_grades = []
            
            for course in courses:
                grade = course.get('final_grade')
                credits = course.get('credits')
                
                if not grade or not credits:
                    continue
                    
                # Skip non-GPA grades (P/NP, W, I, etc.)
                grade_points = self.get_grade_points(grade)
                if grade_points is None:
                    continue
                    
                course_grade_points = grade_points * float(credits)
                total_grade_points += course_grade_points
                total_credits += float(credits)
                
                course_grades.append({
                    'course_id': course['id'],
                    'course_name': course['name'],
                    'course_code': course['code'],
                    'credits': credits,
                    'grade': grade,
                    'grade_points': grade_points,
                    'course_grade_points': course_grade_points
                })
                
            # Calculate GPA
            gpa = total_grade_points / total_credits if total_credits > 0 else 0
            
            return {
                'success': True,
                'term': {
                    'id': term['id'],
                    'name': term['name']
                },
                'gpa': round(gpa, 2),
                'total_credits': total_credits,
                'total_grade_points': total_grade_points,
                'course_grades': course_grades
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating term GPA: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_cumulative_gpa(self):
        """
        Calculate cumulative GPA across all terms.
        
        Returns:
            dict: Cumulative GPA information
        """
        try:
            # Get all courses with grades
            query = """
            SELECT c.id, c.name, c.code, c.credits, c.final_grade, t.name as term_name
            FROM courses c
            LEFT JOIN terms t ON c.term_id = t.id
            WHERE c.final_grade IS NOT NULL
            AND c.final_grade != ''
            """
            
            courses = self.db_manager.execute_query(query)
            
            # Calculate GPA
            total_grade_points = 0
            total_credits = 0
            course_grades = []
            
            for course in courses:
                grade = course.get('final_grade')
                credits = course.get('credits')
                
                if not grade or not credits:
                    continue
                    
                # Skip non-GPA grades (P/NP, W, I, etc.)
                grade_points = self.get_grade_points(grade)
                if grade_points is None:
                    continue
                    
                course_grade_points = grade_points * float(credits)
                total_grade_points += course_grade_points
                total_credits += float(credits)
                
                course_grades.append({
                    'course_id': course['id'],
                    'course_name': course['name'],
                    'course_code': course['code'],
                    'term_name': course.get('term_name', 'Unknown Term'),
                    'credits': credits,
                    'grade': grade,
                    'grade_points': grade_points,
                    'course_grade_points': course_grade_points
                })
                
            # Calculate GPA
            gpa = total_grade_points / total_credits if total_credits > 0 else 0
            
            # Calculate GPA by term
            term_gpas = {}
            terms = self.get_all_terms()
            
            for term in terms:
                term_gpa = self.calculate_term_gpa(term['id'])
                if term_gpa.get('success'):
                    term_gpas[term['id']] = {
                        'name': term['name'],
                        'gpa': term_gpa['gpa'],
                        'credits': term_gpa['total_credits']
                    }
                    
            return {
                'success': True,
                'gpa': round(gpa, 2),
                'total_credits': total_credits,
                'total_grade_points': total_grade_points,
                'course_grades': course_grades,
                'term_gpas': term_gpas
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating cumulative GPA: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    # --------------------------- #
    # Search Functionality       #
    # --------------------------- #
    
    def search_courses(self, query):
        """
        Search for courses by name, code, or description.
        
        Args:
            query (str): Search query
            
        Returns:
            list: List of matching courses
        """
        try:
            # Build search query
            search_query = """
            SELECT c.*, t.name as term_name
            FROM courses c
            LEFT JOIN terms t ON c.term_id = t.id
            WHERE c.name LIKE ? OR c.code LIKE ? OR c.description LIKE ?
            ORDER BY c.name
            """
            params = (f"%{query}%", f"%{query}%", f"%{query}%")
            
            results = self.db_manager.execute_query(search_query, params)
            
            # Get schedules for each course
            for course in results:
                course['schedule'] = self.get_course_schedule(course['id'])
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching courses: {e}", exc_info=True)
            return []
    
    def get_course_statistics(self):
        """
        Get statistics about courses.
        
        Returns:
            dict: Course statistics
        """
        try:
            # Get total number of courses
            total_query = "SELECT COUNT(*) as total_courses FROM courses"
            total_result = self.db_manager.execute_query(total_query)
            total_courses = total_result[0]['total_courses'] if total_result else 0
            
            # Get courses per semester
            semester_query = """
            SELECT semester, COUNT(*) as course_count
            FROM courses
            WHERE semester IS NOT NULL
            GROUP BY semester
            ORDER BY semester DESC
            """
            courses_per_semester = self.db_manager.execute_query(semester_query)
            
            # Get courses per instructor
            instructor_query = """
            SELECT i.name as instructor_name, COUNT(*) as course_count
            FROM courses c
            JOIN instructors i ON c.instructor_id = i.id
            GROUP BY c.instructor_id
            ORDER BY course_count DESC
            """
            courses_per_instructor = self.db_manager.execute_query(instructor_query)
            
            return {
                "total_courses": total_courses,
                "courses_per_semester": courses_per_semester,
                "courses_per_instructor": courses_per_instructor
            }
            
        except Exception as e:
            self.logger.error(f"Error getting course statistics: {e}", exc_info=True)
            return {
                "total_courses": 0,
                "courses_per_semester": [],
                "courses_per_instructor": []
            }
    
    # --------------------------- #
    # Helper Methods            #
    # --------------------------- #
    
    def get_course_statuses(self):
        """
        Get a list of all course statuses.
        
        Returns:
            list: List of status strings
        """
        return [
            self.STATUS_PLANNED, self.STATUS_CURRENT, 
            self.STATUS_COMPLETED, self.STATUS_DROPPED,
            self.STATUS_ARCHIVED
        ]
    
    def get_course_types(self):
        """
        Get a list of all course types.
        
        Returns:
            list: List of course type strings
        """
        return [
            self.TYPE_LECTURE, self.TYPE_LAB, self.TYPE_SEMINAR,
            self.TYPE_STUDIO, self.TYPE_ONLINE, self.TYPE_HYBRID,
            self.TYPE_INDEPENDENT, self.TYPE_OTHER
        ]
    
    def get_grade_options(self):
        """
        Get a list of all grade options.
        
        Returns:
            list: List of grade strings
        """
        return [
            self.GRADE_A_PLUS, self.GRADE_A, self.GRADE_A_MINUS,
            self.GRADE_B_PLUS, self.GRADE_B, self.GRADE_B_MINUS,
            self.GRADE_C_PLUS, self.GRADE_C, self.GRADE_C_MINUS,
            self.GRADE_D_PLUS, self.GRADE_D, self.GRADE_D_MINUS,
            self.GRADE_F, self.GRADE_P, self.GRADE_NP,
            self.GRADE_I, self.GRADE_W, self.GRADE_IP
        ]
    
    def get_grade_points(self, grade):
        """
        Get the grade points for a letter grade.
        
        Args:
            grade (str): The letter grade
            
        Returns:
            float: The grade points, or None if non-GPA grade
        """
        grade_points = {
            self.GRADE_A_PLUS: 4.0,
            self.GRADE_A: 4.0,
            self.GRADE_A_MINUS: 3.7,
            self.GRADE_B_PLUS: 3.3,
            self.GRADE_B: 3.0,
            self.GRADE_B_MINUS: 2.7,
            self.GRADE_C_PLUS: 2.3,
            self.GRADE_C: 2.0,
            self.GRADE_C_MINUS: 1.7,
            self.GRADE_D_PLUS: 1.3,
            self.GRADE_D: 1.0,
            self.GRADE_D_MINUS: 0.7,
            self.GRADE_F: 0.0
        }
        
        return grade_points.get(grade)
    
    def convert_numeric_to_letter_grade(self, percentage):
        """
        Convert a numeric grade to a letter grade.
        
        Args:
            percentage (float): The numeric grade percentage
            
        Returns:
            str: The letter grade
        """
        if percentage >= 97:
            return self.GRADE_A_PLUS
        elif percentage >= 93:
            return self.GRADE_A
        elif percentage >= 90:
            return self.GRADE_A_MINUS
        elif percentage >= 87:
            return self.GRADE_B_PLUS
        elif percentage >= 83:
            return self.GRADE_B
        elif percentage >= 80:
            return self.GRADE_B_MINUS
        elif percentage >= 77:
            return self.GRADE_C_PLUS
        elif percentage >= 73:
            return self.GRADE_C
        elif percentage >= 70:
            return self.GRADE_C_MINUS
        elif percentage >= 67:
            return self.GRADE_D_PLUS
        elif percentage >= 63:
            return self.GRADE_D
        elif percentage >= 60:
            return self.GRADE_D_MINUS
        else:
            return self.GRADE_F
    
    def format_course_list(self, courses, include_details=False):
        """
        Format a list of courses into a human-readable string.
        
        Args:
            courses (list): List of course dictionaries
            include_details (bool, optional): Whether to include more details
            
        Returns:
            str: Formatted course list
        """
        try:
            if not courses:
                return "No courses found"
                
            lines = []
            
            for course in courses:
                code = course.get('code', '')
                name = course.get('name', '')
                credits = course.get('credits', '')
                instructor = course.get('instructor', '')
                term_name = course.get('term_name', '')
                
                # Basic course line
                course_line = f"{code}: {name}"
                if credits:
                    course_line += f" ({credits} credits)"
                lines.append(course_line)
                
                # Add term and instructor
                if term_name or instructor:
                    info_line = ""
                    if term_name:
                        info_line += f"Term: {term_name}"
                    if instructor:
                        if info_line:
                            info_line += " | "
                        info_line += f"Instructor: {instructor}"
                    lines.append(f"  {info_line}")
                    
                # Additional details if requested
                if include_details:
                    if course.get('description'):
                        lines.append(f"  Description: {course['description']}")
                        
                    if course.get('location'):
                        lines.append(f"  Location: {course['location']}")
                        
                    if course.get('course_type'):
                        lines.append(f"  Type: {course['course_type'].title()}")
                        
                    if course.get('status'):
                        lines.append(f"  Status: {course['status'].title()}")
                        
                    if course.get('final_grade'):
                        lines.append(f"  Grade: {course['final_grade']}")
                        
                    # Add schedule info if available
                    if course.get('schedule'):
                        schedule = course['schedule']
                        if schedule:
                            lines.append("  Schedule:")
                            for meeting in schedule:
                                day_name = meeting.get('day_name', '')
                                start_time = meeting.get('start_time', '')
                                end_time = meeting.get('end_time', '')
                                location = meeting.get('location', '')
                                
                                schedule_line = f"    {day_name}: {start_time} - {end_time}"
                                if location:
                                    schedule_line += f" @ {location}"
                                lines.append(schedule_line)
                    
                # Add a blank line between courses
                lines.append("")
                
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Error formatting course list: {e}", exc_info=True)
            return "Error formatting courses"