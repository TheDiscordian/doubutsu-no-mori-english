"""Hash-bound display labels without changing native answer indices or actions."""

import json
from pathlib import Path
import re

from aflib import sha256
from reference_choices import choice_command
from textcodec import decode, encode, tokenize

APPROVALS = Path(__file__).resolve().parents[1]/'translations/contextual_choices.json'


class MissingChoiceLabels(ValueError):
    """An otherwise valid message cannot use absent English label edits."""


def load_contextual_choices(matches, path=APPROVALS):
    rows = json.loads(path.read_text())
    if not isinstance(rows, list):
        raise ValueError('Contextual choices must be a list')
    result = {}
    for row in rows:
        required = {
                'id', 'source_sha256', 'candidate_sha256', 'display_sha256',
                'native_command', 'display_command', 'offset', 'labels', 'evidence'}
        if (not isinstance(row, dict) or not required <= set(row) <= required | {'source_kind'}
                or row.get('source_kind', 'gamecube') not in ('gamecube', 'native_original')
                or not isinstance(row.get('id'), str)
                or not re.fullmatch(r'message:[0-9A-F]{4}', row['id'])
                or row['id'] in result or not isinstance(row['evidence'], str)
                or not row['evidence'].strip() or type(row['offset']) is not int
                or not 0 <= row['offset'] < 1024):
            raise ValueError('Invalid or duplicate contextual-choice approval')
        for key in ('source_sha256', 'candidate_sha256', 'display_sha256'):
            if not isinstance(row[key], str) or not re.fullmatch(r'[0-9a-f]{64}', row[key]):
                raise ValueError('Invalid contextual-choice hash')
        native, display = choice_command(row['native_command']), choice_command(row['display_command'])
        if native == display or native[1] != display[1]:
            raise ValueError('Contextual choices must retain the number and order of answer slots')
        match = matches.get(row['id'], {})
        if row.get('source_kind') == 'native_original':
            if row['id'] in matches:
                raise ValueError('Original contextual choices cannot override a reference approval')
        elif (match.get('source_sha256') != row['source_sha256']
                or match.get('native_choices', {}).get('native_command') != row['native_command']
                or match.get('native_choices', {}).get('adapted_sha256') != row['candidate_sha256']):
            raise ValueError('Contextual choices require the complete native-menu approval')
        labels = row['labels']
        if not isinstance(labels, list) or not 2 <= len(labels) <= 4:
            raise ValueError('Contextual choices require every destination label')
        seen = set()
        for label in labels:
            if (not isinstance(label, dict) or set(label) != {'id', 'source_sha256', 'encoded_sha256'}
                    or not isinstance(label.get('id'), str)
                    or not re.fullmatch(r'select:[0-9A-F]{4}', label['id'])
                    or label['id'] in seen or int(label['id'][7:], 16) >= 460
                    or any(not isinstance(label[k], str) or not re.fullmatch(r'[0-9a-f]{64}', label[k])
                           for k in ('source_sha256', 'encoded_sha256'))):
                raise ValueError('Invalid contextual-choice label binding')
            seen.add(label['id'])
        expected = {f'select:{int.from_bytes(display[i:i+2], "big"):04X}'
                    for i in range(2, len(display), 2)}
        if seen != expected:
            raise ValueError('Contextual-choice labels differ from the exact display menu')
        result[row['id']] = row
    return result


def unique_menu(data, info):
    menus = [t for t in tokenize(data, info) if t.kind == 'cmd' and 0x16 <= t.data[1] <= 0x18]
    if len(menus) != 1:
        raise ValueError('Contextual choices require one complete menu')
    return menus[0]


def validate_labels(row, edits, source_labels, info):
    for label in row['labels']:
        id = label['id']; index = int(id[7:], 16)
        if index >= len(source_labels) or sha256(source_labels[index]) != label['source_sha256']:
            raise ValueError('Stale contextual-choice native label')
        edit = edits.get(id)
        if edit is None:
            raise MissingChoiceLabels('Contextual menu requires complete English labels')
        raw = encode(edit['translation'], info)
        if (edit.get('source_sha256') != label['source_sha256']
                or sha256(raw) != label['encoded_sha256'] or not 0 < len(raw) <= 20
                or any(t.kind != 'text' for t in tokenize(raw, info))):
            raise ValueError('Contextual-choice label differs from its complete approval')


def display_candidate(id, source, candidate, approvals, info):
    row = approvals.get(id)
    if row is None:
        return candidate
    native = bytes.fromhex(row['native_command'])
    display = bytes.fromhex(row['display_command'])
    if (sha256(source) != row['source_sha256'] or sha256(candidate) != row['candidate_sha256']
            or unique_menu(source, info).data != native):
        raise ValueError('Stale contextual-choice source or base candidate')
    menu = unique_menu(candidate, info)
    if menu.offset != row['offset'] or menu.data != native:
        raise ValueError('Contextual-choice base menu differs from its approval')
    if row.get('source_kind') == 'native_original':
        controls = lambda data: [t.data for t in tokenize(data, info) if t.kind == 'cmd']
        if controls(source) != controls(candidate):
            raise ValueError('Original contextual-choice text changes a native command or argument')
    result = candidate[:menu.offset]+display+candidate[menu.offset+len(native):]
    if sha256(result) != row['display_sha256']:
        raise ValueError('Contextual-choice output differs from its complete approval')
    return result


def canonical_candidate(id, source, candidate, approvals, info):
    """Recover the approved native-ID payload for all existing independent guards."""
    row = approvals.get(id)
    if row is None:
        return candidate
    if sha256(candidate) != row['display_sha256']:
        raise ValueError('Native-choice candidate differs from its contextual display approval')
    menu = unique_menu(candidate, info)
    if menu.offset != row['offset'] or menu.data != bytes.fromhex(row['display_command']):
        raise ValueError('Contextual-choice display menu differs from its approval')
    result = candidate[:menu.offset]+bytes.fromhex(row['native_command'])+candidate[menu.offset+len(menu.data):]
    if display_candidate(id, source, result, approvals, info) != candidate:
        raise ValueError('Contextual-choice reverse validation failed')
    return result


def contextualize_edits(edits, source_messages, source_labels, approvals, info):
    """Apply the exact label-only edit; withhold messages missing required labels."""
    by_id = {r['id']: r for r in edits}
    if len(by_id) != len(edits):
        raise ValueError('Duplicate contextual-choice input edit')
    result, changed, withheld = [], [], []
    for edit in edits:
        id = edit['id']; row = approvals.get(id)
        if row is None:
            result.append(edit)
            continue
        source = source_messages[int(id[8:], 16)]
        candidate = display_candidate(id, source, encode(edit['translation'], info), approvals, info)
        try:
            validate_labels(row, by_id, source_labels, info)
        except MissingChoiceLabels as exc:
            withheld.append({'id': id, 'reason': str(exc)})
            continue
        adapted = {**edit, 'translation': decode(candidate, info),
                   'adaptations': [*edit.get('adaptations', []),
                       {'operation': 'use_reviewed_contextual_choice_labels',
                        'native': row['native_command'], 'display': row['display_command']}]}
        result.append(adapted)
        changed.append(id)
    return result, changed, withheld
