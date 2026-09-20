"""Eight distinct formulas inspected on Coupang on 2026-09-20.

Quantity/pack variants are not separate formulas. Source excerpts are visual
transcriptions, not AI-generated facts. Run again safely without duplicate rows.
"""
from products import store
from products.models import Analysis, Source
from products.presenter import product_view

CDN = 'https://thumbnail.coupangcdn.com/thumbnails/remote/'
EYE = '혈중 중성지질·혈행 개선, 건조한 눈 개선에 도움을 줄 수 있음'
MEMORY = '혈행·중성지질·눈 건조·기억력 개선에 도움을 줄 수 있음'
BLOOD = '혈중 중성지질·혈행 개선에 도움을 줄 수 있음'
E = '항산화 작용으로 유해산소로부터 세포 보호에 필요'
D = '칼슘·인 흡수와 이용, 뼈 형성·유지에 필요'


def ing(key, name, amount, unit, quote):
    return (key, name, amount, unit, quote)


PRODUCTS = [
    dict(ids='9249315299-27356171490-94322276550', family='nutrijung-premium-rtg',
         brand='뉴트리정', name='초임계 알티지 프리미엄 오메가3', image='nutrijung.png', units=2,
         label=CDN+'q89/image/vendor_inventory/075b/d9e31067539f6dce06f7b3acbd9f22ebd314e2869ebff85fb35ca2ae1d02.png',
         text='''뉴트리정 초임계 알티지 프리미엄 오메가3 대용량, 180정, 1개
1일 섭취량: 2캡슐(1,040 mg)
EPA와 DHA의 합 600 mg
비타민E 3.3 mg α-TE
[EPA 및 DHA 함유 유지] 혈중 중성지질 개선·혈행 개선·건조한 눈을 개선하여 눈 건강에 도움을 줄 수 있음
[비타민E] 항산화 작용을 하여 유해산소로부터 세포를 보호하는데 필요
의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하시기 바랍니다.
개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.''',
         serving='1일 섭취량: 2캡슐(1,040 mg)',
         ingredients=[ing('epa_dha','EPA + DHA',600,'mg','EPA와 DHA의 합 600 mg'), ing('vitamin_e','비타민 E',3.3,'mg α-TE','비타민E 3.3 mg α-TE')],
         claim=EYE, vitamin='e', warnings=['의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하시기 바랍니다.', '개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.']),
    dict(ids='8230302231-23686281135-94253171009', family='drlean-supercritical-rtg-alpha',
         brand='닥터린', name='초임계 알티지 오메가3 알파', image='drlean.jpg', units=1,
         label=CDN+'q89/image/retail/images/49153332377896-b04cd0ab-7c25-4d5b-9878-b11447d4af3f.jpg',
         text='''닥터린 정품 초임계 알티지 오메가3 알파, 30정, 3개
1일 섭취량: 1캡슐(1,007 mg)
EPA와DHA의 합 600 mg
비타민 E 3.3 mg α-TE
[EPA 및 DHA 함유 유지] 혈중 중성지질 개선·혈행개선·건조한 눈을 개선하여 눈 건강에 도움을 줄 수 있음
[비타민E] 항산화 작용을 하여 유해산소로부터 세포를 보호하는데 필요
의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하십시오.
개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.
이상사례 발생 시 섭취를 중단하고 전문가와 상담하십시오.
특정질환, 특이체질, 알레르기체질, 임산부의 경우에는 간혹 개인에 따라 과민반응이 나타날 수 있으니 원료를 확인하시고, 섭취 전에 전문가와 상담하시기 바랍니다.''',
         serving='1일 섭취량: 1캡슐(1,007 mg)',
         ingredients=[ing('epa_dha','EPA + DHA',600,'mg','EPA와DHA의 합 600 mg'), ing('vitamin_e','비타민 E',3.3,'mg α-TE','비타민 E 3.3 mg α-TE')],
         claim=EYE, vitamin='e', warnings=['의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하십시오.', '개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.', '이상사례 발생 시 섭취를 중단하고 전문가와 상담하십시오.', '특정질환, 특이체질, 알레르기체질, 임산부의 경우에는 간혹 개인에 따라 과민반응이 나타날 수 있으니 원료를 확인하시고, 섭취 전에 전문가와 상담하시기 바랍니다.']),
    dict(ids='35838053-68202-70393847458', family='now-molecularly-distilled-omega3',
         brand='나우푸드', name='멀레큐럴리 디스틸드 오메가3 1000mg', image='now.jpg', units=2, daily=False,
         label=CDN+'492x492ex/image/vendor_inventory/bd01/b0fbca147b11b6bbf3fff3dd0629f9bfc6f5b12928d91956d752434031ad.jpg',
         text='''나우푸드 멀레큐럴리 디스틸드 오메가3 1000mg 피쉬 소프트젤, 200정, 1개
Serving Size 2 Fish Softgels
Fish Oil Concentrate 2 g (2,000 mg)
Eicosapentaenoic Acid (EPA) 360 mg
Docosahexaenoic Acid (DHA) 240 mg''',
         serving='Serving Size 2 Fish Softgels',
         ingredients=[ing('epa','EPA',360,'mg','Eicosapentaenoic Acid (EPA) 360 mg'), ing('dha','DHA',240,'mg','Docosahexaenoic Acid (DHA) 240 mg')],
         claim=None, vitamin=None, warnings=[]),
    dict(ids='6854281548-24019532759-4765824657', family='sportsresearch-triple-strength-1040',
         brand='스포츠리서치', name='오메가3 피쉬오일 트리플 스트렝스 1040mg', image='sportsresearch.jpg', units=1, daily=False,
         label=CDN+'492x492ex/image/vendor_inventory/71ec/ea1bd52d2222ef46add29c37b6f08ab10ff1a3c3f72be2e1bd5e12c1918e.jpg',
         text='''스포츠리서치 1040mg 오메가-3 피쉬 오일 트리플 스트렝스 소프트젤, 180정, 1개
Serving Size: 1 Softgel
Wild Alaska Pollock Fish Oil Concentrate 1250 mg
Total Omega-3 Fatty Acids as TG 1040 mg
EPA (Eicosapentaenoic Acid) 690 mg
DHA (Docosahexaenoic Acid) 260 mg
CONTAINS: Fish (Alaska pollock).''',
         serving='Serving Size: 1 Softgel',
         ingredients=[ing('epa','EPA',690,'mg','EPA (Eicosapentaenoic Acid) 690 mg'), ing('dha','DHA',260,'mg','DHA (Docosahexaenoic Acid) 260 mg')],
         claim=None, vitamin=None, warnings=['CONTAINS: Fish (Alaska pollock).']),
    dict(ids='6936154080-20705239988-91400458970', family='dambaek-omegaessence-1000',
         brand='담백하루', name='초임계 알티지 오메가에센스 1000', image='dambaek.jpg', units=1,
         label=CDN+'q89/image/retail/images/445854978418590-370d58e8-a4ca-4594-895e-a0a75185c8a9.png',
         text='''담백하루 정품 초임계 알티지 오메가에센스 1000, 30정, 2개
1일 섭취량: 1캡슐(1,252 mg)
EPA와 DHA의 합 1000 mg
비타민D 15 μg
[EPA 및 DHA 함유 유지] 혈중 중성지질 개선·혈행개선에 도움을 줄 수 있음
[비타민D] 칼슘과 인이 흡수되고 이용되는데 필요, 뼈의 형성과 유지에 필요, 골다공증발생 위험 감소에 도움을 줌
고등어, 대두, 돼지고기 함유
의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하십시오.
개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.
이상사례 발생 시 섭취를 중단하고 전문가와 상담하십시오.
고칼슘혈증이 있거나 의약품 복용 시 전문가와 상담하십시오.''',
         serving='1일 섭취량: 1캡슐(1,252 mg)',
         ingredients=[ing('epa_dha','EPA + DHA',1000,'mg','EPA와 DHA의 합 1000 mg'), ing('vitamin_d','비타민 D',15,'mcg','비타민D 15 μg')],
         claim=BLOOD, vitamin='d', warnings=['고등어, 대두, 돼지고기 함유', '의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하십시오.', '개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.', '이상사례 발생 시 섭취를 중단하고 전문가와 상담하십시오.', '고칼슘혈증이 있거나 의약품 복용 시 전문가와 상담하십시오.']),
    dict(ids='9652792776-28852463547-95786221057', family='ilyang-supercritical-rtg-900',
         brand='일양약품', name='초임계 rTG 오메가3 900', image='ilyang.png', units=2,
         label=CDN+'q89/image/retail/images/2026/07/16/12/9/794483f0-7c11-4ee0-9b86-e7a0394659be.png',
         text='''일양약품 초임계 rTG 오메가3 900 45.18g, 60정, 1개
1일 섭취량: 2캡슐(1,506 mg)
EPA와 DHA의 합 900 mg
비타민E 3.3 mg α-TE
[EPA 및 DHA 함유 유지] 혈중 중성지질 개선·혈행 개선·기억력 개선·건조한 눈을 개선하여 눈 건강에 도움을 줄 수 있음
[비타민E] 항산화 작용을 하여 유해산소로부터 세포를 보호하는데 필요
의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하십시오.
개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.
이상사례 발생 시 섭취를 중단하고 전문가와 상담하십시오.
특이체질, 알레르기 체질이신 경우 원료 성분을 확인하신 후 섭취하십시오.
대두, 고등어, 돼지고기 함유''',
         serving='1일 섭취량: 2캡슐(1,506 mg)',
         ingredients=[ing('epa_dha','EPA + DHA',900,'mg','EPA와 DHA의 합 900 mg'), ing('vitamin_e','비타민 E',3.3,'mg α-TE','비타민E 3.3 mg α-TE')],
         claim=MEMORY, vitamin='e', warnings=['의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하십시오.', '개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.', '이상사례 발생 시 섭취를 중단하고 전문가와 상담하십시오.', '특이체질, 알레르기 체질이신 경우 원료 성분을 확인하신 후 섭취하십시오.', '대두, 고등어, 돼지고기 함유']),
    dict(ids='6071010112-579858973-4518862314', family='naturalplus-rtg-1200',
         brand='내츄럴플러스', name='알티지 오메가3 1200', image='naturalplus.png', units=1,
         label=CDN+'492x492ex/image/retail/images/2508580550636490-764cf160-9ea7-44a9-ba6c-a59e8e83a0c4.jpg',
         text='''내츄럴플러스 알티지 오메가3 1200, 180정, 234g, 1개
1일 섭취량: 1캡슐(1,301.2 mg)
EPA와 DHA의 합 1,200 mg (EPA 800mg, DHA 400mg)
비타민D 25 μg(1,000IU)''',
         serving='1일 섭취량: 1캡슐(1,301.2 mg)',
         ingredients=[ing('epa','EPA',800,'mg','EPA 800mg'), ing('dha','DHA',400,'mg','DHA 400mg'), ing('vitamin_d','비타민 D',25,'mcg','비타민D 25 μg(1,000IU)')],
         claim=None, vitamin=None, warnings=[]),
    dict(ids='9605631981-28675794442-95681239579', family='dongwha-rtg-vitamin-d-2000',
         brand='동화약품', name='알티지 오메가3 비타민D 2000 IU', image='dongwha.jpg', units=1,
         label=CDN+'492x492ex/image/retail/images/2026/06/29/9/0/25ef3650-2fe0-4f78-af81-33295a3700cd.jpg',
         text='''동화약품 알티지 오메가3 비타민D 2000 IU 63.6g, 60정, 1개
1일 섭취량: 1캡슐(1,060 mg)
비타민D 50 μg(2,000 IU)
비타민E 3.3 mg α-TE
EPA와 DHA의 합 600 mg
[EPA 및 DHA 함유 유지] 혈중 중성지질 개선·혈행 개선에 도움을 줄 수 있음, 건조한 눈을 개선하여 눈 건강에 도움을 줄 수 있음
[비타민D] 칼슘과 인이 흡수되고 이용되는데 필요, 뼈의 형성과 유지에 필요, 골다공증발생 위험 감소에 도움을 줌
[비타민E] 항산화 작용을 하여 유해산소로부터 세포를 보호하는데 필요''',
         serving='1일 섭취량: 1캡슐(1,060 mg)',
         ingredients=[ing('epa_dha','EPA + DHA',600,'mg','EPA와 DHA의 합 600 mg'), ing('vitamin_d','비타민 D',50,'mcg','비타민D 50 μg(2,000 IU)'), ing('vitamin_e','비타민 E',3.3,'mg α-TE','비타민E 3.3 mg α-TE')],
         claim=EYE, vitamin='de', warnings=[]),
]


