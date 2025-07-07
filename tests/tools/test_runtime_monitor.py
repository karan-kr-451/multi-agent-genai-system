import unittest
import time
from unittest.mock import patch, MagicMock
from src.tools.runtime_monitor_tool import RuntimeMonitor, ResourceMetrics

class TestRuntimeMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = RuntimeMonitor(sampling_interval=0.1)

    def tearDown(self):
        if self.monitor._is_monitoring:
            self.monitor.stop_monitoring()

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_collect_metrics(self, mock_net_io, mock_disk, mock_memory, mock_cpu):
        # Setup mock returns
        mock_cpu.return_value = 50.0
        mock_memory.return_value = MagicMock(percent=60.0)
        mock_disk.return_value = MagicMock(percent=70.0)
        mock_net_io.return_value = MagicMock(
            bytes_sent=1000,
            bytes_recv=2000
        )

        # Start monitoring
        self.monitor.start_monitoring()
        time.sleep(0.3)  # Allow some metrics to be collected
        self.monitor.stop_monitoring()

        # Verify metrics were collected
        self.assertTrue(len(self.monitor._metrics_history) > 0)
        latest_metric = self.monitor.get_current_metrics()
        
        self.assertEqual(latest_metric.cpu_percent, 50.0)
        self.assertEqual(latest_metric.memory_percent, 60.0)
        self.assertEqual(latest_metric.disk_usage_percent, 70.0)

    def test_get_metrics_history_time_range(self):
        # Add some test metrics
        now = time.time()
        test_metrics = [
            ResourceMetrics(50.0, 60.0, 70.0, 1000, 2000, now - 100),
            ResourceMetrics(55.0, 65.0, 75.0, 1500, 2500, now - 50),
            ResourceMetrics(60.0, 70.0, 80.0, 2000, 3000, now)
        ]
        
        with self.monitor._lock:
            self.monitor._metrics_history = test_metrics

        # Test getting metrics within a time range
        metrics = self.monitor.get_metrics_history(
            start_time=now-75,
            end_time=now-25
        )
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].cpu_percent, 55.0)

    def test_get_metrics_summary(self):
        # Add test metrics
        now = time.time()
        test_metrics = [
            ResourceMetrics(50.0, 60.0, 70.0, 1000, 2000, now - 100),
            ResourceMetrics(60.0, 70.0, 80.0, 1500, 2500, now - 50),
        ]
        
        with self.monitor._lock:
            self.monitor._metrics_history = test_metrics

        summary = self.monitor.get_metrics_summary()
        
        self.assertEqual(summary['avg_cpu_percent'], 55.0)
        self.assertEqual(summary['max_cpu_percent'], 60.0)
        self.assertEqual(summary['avg_memory_percent'], 65.0)
        self.assertEqual(summary['total_network_bytes_sent'], 2500)

    def test_check_resource_thresholds(self):
        now = time.time()
        test_metric = ResourceMetrics(95.0, 85.0, 75.0, 1000, 2000, now)
        
        with self.monitor._lock:
            self.monitor._metrics_history = [test_metric]

        thresholds = self.monitor.check_resource_thresholds(
            cpu_threshold=90.0,
            memory_threshold=90.0,
            disk_threshold=90.0
        )
        
        self.assertTrue(thresholds['cpu_exceeded'])
        self.assertFalse(thresholds['memory_exceeded'])
        self.assertFalse(thresholds['disk_exceeded'])

    def test_get_performance_report(self):
        now = time.time()
        test_metrics = [
            ResourceMetrics(50.0, 60.0, 70.0, 1000, 2000, now - 100),
            ResourceMetrics(60.0, 70.0, 80.0, 1500, 2500, now),
        ]
        
        with self.monitor._lock:
            self.monitor._metrics_history = test_metrics

        report = self.monitor.get_performance_report()
        
        self.assertIn('current_metrics', report)
        self.assertIn('last_minute_summary', report)
        self.assertIn('last_hour_summary', report)
        self.assertIn('threshold_alerts', report)
        self.assertIn('timestamp', report)

if __name__ == '__main__':
    unittest.main()