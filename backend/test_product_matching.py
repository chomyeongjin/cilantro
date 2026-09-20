import copy
import unittest

from products.matching import classify, category_notice
from products.presenter import product_view
from seed_c_mg_probiotics import PRODUCTS, build


def record(key):
    p=next(p for p in PRODUCTS if p['k']==key)
    listing,analysis,sources,provenance=build(p)
    return dict(listing=listing,analysis=analysis.model_dump(),sources=[s.model_dump() for s in sources],provenance=provenance)


def view(r):
    return classify(product_view(r),r)


class MatchingTests(unittest.TestCase):
    def test_specific_composition_and_no_mutation(self):
        r=record('c2')
        original=copy.deepcopy(r)
        p=view(r)
        self.assertEqual(r,original)
        self.assertEqual({m['ingredientKeys'][0] for m in p['effectMatches'] if m['id']=='immunity'}, {'vitamin_c','vitamin_d','zinc'})
        self.assertTrue(all(m['sourceUrl'] and m['ingredients'] for m in p['effectMatches']))

    def test_probiotics_not_one_bucket(self):
        self.assertIn('immunity',view(record('p1'))['effectIds'])
        self.assertNotIn('immunity',view(record('p3'))['effectIds'])
        self.assertIn('digestive-health',view(record('p8'))['effectIds'])
        self.assertNotIn('digestive-health',view(record('p10'))['effectIds'])
        self.assertNotIn('immunity',view(record('p10'))['effectIds'])

    def test_reformulation_invalidates_product_specific_review(self):
        r=record('p1')
        r['analysis']['ingredients'][0]['amount']=24_000_000_000
        self.assertNotIn('immunity',view(r)['effectIds'])

    def test_no_sleep_or_child_inference(self):
        for p in PRODUCTS:
            v=view(record(p['k']))
            self.assertNotIn('kids',v['ageIds'])
            self.assertNotIn('teens',v['ageIds'])
            self.assertNotIn('sleep-stress',v['effectIds'])
        self.assertIn('현재 50종',category_notice('kids'))

    def test_adult_label_and_high_dose(self):
        self.assertIn('20s',view(record('m3'))['ageIds'])
        self.assertFalse(view(record('m1'))['ageIds'])
        self.assertTrue(view(record('m1'))['selectionCautions'])
        # Merely keeping a bottle away from children does not establish adult use.
        self.assertFalse(view(record('p1'))['ageIds'])
        self.assertIn('20s',view(record('p9'))['ageIds'])
        self.assertNotIn('70-plus',view(record('p9'))['ageIds'])

    def test_age_evidence_is_not_child_product_approval(self):
        from products.age_guidance import age_guidance
        from seed_vitamin_b_batch import PRODUCTS as B_PRODUCTS, build as build_b
        self.assertEqual(len(age_guidance('kids')['items']),4)
        self.assertTrue(all(i['sourceUrl'].startswith('https://') for i in age_guidance('kids')['items']))
        self.assertIsNone(age_guidance('immunity'))
        p=next(p for p in B_PRODUCTS if p['key']=='now-b12-1000')
        listing,analysis,sources,provenance=build_b(p,5)
        result=view(dict(listing=listing,analysis=analysis.model_dump(),sources=[s.model_dump() for s in sources],provenance=provenance))
        self.assertIn('50s-60s',result['ageIds'])
        self.assertIn('70-plus',result['ageIds'])
        self.assertTrue(result['ageMatches'][-1]['ageEvidenceUrl'])

    def test_unknown_dose_not_eligible_nutrient_function(self):
        r=record('c1')
        r['analysis']['ingredients'][0].update(amount=None,unit=None)
        self.assertNotIn('immunity',view(r)['effectIds'])


if __name__=='__main__':
    unittest.main()
