"""Registration through publication works without Coupang. All data is synthetic/temp."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app
from products import store
from products.connectors import IntegrationError
from products.models import ManualProduct, SourceBundle
from products.pipeline import analyze_bundles, load_manifest
from products.registration import register_file
from collect_products import main
from test_products import fixture


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'products.sqlite3'
        self.file = Path(self.directory.name) / 'manual.json'
        config = patch.dict(os.environ, {'PRODUCTS_DB_PATH': str(self.path)}, clear=True)
        config.start()
        self.addCleanup(config.stop)
        self.listing, self.source, self.analysis = fixture()
        self.entry = {'id': 'manual-test-omega-90-us', 'product': self.listing['product'],
                      'productUrl': self.source.url, 'variantNote': 'test formula, 90 capsules, US',
                      'sources': [{k: v for k, v in self.source.model_dump().items() if k != 'retrievedAt'}]}
        self.write([self.entry])

    def write(self, entries):
        self.file.write_text(json.dumps(entries, ensure_ascii=False), encoding='utf-8-sig')

    def test_registration_needs_no_keys_or_network_and_is_idempotent(self):
        with patch('products.connectors.request_json') as network, patch('products.connectors.read_url') as source_http:
            result = register_file(self.file)
            repeated = register_file(self.file)
        self.assertEqual(result['created'], 1)
        self.assertFalse(result['published'])
        self.assertEqual(repeated['unchanged'], 1)
        network.assert_not_called()
        source_http.assert_not_called()
        listing = store.get_listing(self.entry['id'])
        self.assertEqual(listing['buyLink'], self.source.url)
        self.assertEqual(listing['source'], 'manual-manufacturer')
        self.assertEqual(store.stats()['manualListings'], 1)
        self.assertEqual(store.stats()['publications'], 0)

    def test_same_file_analysis_review_publish_api_without_coupang(self):
        register_file(self.file)
        analyzer = Mock(model='test-only', provider='test')
        analyzer.analyze.return_value = (self.analysis, {'model': 'test-only'})
        result = analyze_bundles(load_manifest(self.file), analyzer=analyzer)
        ident = result['results'][0]['analysisId']
        client = TestClient(app)
        self.addCleanup(client.close)
        self.assertEqual(client.get('/api/categories/omega3').json()['total'], 0)
        store.approve(ident, 'test-reviewer')
        product = client.get('/api/products/' + self.entry['id']).json()
        self.assertEqual(product['registrationSource'], 'manual-manufacturer')
        self.assertEqual(product['comparison']['epaDhaMgPerServing'], 750)
        self.assertEqual(client.get('/api/categories/omega3').json()['total'], 1)
        status = client.get('/api/products/status').json()
        self.assertFalse(status['coupangRequired'])
        self.assertTrue(status['ready'])

    def test_batch_validation_and_duplicate_ids_never_partially_write(self):
        for bad_entries in ([self.entry, {**self.entry, 'id': 'coupang-123'}], [self.entry, self.entry]):
            self.write(bad_entries)
            with self.assertRaises(ValueError):
                register_file(self.file)
            self.assertEqual(store.stats()['listings'], 0)

    def test_changes_need_explicit_update_and_conflict_rolls_back_batch(self):
        register_file(self.file)
        changed = {**self.entry, 'buyLink': 'https://manufacturer.example/shop'}
        self.write([{**self.entry, 'id': 'manual-second'}, changed])
        with self.assertRaises(ValueError):
            register_file(self.file)
        self.assertIsNone(store.get_listing('manual-second'))
        self.assertEqual(store.get_listing(self.entry['id'])['buyLink'], self.source.url)
        result = register_file(self.file, update_existing=True)
        self.assertEqual((result['created'], result['updated']), (1, 1))

    def test_updated_buy_link_invalidates_cache_without_changing_publication(self):
        register_file(self.file)
        analyzer = Mock(model='test-only', provider='test')
        analyzer.analyze.return_value = (self.analysis, {'model': 'test-only'})
        old = analyze_bundles(load_manifest(self.file), analyzer=analyzer)['results'][0]['analysisId']
        store.approve(old, 'test-reviewer')
        self.write([{**self.entry, 'buyLink': 'https://manufacturer.example/shop'}])
        register_file(self.file, update_existing=True)
        new = analyze_bundles(load_manifest(self.file), analyzer=analyzer)['results'][0]['analysisId']
        self.assertNotEqual(new, old)
        self.assertEqual(analyzer.analyze.call_count, 2)
        self.assertEqual(store.published()[0]['analysisId'], old)
        store.approve(new, 'test-reviewer')
        self.assertEqual(store.published()[0]['listing']['buyLink'], 'https://manufacturer.example/shop')

    def test_unregistered_source_changes_rejected_before_ai(self):
        register_file(self.file)
        self.entry['variantNote'] = 'another variant'
        self.write([self.entry])
        analyzer = Mock(model='test-only', provider='test')
        result = analyze_bundles(load_manifest(self.file), analyzer=analyzer)
        self.assertEqual(result['results'][0]['errorCode'], 'REGISTERED_SOURCES_MISMATCH')
        analyzer.analyze.assert_not_called()

    def test_input_url_namespace_and_duplicate_source_validation(self):
        cases = [{**self.entry, 'id': '../file'}, {**self.entry, 'id': 'coupang-123'},
                 {**self.entry, 'buyLink': 'javascript:alert(1)'},
                 {**self.entry, 'productUrl': 'https://secret:password@example.com'},
                 {**self.entry, 'product': '  '},
                 {**self.entry, 'sources': self.entry['sources'] * 2}]
        for entry in cases:
            with self.subTest(entry=entry), self.assertRaises(ValidationError):
                ManualProduct.model_validate(entry)
        SourceBundle.model_validate({'productId': 'coupang-123-4-5',
                                     'expectedProductName': 'test', 'variantNote': 'test', 'sources': self.entry['sources']})

    def test_missing_ai_key_fails_before_source_collection(self):
        register_file(self.file)
        fetcher = Mock()
        with patch('products.ai.load_config'), self.assertRaisesRegex(IntegrationError, 'OPENAI_CREDENTIALS_MISSING'):
            analyze_bundles(load_manifest(self.file), fetcher=fetcher)
        fetcher.assert_not_called()

    def test_cli_register_and_missing_key_exit_codes(self):
        with patch('sys.argv', ['collect_products.py', 'register', '--file', str(self.file)]), patch('builtins.print') as output:
            self.assertEqual(main(), 0)
            self.assertEqual(json.loads(output.call_args.args[0])['created'], 1)
        with patch('sys.argv', ['collect_products.py', 'analyze', '--sources', str(self.file)]), \
                patch('products.ai.load_config'), patch('builtins.print') as output:
            self.assertEqual(main(), 1)
            self.assertEqual(json.loads(output.call_args.args[0])['errorCode'], 'OPENAI_CREDENTIALS_MISSING')

    def test_cli_selects_one_product_before_collection(self):
        self.write([self.entry, {**self.entry, 'id': 'manual-second'}])
        args = ['collect_products.py', 'analyze', '--sources', str(self.file),
                '--product-id', 'manual-second', '--max-products', '1']
        with patch('sys.argv', args), patch('builtins.print'), \
                patch('collect_products.analyze_bundles', return_value={'state': 'success'}) as analyze:
            self.assertEqual(main(), 0)
            bundles, limit = analyze.call_args.args
            self.assertEqual([b.productId for b in bundles], ['manual-second'])
            self.assertEqual(limit, 1)
        args[-3] = 'manual-missing'
        with patch('sys.argv', args), patch('builtins.print') as output, \
                patch('collect_products.analyze_bundles') as analyze:
            self.assertEqual(main(), 1)
            self.assertEqual(json.loads(output.call_args.args[0])['errorCode'], 'PRODUCT_NOT_IN_MANIFEST')
            analyze.assert_not_called()


if __name__ == '__main__':
    unittest.main()
