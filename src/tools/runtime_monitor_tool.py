from typing import ClassVar, Dict, List, Optional
import psutil
import time
from dataclasses import dataclass
from langchain_community.tools import BaseTool

@dataclass
class ResourceMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: float

class RuntimeMonitorTool(BaseTool):
    name: ClassVar[str] = "RuntimeMonitorTool"
    description: ClassVar[str] = "Monitor system resource usage and performance metrics. Input should be 'start', 'stop', or 'get_metrics'."

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