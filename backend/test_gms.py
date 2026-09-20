"""GMS transport uses the user-supplied SSAFY contract. No real keys or paid requests."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from fastapi.testclient import TestClient

from main import app
from products.ai import Analyzer
from products.config import ai_settings, load_config, readiness
from products.connectors import IntegrationError, request_json
from products.pipeline import analyze_bundles
from products.store import fingerprint
from test_products import fixture

GMS_ENDPOINT = 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/responses'


class GmsTests(unittest.TestCase):
    def setUp(self):
        self.listing, self.source, self.analysis = fixture()
        self.env = patch.dict(os.environ, {'TRENDS_AUTO_COLLECT': '0', 'AI_PROVIDER': 'gms', 'GMS_KEY': 'test-gms-key',
                                          'OPENAI_API_KEY': 'test-openai-key'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        config = patch('products.ai.load_config')
        config.start()
        self.addCleanup(config.stop)

    def response(self):
        return {'id': 'test-gms-response', 'status': 'completed', 'usage': {'input_tokens': 10},
                'output': [{'type': 'message', 'content': [
                    {'type': 'output_text', 'text': self.analysis.model_dump_json()}]}]}

    def test_gms_request_response_provenance_and_key_isolation(self):
        with patch('products.ai.request_json', return_value=self.response()) as http:
            analysis, provenance = Analyzer().analyze(self.listing, [self.source], 'test variant')
        request, provider = http.call_args.args
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, GMS_ENDPOINT)
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.get_header('Authorization'), 'Bearer test-gms-key')
        self.assertEqual(provider, 'GMS')
        self.assertEqual(payload['model'], 'gpt-4.1')
        self.assertFalse(payload['store'])
        self.assertTrue(payload['text']['format']['strict'])
        self.assertIn('Each ingredient key must be UNIQUE', payload['instructions'])
        self.assertEqual(analysis, self.analysis)
        self.assertEqual(provenance['provider'], 'gms')
        for output in (request.data.decode(), json.dumps(provenance)):
            self.assertNotIn('test-gms-key', output)
            self.assertNotIn('test-openai-key', output)

    def test_auto_selection_and_explicit_override(self):
        os.environ.pop('AI_PROVIDER')
        self.assertEqual(ai_settings()['provider'], 'gms')
        os.environ['AI_PROVIDER'] = 'openai'
        direct = Analyzer()
        self.assertEqual(direct.endpoint, 'https://api.openai.com/v1/responses')
        self.assertEqual(direct.require_credentials(), 'test-openai-key')
        self.assertEqual(direct.model, 'gpt-4o-mini')
        os.environ['AI_PROVIDER'] = 'gms'
        os.environ['GMS_MODEL'] = 'gpt-4.1'
        os.environ['OPENAI_MODEL'] = 'not-the-gms-model'
        self.assertEqual(Analyzer().model, 'gpt-4.1')

    def test_missing_gms_key_does_not_fall_back_or_collect(self):
        os.environ.pop('GMS_KEY')
        with patch('products.ai.request_json') as http, patch('products.pipeline.fetch_source') as source:
            with self.assertRaisesRegex(IntegrationError, '^GMS_CREDENTIALS_MISSING$'):
                analyze_bundles([])
            http.assert_not_called()
            source.assert_not_called()

    def test_http_failure_is_redacted_and_never_retried_on_openai(self):
        with patch('products.connectors.read_url', side_effect=HTTPError('secret-url', 401, 'secret-body', {}, None)) as http:
            with self.assertRaisesRegex(IntegrationError, '^GMS_HTTP_401$'):
                Analyzer().analyze(self.listing, [self.source], 'test')
            self.assertEqual(http.call_count, 1)
            self.assertEqual(http.call_args.kwargs['timeout'], 90)

    def test_refused_incomplete_and_fabricated_citations_rejected(self):
        invalid = self.analysis.model_copy(deep=True)
        invalid.ingredients[0].evidence.quote = 'this does not exist in the label'
        bad_citation = self.response()
        bad_citation['output'][0]['content'][0]['text'] = invalid.model_dump_json()
        cases = [({'status': 'incomplete'}, 'GMS_INCOMPLETE'),
                 ({'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal'}]}]}, 'GMS_REFUSAL'),
                 (bad_citation, 'GMS_ANALYSIS_VALIDATION_FAILED')]
        for response, error in cases:
            with self.subTest(error=error), patch('products.ai.request_json', return_value=response):
                with self.assertRaisesRegex(IntegrationError, '^' + error + '$'):
                    Analyzer().analyze(self.listing, [self.source], 'test')

    def test_provider_is_part_of_cache_identity(self):
        args = (self.listing, [self.source], 'same variant', 'gpt-4.1', 'same prompt')
        self.assertNotEqual(fingerprint(*args, provider='gms'), fingerprint(*args, provider='openai'))

    def test_duplicate_ingredient_keys_are_rejected_without_retry(self):
        invalid = self.analysis.model_copy(deep=True)
        invalid.ingredients.append(invalid.ingredients[0].model_copy(deep=True))
        response = self.response()
        response['output'][0]['content'][0]['text'] = invalid.model_dump_json()
        with patch('products.ai.request_json', return_value=response) as http:
            with self.assertRaisesRegex(IntegrationError, '^GMS_ANALYSIS_VALIDATION_FAILED$'):
                Analyzer().analyze(self.listing, [self.source], 'test variant')
        self.assertEqual(http.call_count, 1)

    def test_readiness_and_env_loader_use_gms_without_exposing_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.env').write_text('AI_PROVIDER=gms\nGMS_KEY=file-key\nGMS_MODEL=gpt-4.1\n', encoding='utf-8-sig')
            with patch('products.config.ROOT', root), patch.dict(os.environ, {}, clear=True):
                load_config()
                self.assertEqual(os.environ['GMS_KEY'], 'file-key')
                status = readiness()
                self.assertTrue(status['aiConfigured'])
                self.assertEqual((status['aiProvider'], status['aiModel']), ('gms', 'gpt-4.1'))
                self.assertNotIn('file-key', json.dumps(status))
            with patch('products.config.ROOT', root), patch.dict(os.environ, {'GMS_KEY': 'process-key'}, clear=True):
                load_config()
                self.assertEqual(os.environ['GMS_KEY'], 'process-key')

    def test_invalid_provider_is_reported_without_network(self):
        os.environ['AI_PROVIDER'] = 'unknown'
        with self.assertRaises(ValueError):
            Analyzer()
        with patch('products.router.store.stats', return_value={'publications': 0}), patch('products.config.load_config'):
            with TestClient(app) as client:
                self.assertEqual(client.get('/api/products/status').status_code, 503)


if __name__ == '__main__':
    unittest.main()
