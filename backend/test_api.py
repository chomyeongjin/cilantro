"""Exercise the integrated root frontend and API without NAVER credentials."""
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app, PUBLIC_FILES
from service import KST, calculate, load_catalog, request_body, save_snapshot


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'trends.sqlite3'
        mock = patch('main.db_path', return_value=self.path)
        mock.start()
        self.addCleanup(mock.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def seed(self, age=1):
        catalog = load_catalog()
        end = datetime.now(KST).date() - timedelta(days=age)
        body = request_body(catalog, end)
        raw = {k: body[k] for k in ('startDate', 'endDate', 'timeUnit')}
        raw['results'] = [
            {'title': item['name'], 'keywords': item['keywords'], 'data': [
                {'period': (end - timedelta(days=89-i)).isoformat(),
                 'ratio': 20 + index if i < 83 else 40 + index}
                for i in range(90)]}
            for index, item in enumerate(catalog)
        ]
        items = calculate(raw, catalog, body, 'test')
        save_snapshot(self.path, body, raw, items, 'test')

    def test_uncollected_state(self):
        self.assertEqual(self.client.get('/api/trending').status_code, 503)
        self.assertFalse(self.client.get('/api/trending/status').json()['ready'])
        self.assertFalse(self.client.get('/health').json()['dataReady'])

    def test_rankings_and_status(self):
        self.seed()
        interest = self.client.get('/api/trending')
        growth = self.client.get('/api/trending?sort=growth')
        self.assertEqual(interest.status_code, 200)
        self.assertEqual(growth.status_code, 200)
        self.assertEqual(interest.headers['cache-control'], 'no-store')
        self.assertEqual(interest.json()[0]['id'], 'lutein')
        self.assertEqual(growth.json()[0]['id'], 'probiotics')
        status = self.client.get('/api/trending/status').json()
        self.assertTrue(status['ready'])
        self.assertFalse(status['stale'])
        self.assertTrue(self.client.get('/health').json()['dataReady'])

    def test_stale_snapshot(self):
        self.seed(age=4)
        self.assertTrue(self.client.get('/api/trending/status').json()['stale'])
        self.assertEqual(self.client.get('/api/trending').status_code, 200)

    def test_invalid_sort_and_unimplemented_api(self):
        self.assertEqual(self.client.get('/api/trending?sort=invalid').status_code, 422)
        self.assertEqual(self.client.get('/api/options').status_code, 404)

    def test_original_frontend_paths(self):
        for path in ['/', '/images/pill_sample.png', *('/' + f for f in PUBLIC_FILES)]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_private_files_are_not_served(self):
        for path in ['/backend/.env', '/backend/service.py', '/backend/data/trends.sqlite3',
                     '/.git/config', '/requirements.txt', '/README.md',
                     '/images/%2e%2e/backend/.env.example']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)


if __name__ == '__main__':
    unittest.main()
