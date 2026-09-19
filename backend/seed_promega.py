"""Import the inspected Coupang label; no AI call or inferred pill dimensions."""
from products import store
from products.models import Analysis, Source

PRODUCT_ID = 'coupang-6586372374-14842723746-82081965637'
URL = 'https://www.coupang.com/vp/products/6586372374?itemId=14842723746&vendorItemId=82081965637'
LABEL_URL = 'https://thumbnail.coupangcdn.com/thumbnails/remote/492x492ex/image/retail/images/9109832319521-80522d84-ea7d-4a01-8a12-cc50ec205c12.jpg'
DETAIL_URL = 'https://thumbnail.coupangcdn.com/thumbnails/remote/q89/image/retail/images/280145705613106-72871b71-322b-459f-a5ec-30ab4f5b044f.jpg'
LABEL = '''영양·기능정보 1일 섭취량: 2캡슐(1,308 mg)
[EPA 및 DHA 함유 유지] 혈행 개선·혈중 중성지질 개선·건조한 눈을 개선하여 눈 건강·기억력 개선에 도움을 줄 수 있음
[비타민E] 항산화 작용을 하여 유해산소로부터 세포를 보호하는데 필요
EPA와 DHA의 합 900mg
비타민E 11 mg α-TE(100%)'''
DETAIL = '''종근당건강 프로메가 오메가3 트리플, 60정, 1개
하루 한 번, 소형캡슐 2알
혈행 개선에 도움을 줄 수 있음
기억력 개선에 도움을 줄 수 있음
혈중 중성지질 개선에 도움을 줄 수 있음
건조한 눈을 개선하여 눈 건강에 도움을 줄 수 있음'''
NOTE = '선택 옵션 60정 1개. 쿠팡 상품 갤러리의 영양·기능정보와 상세 이미지를 직접 확인·전사함. 알약 길이와 섭취 주의사항은 확인하지 못함.'


def evidence(quote, source='promega-label'):
    return {'sourceId': source, 'quote': quote}


def fact(value, quote=None, source='promega-label'):
    return {'value': value, 'evidence': evidence(quote or value, source)}


def main():
    sources = [
        Source(id='promega-label', kind='label', url=LABEL_URL,
               title='쿠팡 상품 갤러리 영양·기능정보 이미지 전사', text=LABEL, retrievedAt='2026-09-20'),
        Source(id='promega-detail', kind='label', url=URL,
               title='선택 옵션 상품명 및 판매 상세 이미지 전사', text=DETAIL, retrievedAt='2026-09-20'),
    ]
    listing = {'id': PRODUCT_ID, 'product': '프로메가 오메가3 트리플',
               'productUrl': URL, 'buyLink': URL, 'source': 'manual-manufacturer',
               'image': '/images/promega-omega3-triple.png',
               'pillImage': '/images/pills/pill1_1.png',
               'raw': {'text': LABEL + '\n' + DETAIL, 'detailImageUrl': DETAIL_URL},
               'discoveredAt': store.now()}
    ingredients = [
        {'key': key, 'name': name, 'amount': amount, 'unit': unit,
         'basis': 'per_serving', 'form': None, 'partOf': None, 'evidence': evidence(quote)}
        for key, name, amount, unit, quote in [
            ('epa_dha', 'EPA + DHA', 900, 'mg', 'EPA와 DHA의 합 900mg'),
            ('vitamin_e', '비타민 E', 11, 'mg α-TE', '비타민E 11 mg α-TE(100%)'),
        ]]
    analysis = Analysis.model_validate({
        'productIdentity': fact('종근당건강 프로메가 오메가3 트리플, 60정, 1개', source='promega-detail'),
        'brand': fact('종근당건강', source='promega-detail'),
        'serving': fact('하루 한 번, 소형캡슐 2알', source='promega-detail'),
        'unitsPerServing': fact(2, '1일 섭취량: 2캡슐(1,308 mg)'),
        'dailyServings': fact(1, '하루 한 번, 소형캡슐 2알', 'promega-detail'),
        'totalContentMg': None, 'pillSizeMm': None, 'formulation': None,
        'ingredients': ingredients,
        'claims': [
            {'text': '혈행·중성지질·눈 건조·기억력 개선에 도움을 줄 수 있음',
             'effectId': 'eye-health', 'ingredientKeys': ['epa_dha'],
             'evidence': evidence('혈행 개선·혈중 중성지질 개선·건조한 눈을 개선하여 눈 건강·기억력 개선에 도움을 줄 수 있음')},
            {'text': '항산화 작용으로 유해산소로부터 세포 보호에 필요',
             'effectId': None, 'ingredientKeys': ['vitamin_e'],
             'evidence': evidence('항산화 작용을 하여 유해산소로부터 세포를 보호하는데 필요')},
        ],
        'audience': [fact(value, quote) for value, quote in [
            ('혈행 건강 관리', '혈행 개선'), ('눈 건조 관리', '건조한 눈을 개선'),
            ('기억력 관리', '기억력 개선에 도움을 줄 수 있음'),
        ]],
        'warnings': [], 'ageGroups': [],
        'summary': '1일 2캡슐(1,308mg) 기준 EPA+DHA 900mg, 비타민 E 11mg α-TE. 60캡슐 포장.',
        'unknowns': ['알약 길이 및 섭취 주의사항 미확인. 부작용이 없다는 의미가 아닙니다.',
                     'EPA와 DHA의 개별 함량 미확인.',
                     '캡슐 중량을 내용물 중량으로 간주하지 않았으며, α-TE는 원료 중량으로 환산하지 않았습니다.'],
    })
    store.save_registrations([listing], update_existing=True)
    digest = store.fingerprint(listing, sources, NOTE, 'browser-image-transcription', 'promega-v1', 'manual')
    ident = store.save_draft(listing, analysis, sources,
                            {'method': 'browser_image_transcription', 'detailImageUrl': DETAIL_URL,
                             'audienceBasis': 'label_function_goals', 'limitations': NOTE}, NOTE, digest)
    store.approve(ident, 'label-and-selected-variant-visually-reviewed; incomplete-warnings-and-size')
    print(f'Product ready: {PRODUCT_ID} (analysis {ident})')


if __name__ == '__main__':
    main()
