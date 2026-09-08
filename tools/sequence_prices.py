"""Exact native invoice amounts in otherwise complete English sequences."""

import re

from aflib import sha256
from textcodec import encode, tokenize


def validate_price_group(group):
    if 'native_price' not in group:
        return
    rule = group['native_price']
    members = group.get('members', [])
    if (not isinstance(rule, dict)
            or set(rule) != {'source_offset', 'reference_offset', 'before', 'after',
                             'adapted_reference_sha256'}
            or group.get('source_kind', 'gamecube') != 'gamecube'
            or not members
            or any(m.get('reference_id', m['id']) != members[0]['id']
                   or 'remove_redundant_cutarticle' in m for m in members)
            or any(type(rule[k]) is not int or not 0 <= rule[k] < 4096
                   for k in ('source_offset', 'reference_offset'))
            or any(not isinstance(rule[k], str)
                   or not re.fullmatch(r'[1-9][0-9]{0,2}(?:,[0-9]{3}){0,2}', rule[k])
                   for k in ('before', 'after'))
            or rule['before'] == rule['after']
            or not isinstance(rule['adapted_reference_sha256'], str)
            or not re.fullmatch(r'[0-9a-f]{64}', rule['adapted_reference_sha256'])):
        raise ValueError('Invalid sequence native-price approval')


def audit_native_price(group, source, info):
    """The independent builder requires the exact whole native numeric token."""
    validate_price_group(group)
    if 'native_price' not in group:
        return
    rule = group['native_price']
    amount = encode(rule['after'].replace(',', ''), info)
    start, end = rule['source_offset'], rule['source_offset']+len(amount)
    tokens = {t.offset: t for t in tokenize(source, info)}
    digits = {encode(str(n), info) for n in range(10)}
    numeric_edges = digits | {encode(',', info)}
    if (sha256(source) != group['members'][0]['source_sha256']
            or source[start:end] != amount
            or any(at not in tokens or tokens[at].kind != 'text'
                   or tokens[at].data not in digits for at in range(start, end))
            or (start-1 in tokens and tokens[start-1].data in numeric_edges)
            or (end in tokens and tokens[end].data in numeric_edges)):
        raise ValueError('Sequence price differs from the complete native amount')


def adapt_reference_price(group, text, info):
    """Only one individually located numeric span changes, before slicing."""
    validate_price_group(group)
    if 'native_price' not in group:
        return text
    rule = group['native_price']
    start, before = rule['reference_offset'], rule['before']
    end = start+len(before)
    if (text[start:end] != before
            or (start and text[start-1] in '0123456789,')
            or (end < len(text) and text[end] in '0123456789,')):
        raise ValueError('Sequence price does not match the complete reference amount')
    adapted = text[:start]+rule['after']+text[end:]
    delivery = lambda value: [t.data for t in tokenize(encode(value, info), info)
                              if t.kind == 'cmd' or t.data == b'\xcd']
    if delivery(text) != delivery(adapted):
        raise ValueError('Sequence price changes a command or line boundary')
    if sha256(encode(adapted, info)) != rule['adapted_reference_sha256']:
        raise ValueError('Sequence price changed the complete adapted reference')
    return adapted
