import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from src.infrastructure.robots_checker import RobotsChecker
from src.outputs.mailer import EmailSender

class TestP1Concurrency:
    """P1 阶段并发测试"""

    def test_smtp_connection_lock(self):
        """验证 SMTP 连接锁"""
        # 模拟并发发送邮件，验证是否正确处理连接
        config = {"email": {"sender": "test@test.local", "recipients": ["r@test.local"]}}
        sender = EmailSender(config)

        # Mock smtplib
        # 注意：默认配置使用 465 端口，会使用 SMTP_SSL
        with patch("smtplib.SMTP_SSL") as mock_smtp_ssl, patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp_ssl.return_value = mock_server
            mock_smtp.return_value = mock_server

            def send_mail_task():
                sender.send_trending_email([{"name": "repo"}], "daily")

            threads = [threading.Thread(target=send_mail_task) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # 验证调用次数
            assert mock_server.sendmail.call_count == 5

    def test_robots_cache_lru(self):
        """验证 Robots 缓存限制 (LRU)"""
        # 假设 RobotsChecker 实现了 LRU 缓存
        checker = RobotsChecker()

        # 如果尚未实现 LRU，这里可能会失败或需要适配现有实现
        # 模拟大量不同的 host 请求
        for i in range(200):
            url = f"https://site{i}.com/page"
            with patch("urllib.robotparser.RobotFileParser.read", return_value=None):
                 with patch("urllib.robotparser.RobotFileParser.can_fetch", return_value=True):
                    checker.can_fetch(url)

        # 验证 LRU 缓存限制生效 (maxsize=128 on _get_parser)
        # lru_cache 会自动淘汰旧条目，验证缓存信息
        cache_info = checker._get_parser.cache_info()
        assert cache_info.maxsize == 128, f"Expected maxsize=128, got {cache_info.maxsize}"
        # 200 requests should result in 128 cached + 72 evicted
        assert cache_info.currsize <= 128, f"Cache size {cache_info.currsize} exceeds maxsize"
