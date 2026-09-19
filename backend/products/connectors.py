"""Official API adapters and explicit, allowlisted source collection (no browser scraping)."""
import hashlib
import hmac
import ipaddress
import json
import os
import socket
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from .config import load_config
from .models import Source, public_url

USER_AGENT = 'CilantroSourceCollector/1.0'
COUPANG_HOST = 'https://api-gateway.coupang.com'
SEARCH_PATH = '/v2/providers/affiliate_open_api/apis/openapi/products/search'
CATEGORY_PATH = '/v2/providers/seller_api/apis/api/v1/marketplace/meta/display-categories/'


class IntegrationError(ValueError):
    """Only redacted codes may leave the adapter, never bodies/credentials."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_url(request, limit=2_000_000, timeout=30):
    with build_opener(NoRedirect).open(request, timeout=timeout) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise IntegrationError('RESPONSE_TOO_LARGE')
        return data, response.headers.get_content_type(), response.headers.get_content_charset() or 'utf-8'


def request_json(request, provider):
    try:
        raw, _, _ = read_url(request, timeout=90 if provider in ('OPENAI', 'GMS') else 30)
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise IntegrationError(f'{provider}_INVALID_RESPONSE')
        return result
    except HTTPError as error:
        raise IntegrationError(f'{provider}_HTTP_{error.code}') from None
    except (URLError, TimeoutError, OSError):
        raise IntegrationError(f'{provider}_CONNECTION_FAILED') from None
    except (ValueError, UnicodeError) as error:
        if isinstance(error, IntegrationError):
            raise
        raise IntegrationError(f'{provider}_INVALID_JSON') from None


def authorization(method, path, query, access_key, secret_key, timestamp=None):
    timestamp = timestamp or datetime.now(timezone.utc).strftime('%y%m%dT%H%M%SZ')
    message = timestamp + method.upper() + path + query
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return (f'CEA algorithm=HmacSHA256, access-key={access_key}, '
            f'signed-date={timestamp}, signature={signature}')


class CoupangClient:
    def __init__(self):
        load_config()

    def _get(self, path, params, role):
        access = os.environ.get(f'COUPANG_{role}_ACCESS_KEY', '')
        secret = os.environ.get(f'COUPANG_{role}_SECRET_KEY', '')
        if not access or not secret:
            raise IntegrationError(f'COUPANG_{role}_CREDENTIALS_MISSING')
        query = urlencode(params)
        request = Request(COUPANG_HOST + path + ('?' + query if query else ''), headers={
            'Authorization': authorization('GET', path, query, access, secret),
            'Accept': 'application/json', 'X-MARKET': 'KR'})
        return request_json(request, 'COUPANG')

    def search(self, keyword, limit=10):
        # Bounded discovery, NOT exhaustive crawling or a market ranking.
        if not keyword.strip() or len(keyword) > 100 or not 1 <= limit <= 10:
            raise ValueError('검색어는 1~100자, limit은 1~10이어야 합니다.')
        params = {'keyword': keyword, 'limit': limit}
        sub_id = os.environ.get('COUPANG_PARTNERS_SUB_ID')
        if sub_id:
            params['subId'] = sub_id
        result = self._get(SEARCH_PATH, params, 'PARTNERS')
        if str(result.get('rCode')) != '0':
            raise IntegrationError('COUPANG_SEARCH_REJECTED')
        data = result.get('data')
        if not isinstance(data, dict) or not isinstance(data.get('productData'), list):
            raise IntegrationError('COUPANG_SEARCH_INVALID_RESPONSE')
        return [normalize_listing(row) for row in data['productData'][:limit]]

    def category(self, code):
        if not str(code).isdigit():
            raise ValueError('카테고리 코드는 숫자여야 합니다.')
        result = self._get(CATEGORY_PATH + str(code), {}, 'SELLER')
        if result.get('code') != 'SUCCESS':
            raise IntegrationError('COUPANG_CATEGORY_REJECTED')
        return result.get('data')


def normalize_listing(raw):
    if not isinstance(raw, dict):
        raise IntegrationError('COUPANG_LISTING_INVALID')
    product_id = str(raw.get('productId', ''))
    name, url = raw.get('productName'), raw.get('productUrl')
    if not product_id.isdigit() or not isinstance(name, str) or not name.strip() or not isinstance(url, str):
        raise IntegrationError('COUPANG_LISTING_INVALID')
    try:
        public_url(url)
        hostname = urlsplit(url).hostname
        if hostname != 'coupang.com' and not hostname.endswith('.coupang.com'):
            raise ValueError('unexpected host')
    except ValueError:
        raise IntegrationError('COUPANG_LISTING_URL_INVALID') from None
    query = parse_qs(urlsplit(url).query)
    variant = []
    for field in ('itemId', 'vendorItemId'):
        value = str(raw.get(field) or query.get(field, [''])[0])
        if value:
            if not value.isdigit():
                raise IntegrationError('COUPANG_VARIANT_INVALID')
        variant.append(value or '0')
    suffix = variant if variant != ['0', '0'] else []
    return {'id': '-'.join(['coupang', product_id, *suffix]), 'product': name.strip(),
            'buyLink': url, 'source': 'coupang-partners',
            'discoveredAt': datetime.now(timezone.utc).isoformat(),
            'raw': raw}


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript') and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def validate_source_url(url):
    public_url(url)
    host = urlsplit(url).hostname.lower()
    allowed = {h.strip().lower() for h in os.environ.get('PRODUCT_SOURCE_HOSTS', '').split(',') if h.strip()}
    if host not in allowed:
        raise IntegrationError('SOURCE_HOST_NOT_ALLOWED')
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            raise IntegrationError('SOURCE_PRIVATE_ADDRESS_BLOCKED')
    except socket.gaierror:
        raise IntegrationError('SOURCE_DNS_FAILED') from None


def fetch_source(spec):
    """Only local CLI/operator mappings can invoke this, never a public URL endpoint."""
    load_config()
    if spec.text is not None:
        text = spec.text
    else:
        validate_source_url(spec.url)
        origin = urlsplit(spec.url)
        robots_url = f'https://{origin.hostname}/robots.txt'
        try:
            robot_bytes, _, encoding = read_url(Request(robots_url, headers={'User-Agent': USER_AGENT}), limit=200_000)
            robots = RobotFileParser()
            robots.parse(robot_bytes.decode(encoding).splitlines())
            if not robots.can_fetch(USER_AGENT, spec.url):
                raise IntegrationError('SOURCE_ROBOTS_DISALLOWED')
        except HTTPError as error:
            if error.code != 404:
                raise IntegrationError(f'SOURCE_ROBOTS_HTTP_{error.code}') from None
        except (URLError, TimeoutError, OSError, UnicodeError, LookupError):
            raise IntegrationError('SOURCE_ROBOTS_UNAVAILABLE') from None
        try:
            data, content_type, encoding = read_url(Request(spec.url, headers={'User-Agent': USER_AGENT}))
            if content_type not in ('text/html', 'text/plain', 'application/xhtml+xml'):
                raise IntegrationError('SOURCE_TEXT_REQUIRED')
            text = data.decode(encoding)
            if content_type != 'text/plain':
                parser = VisibleText()
                parser.feed(text)
                text = '\n'.join(parser.parts)
        except HTTPError as error:
            raise IntegrationError(f'SOURCE_HTTP_{error.code}') from None
        except (URLError, TimeoutError, OSError, UnicodeError, LookupError):
            raise IntegrationError('SOURCE_CONNECTION_FAILED') from None
    if not text.strip() or len(text) > 60000:
        raise IntegrationError('SOURCE_TEXT_EMPTY_OR_TOO_LARGE')
    return Source(id=spec.id, kind=spec.kind, url=spec.url, title=spec.title,
                  text=text, retrievedAt=datetime.now(timezone.utc).isoformat())
