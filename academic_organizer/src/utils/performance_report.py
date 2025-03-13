"""Performance report generation utilities."""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .performance import performance_monitor, PerformanceMetrics
from academic_organizer.database import db_manager

class PerformanceReport:
    """Generate performance reports."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }
        
        for operation, metrics in performance_monitor._metrics.items():
            report['metrics'][operation] = {
                'count': len(metrics),
                'average_execution_time': sum(m.execution_time for m in metrics) / len(metrics),
                'average_memory_usage': sum(m.memory_usage for m in metrics) / len(metrics),
                'min_execution_time': min(m.execution_time for m in metrics),
                'max_execution_time': max(m.execution_time for m in metrics),
                'latest_execution_time': metrics[-1].execution_time if metrics else None,
                'connection_pool_size': db_manager.get_connection_pool_size(),
                'connections_in_use': db_manager.get_connections_in_use(),
                'connections_idle': db_manager.get_connections_idle()
            }
        
        return report
    
    def save_report(self, report: Dict[str, Any]) -> Path:
        """Save performance report to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.output_dir / f'performance_report_{timestamp}.json'
        
        with report_path.open('w') as f:
            json.dump(report, f, indent=2)
        
        return report_path
    
    def generate_and_save(self) -> Path:
        """Generate and save performance report."""
        report = self.generate_report()
        return self.save_report(report)