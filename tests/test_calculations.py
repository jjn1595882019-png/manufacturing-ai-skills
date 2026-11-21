import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bom = load('bom', 'skills/bom-material-planning/scripts/explode_bom.py')
stock = load('stock', 'skills/inventory-shortage-check/scripts/check_shortage.py')


class TestCalculations(unittest.TestCase):
    def setUp(self):
        self.input = json.loads((ROOT / 'examples/bom.json').read_text(encoding='utf-8'))
        self.inventory = json.loads((ROOT / 'examples/inventory.json').read_text(encoding='utf-8'))

    def test_multilevel_loss_and_shared_material(self):
        result = bom.calc(self.input)
        values = {x['code']: x['quantity'] for x in result['demand']}
        self.assertEqual(values, {'M101': '21.00', 'M102': '60'})
        self.assertEqual(len([x for x in result['paths'] if x['material'] == 'M102']), 2)

    def test_cycle_and_unknown_material_rejected(self):
        self.input['bom'].append({'parent': 'A100', 'child': 'P100', 'quantity': '1', 'loss_rate': '0'})
        with self.assertRaisesRegex(ValueError, 'cycle'):
            bom.calc(self.input)
        self.input['bom'][-1]['child'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'unknown material'):
            bom.calc(self.input)

    def test_shortage_and_incoming_dependency(self):
        result = stock.calc(bom.calc(self.input), self.inventory)
        items = {x['code']: x for x in result['items']}
        self.assertEqual(items['M101']['shortage'], '3.00')
        self.assertEqual(items['M102']['status'], 'depends_on_incoming')
        self.assertEqual(items['M102']['shortage_without_incoming'], '20')

    def test_unknown_stock_and_mismatched_unit(self):
        demand = bom.calc(self.input)
        self.inventory['inventory'].pop()
        self.inventory['inventory'][0]['unit'] = 'kg'
        result = stock.calc(demand, self.inventory)['items']
        self.assertTrue(all(x['status'] == 'unknown' and 'shortage' not in x for x in result))

    def test_negative_and_duplicate_values_rejected(self):
        self.inventory['inventory'][0]['on_hand'] = '-1'
        with self.assertRaisesRegex(ValueError, 'nonnegative'):
            stock.calc(bom.calc(self.input), self.inventory)
        self.input['bom'].append(dict(self.input['bom'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate edge'):
            bom.calc(self.input)


if __name__ == '__main__':
    unittest.main()
