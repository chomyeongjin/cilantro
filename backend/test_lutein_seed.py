import json
import tempfile
import unittest
from pathlib import Path

from products import store
from products.matching import classify
from products.presenter import product_view
from seed_catalog_expansion import build, run

DATA = Path(__file__).with_name('data') / 'lutein_review.json'


class LuteinSeedTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads(DATA.read_text(encoding='utf-8'))

    def test_twenty_distinct_formulas_and_evidence(self):
        self.assertEqual(len(self.rows), 20)
        self.assertEqual(len({r['key'] for r in self.rows}), 20)
        formulas = {(r['brand'], tuple(tuple(i) for i in r['ingredients'])) for r in self.rows}
        self.assertEqual(len(formulas), 20)
        for row in self.rows:
            listing, analysis, sources, provenance = build(row)
            record = dict(listing=listing, analysis=analysis.model_dump(),
                          sources=[s.model_dump() for s in sources], provenance=provenance)
            view = classify(product_view(record), record)
            self.assertIn('lutein', view['categoryIds'])
            self.assertIn('eye-health', view['effectIds'])
            self.assertNotIn('kids', view['ageIds'])
            self.assertIsNone(analysis.pillSizeMm)
            self.assertTrue(row['image'].startswith('https://'))
            self.assertIn('coupang.com', row['retail'])
            self.assertEqual(analysis.unitsPerServing.value, 2 if row['reviewKey']=='dbVision' else 1)

    def test_esters_isomers_and_parent_amounts(self):
        rows={r['reviewKey']:r for r in self.rows}
        self.assertEqual(rows['swEst']['ingredients'], [['lutein_esters',20,'mg']])
        self.assertEqual(rows['nb20']['ingredients'][1], ['zeaxanthin',800,'mcg'])
        self.assertIn(['zeaxanthin_isomers',4,'mg','macuguard_blend'],rows['leAsta']['ingredients'])
        self.assertIn(['dha',200,'mg','omega3_total'],rows['dbVision']['ingredients'])

    def test_explicit_publish_and_idempotency(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'products.sqlite3'
            self.assertEqual(run(db,filename=DATA)['ready'],20)
            self.assertEqual(store.published(db),[])
            self.assertEqual(run(db,True,DATA)['added'],20)
            before=store.published(db)
            self.assertEqual(run(db,True,DATA)['skipped'],20)
            self.assertEqual(store.published(db),before)


if __name__=='__main__':
    unittest.main()
