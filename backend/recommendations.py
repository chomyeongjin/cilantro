"""Rule-based supplement picks for /api/recommendations.

No ML/AI and no user profiling — each wellness goal just maps to a fixed
set of candidate supplements from the same 6-item "type" taxonomy products.js
uses (Omega-3 / vitamin B / vitamin C / magnesium / probiotics / lutein).
Age/gender aren't used to rank picks yet: there's no evidence-backed rule
for that here, and inventing one would contradict the "no fake
personalization" stance the rest of this app follows (see README).
"""

SUPPLEMENTS = {
    'omega3': {
        'name': 'omega-3',
        'description': '혈행과 두뇌 건강에 도움을 줘요. 기름 성분이라 식사와 함께 먹으면 흡수가 잘 돼요.',
        'timing': '식사 직후, 낮 12~1시',
        'goals': ['eye-health', 'skin-health', 'sleep-stress'],
    },
    'vitamin-b': {
        'name': 'vitamin B',
        'description': '탄수화물을 에너지로 바꾸는 걸 도와줘요. 아침에 먹으면 하루를 활기차게 시작할 수 있어요.',
        'timing': '아침 식사 후, 7~8시',
        'goals': ['energy-vitality'],
    },
    'vitamin-c': {
        'name': 'vitamin c',
        'description': '피부와 면역력에 도움을 주는 항산화 성분이에요. 아침에 챙겨 먹으면 좋아요.',
        'timing': '아침, 7~8시',
        'goals': ['immunity', 'skin-health'],
    },
    'magnesium': {
        'name': 'magnesium',
        'description': '근육과 신경을 편안하게 이완시켜줘요. 자기 전에 먹으면 숙면에 도움이 돼요.',
        'timing': '취침 전, 밤 21~22시',
        'goals': ['sleep-stress', 'digestive-health'],
    },
    'probiotics': {
        'name': 'probiotics',
        'description': '장 건강에 도움을 주는 유익균이에요. 빈속인 아침에 먹으면 더 효과적이에요.',
        'timing': '공복, 아침 7~8시',
        'goals': ['digestive-health', 'immunity'],
    },
    'lutein': {
        'name': 'lutein',
        'description': '눈의 망막을 지켜주는 성분이에요. 아침 식사와 함께 챙겨 먹으면 좋아요.',
        'timing': '아침 식사와 함께, 7~8시',
        'goals': ['eye-health'],
    },
}

# Used both as the no-goals-selected fallback and as the tiebreaker order
# when several supplements match the same number of goals.
DEFAULT_ORDER = ['magnesium', 'omega3', 'probiotics', 'vitamin-c', 'lutein', 'vitamin-b']

PICK_COUNT = 3


def pick_recommendations(goals):
    goal_set = set(goals or [])
    scores = {sid: sum(1 for g in info['goals'] if g in goal_set)
              for sid, info in SUPPLEMENTS.items()}

    if not any(scores.values()):
        picked = DEFAULT_ORDER[:PICK_COUNT]
    else:
        ranked = sorted(SUPPLEMENTS, key=lambda sid: (-scores[sid], DEFAULT_ORDER.index(sid)))
        picked = ranked[:PICK_COUNT]

    return [
        {
            'id': sid,
            'name': SUPPLEMENTS[sid]['name'],
            'timing': SUPPLEMENTS[sid]['timing'],
            'description': SUPPLEMENTS[sid]['description'],
            'link': f'category.html?id={sid}',
        }
        for sid in picked
    ]
