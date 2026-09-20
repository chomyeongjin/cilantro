"""Stable IDs consumed by the existing products/category/detail frontend."""
OPTIONS = {
    'type': [
        ('omega3', 'Omega-3'), ('vitamin-b', 'vitamin B'), ('vitamin-c', 'vitamin C'),
        ('magnesium', 'magnesium'), ('probiotics', 'probiotics'),
        ('vitamin-d', 'vitamin D'), ('vitamin-e', 'vitamin E'), ('zinc', 'zinc'),
        ('lutein', 'lutein'),
    ],
    'effect': [
        ('immunity', 'Immunity'), ('energy-vitality', 'Energy & Vitality'),
        ('eye-health', 'eye health'), ('digestive-health', 'Digestive health'),
        ('sleep-stress', 'Sleep & Stress'), ('skin-health', 'skin health'),
        ('weight', 'Weight management'), ('bone-joint', 'Bone & Joint'),
    ],
    'age': [('kids', 'Kids'), ('teens', 'Teens'), ('20s', '20s'),
            ('30s-40s', '30s & 40s'), ('50s-60s', '50s & 60s'),
            ('70-plus', '70+')],
}
LABELS = {key: label for group in OPTIONS.values() for key, label in group}
INGREDIENT_TYPES = {
    'epa': 'omega3', 'dha': 'omega3', 'epa_dha': 'omega3', 'ala': 'omega3',
    'omega3_total': 'omega3', 'fish_oil': 'omega3', 'algal_oil': 'omega3',
    'vitamin_b1': 'vitamin-b', 'vitamin_b2': 'vitamin-b', 'vitamin_b3': 'vitamin-b',
    'vitamin_b5': 'vitamin-b', 'vitamin_b6': 'vitamin-b', 'biotin': 'vitamin-b',
    'folate': 'vitamin-b', 'vitamin_b12': 'vitamin-b', 'vitamin_c': 'vitamin-c',
    'magnesium': 'magnesium', 'probiotics': 'probiotics', 'vitamin_d': 'vitamin-d',
    'vitamin_e': 'vitamin-e', 'zinc': 'zinc', 'lutein': 'lutein', 'zeaxanthin': 'lutein',
    'lutein_esters': 'lutein', 'zeaxanthin_isomers': 'lutein',
}
COMPARISON_GUIDES = {
    'omega3': ['1회 섭취 기준 EPA와 DHA', '어유 총량과 EPA·DHA 함량 구분',
               '표시된 TG/rTG/EE 형태', 'EPA·DHA와 ALA 구분'],
    'magnesium': ['원소 마그네슘 함량', '화합물 전체 중량과 구분', '표시된 염 형태'],
    'probiotics': ['표시된 균주', 'CFU 수와 표시 기준 시점', '보관 조건'],
    'vitamin-d': ['D2/D3 형태', '1회 섭취 함량과 단위', '섭취 횟수'],
}


def options(counts=None):
    counts = counts or {}
    return {group: [{'id': key, 'label': label, 'productCount': counts.get(key, 0)}
                    for key, label in entries] for group, entries in OPTIONS.items()}
