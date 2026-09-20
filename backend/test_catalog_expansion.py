import json
import tempfile
import unittest
from pathlib import Path

from products import store
from products.presenter import product_view
from seed_catalog_expansion import DATA, build, run


class ExpansionTests(unittest.TestCase):
    def test_reviewed_rows_and_categories(self):
        rows=json.loads(DATA.read_text(encoding='utf-8'))
        self.assertEqual(len(rows),36)
        for p in rows:
            listing,analysis,sources,provenance=build(p)
            view=product_view(dict(listing=listing,analysis=analysis.model_dump(),sources=[s.model_dump() for s in sources],provenance=provenance))
            self.assertIn(p['category'],view['categoryIds'])
            self.assertTrue(p['image'].startswith('https://www.nowfoods.com/'))
            self.assertIn('coupang.com',p['retail'])
            self.assertIsNone(view['pillSizeMm'])
            self.assertTrue(all(f['amountPerServing'] is not None for f in view['ingredientFacts']))

    def test_publication_is_explicit_and_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'test.sqlite3'
            self.assertEqual(run(db)['ready'],36)
            self.assertEqual(len(store.published(db)),0)
            self.assertEqual(run(db,True)['added'],36)
            before=store.published(db)
            self.assertEqual(run(db,True)['skipped'],36)
            self.assertEqual(store.published(db),before)

    def test_forms_units_and_parent_relationships(self):
        rows={r['reviewKey']:r for r in json.loads(DATA.read_text(encoding='utf-8'))}
        def analysis(key): return build(rows[key])[1]
        self.assertEqual(analysis('m123').ingredients[0].amount,300)
        self.assertIsNone(analysis('m123').unitsPerServing)
        self.assertEqual(analysis('m129').unitsPerServing.value,3)
        self.assertEqual(analysis('b153').ingredients[0].unit,'mcg DFE')
        self.assertEqual(analysis('b153').ingredients[0].amount,1700)
        self.assertEqual(analysis('p128').ingredients[0].unit,'CFU')
        self.assertEqual(analysis('p128').unitsPerServing.value,2)
        self.assertEqual(analysis('c132').ingredients[0].partOf,'ascorbyl_palmitate')
        self.assertEqual(analysis('o0115').ingredients[0].partOf,'fish_oil')
        self.assertNotIn('digestive-health',[c.effectId for c in analysis('p130').claims])


if __name__=='__main__':
    unittest.main()
