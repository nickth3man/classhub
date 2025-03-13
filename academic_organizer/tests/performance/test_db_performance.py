"""Database performance tests."""
import pytest
import time
from ...src.utils.performance import measure_performance, performance_monitor
from ...src.database.models import Course, Assignment, Material

@pytest.mark.performance
class TestDatabasePerformance:
    """Test database performance metrics."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method."""
        performance_monitor.clear_metrics()
    
    @measure_performance("bulk_insert")
    def test_bulk_insert_performance(self, db_session):
        """Test bulk insert performance."""
        courses = [
            Course(name=f"Course {i}", code=f"CODE{i}")
            for i in range(1000)
        ]
        
        start_time = time.perf_counter()
        db_session.bulk_save_objects(courses)
        db_session.commit()
        duration = time.perf_counter() - start_time
        
        assert duration < 2.0, "Bulk insert took too long"
    
    @measure_performance("complex_query")
    def test_complex_query_performance(self, db_session):
        """Test complex query performance."""
        # Create test data
        course = Course(name="Test Course", code="TEST101")
        db_session.add(course)
        db_session.commit()
        
        assignments = [
            Assignment(
                title=f"Assignment {i}",
                course_id=course.id,
                due_date=f"2025-03-{i+1:02d}"
            )
            for i in range(100)
        ]
        db_session.bulk_save_objects(assignments)
        
        materials = [
            Material(
                name=f"Material {i}",
                course_id=course.id,
                file_path=f"/path/to/material_{i}.pdf"
            )
            for i in range(100)
        ]
        db_session.bulk_save_objects(materials)
        db_session.commit()
        
        # Test query performance
        start_time = time.perf_counter()
        result = (
            db_session.query(Course)
            .join(Assignment)
            .join(Material)
            .filter(Course.id == course.id)
            .all()
        )
        duration = time.perf_counter() - start_time
        
        assert duration < 0.1, "Complex query took too long"
    
    def test_connection_pool_performance(self, db_manager):
        """Test connection pool performance."""
        @measure_performance("concurrent_queries")
        def concurrent_operation():
            with db_manager.session_scope() as session:
                session.query(Course).all()
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(concurrent_operation)
                for _ in range(20)
            ]
            concurrent.futures.wait(futures)
        
        avg_time = performance_monitor.get_average_execution_time("concurrent_queries")
        assert avg_time < 0.1, "Connection pool performance is poor"