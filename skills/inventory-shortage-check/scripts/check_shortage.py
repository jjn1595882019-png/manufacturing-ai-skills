#!/usr/bin/env python3
"""Compare demand and inventory using an explicit, auditable simple balance."""
import argparse
from decimal import Decimal, InvalidOperation
import json
import sys
from pathlib import Path


def number(value, label):
    if isinstance(value, bool):
        raise ValueError(f'{label} must be a decimal')
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{label} must be a decimal') from None
    if not n.is_finite() or n < 0:
        raise ValueError(f'{label} must be finite and nonnegative')
    return n


def calc(demand, inventory):
    records = {}
    for row in inventory['inventory']:
        code = row['code']
        if code in records:
            raise ValueError(f'duplicate inventory code: {code}')
        records[code] = row
    result, seen = [], set()
    for item in demand['demand']:
        code = item['code']
        if code in seen:
            raise ValueError(f'duplicate demand code: {code}')
        seen.add(code)
        amount = number(item['quantity'], f'{code} demand')
        base = {'code': code, 'name': item.get('name', code), 'unit': item['unit'], 'demand': str(amount)}
        row = records.get(code)
        if row is None:
            result.append({**base, 'status': 'unknown', 'reason': 'inventory record missing'})
            continue
        if row['unit'] != item['unit']:
            result.append({**base, 'status': 'unknown', 'reason': f"unit mismatch: demand={item['unit']}, inventory={row['unit']}"})
            continue
        on_hand = number(row['on_hand'], f'{code} on_hand')
        allocated = number(row['allocated'], f'{code} allocated')
        on_order = number(row['on_order'], f'{code} on_order')
        available = on_hand - allocated + on_order
        shortage = max(Decimal(0), amount - available)
        without_incoming = max(Decimal(0), amount - (on_hand - allocated))
        result.append({**base, 'on_hand': str(on_hand), 'allocated': str(allocated), 'on_order': str(on_order),
                       'net_available': str(available), 'shortage': str(shortage),
                       'shortage_without_incoming': str(without_incoming),
                       'status': 'shortage' if shortage else ('depends_on_incoming' if without_incoming else 'sufficient'),
                       'warnings': ['allocated exceeds on_hand'] if allocated > on_hand else []})
    return {'formula': 'max(0, demand - (on_hand - allocated + on_order))', 'items': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('demand', type=Path)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = calc(json.loads(args.demand.read_text(encoding='utf-8')), json.loads(args.inventory.read_text(encoding='utf-8')))
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
