"""Reviewed official-label import, not an unattended Coupang crawler.

Retail presence is search-index evidence; current inventory and seller batch
labels are NOT verified. Quantities do not identify a new formula.
"""
from products import store
from products.models import Analysis, Source
from products.presenter import product_view

NOW = 'https://www.nowfoods.com/products/supplements/'
RETAIL = 'https://www.coupang.com/'
STANDARD = 'For adults only. Consult physician if pregnant/nursing, taking medication, or have a medical condition. Keep out of reach of children.'
LIMITS = ['제조사 미국 공식 라벨 기준. 쿠팡 판매분의 라벨 버전·배치 일치는 미확인입니다.',
          '쿠팡 판매 이력은 검색 색인으로 확인했으며 현재 재고·가격은 미확인입니다.',
          '알약 크기 미확인. 제품 사진은 공식 사이트의 대표 포장으로 판매 수량과 다를 수 있습니다.',
          '기능 문구는 제조사 설명의 요약이며 개인별 섭취 권장이나 질병 치료 효과가 아닙니다.']

# key, Korean display, amount, exact unit, source excerpt (not %DV).
def nutrient(key, name, amount, unit, quote):
    return (key, name, amount, unit, quote)

def b(number, amount, quote, unit='mg'):
    return nutrient('vitamin_b'+str(number), '비타민 B'+str(number), amount, unit, quote)

def folate(amount, quote):
    return nutrient('folate', '엽산', amount, 'mcg DFE', quote)

def biotin(amount, quote):
    return nutrient('biotin', '비오틴', amount, 'mcg', quote)

