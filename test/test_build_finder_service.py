import os
import sys
import unittest
from unittest.mock import MagicMock, patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

import services.cache
from services.build_finder.build_fix_service import BuildFixService
from services.build_finder.questionnaire_service import get_build_recommendation


class BuildFixServiceTestCase(unittest.TestCase):

    def test_fix_build_returns_fixed_when_already_compatible(self):
        parts = [{'category': 'CPU', 'name': 'Test CPU'}]
        report = {'compatible': True, 'status': 'compatible'}

        with patch('services.build_finder.build_fix_service.CompatibilityService.evaluate_build', return_value=report) as mocked_eval:
            result = BuildFixService.fix_build(parts)

        self.assertTrue(result['fixed'])
        self.assertEqual(result['components'], parts)
        self.assertEqual(result['changes'], [])
        self.assertEqual(result['compatibility_report'], report)
        mocked_eval.assert_called_once_with(parts)

    def test_fix_build_returns_false_when_incompatible_and_no_fix_possible(self):
        parts = [
            {'category': 'CPU', 'name': 'Test CPU', 'compatibility': {}, 'specs': {}, 'price': 100},
            {'category': 'PSU', 'name': 'Test PSU', 'price': 50, 'specs': {'wattage': 400}}
        ]
        incompatible_report = {'compatible': False, 'issues': [{'severity': 'critical'}]}

        fake_query = MagicMock()
        fake_query.order_by.return_value = fake_query
        fake_query.filter.return_value = fake_query
        fake_query.limit.return_value = fake_query
        fake_query.all.return_value = []
        fake_query.first.return_value = None

        fake_component = MagicMock()
        fake_component.query = fake_query
        with patch('services.build_finder.build_fix_service.CompatibilityService.evaluate_build', return_value=incompatible_report), \
             patch('services.build_finder.build_fix_service.Component', new=fake_component):
            result = BuildFixService.fix_build(parts)

        self.assertFalse(result['fixed'])
        self.assertEqual(result['components'], parts)
        self.assertIsInstance(result['changes'], list)
        self.assertEqual(result['compatibility_report'], incompatible_report)


class QuestionnaireServiceTestCase(unittest.TestCase):

    def setUp(self):
        services.cache._cache_store.clear()

    def test_get_build_recommendation_returns_issue_when_no_builds(self):
        answers = {'targetTier': 'Gaming', 'budget': 'Normal Cost'}
        with patch('services.build_finder.questionnaire_service._generate_all_candidate_builds', return_value=[]):
            result = get_build_recommendation(answers)

        self.assertEqual(result['component_ids'], [])
        self.assertEqual(result['components'], [])
        self.assertEqual(result['total_price'], 0)
        self.assertIn('Unable to assemble any compatible builds.', result['issues'][0])
        self.assertEqual(result['answers'], answers)

    def test_get_build_recommendation_selects_build_and_returns_metadata(self):
        answers = {'targetTier': 'Gaming', 'budget': 'High Cost', 'platform': 'Team Intel & DDR5 Memory'}
        simple_build = {
            'CPU': {'id': 1, 'name': 'CPU1', 'category': 'CPU', 'brand': 'BrandA', 'specs': {}, 'price': 100, 'performance_score': 20},
            'Motherboard': {'id': 2, 'name': 'MB1', 'category': 'Motherboard', 'brand': 'BrandB', 'specs': {}, 'price': 100, 'performance_score': 10},
            'RAM': {'id': 3, 'name': 'RAM1', 'category': 'RAM', 'brand': 'BrandC', 'specs': {}, 'price': 50, 'performance_score': 5},
            '_total_price': 250,
            '_score': 5,
            '_price_tier': 'high'
        }
        evaluated_report = {'compatible': True, 'status': 'compatible'}

        with patch('services.build_finder.questionnaire_service._generate_all_candidate_builds', return_value=[simple_build]), \
             patch('services.build_finder.questionnaire_service._categorize_builds_by_price', return_value={'low': [], 'normal': [], 'high': [simple_build]}), \
             patch('services.build_finder.questionnaire_service.CompatibilityService.evaluate_build', return_value=evaluated_report), \
             patch('services.build_finder.questionnaire_service.BuildFixService.fix_build', return_value={'fixed': False, 'components': [], 'changes': [], 'compatibility_report': evaluated_report}):
            result = get_build_recommendation(answers)

        self.assertEqual(result['component_ids'], [1, 2, 3])
        self.assertEqual(result['total_price'], 250)
        self.assertEqual(result['scenario'], 'gaming')
        self.assertEqual(result['price_tier'], 'high')
        self.assertEqual(result['all_builds_count'], 1)
        self.assertEqual(result['high_count'], 1)
        self.assertEqual(result['compatibility_report'], evaluated_report)

    def test_get_build_recommendation_uses_fix_when_initial_build_incompatible(self):
        answers = {'targetTier': 'Gaming', 'budget': 'Normal Cost', 'platform': 'No Preference (Optimized Value)'}
        initial_build = {
            'CPU': {'id': 1, 'name': 'CPU1', 'category': 'CPU', 'brand': 'BrandA', 'specs': {}, 'price': 100, 'performance_score': 20},
            '_total_price': 100,
            '_score': 1,
            '_price_tier': 'normal'
        }
        incompatible_report = {'compatible': False, 'status': 'incompatible'}
        fixed_build = [{'id': 1, 'name': 'CPU1', 'category': 'CPU', 'brand': 'BrandA', 'specs': {}, 'price': 100, 'performance_score': 20}]
        fixed_report = {'compatible': True, 'status': 'compatible'}

        with patch('services.build_finder.questionnaire_service._generate_all_candidate_builds', return_value=[initial_build]), \
             patch('services.build_finder.questionnaire_service._categorize_builds_by_price', return_value={'low': [], 'normal': [initial_build], 'high': []}), \
             patch('services.build_finder.questionnaire_service.CompatibilityService.evaluate_build', side_effect=[incompatible_report, fixed_report]), \
             patch('services.build_finder.questionnaire_service.BuildFixService.fix_build', return_value={'fixed': True, 'components': fixed_build, 'changes': [], 'compatibility_report': fixed_report}):
            result = get_build_recommendation(answers)

        self.assertEqual(result['components'], fixed_build)
        self.assertEqual(result['compatibility_report'], fixed_report)
        self.assertEqual(result['component_ids'], [1])


if __name__ == '__main__':
    unittest.main()
