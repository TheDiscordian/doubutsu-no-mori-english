"""Complete original N64 translations used by the guarded sequence framework."""

import re

from aflib import sha256
from textcodec import encode, tokenize


def source_kind(group):
    kind = group.get('source_kind', 'gamecube')
    if kind not in ('gamecube', 'native_original'):
        raise ValueError('Unknown sequence text source kind')
    if kind == 'gamecube' and ('original_translation' in group or 'colour_lengths' in group):
        raise ValueError('GameCube sequence cannot contain original-translation permissions')
    return kind


def validate_native_group(group):
    if source_kind(group) != 'native_original':
        return
    whole = group.get('original_translation')
    members = group.get('members')
    if (not isinstance(whole, dict) or set(whole) != {'id', 'text', 'sha256'}
            or not isinstance(whole.get('text'), str) or not whole['text'].strip()
            or not re.fullmatch(r'message:[0-9A-F]{4}', whole.get('id', ''))
            or not re.fullmatch(r'[0-9a-f]{64}', whole.get('sha256', ''))
            or not isinstance(members, list) or not 2 <= len(members) <= 16
            or members[0].get('id') != whole['id']):
        raise ValueError('Native sequence requires one complete original translation and its root')
    if group.get('actor_sources'):
        raise ValueError('Native sequence cannot add actor-source permissions')
    for member in members:
        if (member.get('reference_id') != whole['id']
                or member.get('reference_sha256') != whole['sha256']
                or 'reference_slice' not in member
                or 'remove_redundant_cutarticle' in member):
            raise ValueError('Native sequence members must slice the same complete original translation')
    changes = group.get('colour_lengths', [])
    if not isinstance(changes, list):
        raise ValueError('Native colour approvals must be a list')
    indices = set()
    for change in changes:
        if (not isinstance(change, dict)
                or set(change) != {'command_index', 'original', 'replacement'}
                or type(change['command_index']) is not int or change['command_index'] < 0
                or change['command_index'] in indices
                or any(not isinstance(change[k], str)
                       or not re.fullmatch(r'7F50[0-9A-F]{8}', change[k])
                       for k in ('original', 'replacement'))):
            raise ValueError('Native colour approval requires unique indexed full colour commands')
        before, after = bytes.fromhex(change['original']), bytes.fromhex(change['replacement'])
        if before[:5] != after[:5] or before == after or after[-1] == 0:
            raise ValueError('Native colour approval may change only a nonzero span length')
        indices.add(change['command_index'])


def native_reference(group, info):
    validate_native_group(group)
    if source_kind(group) != 'native_original':
        raise ValueError('Expected a native original sequence')
    whole = group['original_translation']
    if sha256(encode(whole['text'], info)) != whole['sha256']:
        raise ValueError('Native sequence requires the exact complete original translation')
    return whole


def audit_native_translation(group, original, info):
    whole = native_reference(group, info)
    if sha256(original) != group['members'][0]['source_sha256']:
        raise ValueError('Native sequence root source changed')
    commands = lambda data: [t.data for t in tokenize(data, info) if t.kind == 'cmd']
    expected = commands(original)
    for change in group.get('colour_lengths', []):
        index = change['command_index']
        if index >= len(expected) or expected[index] != bytes.fromhex(change['original']):
            raise ValueError('Native colour approval does not match its original command')
        expected[index] = bytes.fromhex(change['replacement'])
    if commands(encode(whole['text'], info)) != expected:
        raise ValueError('Complete native translation changed a field, pause, page, actor, or flow command')
