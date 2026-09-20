"""Source-backed educational copy, NOT product claims or eligibility rules.

Keywords describe nutrient roles, not a promise of benefit from supplementation.
Unknown/limited evidence stays explicit instead of manufacturing an indication.
"""
from copy import deepcopy

REVIEWED_AT = '2026-09-20'
NOTICE = ('effects는 성분의 일반적인 역할이며 이 제품의 치료·예방 효과가 아닙니다. '
          'side effects에는 과량 섭취·상호작용 주의가 포함되며 반드시 발생한다는 뜻은 아닙니다. '
          '복용량·성분 형태·질환·복용약에 따라 달라집니다.')
FOR_NOTICE = ('성분 기준의 관심 대상이며 개인별 복용 권장이나 연령 적합성 판정이 아닙니다. '
              '제품 표시 연령·섭취량과 주의사항을 먼저 확인하세요.')
ODS = 'https://ods.od.nih.gov/factsheets/{}-Consumer/'
SAFETY = 'https://www.nccih.nih.gov/health/safety'
NEI = 'https://www.nei.nih.gov/eye-health-information/clinical-trials/age-related-eye-disease-studies-aredsareds2/aredsareds2-frequently-asked-questions'


def profile(effects, cautions, url, note='', basis='nutrient_role'):
    return dict(effects=effects.split('|'), sideEffects=cautions.split('|'),
                educationSources=[url], educationNote=note,
                educationBasis=basis, educationReviewedAt=REVIEWED_AT)


PROFILES = {}
for key, slug, effects, cautions in [
    ('vitamin_b1', 'Thiamin', '에너지 대사|세포 기능', '유해성 보고 드묾'),
    ('vitamin_b2', 'Riboflavin', '에너지 대사|세포 성장', '유해성 보고 드묾'),
    ('vitamin_b3', 'Niacin', '에너지 대사|세포 기능', '홍조(니코틴산형)|간 손상(고용량)'),
    ('vitamin_b5', 'PantothenicAcid', '에너지 대사|지방 대사', '설사(과량)'),
    ('vitamin_b6', 'VitaminB6', '단백질 대사|면역 기능', '신경 손상(장기 고용량)'),
    ('vitamin_b12', 'VitaminB12', '신경 기능|적혈구 생성', '유해성 보고 드묾'),
    ('biotin', 'Biotin', '영양소 대사', '검사결과 간섭'),
    ('folate', 'Folate', 'DNA 합성|세포 분열', 'B12 결핍 은폐(과량)'),
    ('choline', 'Choline', '세포막 구성|신경 전달', '체취(과량)|저혈압(과량)'),
    ('vitamin_c', 'VitaminC', '항산화|콜라겐 형성|면역 기능', '설사(과량)|복통(과량)'),
    ('vitamin_d', 'VitaminD', '칼슘 흡수|뼈 유지|면역 기능', '고칼슘혈증(과량)'),
    ('vitamin_e', 'VitaminE', '항산화|세포 보호', '출혈 위험(고용량)|항응고제 병용 주의'),
    ('vitamin_a', 'VitaminA', '시각 기능|면역 기능', '간 손상(레티놀 과량)|임신 중 레티놀 과량 주의'),
    ('magnesium', 'Magnesium', '근육 기능|신경 기능|에너지 대사', '설사|신장질환 주의'),
    ('calcium', 'Calcium', '뼈·치아 유지|근육 기능', '변비|복부 팽만'),
    ('potassium', 'Potassium', '신경 전달|근육 기능', '고칼륨혈증(신장질환·과량)'),
    ('zinc', 'Zinc', '면역 기능|상처 회복', '메스꺼움|구리 결핍(과량)'),
    ('epa', 'Omega3FattyAcids', '세포막 구성', '속쓰림|위장 불편|고용량·항응고제 주의'),
    ('dha', 'Omega3FattyAcids', '뇌·망막 구성', '속쓰림|위장 불편|고용량·항응고제 주의'),
    ('epa_dha', 'Omega3FattyAcids', '세포막 구성|중성지질 관리(용량별)', '속쓰림|위장 불편|고용량·항응고제 주의'),
    ('omega3_total', 'Omega3FattyAcids', '세포막 구성|오메가3 공급', '속쓰림|위장 불편|고용량·항응고제 주의'),
    ('fish_oil', 'Omega3FattyAcids', '오메가3 공급', '비린 맛|속쓰림|고용량·항응고제 주의'),
    ('krill_oil', 'Omega3FattyAcids', '오메가3 공급', '위장 불편|고용량·항응고제 주의'),
    ('probiotics', 'Probiotics', '미생물 균형(균주별)', '가스|중증·면역저하 시 감염 주의'),
]:
    PROFILES[key] = profile(effects, cautions, ODS.format(slug))

