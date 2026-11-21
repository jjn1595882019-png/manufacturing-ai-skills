import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DSL_PATH = ROOT / 'dify' / 'product-listing-workflow.yml'


class DifyDSLTests(unittest.TestCase):
    def setUp(self):
        self.dsl = json.loads(DSL_PATH.read_text(encoding='utf-8'))
        self.nodes = {node['id']: node for node in self.dsl['workflow']['graph']['nodes']}
        self.product = json.loads((ROOT / 'examples' / 'product.json').read_text(encoding='utf-8'))

    def execute_code(self, node_id, **inputs):
        context = {}
        exec(self.nodes[node_id]['data']['code'], context)
        return context['main'](**inputs)

    def test_graph_has_ordered_nodes_and_valid_selectors(self):
        edges = self.dsl['workflow']['graph']['edges']
        self.assertEqual([(e['source'], e['target']) for e in edges],
                         [('start', 'validate'), ('validate', 'llm'), ('llm', 'review'), ('review', 'end')])
        for node in self.nodes.values():
            for item in node['data'].get('variables', []):
                if 'value_selector' in item:
                    self.assertIn(item['value_selector'][0], self.nodes)
        for output in self.nodes['end']['data']['outputs']:
            self.assertIn(output['value_selector'][1], self.nodes['review']['data']['outputs'])

    def test_happy_path_requires_human_review(self):
        product_data = self.execute_code('validate', product_json=json.dumps(self.product, ensure_ascii=False))['product_data']
        draft = {'title': '桌面收纳盒', 'selling_points': [{'text': '三个分区', 'evidence_ids': ['F3']}],
                 'description': {'text': '白色收纳盒', 'evidence_ids': ['F4']}, 'missing_information': []}
        result = self.execute_code('review', product_data=product_data, llm_text=json.dumps(draft, ensure_ascii=False))
        self.assertEqual(json.loads(result['review'])['status'], '待人工审核')
        self.assertIn('承重数据未提供', json.loads(result['draft'])['missing_information'])

    def test_bad_input_and_fake_evidence_are_rejected(self):
        with self.assertRaisesRegex(ValueError, '有效 JSON'):
            self.execute_code('validate', product_json='not json')
        draft = {'title': '收纳盒', 'selling_points': [{'text': '包治', 'evidence_ids': ['F999']}],
                 'description': {'text': '白色', 'evidence_ids': ['F4']}, 'missing_information': []}
        with self.assertRaisesRegex(ValueError, '不存在'):
            self.execute_code('review', product_data=json.dumps(self.product), llm_text=json.dumps(draft))

    def test_risk_word_is_flagged(self):
        draft = {'title': '最好收纳盒', 'selling_points': [],
                 'description': {'text': '白色', 'evidence_ids': ['F4']}, 'missing_information': []}
        result = self.execute_code('review', product_data=json.dumps(self.product), llm_text=json.dumps(draft))
        self.assertEqual(json.loads(result['review'])['risk_terms_found'], ['最好'])


if __name__ == '__main__':
    unittest.main()
