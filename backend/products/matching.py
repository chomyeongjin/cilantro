"""Explainable catalogue links, not diagnosis or an efficacy ranking.

Label claims, general nutrient functions, and adult eligibility stay distinct.
Never infer a child's suitability, a sleep benefit from magnesium, or probiotic
benefits from CFU count alone. Product-specific reviews are composition-locked.
"""
import json
import re
from pathlib import Path

from .taxonomy import OPTIONS

REVIEW = json.loads(Path(__file__).resolve().parents[1].joinpath('data/product_matching_review.json').read_text(encoding='utf-8'))
ODS = 'https://ods.od.nih.gov/factsheets/'
REFERENCES = {
    'immune': ODS+'ImmuneFunction-HealthProfessional/',
    'c': ODS+'VitaminC-HealthProfessional/',
    'mg': ODS+'Magnesium-HealthProfessional/',
    'b6': ODS+'VitaminB6-HealthProfessional/',
    'b12': ODS+'VitaminB12-HealthProfessional/',
}
ADULT_IDS = ['20s', '30s-40s', '50s-60s', '70-plus']
EFFECT_IDS = {x[0] for x in OPTIONS['effect']}
NOTICE = '성분의 영양 기능·제품 라벨에 따른 연결입니다. 치료 효과·효능 순위·개인별 섭취 추천이 아닙니다. 함량은 표시된 1회 기준이며 높을수록 효과가 좋은 것은 아닙니다.'
AGE_NOTICE = '연령별 효능 순위가 아니라 성인용 표시가 확인된 비교 후보입니다. 식사·복용약·질환·하루 총 섭취량을 별도로 확인하세요. 고함량 주의 제품과 연령 근거 미확인 제품은 자동 연결에서 제외합니다.'


def category_notice(option_id):
    if option_id in ('kids','teens'):
        return '현재 50종에서 아동·청소년용 연령과 용량을 확인한 제품이 없습니다. 성인용 제품을 임의로 추천하지 않습니다.'
    if option_id in ADULT_IDS:
        return AGE_NOTICE + (' 50대 이후 목록은 B12 흡수 관련 근거가 있는 영양소 포함 후보로 좁혔으며 해당 제품 용량의 권장은 아닙니다.' if option_id in ADULT_IDS[2:] else '')
    if option_id == 'sleep-stress':
        return NOTICE+' 마그네슘 함유만으로 수면·스트레스 효과를 연결하지 않습니다. 현재 충분한 제품별 근거를 검토한 항목이 없습니다.'
    if option_id in EFFECT_IDS:
        return NOTICE
    return None


