"""Import the reviewed catalogue expansion; no inference, no count padding.

Run without --publish to validate/deduplicate. --publish explicitly publishes.
Existing entries are never overwritten. Supports a separate --db for tests.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from products import store
from products.models import Analysis, Source, validate_evidence
from products.presenter import product_view

DATA = Path(__file__).with_name('data') / 'catalog_expansion_review.json'
NAMES = dict(vitamin_c='비타민 C', calcium='칼슘', citrus_bioflavonoids='시트러스 바이오플라보노이드',
    rutin='루틴', alpha_lipoic_acid='알파리포산', rose_hips='로즈힙', sodium='나트륨',
    ascorbyl_palmitate='아스코빌 팔미테이트', magnesium='마그네슘', vitamin_d='비타민 D', zinc='아연',
    inositol='이노시톨', potassium='칼륨', taurine='타우린', vitamin_b12='비타민 B12',
    vitamin_b5='판토텐산(B5)', vitamin_b3='나이아신(B3)', folate='엽산', probiotics='프로바이오틱스',
    xylooligosaccharides='자일로올리고당', epa='EPA', dha='DHA', fish_oil='어유',
    omega3_total='총 오메가3', krill_oil='크릴오일', phospholipids='인지질', astaxanthin='아스타잔틴')
NAMES.update(lutein='루테인', zeaxanthin='지아잔틴', lutein_esters='루테인 에스테르',
    zeaxanthin_isomers='지아잔틴·메소지아잔틴', bilberry_extract='빌베리 추출물',
    saffron_extract='사프란 추출물', alpha_carotene='알파카로틴', macuguard_blend='마쿠가드 복합물')
LIMITS = [
    '제조사 공식 라벨의 1회 섭취량 기준이며 개인별 권장량이 아닙니다.',
    '쿠팡 판매 흔적은 공개 검색 색인으로 확인했습니다. 현재 재고·가격과 판매분 라벨 일치는 미확인입니다.',
    '주요 성분만 표시합니다. 전체 원재료·알레르기·주의사항은 구매 제품 라벨을 확인하세요.',
    '사진은 제조사 대표 포장입니다. 실제 판매 수량·패키지와 다를 수 있습니다.',
    '실제 알약 크기는 미확인입니다. 연령별 적합성과 복용량은 별도 검토가 필요합니다.',
]


def canonical(url):
    u = urlsplit(url)
    return u.netloc.lower().removeprefix('www.') + u.path.rstrip('/')


def build(p):
    def evidence(q): return dict(sourceId='official', quote=q)
    def fact(v, q): return dict(value=v, evidence=evidence(q))
    quotes = [x['quote'] for x in p['warnings'] + p['claims']]
    source = Source(id='official', kind='manufacturer', url=p['url'], title=p['title'],
        text='\n'.join([p['title'], p['brand'], p['facts'], *quotes]), retrievedAt='2026-09-20')
    serving = p['serving'].replace('  | ', ' ')
    match = re.search(r'Serving Size:?\s*(?:\|\s*)?(\d+)\s+(?:(?:Veg|Vegan|Vegetable|Veggie|Chewable)\s+)?(?:Capsules?|Tablets?|Softgels?|Lozenges?)\s*$', p['serving'], re.I)
    ingredients = [dict(key=i[0], name=NAMES[i[0]], amount=i[1], unit=i[2], basis='per_serving',
        form=p['facts'] if i[0] in ('magnesium', 'probiotics', 'vitamin_b3', 'vitamin_b12', 'folate') else None,
        partOf=i[3] if len(i)>3 else None, evidence=evidence(p['facts'])) for i in p['ingredients']]
    analysis = Analysis.model_validate(dict(productIdentity=fact(p['title'], p['title']),
        brand=fact(p['brand'], p['brand']), serving=fact(serving, p['serving']),
        unitsPerServing=fact(int(match[1]), p['serving']) if match else None,
        dailyServings=None, totalContentMg=None, pillSizeMm=None, formulation=None,
        ingredients=ingredients,
        claims=[dict(text=c['text'], effectId=c['effectId'], ingredientKeys=c['ingredientKeys'],
                     evidence=evidence(c['quote'])) for c in p['claims']],
        warnings=[fact(w['text'], w['quote']) for w in p['warnings']], audience=[], ageGroups=[],
        summary='공식 라벨 기준 비교 정보. 복용 추천 아님. ' + (p.get('potencyNote') or ''),
        unknowns=LIMITS + (['균주별 CFU는 미확인입니다.'] if p['category']=='probiotics' else [])))
    validate_evidence(analysis, [source])
    listing = dict(id='manual-'+p['key'], product=p['name'], productUrl=p['retail'], buyLink=p['retail'],
        source='manual-manufacturer', image=p['image'], imageKind='manufacturer',
        raw=dict(formulaKey=p['key'], officialUrl=p['url'], batch='expansion-2026-09-20'), discoveredAt=store.now())
    provenance = dict(method='reviewed_official_label_and_retail_search_index', batch='expansion-2026-09-20',
        formulaKey=p['key'], retailEvidence=dict(url=p['retail'], status='search_index_only', checkedAt='2026-09-20'),
        officialUrl=p['url'], ageSuitabilityReviewRequired=True, targetCategory=p['category'],
        deduplication='brand + formula + strength + dosage form; package count ignored', limitations=LIMITS)
    product_view(dict(listing=listing, analysis=analysis.model_dump(), sources=[source.model_dump()], provenance=provenance))
    return listing, analysis, [source], provenance


def run(path=None, publish=False, filename=DATA):
    rows=json.loads(Path(filename).read_text(encoding='utf-8'))
    if len({p['key'] for p in rows}) != len(rows) or len({canonical(p['url']) for p in rows}) != len(rows):
        raise ValueError('Duplicate formula or official product URL in batch')
    prepared=[(p, build(p)) for p in rows]
    existing=store.published(path)
    known_ids={p['id'] for p in store.list_listings(path)}
    known_urls={canonical(s['url']) for r in existing for s in r['sources'] if s['kind']=='manufacturer'}
    result=dict(ready=0, added=0, skipped=0, categories={})
    for p,(listing,analysis,sources,provenance) in prepared:
        if listing['id'] in known_ids or canonical(p['url']) in known_urls:
            result['skipped']+=1
            continue
        result['ready']+=1
        result['categories'][p['category']]=result['categories'].get(p['category'],0)+1
        if publish:
            store.save_registrations([listing], path=path)
            note='Official label reviewed; seller label/batch and live inventory not verified.'
            digest=store.fingerprint(listing,sources,note,'manual-review','expansion-v1','manual')
            ident=store.save_draft(listing,analysis,sources,provenance,note,digest,path)
            store.approve(ident,'official-label-reviewed-retail-index-verified',path)
            result['added']+=1
        known_ids.add(listing['id'])
        known_urls.add(canonical(p['url']))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--db')
    parser.add_argument('--file', type=Path, default=DATA, help='Reviewed manifest to import')
    args=parser.parse_args()
    print(json.dumps(run(args.db,args.publish,args.file),ensure_ascii=False,indent=2))
