import unittest
from collections import Counter

from products.models import validate_evidence
from products.presenter import product_view
from seed_c_mg_probiotics import PRODUCTS, build


class ReviewedBatchTests(unittest.TestCase):
    def test_thirty_distinct_and_supported(self):
        self.assertEqual(Counter(p['k'][0] for p in PRODUCTS), {'c':10,'m':10,'p':10})
        self.assertEqual(len({p['key'] for p in PRODUCTS}),30)
        for p in PRODUCTS:
            listing,analysis,sources,provenance=build(p)
            validate_evidence(analysis,sources)
            view=product_view(dict(listing=listing,analysis=analysis.model_dump(),sources=[s.model_dump() for s in sources],provenance=provenance))
            self.assertIn({'c':'vitamin-c','m':'magnesium','p':'probiotics'}[p['k'][0]],view['categoryIds'])
            self.assertIsNone(view['pillSizeMm'])
            self.assertTrue(listing['image'].startswith('https://'))
            self.assertFalse(listing['product'].startswith(analysis.brand.value+' '))
            if p['k'][0]=='p':
                self.assertEqual(view['ingredientFacts'][0]['unit'],'CFU')
                self.assertIsNone(view['ingredientFacts'][0]['amountMgPerServing'])
                self.assertTrue(analysis.ingredients[0].form)

    def test_dose_not_compound_or_package_weight(self):
        rows={p['k']:build(p)[1] for p in PRODUCTS}
        self.assertEqual(rows['m5'].ingredients[0].amount,113)
        self.assertEqual(rows['m7'].ingredients[0].amount,144)
        self.assertEqual(rows['m6'].unitsPerServing.value,3)
        self.assertEqual(rows['p9'].unitsPerServing.value,2)
        self.assertEqual(rows['p9'].ingredients[0].amount,10_000_000_000)
        self.assertIsNone(rows['c4'].unitsPerServing)
        self.assertIsNone(rows['c6'].unitsPerServing)
        self.assertEqual(rows['c2'].ingredients[2].amount,15)
        self.assertTrue(any(w.value=='냉장 보관' for w in rows['p3'].warnings))


if __name__=='__main__':
    unittest.main()