PROFILES['biotin']['educationNote'] = '결핍이 없는 사람의 모발·손톱 개선 근거는 제한적입니다. 검사 전 의료진에게 섭취 사실을 알리세요.'
PROFILES['vitamin_b12']['educationNote'] = '충분히 섭취하는 사람에게 추가적인 활력·운동능력 향상이 입증된 것은 아닙니다.'
PROFILES['probiotics']['educationNote'] = '효과는 균주·용량·사용 목적별로 다릅니다. 모든 제품에 장·질·구강 효과가 공통으로 입증된 것은 아닙니다.'
for key in ('lutein', 'zeaxanthin', 'lutein_esters', 'zeaxanthin_isomers'):
    PROFILES[key] = profile('황반 색소|빛 여과', '고용량·장기복용 확인', NEI,
        '루테인·제아잔틴 계열의 역할입니다. 형태별 근거와 함량은 다릅니다. AREDS2 결과는 특정 환자·복합제 연구이며 일반인의 질환 예방 효과가 아닙니다.')

PROFILES.update({
    'alpha_lipoic_acid': profile('항산화|에너지 대사', '메스꺼움|저혈당',
        'https://www.mskcc.org/cancer-care/integrative-medicine/herbs/alpha-lipoic-acid'),
    'inositol': profile('세포 신호 전달', '메스꺼움|가스|설사',
        'https://my.clevelandclinic.org/health/drugs/25173-inositol', '생리적 역할과 보충제의 임상 효과는 다릅니다.'),
    'paba': profile('효과 근거 제한', '알레르기|구토(과량)',
        'https://www.medlineplus.gov/ency/article/002518.htm',
        '필수 비타민이 아닙니다. 자외선차단제 성분의 역할을 먹는 보충제의 효과로 옮기지 않습니다.', 'limited_evidence'),
    'bilberry_extract': profile('효과 근거 제한', '고함량 안전성 자료 제한',
        'https://www.nccih.nih.gov/health/bilberry', '눈 건강 개선 효과를 확정할 근거가 부족합니다.', 'limited_evidence'),
    'black_pepper_extract': profile('흡수 보조(성분별)', '약물 상호작용',
        'https://www.bfr.bund.de/en/service/frequently-asked-questions/topic/benefits-and-risks-of-micronutrient-supplements-in-older-age/',
        '피페린은 함께 섭취한 일부 물질의 이용률에 영향을 줍니다. 흡수 증가가 항상 이득은 아닙니다.'),
    'sodium': profile('체액 균형|신경·근육 기능', '혈압 상승(과량)',
        'https://www.medlineplus.gov/ency/article/002415.htm'),
    'xylooligosaccharides': profile('유익균 먹이', '장기 안전성 자료 제한',
        'https://pubmed.ncbi.nlm.nih.gov/24513849/', '소규모 단기 연구에서 비피더스균 증가. 질환 치료 효과나 장기 안전성 확정은 아닙니다.', 'clinical_research'),
    'saffron_extract': profile('효과 근거 제한', '메스꺼움|두통',
        'https://pmc.ncbi.nlm.nih.gov/articles/PMC5339650/', '제품에 든 용량의 눈 건강·기분 개선 효과를 확정하지 않습니다.', 'limited_evidence'),
    'astaxanthin': profile('효과 근거 제한', '연령·총섭취량 확인',
        'https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2020.5993',
        '성인 용량 안전성 평가를 어린이 적합성이나 임상 효능 근거로 사용하지 않습니다.', 'limited_evidence'),
})

