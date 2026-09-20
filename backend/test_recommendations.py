import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from recommendations import recommend_products
from products.matching import classify
from products.presenter import product_view
from seed_c_mg_probiotics import PRODUCTS, build


def fixtures():
    result=[]
    for p in PRODUCTS:
        listing,analysis,sources,provenance=build(p)
        r=dict(listing=listing,analysis=analysis.model_dump(),sources=[s.model_dump() for s in sources],provenance=provenance)
        result.append(classify(product_view(r),r))
    return result


class RecommendationTests(unittest.TestCase):
    def test_real_ids_and_intersection(self):
        products=fixtures()
        r=recommend_products(products,'20s',['immunity','skin-health'])
        self.assertTrue(r['items'])
        self.assertLessEqual(len(r['items']),3)
        lookup={p['id']:p for p in products}
        for item in r['items']:
            self.assertIn(item['id'],lookup)
            self.assertTrue(lookup[item['id']]['adultLabelEvidence'] or item['reviewRequired'])
            self.assertTrue(item['matchedGoals'])
            self.assertTrue(item['reasons'])
            self.assertTrue(item['link'].startswith('detail.html?id='))
            self.assertNotIn('timing',item)

    def test_no_padding_or_unsafe_fallback(self):
        p=fixtures()
        for age,goals in [('kids',['immunity']),('teens',['energy-vitality']),('20s',['sleep-stress'])]:
            r=recommend_products(p,age,goals)
            self.assertEqual(r['items'],[])
            self.assertEqual(r['status'],'no_verified_match')
        self.assertTrue(recommend_products(p,'20s',[])['items'])

    def test_older_adults_not_restricted_to_b12(self):
        p=fixtures()
        for age in ('50s-60s','70-plus'):
            self.assertTrue(recommend_products(p,age,['immunity'])['items'])
            self.assertTrue(recommend_products(p,age,['digestive-health'])['items'])

    def test_unknown_age_and_cautions_are_visible_not_silent_approval(self):
        p=fixtures()
        unknown=next(x for x in p if x['id']=='manual-solgar-c1000-capsules')
        result=recommend_products([unknown],'70-plus',['immunity'])['items'][0]
        self.assertTrue(result['reviewRequired'])
        self.assertTrue(result['reviewNotes'])
        high=next(x for x in p if x['id']=='manual-now-magnesium400')
        result=recommend_products([high],'20s',['energy-vitality'])['items'][0]
        self.assertTrue(result['reviewRequired'])
        self.assertTrue(any('350mg' in n['text'] for n in result['reviewNotes']))
        high['excludedAgeIds']=['20s']
        self.assertEqual(recommend_products([high],'20s',['energy-vitality'])['items'],[])

    def test_gender_no_invented_profile_and_dedup(self):
        p=fixtures()
        a=recommend_products(p,'20s',['immunity','immunity'],'female')
        b=recommend_products(p,'20s',['immunity'],'male')
        self.assertEqual(a['items'],b['items'])
        self.assertEqual(len({x['id'] for x in a['items']}),len(a['items']))

    def test_endpoint_required_inputs_and_empty_state(self):
        c=TestClient(app)
        self.assertEqual(c.post('/api/recommendations',json={}).status_code,422)
        with patch('main.catalogue',return_value=fixtures()):
            for payload in ({'goals':['immunity']},{'age':'20s'},{'gender':'female'}):
                self.assertEqual(c.post('/api/recommendations',json=payload).status_code,200)
            goals_only=c.post('/api/recommendations',json={'goals':['immunity']}).json()
            self.assertTrue(goals_only['items'])
            self.assertTrue(all(i['reviewRequired'] for i in goals_only['items']))
            gender_only=c.post('/api/recommendations',json={'gender':'female'}).json()
            self.assertEqual(gender_only['items'],[])
            self.assertIn('성별만으로',gender_only['message'])
            r=c.post('/api/recommendations',json={'age':'kids','goals':['immunity']})
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.json()['items'],[])
            self.assertTrue(r.json()['ageGuidance'])
