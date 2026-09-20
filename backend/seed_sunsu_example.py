"""Load the user-supplied label as an explicitly marked example, without AI calls."""
from products import store
from products.models import Analysis, Source

PRODUCT_ID = 'manual-sunsu-rtg-omega3-vitamin-d-60x3-example'
URL = 'https://www.coupang.com/vp/products/1388355334?itemId=23973317495&vendorItemId=91766616313'
NOTE = ('사용자 제공 사진·성분표로 만든 예시입니다. 사진과 라벨은 1캡슐 1,018mg이며, '
        '판매 상품명의 1,000mg 표기와 차이가 있습니다. 제조사 원문 대조 전입니다.')
TEXT = '''사용자 제공 상품명: 순수식품 rTG 오메가3 비타민D 1000mg, 60정, 3개
사용자 제공 브랜드: 순수식품
첨부 라벨 전사:
내용량 1,018 mg X 60 캡슐(61.08 g)
1일 1회, 1회 1캡슐을 물과 함께 섭취하십시오.
1일 섭취량: 1캡슐(1,018 mg)
EPA와 DHA의 합 600 mg
비타민A 210 μg RAE(30%)
비타민D 100 μg(1,000%)
비타민E 3.3 mg α-TE(30%)
EPA및DHA함유유지 혈중 중성지질 개선·혈행 개선·건조한 눈을 개선하여 눈 건강에 도움을 줄 수 있음
비타민A 어두운 곳에서 시각 적응을 위해 필요 피부와 점막을 형성하고 기능을 유지하는데 필요 상피세포의 성장과 발달에 필요
비타민D 칼슘과 인이 흡수되고 이용되는데 필요 뼈의 형성과 유지에 필요 골다공증발생 위험 감소에 도움을 줌
비타민E 항산화 작용을 하여 유해산소로부터 세포를 보호하는데 필요
의약품(항응고제, 항혈소판제, 혈압강하제 등) 복용 시 전문가와 상담하십시오.
개인에 따라 피부 관련 이상반응이 발생할 수 있습니다.
고칼슘혈증이 있거나 의약품 복용 시 전문가와 상담하십시오.
이상사례 발생 시 섭취를 중단하고 전문가와 상담하십시오.
땅콩, 대두, 고등어 함유'''


def evidence(quote):
    return {'sourceId': 'user-label', 'quote': quote}


def fact(value, quote=None):
    return {'value': value, 'evidence': evidence(quote or value)}


def main():
    source = Source(id='user-label', kind='label', url=URL,
                    title='사용자 첨부 성분표 전사 (판매 페이지의 동일 버전 확인 전)',
                    text=TEXT, retrievedAt='2026-09-20')
    listing = {'id': PRODUCT_ID, 'product': 'rTG 오메가3 비타민D · 60캡슐 × 3개',
               'productUrl': URL, 'buyLink': URL, 'source': 'manual-manufacturer',
               'image': '/images/sunsu-omega3-example.png',
               'pillImage': '/images/pills/pill1_1.png',
               'raw': {'example': True, 'text': TEXT}, 'discoveredAt': store.now()}
    ingredients = []
    for key, name, amount, unit, quote in [
        ('epa_dha', 'EPA + DHA', 600, 'mg', 'EPA와 DHA의 합 600 mg'),
        ('vitamin_a', '비타민 A', 210, 'mcg RAE', '비타민A 210 μg RAE(30%)'),
        ('vitamin_d', '비타민 D', 100, 'mcg', '비타민D 100 μg(1,000%)'),
        ('vitamin_e', '비타민 E', 3.3, 'mg α-TE', '비타민E 3.3 mg α-TE(30%)'),
    ]:
        ingredients.append({'key': key, 'name': name, 'amount': amount, 'unit': unit,
                            'basis': 'per_serving', 'form': None, 'partOf': None,
                            'evidence': evidence(quote)})
    analysis = Analysis.model_validate({
        'productIdentity': fact('순수식품 rTG 오메가3 비타민D 1000mg, 60정, 3개'),
        'brand': fact('순수식품'),
        'serving': fact('1일 1회, 1회 1캡슐을 물과 함께 섭취하십시오.'),
        'unitsPerServing': fact(1, '1일 섭취량: 1캡슐(1,018 mg)'),
        'dailyServings': fact(1, '1일 1회, 1회 1캡슐을 물과 함께 섭취하십시오.'),
        'totalContentMg': None, 'pillSizeMm': None, 'formulation': None,
        'ingredients': ingredients,
        'claims': [
            {'text': text, 'effectId': effect, 'ingredientKeys': [key], 'evidence': evidence(quote)}
            for key, effect, text, quote in [
                ('epa_dha', 'eye-health', '혈중 중성지질·혈행 개선, 건조한 눈 개선에 도움을 줄 수 있음',
                 'EPA및DHA함유유지 혈중 중성지질 개선·혈행 개선·건조한 눈을 개선하여 눈 건강에 도움을 줄 수 있음'),
                ('vitamin_a', None, '어두운 곳에서 시각 적응, 피부·점막의 기능 유지에 필요',
                 '비타민A 어두운 곳에서 시각 적응을 위해 필요 피부와 점막을 형성하고 기능을 유지하는데 필요 상피세포의 성장과 발달에 필요'),
                ('vitamin_d', 'bone-joint', '칼슘·인 흡수와 이용, 뼈 형성·유지에 필요',
                 '비타민D 칼슘과 인이 흡수되고 이용되는데 필요 뼈의 형성과 유지에 필요 골다공증발생 위험 감소에 도움을 줌'),
                ('vitamin_e', None, '항산화 작용으로 유해산소로부터 세포 보호에 필요',
                 '비타민E 항산화 작용을 하여 유해산소로부터 세포를 보호하는데 필요'),
            ]],
        'audience': [
            fact('혈행 건강을 관리하려는 분', '혈행 개선'),
            fact('눈 건조를 관리하려는 분', '건조한 눈을 개선하여 눈 건강에 도움을 줄 수 있음'),
            fact('뼈 건강을 관리하려는 분', '뼈의 형성과 유지에 필요'),
        ], 'ageGroups': [],
        'warnings': [fact(line) for line in TEXT.splitlines()[-5:]],
        'summary': '라벨 기준 1일 1캡슐(1,018mg). 60캡슐 포장 3개 묶음의 예시 제품입니다.',
        'unknowns': [NOTE, 'EPA와 DHA의 개별 함량 및 알약 크기는 미확인입니다.',
                     'RAE·α-TE는 활성 환산 단위이므로 원료 중량 비율로 환산하지 않았습니다.'],
    })
    store.save_registrations([listing], update_existing=True)
    digest = store.fingerprint(listing, [source], NOTE, 'manual-transcription', 'example-v3', 'manual')
    ident = store.save_draft(listing, analysis, [source],
                            {'example': True, 'exampleNote': NOTE, 'method': 'user_label_transcription',
                             'audienceBasis': 'label_function_goals'},
                            NOTE, digest)
    store.approve(ident, 'user-requested-example; identity-unverified')
    print(f'Example ready: {PRODUCT_ID} (analysis {ident})')


if __name__ == '__main__':
    main()
