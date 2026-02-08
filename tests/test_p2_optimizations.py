import pytest
import copy
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.scheduler import TrendingScheduler
from src.infrastructure.health_monitor import HealthMonitor

class TestP2Optimizations:
    """P2 Phase Optimization Verification Tests"""

    def test_config_manager_deepcopy(self):
        """
        Verify that ConfigManager.get_all() returns a deep copy.
        Modifying the returned dictionary should NOT affect the internal state.
        """
        # Mock loading config
        with patch("builtins.open", new_callable=MagicMock), \
             patch("yaml.safe_load", return_value={"nested": {"key": "value"}}), \
             patch("pathlib.Path.exists", return_value=True):

            # Reset singleton for test
            ConfigManager._instance = None
            cm = ConfigManager("dummy_path")

            # Force reload/set state to ensure clean state
            cm._config = {"nested": {"key": "original"}}

            # Get config
            config = cm.get_all()

            # Modify nested dictionary
            config["nested"]["key"] = "modified"

            # Check internal state
            # If shallow copy, this assertion would fail (internal state would be "modified")
            # We expect internal state to remain "original" after the fix (using deepcopy)
            internal_config = cm._config

            # Verify independence
            assert internal_config["nested"]["key"] == "original", "ConfigManager should return a deep copy to prevent internal state mutation"

    def test_scheduler_monthly_logic(self):
        """Verify monthly scheduler runs only on the last day of the month"""
        config = {'scheduler': {'monthly': {'enabled': True, 'time': '22:00'}}}
        scheduler = TrendingScheduler(config)
        scheduler._monthly_callback = MagicMock()

        # Test Case 1: Not last day of month
        # 2023-01-15 (Last day is 31)
        with patch('src.infrastructure.scheduler.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 15, 22, 0, 0)
            # Must also patch calendar inside the module or rely on standard lib
            scheduler._monthly_job()
            scheduler._monthly_callback.assert_not_called()

        # Test Case 2: Last day of month
        # 2023-01-31
        with patch('src.infrastructure.scheduler.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 31, 22, 0, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(2023, 1, 31, 22, 0, 0)

            # Mock executor to run synchronously or just verify call attempt
            with patch.object(scheduler, '_execute_with_retry') as mock_execute:
                scheduler._monthly_job()
                mock_execute.assert_called_once()

    @patch('src.infrastructure.health_monitor.psutil')
    def test_health_monitor_disk_check_windows_compatibility(self, mock_psutil):
        """Verify disk check logic is robust"""
        monitor = HealthMonitor()

        # Mock cpu and memory to normal values
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value.percent = 20.0
        mock_psutil.virtual_memory.return_value.available = 8 * 1024 * 1024 * 1024

        # Mock disk usage
        mock_psutil.disk_usage.return_value.percent = 30.0
        mock_psutil.disk_usage.return_value.free = 100 * 1024 * 1024 * 1024

        # Run check
        result = asyncio.run(monitor.check_system_resources())

        assert result.status == "healthy"
        # Verify it called disk_usage
        # Note: P2 optimization might change the argument from '/' to something more robust
        # but for now we verify it works
        mock_psutil.disk_usage.assert_called()
