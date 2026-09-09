"""Explicit native item-name identities, separate from legacy wording matches."""

import json
from pathlib import Path
import re

from aflib import sha256
from textcodec import encode

APPROVALS = Path(__file__).resolve().parents[1]/'translations/item_reference_matches.json'
SHEET_APPROVALS = APPROVALS.with_name('item_sheet_matches.json')
ITEM_ID = re.compile(r'item_(10|2[0-9A-F]):([0-9A-F]{4})')


def identity_key(id):
    match = ITEM_ID.fullmatch(id)
    if not match:
        raise ValueError('Invalid item identity ID')
    index = int(match[2], 16)
    if match[1] == '10':
        index &= ~3
    return f'item_{match[1]}:{index:04X}'


def load_matches(path=APPROVALS, *, include_sheet=True):
    rows = json.loads(path.read_text())
    if not isinstance(rows, list):
        raise ValueError('Item identity approvals must be a list')
    if path == APPROVALS and include_sheet:
        extra = json.loads(SHEET_APPROVALS.read_text())
        if not isinstance(extra, list):
            raise ValueError('Sheet-reviewed item identities must be a list')
        rows += extra
    result = {}
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                or identity_key(row['id']) != row['id'] or row['id'] in result
                or not isinstance(row.get('evidence'), str) or not row['evidence'].strip()
                or not isinstance(row.get('native_name'), str) or not row['native_name'].strip()):
            raise ValueError('Item identity requires a unique root, native name, and evidence')
        for field in ('source_sha256', 'reference_sha256'):
            if not isinstance(row.get(field), str) or not re.fullmatch(r'[0-9a-f]{64}', row[field]):
                raise ValueError('Invalid item identity hash')
        prefix = 'furniture' if row['id'].startswith('item_10:') else row['id'].split(':')[0]
        if not isinstance(row.get('reference_id'), str) or not re.fullmatch(prefix+r':[0-9A-F]{4}', row['reference_id']):
            raise ValueError('Item identity reference must belong to the same name family')
        result[row['id']] = row
    return result


def verify_source(match, native, info):
    if (sha256(native) != match['source_sha256']
            or encode(match['native_name'], info).ljust(10, b' ') != native):
        raise ValueError('Stale item identity source or native name')


def validate_candidate(edit, source_banks, info, matches, *, originals=None):
    """The builder/resource checks exact approved names, including native aliases."""
    from native_item_names import load_names, validate
    originals = load_names() if originals is None else originals
    if validate(edit,source_banks,info,originals):
        if identity_key(edit['id']) in matches:
            raise ValueError('Native item name conflicts with a donor approval')
        return
    if not edit['id'].startswith('item_'):
        if 'item_reference_match' in edit:
            raise ValueError('Item identity metadata belongs only to item names')
        return
    direct = identity_key(edit['id'])
    declared = edit.get('item_reference_match')
    if 'item_reference_match' in edit and not isinstance(declared, str):
        raise ValueError('Item identity declaration must be a named approval')
    if declared is None and direct not in matches:
        return
    key = declared if declared is not None else direct
    if key not in matches:
        raise ValueError('Unknown item identity approval')
    match = matches[key]
    bank, index = key.split(':'); index = int(index, 16)
    if bank not in source_banks or index >= len(source_banks[bank]):
        raise ValueError('Item identity source slot is absent')
    native = source_banks[bank][index]
    verify_source(match, native, info)
    if bank == 'item_10' and (index+4 > len(source_banks[bank])
                             or any(raw != native for raw in source_banks[bank][index:index+4])):
        raise ValueError('Approved furniture rotation names differ')
    target_bank, target_index = edit['id'].split(':')
    target_index = int(target_index, 16)
    if (target_bank not in source_banks or target_index >= len(source_banks[target_bank])
            or source_banks[target_bank][target_index] != native
            or edit['source_sha256'] != sha256(native)):
        raise ValueError('Item identity does not match its target source')
    provenance = edit.get('provenance')
    if not isinstance(provenance, dict):
        raise ValueError('Approved item name requires complete reference provenance')
    if direct != key:
        # Existing cartridge conversion is the authority for placed-name aliases.
        from item_aliases import ordinary_item
        donor = provenance.get('native_equivalent_id', '')
        if not isinstance(donor, str) or not donor.startswith('item_10:') or identity_key(donor) != key:
            raise ValueError('Item identity alias lacks its exact native donor')
        number = int(donor.split(':')[1], 16)+0x1000
        converted = ordinary_item(number)
        if (provenance.get('match_basis') != 'native_placed_conversion_and_identical_source_name'
                or provenance.get('native_item_id') != f'{number:04X}'
                or provenance.get('converted_item_id') != f'{converted:04X}'
                or edit['id'] != f'item_{converted >> 8:02X}:{converted & 255:04X}'):
            raise ValueError('Item identity alias changes the native conversion')
    encoded = encode(edit['translation'], info)
    if (len(encoded) > 16 or sha256(encoded.ljust(16, b' ')) != match['reference_sha256']
            or provenance.get('reference_sha256') != match['reference_sha256']
            or provenance.get('reference_id') != match['reference_id']):
        raise ValueError('Approved item name must retain the complete exact English reference')
