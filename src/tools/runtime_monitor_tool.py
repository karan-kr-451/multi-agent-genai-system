from langchain.tools import BaseTool
import json
import random
import psutil
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional
from collections import deque
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ResourceMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: float

class RuntimeMonitor:
    def __init__(self, sampling_interval: float = 1.0, history_size: int = 3600):
        self._sampling_interval = sampling_interval
        self._history_size = history_size
        self._metrics_history: List[ResourceMetrics] = []
        self._is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start_monitoring(self):
        """Start the monitoring thread."""
        if not self._is_monitoring:
            self._is_monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitoring_loop)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            logger.info("Started system monitoring")

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self._is_monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
        logger.info("Stopped system monitoring")

    def _monitoring_loop(self):
        """Main monitoring loop that collects metrics at regular intervals."""
        while self._is_monitoring:
            try:
                metrics = self._collect_metrics()
                with self._lock:
                    self._metrics_history.append(metrics)
                    if len(self._metrics_history) > self._history_size:
                        self._metrics_history.pop(0)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            time.sleep(self._sampling_interval)

    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        return ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            timestamp=time.time()
        )

    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """Get the most recent metrics."""
        with self._lock:
            if self._metrics_history:
                return self._metrics_history[-1]
            return None

    def get_metrics_history(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[ResourceMetrics]:
        """Get metrics history within the specified time range."""
        with self._lock:
            if not start_time and not end_time:
                return self._metrics_history.copy()

            filtered_metrics = [
                metric for metric in self._metrics_history
                if (not start_time or metric.timestamp >= start_time) and
                (not end_time or metric.timestamp <= end_time)
            ]
            return filtered_metrics

    def get_metrics_summary(
        self,
        time_window: float = 60.0
    ) -> Dict[str, float]:
        """Calculate summary statistics for metrics within the time window."""
        current_time = time.time()
        metrics = self.get_metrics_history(start_time=current_time - time_window)
        
        if not metrics:
            return {}

        return {
            'avg_cpu_percent': sum(m.cpu_percent for m in metrics) / len(metrics),
            'max_cpu_percent': max(m.cpu_percent for m in metrics),
            'avg_memory_percent': sum(m.memory_percent for m in metrics) / len(metrics),
            'max_memory_percent': max(m.memory_percent for m in metrics),
            'avg_disk_usage_percent': sum(m.disk_usage_percent for m in metrics) / len(metrics),
            'total_network_bytes_sent': max(m.network_bytes_sent for m in metrics),
            'total_network_bytes_recv': max(m.network_bytes_recv for m in metrics)
        }

    def check_resource_thresholds(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        disk_threshold: float = 80.0
    ) -> Dict[str, bool]:
        """Check if current resource usage exceeds specified thresholds."""
        current = self.get_current_metrics()
        if not current:
            return {}

        return {
            'cpu_exceeded': current.cpu_percent > cpu_threshold,
            'memory_exceeded': current.memory_percent > memory_threshold,
            'disk_exceeded': current.disk_usage_percent > disk_threshold
        }

    def get_performance_report(self) -> Dict:
        """Generate a comprehensive performance report."""
        current_time = time.time()
        
        return {
            'timestamp': current_time,
            'current_metrics': self.get_current_metrics(),
            'last_minute_summary': self.get_metrics_summary(time_window=60),
            'last_hour_summary': self.get_metrics_summary(time_window=3600),
            'threshold_alerts': self.check_resource_thresholds()
        }

class RuntimeMonitorTool(BaseTool):
    name = "RuntimeMonitorTool"
    description = "Simulates monitoring a deployed application for performance bottlenecks, errors, or security vulnerabilities. Input is a JSON object with 'application_id' and 'duration_minutes'. Returns a simulated report."

    def _run(self, tool_input: str):
        try:
            params = json.loads(tool_input)
            app_id = params.get("application_id", "default_app")
            duration = params.get("duration_minutes", 5)

            report = {
                "application_id": app_id,
                "duration_minutes": duration,
                "status": "monitoring_complete",
                "performance_issues": [],
                "errors_detected": [],
                "security_alerts": []
            }

            # Simulate some random issues
            if random.random() < 0.3: # 30% chance of performance issue
                report["performance_issues"].append({"type": "high_latency", "service": "backend_api", "details": "Average response time increased by 20%"})
            if random.random() < 0.1: # 10% chance of critical error
                report["errors_detected"].append({"type": "critical_error", "service": "database", "details": "Database connection pool exhaustion"})
            if random.random() < 0.05: # 5% chance of security alert
                report["security_alerts"].append({"type": "xss_attempt", "details": "Potential XSS attack detected on login page"})
            
            if not report["performance_issues"] and not report["errors_detected"] and not report["security_alerts"]:
                report["overall_health"] = "healthy"
            else:
                report["overall_health"] = "unhealthy"

            return json.dumps(report)

        except Exception as e:
            return f"An error occurred during runtime monitoring simulation: {e}"

    async def _arun(self, tool_input: str):
        raise NotImplementedError("RuntimeMonitorTool does not support async")

# Instantiate the tool
runtime_monitor_tool = RuntimeMonitorTool()