def build(p):
    product_id, item, vendor = p['ids'].split('-')
    url = f'https://www.coupang.com/vp/products/{product_id}?itemId={item}&vendorItemId={vendor}'
    # Identity comes from the selected page, label facts from its image.
    title, label_text = p['text'].split('\n', 1)
    sources = [Source(id='identity', kind='label', url=url, title='선택 옵션 상품명', text=title, retrievedAt='2026-09-20'),
               Source(id='label', kind='label', url=p['label'], title='상품 상세 라벨 이미지 전사', text=label_text, retrievedAt='2026-09-20')]
    def ev(quote, source='label'):
        return {'sourceId': source, 'quote': quote}
    def fact(value, quote=None, source='label'):
        return {'value': value, 'evidence': ev(quote or value, source)}
    claims, audience = [], []
    if p['claim']:
        quote = next(line for line in label_text.splitlines() if line.startswith('[EPA'))
        claims.append(dict(text=p['claim'], effectId='eye-health' if p['claim'] != BLOOD else None,
                           ingredientKeys=['epa_dha'], evidence=ev(quote)))
        audience.append(fact('혈행 건강 관리', quote))
        if p['claim'] != BLOOD:
            audience.append(fact('눈 건조 관리', quote))
        if p['claim'] == MEMORY:
            audience.append(fact('기억력 관리', quote))
    for vitamin, text, effect in [('d', D, 'bone-joint'), ('e', E, None)]:
        if vitamin in (p['vitamin'] or ''):
            quote = next(line for line in label_text.splitlines() if line.startswith('[비타민'+vitamin.upper()))
            claims.append(dict(text=text, effectId=effect, ingredientKeys=['vitamin_'+vitamin], evidence=ev(quote)))
            if vitamin == 'd':
                audience.append(fact('뼈 건강 관리', quote))
    unknowns = ['알약 길이 미확인. 성분별 부작용을 임의로 추정하지 않았습니다.',
                '캡슐 중량은 순수 내용물 중량이 아니므로 전체 성분 구성비로 사용하지 않았습니다.']
    if not p['warnings']:
        unknowns.append('섭취 주의사항 미확인. 부작용이 없다는 의미가 아닙니다.')
    if not p['claim']:
        unknowns.append('제품별 기능성 문구 미확인. 다른 제품의 기능성을 복사하지 않았습니다.')
    if not p.get('daily', True):
        unknowns.append('Serving Size 기준 함량이며 하루 섭취 횟수는 미확인입니다.')
    analysis = Analysis.model_validate(dict(
        productIdentity=fact(title, source='identity'), brand=fact(p['brand'], source='identity'),
        serving=fact(p['serving']), unitsPerServing=fact(p['units'], p['serving']),
        dailyServings=fact(1, p['serving']) if p.get('daily', True) else None,
        totalContentMg=None, pillSizeMm=None, formulation=None,
        ingredients=[dict(key=k,name=n,amount=a,unit=u,basis='per_serving',form=None,partOf=None,evidence=ev(q)) for k,n,a,u,q in p['ingredients']],
        claims=claims, audience=audience, warnings=[fact(w) for w in p['warnings']], ageGroups=[],
        summary=p['serving']+' 기준. '+', '.join(f'{n} {a}{u}' for k,n,a,u,q in p['ingredients']), unknowns=unknowns))
    listing = dict(id='coupang-'+p['ids'], product=p['name'], productUrl=url, buyLink=url,
                   source='manual-manufacturer', image='/images/omega3/'+p['image'], imageKind='retailer',
                   pillImage='/images/pills/pill1_1.png', raw=dict(text=p['text'],formulaKey=p['family']), discoveredAt=store.now())
    provenance = dict(method='browser_image_transcription', formulaKey=p['family'],
                      deduplication='brand + named formula; package count ignored', audienceBasis='label_function_goals',
                      limitations=unknowns)
    product_view(dict(listing=listing,analysis=analysis.model_dump(),sources=[s.model_dump() for s in sources],provenance=provenance))
    return listing, analysis, sources, provenance


def main():
    assert len({p['family'] for p in PRODUCTS}) == len(PRODUCTS) == 8
    prepared = [build(p) for p in PRODUCTS]  # Validate the whole batch before saving.
    for listing, analysis, sources, provenance in prepared:
        # Guard against importing the same formula under a different quantity ID.
        duplicate = next((r for r in store.list_listings() if r['id'] != listing['id'] and
                          r.get('raw', {}).get('formulaKey') == provenance['formulaKey']), None)
        if duplicate:
            print('Skipped quantity variant:', listing['id'])
            continue
        note = 'Selected variant inspected; package quantity not part of formula identity.'
        store.save_registrations([listing], update_existing=True)
        digest = store.fingerprint(listing, sources, note, 'visual-transcription', 'omega3-batch-v1', 'manual')
        ident = store.save_draft(listing, analysis, sources, provenance, note, digest)
        store.approve(ident, 'selected-variant-and-label-visually-reviewed')
        print('Ready:', listing['id'], 'analysis', ident)


if __name__ == '__main__':
    main()
