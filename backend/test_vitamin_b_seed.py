import unittest

from products.models import validate_evidence
from products.presenter import product_view
from seed_vitamin_b_batch import PRODUCTS, build


class VitaminBImportTests(unittest.TestCase):
    def test_ten_distinct_formulas_with_evidence(self):
        self.assertEqual(len({p['key'] for p in PRODUCTS}), 10)
        for index, product in enumerate(PRODUCTS):
            listing, analysis, sources, provenance = build(product, index)
            validate_evidence(analysis, sources)
            view = product_view(dict(listing=listing, analysis=analysis.model_dump(),
                                     sources=[s.model_dump() for s in sources], provenance=provenance))
            self.assertIn('vitamin-b', view['categoryIds'])
            self.assertEqual(view['imageKind'], 'manufacturer')
            self.assertIsNone(view['pillSizeMm'])
            self.assertTrue(view['unknowns'])
            for fact in view['ingredientFacts']:
                if fact['unit'] in ('mcg DFE', 'mg NE'):
                    self.assertIsNone(fact['amountMgPerServing'])

    def test_serving_and_merged_niacin(self):
        self.assertEqual(build(PRODUCTS[8], 8)[1].unitsPerServing.value, 2)
        thorne = build(PRODUCTS[9], 9)[1]
        niacin = next(i for i in thorne.ingredients if i.key == 'vitamin_b3')
        self.assertEqual(niacin.amount, 140)
        self.assertIn('130mg', niacin.evidence.quote)


if __name__ == '__main__':
    unittest.main()
