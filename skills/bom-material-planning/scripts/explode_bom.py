#!/usr/bin/env python3
"""Expand an explicitly supplied BOM; produce auditable JSON on stdout or in a file."""
import argparse
from collections import defaultdict
from decimal import Decimal, InvalidOperation
import json
import sys
from pathlib import Path


def number(value, label, *, positive=False):
    if isinstance(value, bool):
        raise ValueError(f'{label} must be a decimal')
    try:
        n = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f'{label} must be a decimal') from None
    if not n.is_finite() or n < 0 or (positive and n == 0):
        raise ValueError(f'{label} must be finite and {"positive" if positive else "nonnegative"}')
    return n


def calc(data):
    materials = {}
    for item in data['materials']:
        code, unit = item['code'], item['unit']
        if not isinstance(code, str) or not code.strip() or not isinstance(unit, str) or not unit.strip():
            raise ValueError('material code and unit must be nonempty strings')
        if code in materials:
            raise ValueError(f'duplicate material: {code}')
        materials[code] = {'code': code, 'name': item.get('name', code), 'unit': unit}
    root = data['root']
    if root not in materials:
        raise ValueError(f'unknown root: {root}')
    target = number(data['quantity'], 'quantity', positive=True)
    children, edges = defaultdict(list), set()
    for row in data['bom']:
        parent, child = row['parent'], row['child']
        if parent not in materials or child not in materials:
            raise ValueError(f'unknown material in edge: {parent} -> {child}')
        if (parent, child) in edges:
            raise ValueError(f'duplicate edge: {parent} -> {child}')
        edges.add((parent, child))
        children[parent].append((child, number(row['quantity'], 'edge quantity', positive=True), number(row['loss_rate'], 'loss_rate')))
    if not children[root]:
        raise ValueError('root has no BOM children; supply a complete BOM')
    paths, totals = [], defaultdict(Decimal)

    def walk(code, qty, path):
        if code in path:
            raise ValueError('BOM cycle: ' + ' -> '.join(path + [code]))
        new_path = path + [code]
        if not children[code]:
            totals[code] += qty
            paths.append({'path': new_path, 'material': code, 'quantity': str(qty), 'unit': materials[code]['unit']})
            return
        for child, usage, loss in children[code]:
            walk(child, qty * usage * (Decimal(1) + loss), new_path)

    walk(root, target, [])
    return {'root': root, 'production_quantity': str(target), 'formula': 'parent_quantity * usage * (1 + loss_rate)',
            'demand': [{**materials[c], 'quantity': str(totals[c])} for c in sorted(totals)], 'paths': paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = calc(json.loads(args.input.read_text(encoding='utf-8')))
        text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            args.output.write_text(text, encoding='utf-8')
        else:
            sys.stdout.write(text)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'Input error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
