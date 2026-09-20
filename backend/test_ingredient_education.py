import copy
import unittest
from pathlib import Path

from products import store
from products.ingredient_education import PROFILES, audience_for, ingredient_education
from products.presenter import product_view
from products.matching import classify


class IngredientEducationTests(unittest.TestCase):
    def test_published_catalogue_coverage_and_unchanged_claims(self):
        records = store.published(Path(__file__).with_name('data') / 'products.sqlite3')
        self.assertGreaterEqual(len(records), 106)
        for record in records:
            before = copy.deepcopy(record)
            view = product_view(record)
            self.assertTrue(view['for'], view['id'])
            self.assertEqual(view['claims'], record['analysis']['claims'])
            for fact in view['ingredientFacts']:
                self.assertIn(fact['key'], PROFILES)
                self.assertNotEqual(fact['educationBasis'], 'not_reviewed')
                for field in ('effects', 'sideEffects', 'educationSources'):
                    self.assertTrue(fact[field], (view['id'], fact['key'], field))
                self.assertNotIn('미확인', fact['effects'] + fact['sideEffects'])
            for bubble in view['ingredients']:
                self.assertTrue(bubble['effects'])
                self.assertTrue(bubble['sideEffects'])
            # Educational copy must never create additional matching eligibility.
            stripped = copy.deepcopy(view)
            for fact in stripped['ingredientFacts']:
                for field in ingredient_education(fact['key']):
                    fact.pop(field, None)
            a, b = classify(view, record), classify(stripped, record)
            self.assertEqual(a['effectIds'], b['effectIds'])
            self.assertEqual(a['ageIds'], b['ageIds'])
            self.assertEqual(record, before)

    def test_keyword_limits_and_evidence(self):
        for key, row in PROFILES.items():
            for text in row['effects'] + row['sideEffects']:
                self.assertLessEqual(len(text), 25, (key, text))
            self.assertTrue(all(url.startswith('https://') for url in row['educationSources']))

    def test_limited_evidence_and_cautions_are_not_promises(self):
        self.assertEqual(ingredient_education('paba')['effects'], ['효과 근거 제한'])
        self.assertIn('검사결과 간섭', ingredient_education('biotin')['sideEffects'])
        self.assertIn('니코틴산형', ' '.join(ingredient_education('vitamin_b3')['sideEffects']))
        self.assertNotIn('피로 회복', ingredient_education('vitamin_b12')['effects'])
        self.assertEqual(ingredient_education('unknown_future_key')['educationBasis'], 'not_reviewed')
        mutated = ingredient_education('biotin')
        mutated['effects'].clear()
        self.assertTrue(ingredient_education('biotin')['effects'])

    def test_audience_is_composition_specific_not_age_approval(self):
        facts = [{'key': 'probiotics', 'amount': 1}]
        self.assertIn('구강용', audience_for(facts, {'product': '오랄바이오틱'})[0])
        self.assertIn('여성용', audience_for(facts, {'product': '펨 도필루스 10억'})[0])
        self.assertIn('균주별', audience_for(facts, {'product': '프로바이오틱-10'})[0])
        combined = audience_for([{'key': 'lutein'}, {'key': 'dha'}, {'key': 'vitamin_c'}], {'product': '복합제'})
        self.assertEqual(len(combined), 3)
        self.assertFalse(any('어린이' in s or '임산부' in s for s in combined))


if __name__ == '__main__':
    unittest.main()
