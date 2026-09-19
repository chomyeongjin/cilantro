import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = ('COUPANG_PARTNERS_ACCESS_KEY', 'COUPANG_PARTNERS_SECRET_KEY',
        'COUPANG_PARTNERS_SUB_ID', 'COUPANG_SELLER_ACCESS_KEY', 'COUPANG_SELLER_SECRET_KEY',
        'OPENAI_API_KEY', 'OPENAI_MODEL', 'AI_PROVIDER', 'GMS_KEY', 'GMS_MODEL',
        'PRODUCT_SOURCE_HOSTS')

AI_PROVIDERS = {
    'gms': {'endpoint': 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/responses',
            'keyName': 'GMS_KEY', 'modelName': 'GMS_MODEL', 'defaultModel': 'gpt-4.1'},
    'openai': {'endpoint': 'https://api.openai.com/v1/responses',
               'keyName': 'OPENAI_API_KEY', 'modelName': 'OPENAI_MODEL', 'defaultModel': 'gpt-4o-mini'},
}


def load_config():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            key, sep, value = line.strip().partition('=')
            if sep and key in KEYS:
                os.environ.setdefault(key, value.strip().strip('\"').strip("'"))


def database_path():
    return Path(os.environ.get('PRODUCTS_DB_PATH', ROOT / 'data' / 'products.sqlite3'))


def ai_settings():
    # Only return setting names/URLs, never secrets. Explicit selection cannot fall back.
    provider = (os.environ.get('AI_PROVIDER') or ('gms' if os.environ.get('GMS_KEY') else 'openai')).strip().lower()
    if provider not in AI_PROVIDERS:
        raise ValueError('AI_PROVIDER는 gms 또는 openai여야 합니다.')
    settings = AI_PROVIDERS[provider]
    return {**settings, 'provider': provider,
            'model': os.environ.get(settings['modelName'], '').strip() or settings['defaultModel']}


def readiness():
    load_config()
    settings = ai_settings()
    return {'registrationMode': 'manual_or_coupang', 'coupangRequired': False,
            'coupangConfigured': all(os.environ.get(k) for k in KEYS[:2]),
            'aiConfigured': bool(os.environ.get(settings['keyName'], '').strip()),
            'aiProvider': settings['provider'], 'aiModel': settings['model'],
            'sourceHostsConfigured': bool(os.environ.get('PRODUCT_SOURCE_HOSTS'))}