PRODUCTS = [
 dict(key='now-b50-tablets', brand='나우푸드', name='B-50', title='Vitamin B-50 Tablets',
      url=NOW+'vitamin-b-50-tablets', retail=RETAIL+'vp/products/9397967670',
      serving='Serving Size: 1 Tablet', units=1,
      ingredients=[b(1,50,'Thiamin (Vitamin B-1) (from Thiamin HCl) 50 mg'), b(2,50,'Riboflavin (Vitamin B-2) 50 mg'), b(3,50,'Niacin (Vitamin B-3) (as Niacinamide) 50 mg'), b(6,50,'Vitamin B-6 (from Pyridoxine HCl) 50 mg'), folate(680,'Folate 680 mcg DFE (400 mcg folic acid)'), b(12,50,'Vitamin B-12 (as Cyanocobalamin) 50 mcg','mcg'), biotin(50,'Biotin 50 mcg'), b(5,50,'Pantothenic Acid (from Calcium Pantothenate) 50 mg'), nutrient('choline','콜린',50,'mg','Choline (from Choline Bitartrate) 50 mg'), nutrient('paba','PABA',50,'mg','PABA (Para-Aminobenzoic Acid) 50 mg'), nutrient('inositol','이노시톨',50,'mg','Inositol 50 mg')],
      claim=('에너지 생성','Supports Energy Production'), warnings=[STANDARD,'This product contains Biotin which may interfere with some blood test results.']),
 dict(key='now-b1-100',brand='나우푸드',name='B-1 100mg',title='Vitamin B-1 100 mg Tablets',url=NOW+'vitamin-b-1-100-mg-tablets',retail=RETAIL+'vp/products/28024',serving='Serving Size: 1 Tablet',units=1,
      ingredients=[b(1,100,'Thiamin (Vitamin B-1) (from Thiamin HCl) 100 mg')],claim=('에너지 생성','Supports Energy Production'),warnings=[STANDARD]),
 dict(key='now-b2-100',brand='나우푸드',name='B-2 100mg',title='Vitamin B-2 100 mg Veg Capsules',url=NOW+'vitamin-b-2-100-mg-veg-capsules',retail=RETAIL+'vp/products/28026',serving='Serving Size: 1 Veg Capsule',units=1,
      ingredients=[b(2,100,'Riboflavin (Vitamin B-2) 100 mg')],claim=('에너지 생성','Riboflavin is an important enzyme cofactor necessary for energy production from carbohydrate, fat, and protein.'),warnings=[STANDARD]),
 dict(key='now-b6-100',brand='나우푸드',name='B-6 100mg',title='Vitamin B-6 100 mg Veg Capsules',url=NOW+'vitamin-b-6-100-mg-veg-capsules',retail=RETAIL+'np/search?channel=user&q=b6',serving='Serving Size: 1 Veg Capsule',units=1,
      ingredients=[b(6,100,'Vitamin B-6 (as Pyridoxine HCl) 100 mg')],claim=('신경계 건강','Important for Nervous System Function'),warnings=['Do not exceed the recommended dose.',STANDARD]),
 dict(key='now-niacinamide-500',brand='나우푸드',name='나이아신아미드 B-3 500mg',title='Niacinamide (B-3) 500 mg Veg Capsules',url=NOW+'niacinamide-b-3-500-mg-veg-capsules',retail=RETAIL+'np/best100/bestseller/310535',serving='Serving Size: 1 Veg Capsule',units=1,
      ingredients=[b(3,500,'Niacin (as Niacinamide) (Vitamin B-3) 500 mg')],claim=('에너지 생성','Energy Production'),warnings=['For adults only. Consult physician if pregnant/nursing, taking medication, or have a medical condition (liver problems, stomach ulcers, diabetes, gout, etc.). Keep out of reach of children.']),
 dict(key='now-b12-1000',brand='나우푸드',name='B-12 1000mcg 로젠지',title='Vitamin B-12 1,000 mcg Lozenges',url=NOW+'vitamin-b-12-1000-mcg-lozenges',retail=RETAIL+'vp/products/3316288',serving='Serving Size: 1 Lozenge',units=1,
      ingredients=[b(12,1000,'Vitamin B-12 (as Cyanocobalamin) 1 mg (1,000 mcg)','mcg'),folate(170,'Folate 170 mcg DFE (100 mcg folic acid)')],claim=('에너지 생성','Essential for Energy Production'),warnings=[STANDARD,'Xylitol is harmful to pets; seek veterinary care immediately if ingestion is suspected.']),
 dict(key='now-biotin-5000',brand='나우푸드',name='비오틴 5000mcg',title='Biotin 5,000 mcg Veg Capsules',url=NOW+'biotin-5000-mcg-veg-capsules',retail=RETAIL+'np/categories/497455',serving='Serving Size: 1 Veg Capsule',units=1,
      ingredients=[biotin(5000,'Biotin 5 mg (5,000 mcg)')],claim=('아미노산 대사','Supports Amino Acid Metabolism'),warnings=[STANDARD,'This product contains Biotin which may interfere with some blood test results.']),
 dict(key='solgar-bcomplex-100-capsules',brand='솔가',name='B-컴플렉스 100',title='B-Complex “100” Vegetable Capsules',url='https://www.solgar.com/products/b-complex-100-vegetable-capsules',retail=RETAIL+'vp/products/8136129840',serving='Serving Size: 1 Vegetable Capsule',units=1,
      ingredients=[b(1,100,'Thiamin (vitamin B1) (as thiamin mononitrate) 100 mg'),b(2,100,'Riboflavin (vitamin B2) 100 mg'),b(3,100,'Niacin (vitamin B3) (as niacinamide) 100 mg'),b(6,100,'Vitamin B6 (as pyridoxine HCI) 100 mg'),folate(666,'Folate 666 mcg DFE (400 mcg folic acid)'),b(12,100,'Vitamin B12 (as cyanocobalamin) 100 mcg','mcg'),biotin(100,'Biotin (as d-biotin) 100 mcg'),b(5,100,'Pantothenic Acid (vitamin B5) (as d-calcium pantothenate) 100 mg'),nutrient('choline','콜린',20,'mg','Choline (as choline bitartrate) 20 mg'),nutrient('inositol','이노시톨',100,'mg','Inositol 100 mg')],
      claim=('에너지 생성','Support daily energy'),warnings=['Not intended for use by pregnant or nursing women.','If you are taking any medications, have any medical condition or are planning to undergo any clinical lab testing, consult your healthcare practitioner before use.']),
 dict(key='lifeextension-bioactive-bcomplex',brand='라이프익스텐션',name='바이오액티브 컴플리트 B-컴플렉스',title='BioActive Complete B-Complex',url='https://www.lifeextension.com/vitamins-supplements/item01945/bioactive-complete-b-complex',retail=RETAIL+'np/products/brand-shop?brandName=%EB%9D%BC%EC%9D%B4%ED%94%84%EC%9D%B5%EC%8A%A4%ED%85%90%EC%85%98',serving='Serving Size 2 vegetarian capsules',units=2,
      ingredients=[b(1,100,'Thiamine (vitamin B1) (as thiamine HCl) 100 mg'),b(2,75,'Riboflavin (vitamin B2) (as riboflavin and riboflavin 5’-phosphate) 75 mg'),b(3,100,'Niacin (as niacinamide and niacin) 100 mg•','mg NE'),b(6,100,'Vitamin B6 (as pyridoxine HCl and pyridoxal 5’-phosphate) 100 mg'),folate(680,'Folate (as L-5-methyltetrahydrofolate calcium salt) 680 mcg°'),b(12,300,'Vitamin B12 (as methylcobalamin) 300 mcg','mcg'),biotin(1000,'Biotin 1000 mcg'),b(5,500,'Pantothenic acid (as D-calcium pantothenate) 500 mg'),nutrient('calcium','칼슘',50,'mg','Calcium (as D-calcium pantothenate, dicalcium phosphate) 50 mg'),nutrient('inositol','이노시톨',100,'mg','Inositol 100 mg'),nutrient('paba','PABA',50,'mg','PABA (para-aminobenzoic acid) 50 mg')],
      extra='•NE (niacin equivalents). °DFE (dietary folate equivalents)',claim=('에너지 생성','Boosts energy production and promotes a healthy metabolism'),warnings=['Temporary flushing, itching, rash, or gastric disturbances may occur','KEEP OUT OF REACH OF CHILDREN','DO NOT EXCEED RECOMMENDED DOSE']),
 dict(key='thorne-basic-bcomplex',brand='쏜',name='베이직 B 컴플렉스',title='Basic B Complex',url='https://www.thorne.com/products/dp/basic-b-complex',retail=RETAIL+'vp/products/433050?itemId=14388898370&vendorItemId=92551196042',serving='Serving Size: 1 Capsule(s)',units=1,
      ingredients=[b(1,110,'Vitamin B1 (Thiamin HCI) 110mg'),b(2,10,"Vitamin B2 (Riboflavin 5'-Phosphate Sodium) 10mg"),b(3,140,'Vitamin B3 (Niacin) 10mg\nVitamin B3 (Niacinamide) 130mg'),b(5,110,'Vitamin B5 (Pantothenic Acid) 110mg'),b(6,10,"Vitamin B6 (as Pyridoxal 5'-Phosphate) 10mg"),b(12,400,'Vitamin B12 (as Methylcobalamin) 400mcg','mcg'),folate(667,'Folate (L-5-MTHF) 667mcg DFE'),biotin(400,'Biotin 400mcg'),nutrient('choline','콜린',28,'mg','Choline (Citrate) 28mg')],
      claim=('에너지 생성','Promotes cellular energy production'),warnings=['This product is contraindicated in an individual with a history of hypersensitivity to any of its ingredients.','If pregnant, consult your health-care practitioner before using this product.',"5-methyltetrahydrofolate (5-MTHF) supplementation is not recommended concurrent with methotrexate cancer therapy, as it can interfere with methotrexate's anti-neoplastic activity"]),
]

