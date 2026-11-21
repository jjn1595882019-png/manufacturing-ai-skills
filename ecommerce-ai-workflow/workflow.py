#!/usr/bin/env python3
"""Product listing workflow with an offline demonstration and optional model call."""
import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
RISK_TERMS = ('绝对', '第一', '最好', '永久', '100%', '包治', '国家级')
TITLE_LIMIT = 30  # Demonstration threshold, not any platform's policy.


class WorkflowError(ValueError):
    pass


def nonempty_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f'{field} must be a nonempty string')
    return value.strip()


def string_list(value, field, *, required=False):
    if not isinstance(value, list) or (required and not value):
        raise WorkflowError(f'{field} must be a {"nonempty " if required else ""}list')
    return [nonempty_text(item, field) for item in value]


def validate_product(product):
    if not isinstance(product, dict):
        raise WorkflowError('product must be a JSON object')
    for field in ('product_name', 'platform', 'audience'):
        nonempty_text(product.get(field), field)
    facts = product.get('facts')
    if not isinstance(facts, list) or not facts:
        raise WorkflowError('facts must be a nonempty list')
    ids = set()
    for item in facts:
        if not isinstance(item, dict):
            raise WorkflowError('each fact must be an object')
        identifier = nonempty_text(item.get('id'), 'fact id')
        nonempty_text(item.get('label'), 'fact label')
        nonempty_text(item.get('value'), 'fact value')
        if identifier in ids:
            raise WorkflowError(f'duplicate fact id: {identifier}')
        ids.add(identifier)
    string_list(product.get('missing_information', []), 'missing_information')
    return ids


def validate_output(result, fact_ids, input_missing):
    if not isinstance(result, dict):
        raise WorkflowError('model output must be a JSON object')
    title = nonempty_text(result.get('title'), 'title')
    points = result.get('selling_points')
    if not isinstance(points, list):
        raise WorkflowError('selling_points must be a list')

    def validate_claim(claim, label):
        if not isinstance(claim, dict):
            raise WorkflowError(f'{label} must be an object')
        nonempty_text(claim.get('text'), f'{label}.text')
        evidence = string_list(claim.get('evidence_ids'), f'{label}.evidence_ids', required=True)
        unknown = set(evidence) - fact_ids
        if unknown:
            raise WorkflowError(f'{label} cites unknown facts: {sorted(unknown)}')

    for point in points:
        validate_claim(point, 'selling_point')
    validate_claim(result.get('description'), 'description')
    missing = string_list(result.get('missing_information'), 'missing_information')
    combined = list(dict.fromkeys(input_missing + missing))
    texts = [title, result['description']['text']] + [p['text'] for p in points]
    found = [term for term in RISK_TERMS if any(term in text for text in texts)]
    return {'title': title, 'selling_points': points, 'description': result['description'],
            'missing_information': combined,
            'review': {'status': 'needs_human_review', 'title_length': len(title),
                       'title_exceeds_demo_limit': len(title) > TITLE_LIMIT,
                       'risk_terms_found': found,
                       'note': '引用 ID 存在不保证文案被事实支持；请人工核对事实、平台规则及全部内容。'}}


def demo_response(product):
    # Offline fixture deliberately restricted to the bundled sample facts.
    expected = json.loads((ROOT / 'examples' / 'product.json').read_text(encoding='utf-8'))
    if product != expected:
        raise WorkflowError('demo mode only supports the bundled example; use live mode for other inputs')
    return {'title': '三分区桌面文具收纳盒',
            'selling_points': [{'text': '三个分区，整理桌面文具', 'evidence_ids': ['F3']},
                               {'text': '白色塑料盒，尺寸约 20 × 10 × 8 厘米', 'evidence_ids': ['F1', 'F2', 'F4']}],
            'description': {'text': '这款白色桌面收纳盒采用塑料材质，设有三个分区，尺寸为长20、宽10、高8厘米。',
                            'evidence_ids': ['F1', 'F2', 'F3', 'F4']},
            'missing_information': []}


def request_model(product, api_url, api_key, model):
    parsed = urlparse(api_url)
    if parsed.scheme != 'https' or not parsed.netloc:
        raise WorkflowError('LLM_API_URL must be a complete HTTPS endpoint')
    system = (ROOT / 'prompts' / 'listing_system.txt').read_text(encoding='utf-8')
    payload = {'model': model, 'messages': [{'role': 'system', 'content': system},
               {'role': 'user', 'content': json.dumps(product, ensure_ascii=False)}], 'temperature': 0.2}
    req = Request(api_url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                  headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + api_key}, method='POST')
    try:
        with urlopen(req, timeout=45) as resp:
            response = json.loads(resp.read().decode('utf-8'))
        content = response['choices'][0]['message']['content']
        return json.loads(content)
    except HTTPError as exc:
        raise WorkflowError(f'model service HTTP error: {exc.code}') from None
    except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise WorkflowError(f'model request or JSON response failed: {type(exc).__name__}') from None


def run(product, mode='demo'):
    ids = validate_product(product)
    if mode == 'demo':
        response = demo_response(product)
    elif mode == 'live':
        config = {key: os.environ.get(key, '').strip() for key in ('LLM_API_URL', 'LLM_API_KEY', 'LLM_MODEL')}
        if not all(config.values()):
            raise WorkflowError('live mode requires LLM_API_URL, LLM_API_KEY and LLM_MODEL environment variables')
        response = request_model(product, config['LLM_API_URL'], config['LLM_API_KEY'], config['LLM_MODEL'])
    else:
        raise WorkflowError(f'unknown mode: {mode}')
    return {'mode': mode, 'product_name': product['product_name'],
            'result': validate_output(response, ids, product.get('missing_information', []))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--mode', choices=('demo', 'live'), default='demo')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        product = json.loads(args.input.read_text(encoding='utf-8'))
        output = json.dumps(run(product, args.mode), ensure_ascii=False, indent=2) + '\n'
        if args.output:
            args.output.write_text(output, encoding='utf-8')
        else:
            sys.stdout.write(output)
    except (OSError, ValueError, TypeError) as exc:
        print(f'Workflow error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
