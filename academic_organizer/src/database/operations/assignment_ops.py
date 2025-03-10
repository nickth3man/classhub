from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from ..models.assignment import Assignment
from ..base import session_scope
from ...utils.logger import get_logger

logger = get_logger(__name__)

class AssignmentManager:
    """Manages database operations for assignments."""

    @staticmethod
    def create_assignment(assignment_data):
        """Create a new assignment."""
        try:
            with session_scope() as session:
                assignment = Assignment.from_dict(assignment_data, session)
                session.add(assignment)
                session.flush()
                return assignment.to_dict()
        except SQLAlchemyError as e:
            logger.error(f"Database error creating assignment: {e}")
            raise

    @staticmethod
    def get_assignment(assignment_id):
        """Retrieve an assignment by ID."""
        try:
            with session_scope() as session:
                assignment = session.query(Assignment).get(assignment_id)
                return assignment.to_dict() if assignment else None
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving assignment: {e}")
            raise

    @staticmethod
    def update_assignment(assignment_id, assignment_data):
        """Update an existing assignment."""
        try:
            with session_scope() as session:
                assignment = session.query(Assignment).get(assignment_id)
                if not assignment:
                    raise ValueError(f"Assignment not found: {assignment_id}")

                # Update fields
                for key, value in assignment_data.items():
                    if key == 'course':
                        continue  # Handle course separately
                    if key == 'due_date':
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    setattr(assignment, key, value)

                session.flush()
                return assignment.to_dict()
        except SQLAlchemyError as e:
            logger.error(f"Database error updating assignment: {e}")
            raise

    @staticmethod
    def delete_assignment(assignment_id):
        """Delete an assignment."""
        try:
            with session_scope() as session:
                assignment = session.query(Assignment).get(assignment_id)
                if assignment:
                    session.delete(assignment)
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting assignment: {e}")
            raise

    @staticmethod
    def get_all_assignments():
        """Retrieve all assignments."""
        try:
            with session_scope() as session:
                assignments = session.query(Assignment).all()
                return [a.to_dict() for a in assignments]
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving all assignments: {e}")
            raise