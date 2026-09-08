"""Explicit mail-reference identities for native main-bank letter fragments.

This path copies complete reference text, appending only the native dialogue
ending. It does not install mail-bank text or authorise mail engine changes.
"""

import json
from pathlib import Path
import re

from aflib import sha256
from textcodec import LATIN, encode, tokenize
from textvalidate import validate_entry

APPROVALS = Path(__file__).resolve().parents[1]/'translations/reference_mail_fragments.json'
FIELDS = set(range(0x24, 0x2E)) | set(range(0x36, 0x40))
POLICY = 'reference_text'
ENDING = b'\x7f\x00'
KEYS = {'id', 'reference_id', 'source_sha256', 'native_reference_sha256',
        'reference_sha256', 'encoded_sha256', 'comparison', 'evidence'}


def load_fragment_matches(path=APPROVALS):
    rows = json.loads(path.read_text())
    if not isinstance(rows, list):
        raise ValueError('Mail-fragment approvals must be a list')
    matches = {}
    for row in rows:
        if (not isinstance(row, dict) or set(row) != KEYS
                or not isinstance(row['id'], str)
                or not re.fullmatch(r'message:[0-9A-F]{4}', row['id'])
                or not isinstance(row['reference_id'], str)
                or not re.fullmatch(r'mail[abc]:[0-9A-F]{4}', row['reference_id'])
                or row['comparison'] not in ('identical_body', 'reviewed_native_variation')
                or not isinstance(row['evidence'], str) or not row['evidence'].strip()
                or any(not isinstance(row[key], str) or not re.fullmatch(r'[0-9a-f]{64}', row[key])
                       for key in KEYS if key.endswith('sha256'))
                or row['id'] in matches):
            raise ValueError('Invalid or duplicate mail-fragment approval')
        matches[row['id']] = row
    return matches


def fragment_fields(data, info, *, english=False):
    fields, visible = [], False
    for token in tokenize(data, info):
        if token.kind == 'cmd' and token.data[1] in FIELDS:
            fields.append(token.data)
        elif token.kind == 'text':
            if english and token.data[0] not in LATIN | {0xCD}:
                raise ValueError('Mail fragment contains non-English text')
            visible |= token.data not in (b' ', b'\xcd')
        else:
            raise ValueError('Mail fragment contains a non-field command or glyph')
    if not visible:
        raise ValueError('Mail fragment must contain visible text')
    return fields


def verify_fragment_source(record, source, native_reference, info):
    if (sha256(source) != record['source_sha256']
            or sha256(native_reference) != record['native_reference_sha256']
            or not source.endswith(ENDING)):
        raise ValueError('Stale mail-fragment native source or ending')
    body = source[:-len(ENDING)]
    if fragment_fields(body, info) != fragment_fields(native_reference, info):
        raise ValueError('Mail-fragment native field sequence differs')
    identical = body.strip(b' \xcd') == native_reference.strip(b' \xcd')
    if identical != (record['comparison'] == 'identical_body'):
        raise ValueError('Mail-fragment native comparison differs from approval')


def validate_fragment_candidate(id, source, candidate, matches, sources, info, policy):
    record = matches.get(id)
    if record is None:
        return
    bank, number = record['reference_id'].split(':')
    index = int(number, 16)
    if bank not in sources or index >= len(sources[bank]):
        raise ValueError('Mail-fragment native reference is absent')
    verify_fragment_source(record, source, sources[bank][index], info)
    if (policy != POLICY or sha256(candidate) != record['encoded_sha256']
            or not candidate.endswith(ENDING)
            or sha256(candidate[:-len(ENDING)]) != record['reference_sha256']):
        raise ValueError('Mail-fragment candidate differs from complete approved reference')
    fragment_fields(candidate[:-len(ENDING)], info, english=True)
    # Main-dialogue validation, not mail-field capacity or mail-dispatch policy.
    # No added fields, pauses, actions, or commands are permitted by this path.
    validate_entry(source, candidate, info, 'message', POLICY)


def reference_fragment_edits(matches, sources, references, inventory, info):
    edits = {}
    for id, record in matches.items():
        native_index = int(id.split(':')[1], 16)
        if native_index >= len(sources['message']):
            raise ValueError('Mail-fragment main source is absent')
        source = sources['message'][native_index]
        reference = references.get(record['reference_id'])
        row = inventory.get(record['reference_id'])
        if (not reference or not row or reference.get('id') != record['reference_id']
                or row.get('id') != record['reference_id']
                or reference.get('sha256') != record['reference_sha256']
                or row.get('source_sha256') != record['native_reference_sha256']):
            raise ValueError('Stale mail-fragment reference inventory')
        reference_data = encode(reference['text'], info)
        if (sha256(reference_data) != record['reference_sha256']
                or encode(row['legacy'], info) != reference_data):
            raise ValueError('Mail-fragment complete English reference or legacy agreement changed')
        candidate = reference_data + ENDING
        validate_fragment_candidate(id, source, candidate, matches, sources, info, POLICY)
        edits[id] = {'id': id, 'source_sha256': record['source_sha256'],
                     'translation': reference['text']+'{cmd:7F00}', 'control_policy': POLICY,
                     'status': 'mechanically_validated_candidate_not_reviewed',
                     'provenance': {'source': 'user-supplied GAFE01 revision 0 disc',
                                    'reference_id': record['reference_id'],
                                    'reference_sha256': record['reference_sha256'],
                                    'native_reference_sha256': record['native_reference_sha256'],
                                    'match_basis': 'reviewed_cross_bank_mail_fragment',
                                    'comparison': record['comparison']},
                     'adaptations': [{'operation': 'append_native_dialogue_ending', 'command': '7F00'}]}
    return edits
