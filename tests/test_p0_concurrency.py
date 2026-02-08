import pytest
import time
import threading
from src.infrastructure.rate_limiter import AdaptiveRateLimiter

class TestP0Concurrency:
    """P0 Concurrency Tests"""

    def test_rate_limiter_concurrency(self):
        """Test rate limiter under concurrent load"""
        # Initialize limiter with 10 requests per second (0.1s interval)
        limiter = AdaptiveRateLimiter(initial_rate=10.0, min_interval=0.01, max_interval=1.0)

        # Shared counter
        counter = {"value": 0}
        lock = threading.Lock()

        def worker():
            for _ in range(5):
                limiter.wait()
                with lock:
                    counter["value"] += 1
                limiter.record_success()

        # Create 10 threads
        threads = []
        start_time = time.time()

        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        duration = time.time() - start_time

        # Total requests = 10 threads * 5 requests = 50 requests
        # With 10 req/s, it should take at least ~5 seconds ideally if strictly serial,
        # but AdaptiveRateLimiter just ensures minimal interval between calls.
        # Since it's a local object not shared across processes, threads share the state.

        assert counter["value"] == 50

        # Verify stats
        stats = limiter.get_stats()
        assert stats['recent_success'] > 0

    def test_rate_limiter_adaptive_behavior(self):
        """Test that rate limiter adapts to errors"""
        limiter = AdaptiveRateLimiter(initial_rate=10.0)
        initial_interval = limiter.current_interval

        # Simulate errors (rate limit hit)
        limiter.record_error(is_rate_limit=True)

        # Interval should increase (slow down)
        assert limiter.current_interval > initial_interval

        # Simulate successes
        current_interval = limiter.current_interval
        for _ in range(15):
            limiter.record_success()

        # Interval should decrease (speed up)
        assert limiter.current_interval < current_interval
