"""NAVER DataLab collection, complete-window scoring and atomic snapshots."""
import hashlib
import json
import math
import os
import sqlite3
import time
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
KST = timezone(timedelta(hours=9))
SOURCE_URL = 'https://datalab.naver.com/keyword/trendSearch.naver'
SCORE_VERSION = 'means-7-vs-28-v1'


def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            key, sep, value = line.strip().partition('=')
            if sep and key in ('NAVER_CLIENT_ID', 'NAVER_CLIENT_SECRET'):
                os.environ.setdefault(key, value.strip().strip('\"').strip("'"))


def load_catalog():
    catalog = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    if not 1 <= len(catalog) <= 5:
        raise ValueError('MVP는 한 요청으로 최대 5개 그룹만 비교합니다.')
    seen, names, ids = set(), set(), set()
    for item in catalog:
        if item['id'] in ids or item['name'] in names:
            raise ValueError('중복 주제 ID/이름')
        ids.add(item['id']); names.add(item['name'])
        if not 1 <= len(item['keywords']) <= 20:
            raise ValueError('그룹별 검색어는 1~20개여야 합니다.')
        local = set()
        for keyword in item['keywords']:
            if not isinstance(keyword, str) or not keyword.strip():
                raise ValueError('빈 검색어')
            normalized = ''.join(keyword.lower().split())
            if normalized in seen:
                raise ValueError('그룹 간 중복 검색어: ' + keyword)
            local.add(normalized)
        seen.update(local)
    return catalog


def request_body(catalog, end):
    return {'startDate': (end - timedelta(days=89)).isoformat(),
            'endDate': end.isoformat(), 'timeUnit': 'date',
            'keywordGroups': [{'groupName': x['name'], 'keywords': x['keywords']}
                              for x in catalog]}


def fetch_naver(body):
    load_env()
    client = os.environ.get('NAVER_CLIENT_ID', '')
    secret = os.environ.get('NAVER_CLIENT_SECRET', '')
    if not client or not secret or client == 'YOUR_CLIENT_ID' or secret == 'YOUR_CLIENT_SECRET':
        raise ValueError('backend/.env에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정하세요.')
    for attempt in range(3):
        request = Request('https://naverapihub.apigw.ntruss.com/search-trend/v1/search',
                          data=json.dumps(body).encode(), method='POST',
                          headers={'Content-Type': 'application/json',
                                   'X-NCP-APIGW-API-KEY-ID': client,
                                   'X-NCP-APIGW-API-KEY': secret})
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise ValueError(f'NAVER 응답 오류 HTTP {error.code}. 키/API 권한/한도를 확인하세요.') from None
        except (URLError, TimeoutError):
            if attempt == 2:
                raise ValueError('NAVER 연결 실패. 이전 정상 데이터는 유지됩니다.') from None
        time.sleep(2 ** attempt)


