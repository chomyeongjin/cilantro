import copy
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from service import calculate, collect, load_catalog, ranked, read_snapshot, request_body, save_snapshot


class TrendsTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()
        self.end = date(2026, 9, 15)
        self.body = request_body(self.catalog, self.end)
        self.raw = {**{k: self.body[k] for k in ('startDate','endDate','timeUnit')}, 'results': []}
        for index, item in enumerate(self.catalog):
            self.raw['results'].append({'title':item['name'], 'keywords':item['keywords'], 'data':[
                {'period':(self.end-timedelta(days=89-i)).isoformat(),
                 'ratio':(20+index if i < 83 else 40+index)} for i in range(90)]})

    def calc(self):
        return calculate(self.raw, self.catalog, self.body, '2026-09-16T00:00:00+00:00')

    def test_windows_and_growth(self):
        item = self.calc()[0]
        self.assertEqual(item['interestIndex'],40)
        self.assertEqual(item['baselineIndex'],20)
        self.assertEqual(item['growth7d'],100)
        self.assertEqual(len(item['how']['chart']),90)
        self.assertEqual(item['what'], self.catalog[0]['description'])
        self.assertTrue(item['whatSource']['url'].startswith('https://'))

    def test_collection_saves_news_with_trend_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trends.db'
            items = collect(self.end, path, lambda body: self.raw, news_fetcher=lambda item: [])
            self.assertEqual(read_snapshot(path), items)
            self.assertEqual(items[0]['whyEvidence']['status'], 'no_recent_news')

    def test_zero_baseline(self):
        for p in self.raw['results'][0]['data'][:-7]: p['ratio'] = 0
        item = self.calc()[0]
        self.assertIsNone(item['growth7d'])
        self.assertFalse(item['growthEligible'])

    def test_missing_is_not_zero(self):
        self.raw['results'][0]['data'].pop(-3)
        item = self.calc()[0]
        self.assertIsNone(item['interestIndex'])
        self.assertIsNone(item['how']['chart'][-3]['value'])

    def test_common_date(self):
        self.raw['results'][0]['data'].pop()
        self.assertEqual({i['dataThrough'] for i in self.calc()}, {'2026-09-14'})

    def test_common_date_must_exist_in_every_series(self):
        self.raw['results'][0]['data'].pop()
        self.raw['results'][1]['data'].pop(-2)
        self.assertEqual({i['dataThrough'] for i in self.calc()}, {'2026-09-13'})

    def test_malformed_response_rejected(self):
        for raw in [None, [], {**self.raw, 'results': None}, {**self.raw, 'results': [None] * 5}]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                calculate(raw, self.catalog, self.body, 'test')
        for value in [True, None, '10']:
            self.raw['results'][0]['data'][0]['ratio'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.calc()

    def test_unrankable_collection_preserves_previous(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trends.db'
            original = self.calc()
            save_snapshot(path, self.body, self.raw, original, 'test')
            for result in self.raw['results']:
                result['data'].pop(-3)
            with self.assertRaises(ValueError):
                collect(self.end, path, lambda body: self.raw)
            self.assertEqual(read_snapshot(path), original)

    def test_historical_collection_does_not_replace_current(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trends.db'
            original = self.calc()
            save_snapshot(path, self.body, self.raw, original, 'test')
            old = copy.deepcopy(original)
            for item in old:
                item['dataThrough'] = '2026-09-01'
            save_snapshot(path, self.body, self.raw, old, 'test-later')
            self.assertEqual(read_snapshot(path), original)

    def test_empty_database_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'empty.db'
            path.touch()
            self.assertIsNone(read_snapshot(path))

    def test_partial_response_rejected(self):
        self.raw['results'].pop()
        with self.assertRaises(ValueError): self.calc()

    def test_nonfinite_and_duplicate_rejected(self):
        self.raw['results'][0]['data'][0]['ratio'] = float('nan')
        with self.assertRaises(ValueError): self.calc()
        self.raw['results'][0]['data'][0]['ratio'] = 10
        self.raw['results'][0]['data'].append(self.raw['results'][0]['data'][0])
        with self.assertRaises(ValueError): self.calc()

    def test_rankings_differ_and_no_mutation(self):
        items = self.calc(); before = copy.deepcopy(items)
        self.assertEqual(ranked(items)[0]['id'], self.catalog[-1]['id'])
        self.assertEqual(ranked(items,'growth')[0]['id'], self.catalog[0]['id'])
        self.assertEqual(items,before)

    def test_negative_growth_not_rising(self):
        for result in self.raw['results']:
            for point in result['data'][-7:]: point['ratio'] = 1
        self.assertEqual(ranked(self.calc(),'growth'),[])

    def test_low_baseline_excluded(self):
        for point in self.raw['results'][0]['data'][:-7]: point['ratio'] = .01
        self.assertEqual(self.calc()[0]['quality'],'low_baseline')

    def test_atomic_snapshot_and_failed_fetch_preserves(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'trends.db'
            self.assertIsNone(read_snapshot(path))
            items = self.calc()
            save_snapshot(path,self.body,self.raw,items,'test')
            with self.assertRaises(ValueError):
                collect(self.end,path,lambda body: (_ for _ in ()).throw(ValueError('failure')))
            self.assertEqual(read_snapshot(path),items)

    def test_api_hub_authentication(self):
        import io
        from service import fetch_naver
        credentials = {'NAVER_CLIENT_ID': 'test-id', 'NAVER_CLIENT_SECRET': 'test-secret'}
        with patch('service.load_env'), patch.dict('os.environ', credentials, clear=True), \
                patch('service.urlopen', return_value=io.BytesIO(b'{}')) as network:
            self.assertEqual(fetch_naver(self.body), {})
            request = network.call_args.args[0]
            self.assertEqual(request.full_url,
                             'https://naverapihub.apigw.ntruss.com/search-trend/v1/search')
            headers = {key.lower(): value for key, value in request.header_items()}
            self.assertEqual(headers['x-ncp-apigw-api-key-id'], 'test-id')
            self.assertEqual(headers['x-ncp-apigw-api-key'], 'test-secret')
            self.assertNotIn('x-naver-client-id', headers)

    def test_no_credentials_no_network(self):
        from service import fetch_naver
        with patch('service.load_env'), patch.dict('os.environ',{},clear=True), patch('service.urlopen') as network:
            with self.assertRaises(ValueError): fetch_naver(self.body)
            network.assert_not_called()


if __name__ == '__main__': unittest.main()
