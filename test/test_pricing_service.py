import os
import sys
import unittest
from unittest.mock import MagicMock, patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from services.pricing.pricing_service import calculate_build_total, get_store_prices, cheapest_build, price_budget_check


class PricingServiceTestCase(unittest.TestCase):

    def test_calculate_build_total_sums_component_prices(self):
        comp1 = MagicMock()
        comp1.id = 1
        comp1.name = 'Part1'
        comp1.category = 'CPU'
        comp1.price = 100
        comp2 = MagicMock()
        comp2.id = 2
        comp2.name = 'Part2'
        comp2.category = 'RAM'
        comp2.price = 50

        query = MagicMock()
        query.filter.return_value.all.return_value = [comp1, comp2]

        fake_component = MagicMock()
        fake_component.query = query
        with patch('services.pricing.pricing_service.Component', new=fake_component):
            result = calculate_build_total([1, 2])

        self.assertEqual(result['total'], 150)
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['breakdown'][0]['name'], 'Part1')

    def test_get_store_prices_returns_cheapest_store_list(self):
        link1 = MagicMock(store_name='StoreA', price=120, url='http://a')
        link2 = MagicMock(store_name='StoreB', price=130, url='http://b')

        query = MagicMock()
        query.filter_by.return_value.order_by.return_value.all.return_value = [link1, link2]

        fake_link = MagicMock()
        fake_link.query = query
        with patch('services.pricing.pricing_service.Link', new=fake_link):
            result = get_store_prices(1)

        self.assertEqual(result['cheapest']['store'], 'StoreA')
        self.assertEqual(len(result['stores']), 2)

    def test_cheapest_build_uses_store_prices_and_fallback(self):
        comp = MagicMock(name='Part1', price=120)
        fake_component = MagicMock()
        fake_component.query.get.return_value = comp
        with patch('services.pricing.pricing_service.get_store_prices', return_value={'cheapest': {'store': 'StoreA', 'price': 120, 'url': 'http://a'}, 'stores': [{'store': 'StoreA', 'price': 120, 'url': 'http://a'}]}), \
             patch('services.pricing.pricing_service.Component', new=fake_component):
            result = cheapest_build([1])

        self.assertEqual(result['total'], 120)
        self.assertEqual(result['breakdown'][0]['store'], 'StoreA')

    def test_price_budget_check_reports_under_and_over(self):
        with patch('services.pricing.pricing_service.calculate_build_total', return_value={'total': 100, 'breakdown': [{'price': 100}], 'count': 1}):
            result_under = price_budget_check([1], 150)
            result_over = price_budget_check([1], 50)

        self.assertTrue(result_under['within_budget'])
        self.assertFalse(result_over['within_budget'])
        self.assertEqual(result_over['difference'], 50)


if __name__ == '__main__':
    unittest.main()