def calculate(raw, catalog, body, fetched_at):
    """No missing-day zero fill, no merging independently normalized requests."""
    if any(raw.get(k) != body[k] for k in ('startDate', 'endDate', 'timeUnit')):
        raise ValueError('응답의 조회 조건이 요청과 다릅니다.')
    results = raw.get('results', [])
    if len(results) != len(catalog):
        raise ValueError('일부 주제 응답 누락: 이전 스냅샷을 유지합니다.')
    by_name = {r['title']: r for r in results}
    if set(by_name) != {c['name'] for c in catalog}:
        raise ValueError('응답 주제 불일치')
    series = {}
    start, end = date.fromisoformat(body['startDate']), date.fromisoformat(body['endDate'])
    for item in catalog:
        result = by_name[item['name']]
        if result.get('keywords') != item['keywords']:
            raise ValueError('응답 검색어 불일치')
        points = {}
        for point in result['data']:
            day = date.fromisoformat(point['period'])
            value = float(point['ratio'])
            if day in points or not start <= day <= end or not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError('중복 날짜 또는 유효하지 않은 검색 관심도')
            points[day] = value
        if not points:
            raise ValueError('조회 가능한 시계열이 없는 주제: ' + item['name'])
        series[item['id']] = points
    common_end = min(max(points) for points in series.values())
    # Do not silently publish an arbitrarily old common date as new data.
    if (end - common_end).days > 3:
        raise ValueError('공통 마지막 데이터가 요청 종료일보다 3일 넘게 지연됐습니다.')
    current_days = [common_end - timedelta(days=i) for i in range(7)]
    baseline_days = [common_end - timedelta(days=i) for i in range(7, 35)]
    version = hashlib.sha256(json.dumps(body['keywordGroups'], ensure_ascii=False,
                                       sort_keys=True).encode()).hexdigest()[:12]
    items = []
    for item in catalog:
        points = series[item['id']]
        current = (sum(points[d] for d in current_days) / 7
                   if all(d in points for d in current_days) else None)
        baseline = (sum(points[d] for d in baseline_days) / 28
                    if all(d in points for d in baseline_days) else None)
        growth = ((current / baseline - 1) * 100
                  if current is not None and baseline is not None and baseline > 0 else None)
        quality = ('insufficient_data' if current is None or baseline is None
                   else 'no_baseline' if baseline == 0 else 'ok')
        # A transparent relative threshold, invariant to multiplying the whole request.
        # At least 5% of the largest baseline; never described as a volume threshold.
        items.append({**item, 'interestIndex': current, 'baselineIndex': baseline,
                      'growth7d': growth, 'quality': quality,
                      'how': {'chart': [{'label': d.isoformat(), 'value': points.get(d)}
                                       for d in (start + timedelta(days=i)
                                                 for i in range((common_end-start).days+1))]}})
    largest_baseline = max((i['baselineIndex'] or 0 for i in items), default=0)
    for item in items:
        item['growthEligible'] = (item['quality'] == 'ok' and
                                  item['baselineIndex'] >= largest_baseline * 0.05)
        if item['quality'] == 'ok' and not item['growthEligible']:
            item['quality'] = 'low_baseline'
        item.update(source='NAVER DataLab', sourceUrl=SOURCE_URL,
                    dataThrough=common_end.isoformat(), fetchedAt=fetched_at,
                    keywordSetVersion=version, scoreVersion=SCORE_VERSION,
                    rankingScope=f'설정된 {len(catalog)}개 영양제 주제',
                    what=f"{item['name']} 관련 검색어 묶음의 관심도입니다. 특정 제품의 판매·효능 순위가 아닙니다.")
        growth = item['growth7d']
        item['why'] = (f'최근 7일 평균이 직전 28일 평균 대비 {growth:+.1f}% 변화했습니다.'
                       if growth is not None else '비교 기간의 데이터 또는 기준 관심도가 부족합니다.')
        if item['quality'] == 'low_baseline':
            item['why'] += ' 기준 관심도가 작아 상승률 순위에서 제외했습니다.'
        item['how']['summary'] = (f"{common_end.isoformat()}까지의 상대 검색 관심도(0~100). "
                                   '같은 요청·기간의 최고점 기준이며 실제 검색 횟수가 아닙니다.')
    return items


def db_path():
    return ROOT / 'data' / 'trends.sqlite3'


def save_snapshot(path, body, raw, items, fetched_at):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=30)) as connection, connection:
        connection.execute('CREATE TABLE IF NOT EXISTS snapshots '
                           '(id INTEGER PRIMARY KEY, fetched_at TEXT NOT NULL, '
                           'request_json TEXT NOT NULL, raw_json TEXT NOT NULL, items_json TEXT NOT NULL)')
        connection.execute('INSERT INTO snapshots (fetched_at,request_json,raw_json,items_json) VALUES (?,?,?,?)',
                           (fetched_at, json.dumps(body, ensure_ascii=False),
                            json.dumps(raw, ensure_ascii=False), json.dumps(items, ensure_ascii=False, allow_nan=False)))


def read_snapshot(path):
    path = Path(path)
    if not path.exists():
        return None
    with closing(sqlite3.connect(path)) as connection:
        row = connection.execute('SELECT items_json FROM snapshots ORDER BY id DESC LIMIT 1').fetchone()
    return json.loads(row[0]) if row else None


def ranked(items, sort='interest'):
    if sort not in ('interest', 'growth'):
        raise ValueError('정렬은 interest 또는 growth')
    key = 'interestIndex' if sort == 'interest' else 'growth7d'
    eligible = [i for i in items if i[key] is not None and
                (sort != 'growth' or (i['growthEligible'] and i['growth7d'] > 0))]
    eligible.sort(key=lambda i: (-i[key], i['id']))
    output, rank, previous = [], 0, None
    for position, item in enumerate(eligible, 1):
        if item[key] != previous:
            rank = position
        previous = item[key]
        output.append({**item, 'rank': rank, 'rankingType': sort,
                       'interestIndex': round(item['interestIndex'], 2),
                       'growth7d': round(item['growth7d'], 2) if item['growth7d'] is not None else None})
    return output


def collect(end=None, path=None, fetcher=fetch_naver):
    today = datetime.now(KST).date()
    end = end or today - timedelta(days=1)
    if end >= today:
        raise ValueError('오늘 또는 미래 데이터는 집계하지 않습니다.')
    catalog = load_catalog()
    body = request_body(catalog, end)
    raw = fetcher(body)
    fetched_at = datetime.now(timezone.utc).isoformat()
    items = calculate(raw, catalog, body, fetched_at)
    save_snapshot(path or db_path(), body, raw, items, fetched_at)
    return items
