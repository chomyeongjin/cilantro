import unittest
from threading import Event
from unittest.mock import Mock

from scheduler import Collector


class CollectorTests(unittest.TestCase):
    def test_failure_retries_then_success_clears_error(self):
        fetch = Mock(side_effect=[ValueError('private upstream response'), []])
        collector = Collector(fetch=fetch)
        self.assertEqual(collector.run_once(), 900)
        self.assertNotIn('private', collector.state['lastError'])
        self.assertFalse(collector.state['running'])
        self.assertIsNone(collector.state['lastSuccessAt'])
        self.assertEqual(collector.run_once(), 86400)
        self.assertIsNone(collector.state['lastError'])
        self.assertIsNotNone(collector.state['lastSuccessAt'])

    def test_background_collects_immediately_and_stops_waiting(self):
        fetched = Event()
        collector = Collector(fetch=fetched.set)
        collector.start()
        try:
            self.assertTrue(fetched.wait(2))
        finally:
            collector.stop()
        self.assertFalse(collector.thread.is_alive())


if __name__ == '__main__':
    unittest.main()
