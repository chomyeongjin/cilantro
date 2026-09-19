"""Register real manufacturer products without Coupang or AI credentials."""
import json
from pathlib import Path

from . import store
from .models import ManualProduct


def read_entries(filename):
    file = Path(filename)
    if file.stat().st_size > 5_000_000:
        raise ValueError('등록 파일은 5MB 이하여야 합니다.')
    entries = json.loads(file.read_text(encoding='utf-8-sig'))
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError('등록/출처 파일은 1~100개 제품의 배열이어야 합니다.')
    return entries


def register_file(filename, update_existing=False, path=None):
    # Validate the WHOLE batch before the atomic write. No network or AI calls.
    products = [ManualProduct.model_validate(row) for row in read_entries(filename)]
    if len({p.id for p in products}) != len(products):
        raise ValueError('등록 파일의 제품 ID가 중복됩니다.')
    listings = [{
        'id': p.id, 'product': p.product, 'productUrl': p.productUrl,
        'buyLink': p.buyLink or p.productUrl, 'source': 'manual-manufacturer',
        'variantNote': p.variantNote, 'discoveredAt': store.now(),
        'raw': p.model_dump(),
    } for p in products]
    counts = store.save_registrations(listings, update_existing=update_existing, path=path)
    return {**counts, 'productIds': [p.id for p in products], 'state': 'registered',
            'nextStep': 'analyze', 'published': False}
