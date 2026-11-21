import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.product = json.loads((ROOT / 'examples' / 'product.json').read_text(encoding='utf-8'))

    def test_demo_is_auditable_and_requires_review(self):
        result = workflow.run(self.product)['result']
        self.assertEqual(result['review']['status'], 'needs_human_review')
        self.assertIn('承重数据未提供', result['missing_information'])
        self.assertEqual(result['selling_points'][0]['evidence_ids'], ['F3'])

    def test_unknown_evidence_is_rejected(self):
        result = workflow.demo_response(self.product)
        result['selling_points'][0]['evidence_ids'] = ['MISSING']
        with self.assertRaisesRegex(workflow.WorkflowError, 'unknown facts'):
            workflow.validate_output(result, workflow.validate_product(self.product), [])

    def test_risky_terms_flag_but_never_approve(self):
        result = workflow.demo_response(self.product)
        result['title'] = '绝对最好收纳盒'
        result = workflow.validate_output(result, workflow.validate_product(self.product), [])
        self.assertEqual(result['review']['risk_terms_found'], ['绝对', '最好'])
        self.assertEqual(result['review']['status'], 'needs_human_review')

    def test_invalid_input_and_duplicate_ids_rejected(self):
        self.product['facts'][1]['id'] = self.product['facts'][0]['id']
        with self.assertRaisesRegex(workflow.WorkflowError, 'duplicate'):
            workflow.validate_product(self.product)
        with self.assertRaisesRegex(workflow.WorkflowError, 'product'):
            workflow.validate_product([])

    def test_demo_does_not_pretend_to_generate_for_custom_input(self):
        self.product['product_name'] = '其他商品'
        with self.assertRaisesRegex(workflow.WorkflowError, 'bundled example'):
            workflow.run(self.product)

    def test_live_mode_calls_model_and_preserves_known_missing(self):
        model_output = workflow.demo_response(self.product)
        env = {'LLM_API_URL': 'https://example.com/v1/chat/completions', 'LLM_API_KEY': 'test', 'LLM_MODEL': 'test'}
        with patch.dict('os.environ', env), patch('workflow.request_model', return_value=model_output) as call:
            result = workflow.run(self.product, 'live')
        call.assert_called_once()
        self.assertEqual(result['mode'], 'live')
        self.assertIn('承重数据未提供', result['result']['missing_information'])

    def test_missing_live_config(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(workflow.WorkflowError, 'requires'):
                workflow.run(self.product, 'live')


if __name__ == '__main__':
    unittest.main()