def classify(product, record):
    facts = {f['key']:f for f in product['ingredientFacts']}
    sources = {s['id']:s for s in record['sources']}
    matches = []
    cautions = []

    def link(option, text, keys, basis, url, quote=None):
        if option not in EFFECT_IDS or not keys or not all(k in facts for k in keys):
            return
        evidence = [dict(key=k,name=facts[k]['name'],amount=facts[k]['amountPerServing'],unit=facts[k]['unit'],
                         label=facts[k]['evidence'],labelUrl=sources.get(facts[k]['evidence']['sourceId'],{}).get('url')) for k in keys]
        matches.append(dict(id=option,reason=text,ingredientKeys=keys,ingredients=evidence,
                            basis=basis,sourceUrl=url,quote=quote))

    # Keep only actual reviewed functional claims, not words found in warnings/nav.
    for c in product['claims']:
        keys = c['ingredientKeys']
        if not keys and c['effectId']=='energy-vitality':
            keys = [k for k in facts if k.startswith('vitamin_b') or k in ('folate','biotin')]
        source = sources.get(c['evidence']['sourceId'],{})
        if c['effectId']:
            link(c['effectId'],c['text'],keys,'product_label',source.get('url'),c['evidence']['quote'])
        # Explicit digestive claims only; women's vaginal balance is NOT gut health.
        if c['text']=='장내 균형' and 'probiotics' in facts:
            link('digestive-health','해당 균주 배합의 장내 균형 표시',['probiotics'],'product_label',source.get('url'),c['evidence']['quote'])
        if 'vitamin_a' in keys and '피부' in c['text']:
            link('skin-health','비타민 A의 피부·점막 유지 표시',['vitamin_a'],'product_label',source.get('url'),c['evidence']['quote'])

    # Physiological nutrient roles, expressly NOT proof of finished-product efficacy.
    for key in ('vitamin_c','vitamin_d','zinc','vitamin_a'):
        f = facts.get(key)
        if f and f['amountPerServing'] is not None and f['amountPerServing']>0:
            link('immunity',f["name"]+'의 정상 면역 기능 관련 영양소 보충',[key],'nutrient_function',REFERENCES['immune'])
    if facts.get('vitamin_c',{}).get('amountPerServing',0):
        link('skin-health','비타민 C의 콜라겐 합성 기능',['vitamin_c'],'nutrient_function',REFERENCES['c'])
    if facts.get('magnesium',{}).get('amountMgPerServing',0):
        link('energy-vitality','원소 마그네슘의 에너지 대사 기능',['magnesium'],'nutrient_function',REFERENCES['mg'])

    review = REVIEW.get(product['id'],{})
    actual = sorted((i['key'],i['amount'],i['unit']) for i in record['analysis']['ingredients'])
    expected = sorted((i[0],i[1],i[2] if len(i)>2 else 'mg') for i in review.get('expectedIngredients',[]))
    if actual != expected:
        review = {}  # A reformulated product needs a new review.
    for extra in review.get('effects',[]):
        link(extra['id'],extra['text'],['probiotics'],'manufacturer_statement',review['url'],extra['quote'])

    def high(key,threshold,unit):
        f=facts.get(key,{})
        return f.get('unit')==unit and f.get('amountPerServing') is not None and f['amountPerServing']>=threshold
    if high('vitamin_b6',12.000001,'mg'):
        cautions.append(dict(text='B6 1회 함량이 EFSA 성인 일일 상한 12mg보다 높습니다. 장기 섭취·중복 복용 상담 필요.',sourceUrl=REFERENCES['b6']))
    if high('magnesium',350.000001,'mg'):
        cautions.append(dict(text='마그네슘 1회 함량이 미국 성인 보충제 일일 상한 350mg보다 높습니다. 설사·신장질환·복용약 확인 필요.',sourceUrl=REFERENCES['mg']))
    if high('vitamin_d',100,'mcg'):
        cautions.append(dict(text='비타민 D 1회 100μg 이상: 중복 섭취와 하루 총량을 전문가와 확인하세요.',sourceUrl=ODS+'VitaminD-HealthProfessional/'))
    if high('vitamin_b3',100,'mg') or high('vitamin_b3',100,'mg NE'):
        cautions.append(dict(text='고함량 B3 포함: 나이만으로 권하지 않으며 형태·복용약·라벨 주의사항 확인이 필요합니다.',sourceUrl=next(iter(sources.values()),{}).get('url')))

    adult_quote=review.get('adultQuote')
    adult_url=review.get('url')
    if not adult_quote:
        for s in sources.values():
            found=re.search(r'\b(?:For adults only|Adults only|Suggested Adult Use)\b',s['text'],re.I)
            if found:
                adult_quote,adult_url=found.group(),s['url']
                break
    # KEEP OUT OF REACH OF CHILDREN is a storage warning, not an adult indication.
    ages=[]
    if adult_quote and not cautions and product['analysisStatus']!='example':
        for age in ADULT_IDS:
            if age in ('50s-60s','70-plus') and not facts.get('vitamin_b12',{}).get('amountPerServing'):
                continue
            reason='성인용 표시 확인 · 나이별 효과 입증 아님'
            if age in ('50s-60s','70-plus') and 'vitamin_b12' in facts:
                reason='성인용 B12 포함 · 50대 이후 흡수 저하 가능성 검토, 용량 상담 필요'
            ages.append(dict(id=age,reason=reason,basis='adult_label_not_age_efficacy',sourceUrl=adult_url,quote=adult_quote,
                             ageEvidenceUrl=REFERENCES['b12'] if age in ('50s-60s','70-plus') else None))

    product.update(effectIds=list(dict.fromkeys(m['id'] for m in matches)),ageIds=[a['id'] for a in ages],
                   effectMatches=matches,ageMatches=ages,selectionCautions=cautions,
                   matchingVersion='reviewed-ingredient-functions-v1',matchingNotice=NOTICE,
                   adultLabelEvidence=dict(quote=adult_quote,sourceUrl=adult_url) if adult_quote else None,
                   ageStatus='adult_label_candidate' if ages else 'not_auto_linked')
    return product
