"""One in-process collector. Use one server worker, or disable for external scheduling."""
import logging
from datetime import datetime, timezone
from threading import Event, Thread

from service import collect

logger = logging.getLogger(__name__)


class Collector:
    def __init__(self, fetch=collect, success_delay=86400, retry_delay=900):
        self.fetch = fetch
        self.success_delay = success_delay
        self.retry_delay = retry_delay
        self.stopped = Event()
        self.thread = None
        self.state = {'enabled': False, 'running': False, 'lastAttemptAt': None,
                      'lastSuccessAt': None, 'lastError': None, 'nextAttemptAt': None}

    def run_once(self):
        now = datetime.now(timezone.utc).isoformat()
        self.state = {**self.state, 'running': True, 'lastAttemptAt': now, 'nextAttemptAt': None}
        delay = self.success_delay
        try:
            self.fetch()
            self.state = {**self.state, 'lastSuccessAt': datetime.now(timezone.utc).isoformat(), 'lastError': None}
        except Exception as error:
            # Never return exception text containing upstream payloads or credentials.
            logger.warning('Trend collection failed (%s); retaining previous snapshot.', type(error).__name__)
            self.state = {**self.state, 'lastError': '수집에 실패했습니다. 인증 설정과 연결 상태를 확인하세요.'}
            delay = self.retry_delay
        finally:
            next_attempt = datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + delay, timezone.utc)
            self.state = {**self.state, 'running': False, 'nextAttemptAt': next_attempt.isoformat()}
        return delay

    def _run(self):
        while not self.stopped.is_set():
            if self.stopped.wait(self.run_once()):
                break

    def start(self):
        self.state = {**self.state, 'enabled': True}
        self.thread = Thread(target=self._run, name='trend-collector', daemon=True)
        self.thread.start()

    def stop(self):
        self.stopped.set()
        if self.thread:
            self.thread.join(timeout=1)