# Explicitly reviewed limitations, not invented clinical effects from plant names.
for key in ('acerola', 'rose_hips', 'rutin', 'citrus_bioflavonoids', 'taurine',
            'phospholipids', 'macuguard_blend', 'alpha_carotene', 'ascorbyl_palmitate'):
    PROFILES[key] = profile('효과 근거 제한', '안전성 개별 확인', SAFETY,
        '이 원료·형태·용량의 보충 효과와 부작용을 확정할 개별 자료는 이번 검토에 충분하지 않습니다. '
        '복합물의 하위 성분은 각각의 설명을 참고하세요. 자료 부족은 효과 없음·안전함을 뜻하지 않습니다.', 'limited_evidence')

PROFILES['alpha_carotene'] = profile('비타민 A 전구체', '고함량 안전성 개별 확인',
    'https://ods.od.nih.gov/factsheets/VitaminA-HealthProfessional/',
    '체내에서 일부가 비타민 A로 전환됩니다. 레티놀·베타카로틴의 고용량 위험을 그대로 적용하지 않습니다.')
PROFILES['taurine'] = profile('담즙산 대사|체액 균형', '장기 보충 안전성 확인',
    'https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/expert-answers/taurine/faq-20058177',
    '체내 생리적 역할입니다. 보충제의 피로 회복·활력 향상을 보장하지 않습니다.')
PROFILES['ascorbyl_palmitate'] = profile('비타민 C 공급', '총 비타민 C 섭취량 확인',
    'https://dsld.od.nih.gov/ingredient/Vitamin%2BC',
    '비타민 C의 한 형태입니다. 원료 중량 전체를 비타민 C 함량으로 계산하지 않습니다. '
    '라벨 데이터베이스는 임상 효능 보증이 아닙니다.')
PROFILES['ascorbyl_palmitate']['educationSources'].append(ODS.format('VitaminC'))


def ingredient_education(key):
    return deepcopy(PROFILES.get(key, profile('효과 근거 제한', '안전성 개별 확인', SAFETY,
        '아직 성분별 검토 전입니다.', 'not_reviewed')))


def audience_for(facts, listing):
    """Interests derived from composition; never a child/pregnancy eligibility claim."""
    keys = {f['key'] for f in facts if f.get('amount') is None or f['amount'] > 0}
    targets = []
    if keys & {'lutein', 'lutein_esters', 'zeaxanthin', 'zeaxanthin_isomers'}:
        targets.append('눈 건강 성분을 비교하는 분')
    if keys & {'fish_oil', 'krill_oil', 'epa', 'dha', 'epa_dha', 'omega3_total'}:
        targets.append('오메가3 섭취를 점검하는 분')
    if 'probiotics' in keys:
        name = listing['product'].lower()
        if any(word in name for word in ('oral', '구강', '오랄')):
            targets.append('구강용 유산균을 비교하는 분')
        elif any(word in name for word in ('women', '여성', 'fem', '우먼', '펨 도필루스')):
            targets.append('여성용 유산균을 비교하는 분')
        else:
            targets.append('균주별 유산균을 비교하는 분')
    bkeys = {k for k in keys if k.startswith('vitamin_b')} | (keys & {'biotin', 'folate'})
    if len(bkeys) >= 3:
        targets.append('B군 섭취를 점검하는 분')
    elif 'vitamin_b12' in keys:
        targets.append('B12 섭취를 점검하는 분')
    for key, label in [('magnesium', '마그네슘'), ('vitamin_c', '비타민 C'),
                       ('vitamin_d', '비타민 D'), ('calcium', '칼슘'), ('zinc', '아연')]:
        if key in keys:
            targets.append(f'{label} 섭취를 점검하는 분')
    return targets[:4] or ['표시 성분과 섭취량을 비교하는 분']
