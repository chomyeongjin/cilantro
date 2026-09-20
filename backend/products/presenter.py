"""Conservative deterministic units and the existing frontend response contract."""
from .models import Analysis
from .taxonomy import COMPARISON_GUIDES, INGREDIENT_TYPES, LABELS
from .ingredient_education import ingredient_education, audience_for, NOTICE, FOR_NOTICE

MASS_TO_MG = {'g': 1000, 'mg': 1, 'mcg': 0.001}


def per_serving(ingredient, analysis):
    if ingredient.amount is None:
        return None
    if ingredient.basis == 'per_serving':
        return ingredient.amount
    if ingredient.basis == 'per_unit' and analysis.unitsPerServing:
        return ingredient.amount * analysis.unitsPerServing.value
    if ingredient.basis == 'per_daily' and analysis.dailyServings:
        return ingredient.amount / analysis.dailyServings.value
    return None


def number(value):
    return f'{value:,.6f}'.rstrip('0').rstrip('.')


def product_view(record):
    analysis = Analysis.model_validate(record['analysis'])
    listing = record['listing']
    types = list(dict.fromkeys(INGREDIENT_TYPES[i.key] for i in analysis.ingredients if i.key in INGREDIENT_TYPES))
    # Claim/age classification only appears after explicit review of source statements.
    effects = list(dict.fromkeys(c.effectId for c in analysis.claims if c.effectId))
    ages = list(dict.fromkeys(a.id for a in analysis.ageGroups))
    facts = []
    for ingredient in analysis.ingredients:
        amount = per_serving(ingredient, analysis)
        mg = amount * MASS_TO_MG[ingredient.unit] if amount is not None and ingredient.unit in MASS_TO_MG else None
        facts.append({**ingredient.model_dump(), **ingredient_education(ingredient.key), 'amountPerServing': amount,
                      'amountMgPerServing': mg, 'basisLabel': '표시된 1회 섭취량 기준' if amount is not None else '기준 미확인'})
    by_key = {f['key']: f for f in facts}
    # Reject physically inconsistent known parent/child amounts.
    for fact in facts:
        children = [f for f in facts if f['partOf'] == fact['key'] and f['amountMgPerServing'] is not None]
        if fact['amountMgPerServing'] is not None and sum(f['amountMgPerServing'] for f in children) > fact['amountMgPerServing'] + 1e-6:
            raise ValueError('하위 성분 합계가 표시된 상위 성분 함량보다 큽니다.')

    def mg(key):
        return by_key.get(key, {}).get('amountMgPerServing')

    epa, dha, combined = mg('epa'), mg('dha'), mg('epa_dha')
    if epa is not None and dha is not None:
        derived = epa + dha
        if combined is not None and abs(combined - derived) > 0.01:
            raise ValueError('EPA+DHA 합계와 개별 성분 함량이 일치하지 않습니다.')
        combined = derived
    metrics = {'epaMgPerServing': epa, 'dhaMgPerServing': dha, 'epaDhaMgPerServing': combined,
               'fishOilMgPerServing': mg('fish_oil'), 'alaMgPerServing': mg('ala'),
               'elementalMagnesiumMgPerServing': mg('magnesium'),
               'elementalZincMgPerServing': mg('zinc')}
    if combined is not None:
        for parent in ('omega3_total', 'fish_oil'):
            if mg(parent) is not None and combined > mg(parent) + 0.01:
                raise ValueError('EPA+DHA 함량이 표시된 전체 오일/오메가3 함량보다 큽니다.')

    # No made-up % or NaN in the legacy bubble UI. Only full-formula denominator works.
    bubbles = []
    total = analysis.totalContentMg.value if analysis.totalContentMg else None
    roots = [f for f in facts if not f['partOf'] and f['amountMgPerServing'] is not None and f['amountMgPerServing'] > 0]
    if total is not None:
        if sum(f['amountMgPerServing'] for f in roots) > total + 0.01:
            raise ValueError('성분 합계가 전체 제형 중량을 초과합니다. 포함 관계를 확인하세요.')
        for index, fact in enumerate(sorted(roots, key=lambda f: -f['amountMgPerServing'])[:5], 1):
            bubbles.append({'id': fact['key'], 'name': fact['name'], 'rank': index,
                            'amount': f"{number(fact['amountPerServing'])}{fact['unit']} / 1회",
                            'pct': fact['amountMgPerServing'] / total * 100,
                            'effects': fact['effects'],
                            'sideEffects': fact['sideEffects'], 'evidence': fact['evidence']})

    main_effects = [f'표시 기능성: {c.text}' for c in analysis.claims[:3]]
    if not main_effects:
        main_effects = [f"{f['name']} {number(f['amountPerServing'])}{f['unit']} / 1회"
                        for f in facts if f['amountPerServing'] is not None][:3]
    if not main_effects:
        main_effects = ['성분 함량·기능성 표시 확인 필요']
    return {
        'id': listing['id'], 'brand': analysis.brand.value if analysis.brand else '브랜드 미확인',
        'registrationSource': listing.get('source'), 'productUrl': listing.get('productUrl'),
        'product': listing['product'],
        'image': listing.get('image', '/images/pill_sample.png'),
        'imageKind': listing.get('imageKind', 'user_provided') if listing.get('image') else 'placeholder',
        'pillSizeMm': analysis.pillSizeMm.value if analysis.pillSizeMm else None,
        'pillImage': listing.get('pillImage'),
        'mainEffects': main_effects, 'categoryId': types[0] if types else 'all',
        'categoryLabel': LABELS.get(types[0], '영양제') if types else '영양제',
        'categoryIds': types, 'effectIds': effects, 'ageIds': ages,
        'for': audience_for(facts, listing), 'forBasis': 'composition_interests',
        'labelAudience': [f.value for f in analysis.audience], 'forNote': FOR_NOTICE,
        'ingredientEducationNotice': NOTICE, 'buyLink': listing['buyLink'],
        'ingredients': bubbles, 'ingredientFacts': facts, 'comparison': metrics,
        'serving': analysis.serving.model_dump() if analysis.serving else None,
        'formulation': analysis.formulation.model_dump() if analysis.formulation else None,
        'summary': analysis.summary, 'warnings': [f.model_dump() for f in analysis.warnings],
        'claims': [c.model_dump() for c in analysis.claims], 'claimBasis': 'reviewed_label_statements',
        'unknowns': analysis.unknowns,
        'diagramStatus': 'available' if bubbles else 'full_formula_mass_unavailable',
        'pctBasis': 'full_formula_mass_per_serving' if bubbles else None,
        'analysisStatus': 'example' if record['provenance'].get('example') else 'reviewed',
        'exampleNote': record['provenance'].get('exampleNote'),
        'analysisId': record.get('analysisId'),
        'reviewedAt': record.get('reviewedAt'), 'provenance': record['provenance'],
        'sources': [{k: s[k] for k in ('id', 'kind', 'title', 'url', 'retrievedAt')} for s in record['sources']],
        'comparisonGuide': list(dict.fromkeys(point for kind in types for point in COMPARISON_GUIDES.get(kind, []))),
    }
