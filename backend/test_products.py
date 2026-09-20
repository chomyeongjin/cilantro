"""Synthetic labels are used ONLY in temporary test databases, never live product data."""
import hashlib
import hmac
import json
import os
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app
from products import store
from products.ai import Analyzer
from products.connectors import (CoupangClient, IntegrationError, authorization, fetch_source,
                                 normalize_listing, request_json, validate_source_url)
from products.models import Analysis, Source, SourceBundle, SourceSpec, validate_evidence
from products.pipeline import analyze_bundles, discover
from products.presenter import product_view


def evidence(quote):
    return {'sourceId': 'label', 'quote': quote}


def text_fact(value):
    return {'value': value, 'evidence': evidence(value)}


def num_fact(value, quote):
    return {'value': value, 'evidence': evidence(quote)}


def fixture(product_id='123'):
    # Illustrative strings only. No claim about an actual branded supplement.
    raw = {'productId': product_id, 'productName': 'TEST ONLY Omega Complex',
           'productUrl': f'https://www.coupang.com/vp/products/{product_id}', 'productPrice': 10000}
    listing = normalize_listing(raw)
    label = ('TEST ONLY Omega Complex\nTest Brand\nServing: 2 softgels\n'
             'Fish oil 1 g per serving\nEPA 500 mg per serving\nDHA 250 mg per serving\n'
             'Total formula mass 1500 mg per serving\nSoftgel length 20 mm\n'
             'Eye label claim\nAdults only\nTest warning')
    source = Source(id='label', kind='label', url='https://manufacturer.example/label',
                    title='Synthetic test label', text=label, retrievedAt='2026-09-17T00:00:00Z')
    ingredients = [
        {'key': 'fish_oil', 'name': 'Fish oil', 'amount': 1, 'unit': 'g', 'basis': 'per_serving',
         'form': None, 'partOf': None, 'evidence': evidence('Fish oil 1 g per serving')},
        {'key': 'epa', 'name': 'EPA', 'amount': 500, 'unit': 'mg', 'basis': 'per_serving',
         'form': None, 'partOf': 'fish_oil', 'evidence': evidence('EPA 500 mg per serving')},
        {'key': 'dha', 'name': 'DHA', 'amount': 250, 'unit': 'mg', 'basis': 'per_serving',
         'form': None, 'partOf': 'fish_oil', 'evidence': evidence('DHA 250 mg per serving')},
    ]
    analysis = Analysis.model_validate({
        'productIdentity': text_fact('TEST ONLY Omega Complex'), 'brand': text_fact('Test Brand'),
        'serving': text_fact('Serving: 2 softgels'), 'unitsPerServing': num_fact(2, 'Serving: 2 softgels'),
        'dailyServings': None, 'totalContentMg': None, 'pillSizeMm': None, 'formulation': None,
        'ingredients': ingredients,
        'claims': [{'text': '테스트 표시 문구', 'effectId': 'eye-health', 'ingredientKeys': ['dha'],
                    'evidence': evidence('Eye label claim')}],
        'warnings': [text_fact('Test warning')], 'audience': [text_fact('Adults only')], 'ageGroups': [],
        'summary': '테스트용 분석', 'unknowns': ['전체 제형 중량 미확인']})
    return listing, source, analysis


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'products.sqlite3'
        env = patch.dict(os.environ, {'PRODUCTS_DB_PATH': str(self.path), 'TRENDS_AUTO_COLLECT': '0'})
        env.start()
        self.addCleanup(env.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.listing, self.source, self.analysis = fixture()

    def seed(self, approved=True, digest='v1', product_id='123'):
        listing, source, analysis = fixture(product_id)
        store.save_listings([listing])
        ident = store.save_draft(listing, analysis, [source], {'model': 'fake', 'promptVersion': 'test'}, 'test', digest)
        if approved:
            store.approve(ident, 'test-reviewer')
        return ident

    def view(self, analysis=None):
        return product_view({'listing': self.listing, 'analysis': (analysis or self.analysis).model_dump(),
                             'sources': [self.source.model_dump()], 'provenance': {'model': 'fake'}})

    def test_empty_state_options_and_no_fake_products(self):
        options = self.client.get('/api/options').json()
        self.assertEqual(set(options), {'type', 'effect', 'age'})
        self.assertEqual(options['type'][0]['id'], 'omega3')
        self.assertEqual(options['type'][0]['productCount'], 0)
        frontend_ids = {
            'type': {'omega3', 'vitamin-b', 'vitamin-c', 'magnesium', 'probiotics', 'lutein'},
            'effect': {'immunity', 'energy-vitality', 'eye-health', 'digestive-health',
                       'sleep-stress', 'skin-health'},
            'age': {'kids', 'teens', '20s', '30s-40s', '50s-60s', '70-plus'},
        }
        for group, ids in frontend_ids.items():
            self.assertTrue(ids <= {item['id'] for item in options[group]})
            for option_id in ids:
                with self.subTest(option_id=option_id):
                    self.assertEqual(self.client.get(f'/api/categories/{option_id}').status_code, 200)
        response = self.client.get('/api/categories/omega3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['products'], [])
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertFalse(self.client.get('/api/products/status').json()['ready'])
        self.assertEqual(self.client.get('/api/products/coupang-123').status_code, 404)

    def test_draft_is_hidden_then_approval_satisfies_frontend(self):
        ident = self.seed(False)
        self.assertEqual(self.client.get('/api/categories/omega3').json()['total'], 0)
        store.approve(ident, 'reviewer')
        category = self.client.get('/api/categories/omega3').json()
        self.assertEqual(category['total'], 1)
        product = self.client.get('/api/products/coupang-123').json()
        expected = {'brand', 'product', 'image', 'mainEffects', 'pillSizeMm', 'categoryId',
                    'categoryLabel', 'for', 'buyLink', 'ingredients'}
        self.assertTrue(expected <= product.keys())
        self.assertEqual(product['comparison']['epaDhaMgPerServing'], 750)
        self.assertEqual(product['comparison']['fishOilMgPerServing'], 1000)
        self.assertEqual(product['ingredients'], [])
        self.assertIsNone(product['pillSizeMm'])
        self.assertNotIn('text', product['sources'][0])
        self.assertNotIn('reviewer', product)
        self.assertEqual(self.client.get('/api/categories/eye-health').json()['total'], 1)
        # Adult-labelled comparison candidates are distinct from age efficacy.
        adult_category = self.client.get('/api/categories/20s').json()
        self.assertEqual(adult_category['total'], 1)
        self.assertIn('효능 순위가 아니라', adult_category['selectionNotice'])
        self.assertEqual(product['ageMatches'][0]['basis'], 'adult_label_not_age_efficacy')
        self.assertEqual(self.client.get('/api/categories/kids').json()['total'], 0)
        self.assertEqual(self.client.get('/api/categories/50s-60s').json()['total'], 0)
        self.assertEqual(self.client.get('/api/categories/omega3?effect=immunity').json()['total'], 0)

    def test_filters_pagination_compare_and_invalid_routes(self):
        self.seed()
        self.seed(product_id='456')
        page = self.client.get('/api/categories/all?limit=1').json()
        self.assertEqual((page['total'], len(page['products']), page['nextOffset']), (2, 1, 1))
        self.assertEqual(self.client.get('/api/products/compare?ids=coupang-123,coupang-456').status_code, 200)
        for url, status in [('/api/products/compare?ids=coupang-123', 422),
                            ('/api/products/compare?ids=coupang-123,coupang-999', 404),
                            ('/api/categories/omega3?age=unknown', 422),
                            ('/api/categories/unknown', 404), ('/api/categories/all?limit=0', 422)]:
            self.assertEqual(self.client.get(url).status_code, status)

    def test_failed_refresh_and_new_draft_preserve_approved_version(self):
        old = self.seed()
        client = Mock()
        client.search.side_effect = IntegrationError('COUPANG_HTTP_403')
        with self.assertRaises(IntegrationError):
            discover('test', client=client)
        new = self.seed(False, 'v2')
        self.assertNotEqual(old, new)
        self.assertEqual(self.client.get('/api/products/coupang-123').json()['analysisId'], old)
        self.assertEqual(store.stats()['lastRun']['state'], 'failed')

    def test_revision_is_a_new_hidden_version(self):
        old = self.seed()
        revised = self.analysis.model_copy(deep=True)
        revised.summary = '검토자가 수정한 테스트 설명'
        new = store.revise(old, revised, 'editor')
        self.assertNotEqual(old, new)
        self.assertEqual(self.client.get('/api/products/coupang-123').json()['analysisId'], old)
        store.approve(new, 'reviewer')
        self.assertEqual(self.client.get('/api/products/coupang-123').json()['summary'], revised.summary)

    def test_evidence_and_product_identity_fail_closed(self):
        changed = self.analysis.model_copy(deep=True)
        changed.ingredients[0].evidence.quote = 'invented source sentence'
        with self.assertRaises(ValueError):
            validate_evidence(changed, [self.source])
        changed = self.analysis.model_copy(deep=True)
        changed.brand.evidence.sourceId = 'missing'
        with self.assertRaises(ValueError):
            validate_evidence(changed, [self.source])

    def test_no_fabricated_percentage_and_no_double_counting(self):
        view = self.view()
        self.assertEqual(view['ingredients'], [])
        self.analysis.totalContentMg = type(self.analysis.unitsPerServing).model_validate(num_fact(1500, 'Total formula mass 1500 mg per serving'))
        view = self.view()
        self.assertEqual(len(view['ingredients']), 1)  # EPA/DHA already inside fish oil.
        self.assertAlmostEqual(view['ingredients'][0]['pct'], 1000 / 1500 * 100)
        self.assertEqual(view['ingredients'][0]['amount'], '1g / 1회')
        self.analysis.ingredients[1].amount = 2000
        with self.assertRaises(ValueError):
            self.view()

    def test_units_serving_and_missing_values(self):
        self.analysis.ingredients[1].basis = 'per_unit'
        self.analysis.ingredients[1].amount = 250
        self.assertEqual(self.view()['comparison']['epaMgPerServing'], 500)
        self.analysis.unitsPerServing = None
        self.assertIsNone(self.view()['comparison']['epaMgPerServing'])
        self.analysis.ingredients[1].basis = 'per_daily'
        self.analysis.dailyServings = None
        self.assertIsNone(self.view()['comparison']['epaMgPerServing'])
        self.analysis.ingredients[1].unit = 'IU'
        self.analysis.ingredients[1].basis = 'per_serving'
        self.assertIsNone(self.view()['comparison']['epaMgPerServing'])
        self.analysis.ingredients[1].unit = 'mcg'
        self.analysis.ingredients[1].amount = 500000
        self.assertEqual(self.view()['comparison']['epaMgPerServing'], 500)

    def test_invalid_numbers_relations_and_serving(self):
        raw = self.analysis.model_dump()
        for bad in (float('nan'), float('inf'), -1):
            raw['ingredients'][0]['amount'] = bad
            with self.assertRaises(ValidationError):
                Analysis.model_validate(raw)
        raw = self.analysis.model_dump()
        raw['ingredients'][0]['partOf'] = 'epa'
        with self.assertRaises(ValidationError):
            Analysis.model_validate(raw)
        raw = self.analysis.model_dump()
        raw['serving'] = None
        with self.assertRaises(ValidationError):
            Analysis.model_validate(raw)

    def test_cache_prevents_repeat_ai_and_variant_mismatch(self):
        store.save_listings([self.listing])
        bundle = SourceBundle(productId=self.listing['id'], expectedProductName=self.listing['product'],
                              variantNote='exact test variant', sources=[SourceSpec(
                                  id='label', kind='label', url=self.source.url, title=self.source.title, text=self.source.text)])
        analyzer = Mock(model='fake', provider='test')
        analyzer.analyze.return_value = (self.analysis, {'model': 'fake'})
        first = analyze_bundles([bundle], analyzer=analyzer)
        second = analyze_bundles([bundle], analyzer=analyzer)
        self.assertEqual(first['results'][0]['state'], 'needs_review')
        self.assertEqual(second['results'][0]['state'], 'cached')
        analyzer.analyze.assert_called_once()
        bundle.expectedProductName = 'wrong variant'
        result = analyze_bundles([bundle], analyzer=analyzer)
        self.assertEqual(result['results'][0]['errorCode'], 'PRODUCT_VARIANT_NAME_MISMATCH')
        self.assertEqual(store.stats()['publications'], 0)

    def test_corrupt_store_and_private_files(self):
        self.path.write_bytes(b'not sqlite')
        for url in ('/api/options', '/api/products/status', '/api/categories/omega3'):
            self.assertEqual(self.client.get(url).status_code, 503)
        for url in ('/backend/products/config.py', '/backend/data/products.sqlite3', '/backend/.env'):
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertNotEqual(self.client.post('/api/products/approve', json={'id': 1}).status_code, 200)


class ConnectorTests(unittest.TestCase):
    def test_hmac_signature_signs_exact_encoded_query_in_utc(self):
        date, path, query = '260917T010000Z', '/test', 'keyword=%EC%98%A4%EB%A9%94%EA%B0%803&limit=10'
        expected = hmac.new(b'secret', (date + 'GET' + path + query).encode(), hashlib.sha256).hexdigest()
        self.assertEqual(authorization('get', path, query, 'access', 'secret', date),
                         f'CEA algorithm=HmacSHA256, access-key=access, signed-date={date}, signature={expected}')

    def test_search_contract_and_variants(self):
        raw = {'productId': 123, 'productName': 'test',
               'productUrl': 'https://www.coupang.com/vp/products/123?itemId=4&vendorItemId=5'}
        with patch('products.connectors.load_config'), patch.dict(os.environ, {
            'COUPANG_PARTNERS_ACCESS_KEY': 'access', 'COUPANG_PARTNERS_SECRET_KEY': 'secret'}, clear=True), \
                patch('products.connectors.request_json', return_value={'rCode': '0', 'data': {'productData': [raw]}}) as http:
            items = CoupangClient().search('오메가 3')
            self.assertEqual(items[0]['id'], 'coupang-123-4-5')
            request = http.call_args.args[0]
            self.assertIn('affiliate_open_api', request.full_url)
            self.assertIn('keyword=%EC%98%A4%EB%A9%94%EA%B0%80+3', request.full_url)
            self.assertIn('signed-date=', request.get_header('Authorization'))
        raw['productUrl'] = 'javascript:alert(1)'
        with self.assertRaises(IntegrationError):
            normalize_listing(raw)

    def test_missing_keys_do_not_make_network_calls(self):
        with patch('products.connectors.load_config'), patch.dict(os.environ, {}, clear=True), \
                patch('products.connectors.request_json') as http:
            with self.assertRaisesRegex(IntegrationError, 'CREDENTIALS_MISSING'):
                CoupangClient().search('오메가3')
            http.assert_not_called()

    def test_source_host_private_address_robots_and_redirect_blocks(self):
        spec = SourceSpec(id='label', kind='manufacturer', url='https://manufacturer.example/label', title='test', text=None)
        with patch('products.connectors.load_config'), patch.dict(os.environ, {'PRODUCT_SOURCE_HOSTS': 'manufacturer.example'}), \
                patch('products.connectors.socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))]):
            with self.assertRaisesRegex(IntegrationError, 'PRIVATE_ADDRESS'):
                fetch_source(spec)
        with patch('products.connectors.load_config'), patch('products.connectors.validate_source_url'), \
                patch('products.connectors.read_url', return_value=(b'User-agent: *\nDisallow: /', 'text/plain', 'utf-8')) as http:
            with self.assertRaisesRegex(IntegrationError, 'ROBOTS_DISALLOWED'):
                fetch_source(spec)
            self.assertEqual(http.call_count, 1)
        with patch('products.connectors.load_config'), patch('products.connectors.validate_source_url'), \
                patch('products.connectors.read_url', side_effect=HTTPError(spec.url, 302, 'redirect', {}, None)):
            with self.assertRaisesRegex(IntegrationError, 'HTTP_302'):
                fetch_source(spec)
        with patch.dict(os.environ, {'PRODUCT_SOURCE_HOSTS': ''}):
            with self.assertRaisesRegex(IntegrationError, 'NOT_ALLOWED'):
                validate_source_url(spec.url)

    def test_ai_schema_request_and_refusal(self):
        listing, source, analysis = fixture()
        response = {'status': 'completed', 'id': 'test-response', 'output': [
            {'type': 'message', 'content': [{'type': 'output_text', 'text': analysis.model_dump_json()}]}]}
        with patch('products.ai.load_config'), patch.dict(os.environ, {'OPENAI_API_KEY': 'private-key'}, clear=True), \
                patch('products.ai.request_json', return_value=response) as http:
            actual, _ = Analyzer().analyze(listing, [source], 'test variant')
            self.assertEqual(actual.ingredients[1].key, 'epa')
            payload = json.loads(http.call_args.args[0].data)
            self.assertFalse(payload['store'])
            self.assertTrue(payload['text']['format']['strict'])
            self.assertNotIn('private-key', payload['input'])
            self.assertNotIn('tools', payload)
            http.return_value = {'status': 'incomplete'}
            with self.assertRaisesRegex(IntegrationError, 'INCOMPLETE'):
                Analyzer().analyze(listing, [source], 'test')
            http.return_value = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal'}]}]}
            with self.assertRaisesRegex(IntegrationError, 'REFUSAL'):
                Analyzer().analyze(listing, [source], 'test')

    def test_transport_errors_are_redacted(self):
        with patch('products.connectors.read_url', side_effect=URLError('private-key inside error')):
            with self.assertRaisesRegex(IntegrationError, '^OPENAI_CONNECTION_FAILED$'):
                request_json(Mock(), 'OPENAI')
        with patch('products.connectors.read_url', side_effect=HTTPError('private', 401, 'secret', {}, None)):
            with self.assertRaisesRegex(IntegrationError, '^COUPANG_HTTP_401$'):
                request_json(Mock(), 'COUPANG')


if __name__ == '__main__':
    unittest.main()
