"""Retain one reviewed native random branch beside complete English wording."""

import re

from textcodec import decode, encode, tokenize


def branch(value):
    if not isinstance(value, str) or not re.fullmatch(r'7F(?:13|14)[0-9A-F]+', value):
        raise ValueError('Native random branch requires a complete 13/14 command')
    raw = bytes.fromhex(value)
    if len(raw) != {0x13: 6, 0x14: 8}[raw[1]]:
        raise ValueError('Native random branch has the wrong command length')
    return raw


def validate_rule(rule):
    if (not isinstance(rule, dict)
            or set(rule) != {'source_offset', 'reference_offset', 'native_command', 'reference_command'}
            or any(type(rule.get(k)) is not int or not 0 <= rule[k] < 1024
                   for k in ('source_offset', 'reference_offset'))):
        raise ValueError('Invalid complete native random-branch rule')
    native, reference = branch(rule['native_command']), branch(rule['reference_command'])
    targets = lambda raw: {raw[n:n+2] for n in range(2, len(raw), 2)}
    if native == reference or targets(native) != targets(reference):
        raise ValueError('Random-branch adaptation must retain the same destination set')


def restore(text, source, rule, info):
    validate_rule(rule)
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    reference = encode(text, reference_info)
    routes = lambda raw, descriptors: [t for t in tokenize(raw, descriptors)
                                       if t.kind == 'cmd' and t.data[1] in (0x13, 0x14)]
    native_routes, english_routes = routes(source, info), routes(reference, reference_info)
    native, before = branch(rule['native_command']), branch(rule['reference_command'])
    if (len(native_routes) != 1 or len(english_routes) != 1
            or native_routes[0].offset != rule['source_offset']
            or native_routes[0].data != native
            or english_routes[0].offset != rule['reference_offset']
            or english_routes[0].data != before):
        raise ValueError('Random branch differs from the unique approved source/reference span')
    offset = rule['reference_offset']
    adapted = reference[:offset]+native+reference[offset+len(before):]
    # The approval cannot conceal additional choice, branch, actor, or quest
    # changes. Retain every gameplay command exactly before the general adapter.
    gameplay = lambda raw, descriptors: [t.data for t in tokenize(raw, descriptors)
                                         if t.kind == 'cmd' and 8 <= t.data[1] <= 0x19]
    if gameplay(source, info) != gameplay(adapted, reference_info):
        raise ValueError('Random-branch restoration changes another native gameplay command')
    return decode(adapted, reference_info), [{
        'operation': 'retain_complete_native_random_branch',
        'source_offset': rule['source_offset'], 'reference_offset': offset,
        'native': rule['native_command'], 'gamecube': rule['reference_command']}]
