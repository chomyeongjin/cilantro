"""Import 30 reviewed official labels. No scraping, LLM inference, or invented sizes.

Retail presence comes from search-index listings, not live stock verification.
Run from the repository: .venv/Scripts/python.exe backend/seed_c_mg_probiotics.py
"""
import json
from pathlib import Path

from products import store
from products.models import Analysis, Source, validate_evidence
from products.presenter import product_view

PRODUCTS = json.loads(Path(__file__).with_name('data').joinpath('reviewed_c_mg_probiotics.json').read_text(encoding='utf-8'))
NAMES = {'vitamin_c': '비타민 C', 'vitamin_d': '비타민 D', 'zinc': '아연', 'calcium': '칼슘',
         'rose_hips': '로즈힙', 'citrus_bioflavonoids': '시트러스 바이오플라보노이드',
         'acerola': '아세로라', 'rutin': '루틴', 'sodium': '나트륨', 'magnesium': '마그네슘',
         'black_pepper_extract': '흑후추 추출물', 'probiotics': '프로바이오틱스'}
LIMITS = ['제조사 미국 공식 라벨 기준. 쿠팡 판매분의 라벨 버전·배치 일치는 미확인입니다.',
          '쿠팡 판매 이력은 검색 색인으로 확인했으며 현재 재고·가격은 미확인입니다.',
          '알약 크기 미확인. 사진은 제조사 대표 포장으로 판매 수량과 다를 수 있습니다.',
          '기능 문구는 제조사 설명의 요약이며 개인별 섭취 권장이나 질병 치료 효과가 아닙니다.',
          '주요 성분만 표시합니다. 전체 원재료·알레르기·주의사항은 실제 제품 라벨을 확인하세요.']


def build(p):
    def ev(q): return dict(sourceId='official', quote=q)
    def fact(v, q): return dict(value=v, evidence=ev(q))
    brand = next(b for prefix, b in [('now-', '나우푸드'), ('solgar-', '솔가'),
        ('lifeextension-', '라이프익스텐션'), ('doctorsbest-', '닥터스베스트'), ('jarrow-', '자로우')] if p['key'].startswith(prefix))
    serving = p['facts'].splitlines()[0].replace(' | ', ' ')
    source_text = '\n'.join([p['title'], p['url'], p['facts'], p['claim'] or '',
                             *dict.fromkeys(p['warnings']), p['storage'] or '', p['potency'] or ''])
    source = Source(id='official', kind='manufacturer', url=p['url'], title=p['title'],
                    text=source_text, retrievedAt='2026-09-20')
    category = {'c': 'vitamin-c', 'm': 'magnesium', 'p': 'probiotics'}[p['k'][0]]
    label = ('면역·콜라겐' if p['k']=='c7' else '항산화') if category=='vitamin-c' else (
        ('인지 건강' if p['k']=='m7' else '신경계 건강') if category=='magnesium' else
        ('여성 균형' if p['k'] in ('p8', 'p10') else '장내 균형'))
    ingredients = [dict(key=r[0], name=NAMES[r[0]], amount=r[1], unit=r[2] if len(r)>2 else 'mg',
        basis='per_serving', form=None, partOf=None, evidence=ev(p['facts'])) for r in p['ingredients']]
    # Preserve chemical forms / strain identifiers as label text; never infer CFU per strain.
    if category in ('magnesium', 'probiotics'):
        ingredients[0]['form'] = p['facts'].split('--- | --- | ---')[-1].strip() if '--- | --- | ---' in p['facts'] else p['facts']
    warnings = [fact(w,w) for w in dict.fromkeys(p['warnings'])]
    if p['storage']:
        storage_ko = '냉장 보관' if 'REFRIGER' in p['storage'] else ('25°C 이하 보관' if '25°C' in p['storage'] else '서늘하고 건조한 곳 보관')
        warnings.append(fact(storage_ko, p['storage']))
    unknowns = list(LIMITS)
    if category=='probiotics':
        unknowns.append('균주별 CFU는 미확인입니다. 혼합물 총 CFU를 표시합니다.')
        if not p['potency']: unknowns.append('CFU 보장 시점은 미확인입니다.')
        if not p['storage']: unknowns.append('보관 조건은 공식 라벨에서 별도 확인이 필요합니다.')
    analysis = Analysis.model_validate(dict(productIdentity=fact(p['title'],p['title']),
        brand=fact(brand,p['url']), serving=fact(serving,p['facts'].splitlines()[0]),
        unitsPerServing=fact(p['units'],p['facts'].splitlines()[0]) if p['units'] else None,
        dailyServings=None,totalContentMg=None,pillSizeMm=None,formulation=None,
        ingredients=ingredients, claims=[dict(text=label,effectId=None,ingredientKeys=[ingredients[0]['key']],evidence=ev(p['claim']))] if p['claim'] else [],
        warnings=warnings, audience=[fact(label+' 관리',p['claim'])] if p['claim'] else [], ageGroups=[],
        summary='제조사 공식 라벨의 1회 섭취량 기준. '+('분말 제품. ' if not p['units'] else '')+
            ('표시 보관 조건에서 유통기한까지 CFU 보장. ' if p['potency'] else '')+'섭취 권장 아님.',unknowns=unknowns))
    validate_evidence(analysis,[source])
    listing=dict(id='manual-'+p['key'],product=p['name'].removeprefix(brand+' '),productUrl=p['retail'],buyLink=p['retail'],
        source='manual-manufacturer',image=p['image'],imageKind='manufacturer',
        raw=dict(formulaKey=p['key'],officialUrl=p['url'],retailEvidence='search_index_listing_not_live_verified'),discoveredAt=store.now())
    provenance=dict(method='reviewed_official_labels',batch='c-mg-probiotics-2026-09-20',
        formulaKey=p['key'],retailEvidence=dict(url=p['retail'],status='search_index_only',checkedAt='2026-09-20'),
        deduplication='brand + formula + strength + dosage form; package count ignored',
        potencyEvidence=p['potency'],storageEvidence=p['storage'],limitations=LIMITS)
    product_view(dict(listing=listing,analysis=analysis.model_dump(),sources=[source.model_dump()],provenance=provenance))
    return listing,analysis,[source],provenance


def main():
    assert len(PRODUCTS)==len({p['key'] for p in PRODUCTS})==30
    prepared=[build(p) for p in PRODUCTS]  # Validate the whole batch before any writes.
    existing={r.get('raw',{}).get('formulaKey'):r['id'] for r in store.list_listings()}
    for listing,analysis,sources,provenance in prepared:
        if existing.get(provenance['formulaKey'],listing['id'])!=listing['id']:
            print('Skipped duplicate:',listing['id'])
            continue
        note='Official US label reviewed; seller batch and live inventory unverified.'
        store.save_registrations([listing],update_existing=True)
        digest=store.fingerprint(listing,sources,note,'manual-official-label','c-mg-probiotics-v1','manual')
        ident=store.save_draft(listing,analysis,sources,provenance,note,digest)
        store.approve(ident,'official-label-reviewed-retailer-batch-unverified')
        print('Ready:',listing['id'],ident)


if __name__=='__main__':
    main()
