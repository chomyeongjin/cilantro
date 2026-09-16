"""Recent reporting is context, not proof that a story caused a search spike."""
import html
import json
import os
import re
import logging
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor

KST = timezone(timedelta(hours=9))
NEWS_ENDPOINT = 'https://naverapihub.apigw.ntruss.com/search/v1/news'


def fetch_news(item):
    news_client = os.environ.get('NAVER_NEWS_CLIENT_ID', '')
    news_secret = os.environ.get('NAVER_NEWS_CLIENT_SECRET', '')
    # Never mix the ID of one application with the secret of another.
    client, secret = ((news_client, news_secret) if news_client or news_secret else
                      (os.environ.get('NAVER_CLIENT_ID', ''), os.environ.get('NAVER_CLIENT_SECRET', '')))
    if not client or not secret:
        raise ValueError('뉴스 검색 인증 정보 없음')
    query = urlencode({'query': item.get('newsQuery', item['name']), 'display': 100, 'sort': 'date'})
    request = Request(NEWS_ENDPOINT + '?' + query, headers={
        'X-NCP-APIGW-API-KEY-ID': client, 'X-NCP-APIGW-API-KEY': secret})
    with urlopen(request, timeout=10) as response:
        raw = json.load(response)
    if not isinstance(raw, dict) or not isinstance(raw.get('items'), list):
        raise ValueError('뉴스 검색 응답 형식 오류')
    return raw['items']


def plain_text(value):
    return ' '.join(html.unescape(re.sub(r'<[^>]*>', '', str(value or ''))).split())


def select_sources(raw_items, item):
    end = date.fromisoformat(item['dataThrough'])
    start = end - timedelta(days=6)
    terms = [''.join(k.lower().split()) for k in [item['name'], *item['keywords']]]
    seen_urls, seen_titles, sources = set(), set(), []
    for entry in raw_items:
        if not isinstance(entry, dict):
            continue
        try:
            published = parsedate_to_datetime(entry.get('pubDate', ''))
            if published.tzinfo is None:
                continue
            day = published.astimezone(KST).date()
            url = entry.get('originallink') or entry.get('link') or ''
            parsed = urlsplit(url)
            if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
                continue
        except (ValueError, TypeError, AttributeError, OverflowError):
            continue
        title = plain_text(entry.get('title'))
        normalized = ''.join(title.lower().split())
        if (not start <= day <= end or not title or not any(term in normalized for term in terms)
                or url in seen_urls or normalized in seen_titles):
            continue
        seen_urls.add(url)
        seen_titles.add(normalized)
        sources.append({'title': title[:200], 'url': url, 'publisher': parsed.hostname,
                        'publishedAt': day.isoformat(), 'kind': 'news'})
    sources.sort(key=lambda source: source['publishedAt'], reverse=True)
    return sources[:3]


def attach_news(items, fetcher=fetch_news):
    def enrich(item):
        error_code = None
        try:
            sources = select_sources(fetcher(item), item)
            state = 'available' if sources else 'no_recent_news'
        except Exception as error:
            # News failures must not discard a valid trend snapshot or leak credentials.
            sources, state = [], 'unavailable'
            error_code = f'HTTP_{error.code}' if isinstance(getattr(error, 'code', None), int) else type(error).__name__
            logging.getLogger(__name__).warning('News lookup failed for %s (%s)', item['id'], error_code)
        growth = item['growth7d']
        if growth is None:
            trend = '최근 관심도의 상승 여부를 판단할 비교 데이터가 부족합니다.'
        elif growth <= 0:
            trend = '최근 7일 평균 관심도는 직전 28일 평균보다 상승하지 않았습니다.'
        else:
            trend = '최근 7일 평균 검색 관심도가 직전 28일 평균보다 높아졌습니다.'
        if sources:
            explanation = '기사 제목과 발행일로 최근 이슈를 살펴보세요. 검색 변화와의 인과관계는 확인되지 않았습니다.'
        elif state == 'unavailable':
            explanation = '현재 관련 뉴스를 불러오지 못해 이유를 확인할 수 없습니다.'
        else:
            explanation = '해당 기간의 관련 보도가 확인되지 않아 이유를 특정하기 어렵습니다.'
        item['why'] = f'{trend} {explanation}'
        item['whySources'] = sources
        item['whyEvidence'] = {'status': state, 'causality': 'unverified',
                               'errorCode': error_code,
                               'windowStart': (date.fromisoformat(item['dataThrough']) - timedelta(days=6)).isoformat(),
                               'windowEnd': item['dataThrough'],
                               'checkedAt': datetime.now(timezone.utc).isoformat()}
        return item
    with ThreadPoolExecutor(max_workers=5) as pool:
        return list(pool.map(enrich, items))
