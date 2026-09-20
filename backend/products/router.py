import json
import sqlite3
from fastapi import APIRouter, HTTPException, Query

from . import store
from .config import readiness
from .presenter import product_view
from .matching import classify, category_notice
from .age_guidance import age_guidance
from .taxonomy import LABELS, OPTIONS, options

router = APIRouter()


def catalogue():
    try:
        return [classify(product_view(record), record) for record in store.published()]
    except (sqlite3.Error, OSError, ValueError, KeyError):
        raise HTTPException(503, '제품 저장소를 읽을 수 없습니다.') from None


def all_ids(product):
    return set(product['categoryIds'] + product['effectIds'] + product['ageIds'])


@router.get('/api/options')
def get_options():
    counts = {}
    for product in catalogue():
        for key in all_ids(product):
            counts[key] = counts.get(key, 0) + 1
    return options(counts)


@router.get('/api/products/status')
def get_status():
    try:
        counts = store.stats()
    except (sqlite3.Error, OSError, json.JSONDecodeError):
        raise HTTPException(503, '제품 저장소를 읽을 수 없습니다.') from None
    try:
        configuration = readiness()
    except ValueError:
        raise HTTPException(503, 'AI_PROVIDER 설정을 확인하세요. gms 또는 openai를 사용하세요.') from None
    return {**counts, **configuration, 'ready': counts['publications'] > 0,
            'collectionMode': 'explicit_cli_batch', 'publicationRule': 'source_review_required'}


def filtered(items, type_id=None, effect_id=None, age_id=None):
    for group, key in (('type', type_id), ('effect', effect_id), ('age', age_id)):
        if key is not None and key not in dict(OPTIONS[group]):
            raise HTTPException(422, f'알 수 없는 {group} 필터입니다.')
    return [p for p in items if (not type_id or type_id in p['categoryIds'])
            and (not effect_id or effect_id in p['effectIds']) and (not age_id or age_id in p['ageIds'])]


@router.get('/api/categories/{option_id}')
def get_category(option_id: str, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100),
                 type: str | None = None, effect: str | None = None, age: str | None = None):
    if option_id not in LABELS and option_id != 'all':
        raise HTTPException(404, '카테고리를 찾을 수 없습니다.')
    items = filtered(catalogue(), type, effect, age)
    items = [p for p in items if option_id == 'all' or option_id in all_ids(p)]
    return {'id': option_id, 'label': LABELS.get(option_id, '전체 영양제'),
            'selectionNotice': category_notice(option_id),
            'ageGuidance': age_guidance(option_id),
            'products': items[offset:offset + limit], 'total': len(items), 'offset': offset, 'limit': limit,
            'nextOffset': offset + limit if offset + limit < len(items) else None,
            'dataStatus': 'ready' if items else 'no_reviewed_products',
            'message': None if items else '아직 출처 검토를 마친 제품이 없습니다.'}


@router.get('/api/products/compare')
def compare(ids: str = Query(min_length=1, max_length=1000)):
    requested = list(dict.fromkeys(ids.split(',')))
    if not 2 <= len(requested) <= 6:
        raise HTTPException(422, '비교할 서로 다른 제품 ID를 2~6개 입력하세요.')
    items = {p['id']: p for p in catalogue()}
    if any(key not in items for key in requested):
        raise HTTPException(404, '비교할 제품을 찾을 수 없습니다.')
    return {'basis': '각 제품에 표시된 1회 섭취량', 'products': [items[key] for key in requested],
            'efficacyRanking': None, 'note': '1회 섭취 개수가 다를 수 있습니다. 미확인 함량은 0이 아닙니다.'}


@router.get('/api/products/{product_id}')
def get_product(product_id: str):
    product = next((p for p in catalogue() if p['id'] == product_id), None)
    if product is None:
        raise HTTPException(404, '출처 검토를 마친 제품을 찾을 수 없습니다.')
    return product
