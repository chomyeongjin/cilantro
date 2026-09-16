import io
import unittest
from unittest.mock import patch

from news import attach_news, fetch_news, select_sources


class NewsTests(unittest.TestCase):
    def setUp(self):
        self.item = {'id': 'omega3', 'name': '오메가3', 'keywords': ['오메가3'],
                     'dataThrough': '2026-09-15', 'growth7d': 5}
        self.article = {'title': '<b>오메가3</b> 연구 &amp; 건강 정보',
                        'originallink': 'https://example.com/story',
                        'pubDate': 'Tue, 15 Sep 2026 09:00:00 +0900'}

    def test_dates_relevance_deduplication_and_safe_links(self):
        candidates = [self.article, self.article.copy(),
                      {**self.article, 'title': '다른 주제'},
                      {**self.article, 'originallink': 'javascript:alert(1)'},
                      {**self.article, 'pubDate': 'Wed, 16 Sep 2026 09:00:00 +0900'},
                      {**self.article, 'pubDate': 'Tue, 08 Sep 2026 09:00:00 +0900'},
                      {**self.article, 'pubDate': 'bad date'}, None]
        sources = select_sources(candidates, self.item)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]['title'], '오메가3 연구 & 건강 정보')
        self.assertEqual(sources[0]['publishedAt'], '2026-09-15')

    def test_failure_does_not_discard_trend_or_leak_errors(self):
        def fail(item):
            raise ValueError('secret credential')
        result = attach_news([self.item], fail)[0]
        self.assertEqual(result['growth7d'], 5)
        self.assertEqual(result['whyEvidence']['status'], 'unavailable')
        self.assertNotIn('secret credential', str(result))

    def test_reports_context_without_claiming_causality(self):
        result = attach_news([self.item], lambda item: [self.article])[0]
        self.assertEqual(result['whyEvidence']['causality'], 'unverified')
        self.assertEqual(result['whyEvidence']['status'], 'available')
        self.assertEqual(len(result['whySources']), 1)
        self.assertIn('인과관계는 확인되지', result['why'])

    def test_falling_trend_does_not_claim_rise_and_empty_news_is_distinct(self):
        self.item['growth7d'] = -2
        result = attach_news([self.item], lambda item: [])[0]
        self.assertEqual(result['whyEvidence']['status'], 'no_recent_news')
        self.assertIn('상승하지 않았습니다', result['why'])

    def test_news_authentication_and_separate_keys(self):
        with patch.dict('os.environ', {'NAVER_CLIENT_ID': 'trend-id', 'NAVER_CLIENT_SECRET': 'trend-secret',
                                      'NAVER_NEWS_CLIENT_ID': 'news-id', 'NAVER_NEWS_CLIENT_SECRET': 'news-secret'}, clear=True), \
             patch('news.urlopen', return_value=io.BytesIO(b'{"items": []}')) as network:
            self.assertEqual(fetch_news(self.item), [])
            request = network.call_args.args[0]
            self.assertTrue(request.full_url.startswith('https://naverapihub.apigw.ntruss.com/search/v1/news?'))
            headers = {k.lower(): v for k, v in request.header_items()}
            self.assertEqual(headers['x-ncp-apigw-api-key-id'], 'news-id')
            self.assertEqual(headers['x-ncp-apigw-api-key'], 'news-secret')


if __name__ == '__main__':
    unittest.main()