def build(p, index):
    def ev(q): return dict(sourceId='official',quote=q)
    def fact(value,q): return dict(value=value,evidence=ev(q))
    source_brand = 'NOW' if index < 7 else ['Solgar', 'Life Extension', 'Thorne'][index-7]
    text='\n'.join([source_brand,p['title'],p['serving'],*[r[4] for r in p['ingredients']],p.get('extra',''),p['claim'][1],*p['warnings']])
    sources=[Source(id='official',kind='manufacturer',url=p['url'],title=p['title']+' — official label excerpts',text=text,retrievedAt='2026-09-20')]
    analysis=Analysis.model_validate(dict(productIdentity=fact(p['title'],p['title']),brand=fact(p['brand'],source_brand),
        serving=fact(p['serving'],p['serving']),unitsPerServing=fact(p['units'],p['serving']),dailyServings=None,
        totalContentMg=None,pillSizeMm=None,formulation=None,
        ingredients=[dict(key=k,name=n,amount=a,unit=u,basis='per_serving',form=None,partOf=None,evidence=ev(q)) for k,n,a,u,q in p['ingredients']],
        claims=[dict(text=p['claim'][0],effectId='energy-vitality' if p['claim'][0]=='에너지 생성' else None,ingredientKeys=[],evidence=ev(p['claim'][1]))],
        warnings=[fact(w,w) for w in p['warnings']],audience=[fact(p['claim'][0]+' 관리',p['claim'][1])],ageGroups=[],
        summary='제조사 공식 라벨의 1회 섭취량 기준. 섭취 권장 아님.',unknowns=LIMITS+['하루 섭취 횟수는 별도 확인이 필요합니다.']))
    listing=dict(id='manual-'+p['key'],product=p['name'],productUrl=p['retail'],buyLink=p['retail'],
        source='manual-manufacturer',image='/images/vitamin-b/'+str(index)+('.avif' if index in (7,8) else '.png'),imageKind='manufacturer',
        raw=dict(formulaKey=p['key'],officialUrl=p['url'],retailEvidence='search_index_listing_not_live_verified'),discoveredAt=store.now())
    if index==9:
        listing['image']='https://d1vo8zfysxy97v.cloudfront.net/media/product/b104__v0dd31dc4e6477b012e24bac31fd70fe7fe8bdd09.png'
    provenance=dict(method='official_site_review_and_manual_structuring',formulaKey=p['key'],retailEvidence=dict(url=p['retail'],status='search_index_only',checkedAt='2026-09-20'),deduplication='brand + formula + strength + dosage form; package count ignored',limitations=LIMITS)
    product_view(dict(listing=listing,analysis=analysis.model_dump(),sources=[s.model_dump() for s in sources],provenance=provenance))
    return listing,analysis,sources,provenance

def main():
    assert len({p['key'] for p in PRODUCTS})==10
    prepared=[build(p,i) for i,p in enumerate(PRODUCTS)]
    for listing,analysis,sources,provenance in prepared:
        duplicate=next((r for r in store.list_listings() if r['id']!=listing['id'] and r.get('raw',{}).get('formulaKey')==provenance['formulaKey']),None)
        if duplicate:
            print('Skipped duplicate formula:',listing['id'])
            continue
        note='Official US label reviewed; retailer listing presence only, seller batch not verified.'
        store.save_registrations([listing],update_existing=True)
        digest=store.fingerprint(listing,sources,note,'manual-official-label','vitamin-b-v1','manual')
        ident=store.save_draft(listing,analysis,sources,provenance,note,digest)
        store.approve(ident,'official-label-reviewed-retailer-batch-unverified')
        print('Ready:',listing['id'],ident)

if __name__=='__main__':
    main()
