"""Saved-product comparison candidates, never a regimen or efficacy ranking."""
from products.age_guidance import age_guidance
from products.taxonomy import LABELS


def recommend_products(products, age, goals, gender=None):
    goals=list(dict.fromkeys(goals))
    candidates=[]
    adult=age in ('20s','30s-40s','50s-60s','70-plus')
    gender_only=age is None and not goals and gender is not None
    for p in products:
        if gender_only or (age is None and not goals):
            continue
        if p.get('analysisStatus')=='example':
            continue
        if age is not None and not adult and (age not in p.get('ageIds',[]) or p.get('selectionCautions')):
            continue
        if age in p.get('excludedAgeIds',[]):
            continue
        matched=[g for g in goals if g in p.get('effectIds',[])]
        if matched or (not goals and age in p.get('ageIds',[])):
            needs_review=not p.get('adultLabelEvidence') if adult else age is None
            needs_review=needs_review or bool(p.get('selectionCautions'))
            candidates.append((p,matched,needs_review))
    total=len(candidates)
    picks=[]
    selected_types=set()
    while candidates and len(picks)<3:
        candidates.sort(key=lambda pair:(pair[2],-len(pair[1]),
            not any(a.get('ageEvidenceUrl') for a in pair[0].get('ageMatches',[]) if a['id']==age),
            pair[0]['categoryId'] in selected_types,pair[0]['id']))
        p,matched,needs_review=candidates.pop(0)
        selected_types.add(p['categoryId'])
        picks.append(dict(id=p['id'],name=p['brand']+' '+p['product'],image=p['image'],
            link='detail.html?id='+p['id'],categoryId=p['categoryId'],matchedGoals=matched,
            reasons=[m for m in p.get('effectMatches',[]) if m['id'] in matched],
            serving=p.get('serving'),warnings=p.get('warnings',[]),unknowns=p.get('unknowns',[]),
            ageReasons=[a for a in p.get('ageMatches',[]) if a['id']==age],
            reviewRequired=needs_review,
            eligibilityLabel='추가 확인 필요 · 복용 추천 아님' if needs_review else '성인용 표시 확인 · 비교 후보',
            reviewNotes=([dict(text='연령 미선택: 성분·목적 관련성만 표시하며 본인 연령의 섭취 적합성은 확인하지 않았습니다.')] if age is None else [])+([dict(text='대상 연령 표시 미확인: 실제 제품 라벨·전문가 확인 전 복용 여부를 판단할 수 없습니다.')] if adult and not p.get('adultLabelEvidence') else [])+p.get('selectionCautions',[])))
    covered={g for p in picks for g in p['matchedGoals']}
    return dict(received=True,version=2,policyVersion=3,items=picks,totalCandidates=total,
        selections=dict(age=age,goals=goals,gender=gender),
        unmatchedGoals=[dict(id=g,label=LABELS[g]) for g in goals if g not in covered],
        ageGuidance=age_guidance(age),status='matched' if picks else 'no_verified_match',
        message='성별만으로 연결된 제품 태그는 아직 없습니다. AGE 또는 GOAL을 선택하면 해당 제품을 확인할 수 있습니다.' if gender_only else ('목적 관련 제품을 비교용으로 표시합니다. 추가 확인 필요 항목은 복용 추천이 아닙니다. 함께 복용하라는 조합도 아닙니다.' if picks else '해당 조건으로 표시할 제품이 없습니다. 어린이·청소년 보호 조건과 효과 근거 조건은 유지합니다.'),
        notices=['성인용 표시 확인 후보를 먼저 표시하고, 그 안에서 목적 일치·연령별 영양 근거를 반영합니다. 효능·안전성 순위가 아닙니다.',
                 '연령은 검토된 연결 기준에만 사용합니다. 성별 선택으로 신체 특성·임신 여부·영양 필요를 추정하지 않아 성별은 분류에 사용하지 않습니다.',
                 '복용약·질환·알레르기·임신/수유·다른 영양제와의 중복은 확인하지 못했습니다. 복용 여부와 용량은 전문가 및 실제 라벨을 확인하세요.',
                 '근거 없는 복용 시간이나 용량을 생성하지 않습니다.'])
