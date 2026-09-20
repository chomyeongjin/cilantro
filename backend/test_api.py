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
        self.assertEqual(self.client.get('/api/trending').headers['cache-control'], 'no-store')
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
        self.assertIn('카로티노이드', interest.json()[0]['what'])
        self.assertEqual(len(interest.json()[0]['how']['chart']), 90)
        self.assertEqual(growth.json()[0]['id'], 'probiotics')
        status = self.client.get('/api/trending/status').json()
        self.assertTrue(status['ready'])
        self.assertFalse(status['stale'])
        self.assertTrue(self.client.get('/health').json()['dataReady'])
        self.assertEqual(status['interestCount'], 5)
        self.assertEqual(status['growthCount'], 5)
        self.assertEqual(self.client.get('/api/trending/status').headers['cache-control'], 'no-store')

    def test_corrupt_database_returns_service_unavailable(self):
        self.path.write_bytes(b'not a sqlite database')
        for endpoint in ['/api/trending', '/api/trending/status', '/health']:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.get(endpoint).status_code, 503)

    def test_lifespan_can_disable_background_collection(self):
        with patch.dict('os.environ', {'TRENDS_AUTO_COLLECT': '0'}), patch('main.Collector.start') as start:
            with TestClient(app) as client:
                self.assertFalse(client.get('/api/trending/status').json()['collection']['enabled'])
            start.assert_not_called()

    def test_lifespan_starts_and_stops_collector(self):
        with patch.dict('os.environ', {'TRENDS_AUTO_COLLECT': '1'}), patch('main.Collector') as factory:
            with TestClient(app):
                factory.return_value.start.assert_called_once()
            factory.return_value.stop.assert_called_once()

    def test_stale_snapshot(self):
        self.seed(age=4)
        self.assertTrue(self.client.get('/api/trending/status').json()['stale'])
        self.assertEqual(self.client.get('/api/trending').status_code, 200)

    def test_invalid_sort_and_unimplemented_api(self):
        self.assertEqual(self.client.get('/api/trending?sort=invalid').status_code, 422)
        self.assertEqual(self.client.get('/api/not-implemented').status_code, 404)

    def test_recommendation_frontend_contract_survives_merge(self):
        response = self.client.post('/api/recommendations', json={
            'age': '50s-60s', 'gender': 'female', 'goals': ['energy-vitality']})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['received'])
        self.assertEqual(response.json()['version'], 2)
        self.assertLessEqual(len(response.json()['items']), 3)
        for item in response.json()['items']:
            self.assertTrue(item['link'].startswith('detail.html?id='))
            self.assertTrue(item['reasons'])

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
