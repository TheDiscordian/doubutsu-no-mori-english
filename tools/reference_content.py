"""Complete reference/output bindings without new command or runtime permissions."""

import re

from aflib import sha256
from textcodec import encode, tokenize
from reference_mood import validate_rule as validate_mood_rule, restore as restore_native_mood
from reference_random import validate_rule as validate_random_rule, restore as restore_native_random

STARTUP_STORAGE_SPANS = {
    'message:13F2': ("in {cmd:7F50198CDC08}{cmd:7F28}'s", 'in'),
    'message:141A': ('in {cmd:7F50198CDC06}{cmd:7F28} ', 'in '),
    'message:1442': ("in {cmd:7F50198CDC08}{cmd:7F28}'s", 'in'),
    'message:146A': ("in {cmd:7F50198CDC08}{cmd:7F28}'s ", 'in '),
    'message:1492': ("in {cmd:7F50198CDC08}{cmd:7F28}'s ", 'in '),
    'message:14BA': ("in {cmd:7F50198CDC08}{cmd:7F28}'s", 'in'),
}


def validate_content_approval(record):
    if 'complete_reference' not in record:
        return
    rule = record['complete_reference']
    if (not isinstance(rule, dict) or set(rule)-{'adapted_sha256', 'spans', 'omit_startup_storage_location', 'native_mood', 'native_random'}
            or 'adapted_sha256' not in rule
            or not record['id'].startswith('message:')
            or any(key in record for key in ('controller', 'native_choices', 'native_actor_request',
                                             'available_fields', 'speaker_catchphrase',
                                             'native_equivalent_id', 'resident_animations'))
            or not isinstance(rule['adapted_sha256'], str)
            or not re.fullmatch(r'[0-9a-f]{64}', rule['adapted_sha256'])):
        raise ValueError('Invalid complete-reference approval')
    if 'native_mood' in rule:
        if 'spans' in rule or 'omit_startup_storage_location' in rule or 'native_random' in rule or record.get('reference_id') != record['id']:
            raise ValueError('Native mood restoration cannot combine with wording or storage adaptations')
        validate_mood_rule(rule['native_mood'])
    if 'native_random' in rule:
        if set(rule) != {'adapted_sha256', 'native_random'} or record.get('reference_id') != record['id']:
            raise ValueError('Native random branches cannot combine with other content adaptations')
        validate_random_rule(rule['native_random'])
    if 'spans' in rule:
        if not isinstance(rule['spans'], list) or not rule['spans']:
            raise ValueError('Invalid complete-reference spans')
        for span in rule['spans']:
            if (not isinstance(span, dict) or set(span) != {'offset', 'before', 'after'}
                    or type(span['offset']) is not int or not 0 <= span['offset'] < 4096
                    or not isinstance(span['before'], str) or not span['before']
                    or not isinstance(span['after'], str) or not span['after']
                    or span['before'] == span['after']):
                raise ValueError('Invalid complete-reference span')
    if 'omit_startup_storage_location' in rule:
        spans = rule.get('spans', [])
        if (rule['omit_startup_storage_location'] is not True
                or record['id'] not in STARTUP_STORAGE_SPANS
                or record.get('reference_id') != record['id']
                or len(spans) != 1
                or (spans[0]['before'], spans[0]['after']) != STARTUP_STORAGE_SPANS[record['id']]):
            raise ValueError('Invalid startup storage-location omission')


def verify_content_reference(reference, source, record, info):
    if not record or 'complete_reference' not in record:
        return
    validate_content_approval(record)
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    if (sha256(source) != record['source_sha256'] or reference['id'] != record['reference_id']
            or reference['sha256'] != record['reference_sha256']
            or sha256(encode(reference['text'], reference_info)) != record['reference_sha256']):
        raise ValueError('Stale complete-reference source or reference')
    if record['complete_reference'].get('omit_startup_storage_location'):
        native = [t.data for t in tokenize(source, info) if t.kind == 'cmd']
        commands = [t.data for t in tokenize(encode(reference['text'], info), info) if t.kind == 'cmd']
        if (b'\x7f\x28' in native or commands.count(b'\x7f\x28') != 1
                or not all(bytes((0x7f, code)) in native
                           for code in (0x1c, 0x2f, 0x1d, 0x1e, 0x20, 0x21, 0x22))):
            raise ValueError('Startup storage-location omission requires native clock fields and no storage field')


def adapt_content_reference(reference, source, record, info):
    """Apply only explicit source-bound wording spans, without moving delivery."""
    if not record or 'complete_reference' not in record:
        return reference['text'], []
    verify_content_reference(reference, source, record, info)
    if 'native_mood' in record['complete_reference']:
        return restore_native_mood(reference['text'], source, record['complete_reference']['native_mood'], info)
    if 'native_random' in record['complete_reference']:
        return restore_native_random(reference['text'], source, record['complete_reference']['native_random'], info)
    text = reference['text']
    previous_end = 0
    parts, changes = [], []
    for span in record['complete_reference'].get('spans', []):
        start, before, after = span['offset'], span['before'], span['after']
        # Offsets count characters in the decoded reference, not glyph bytes.
        if start < previous_end or text[start:start+len(before)] != before:
            raise ValueError('Complete-reference span does not match its approval')
        # Colour span counts may change with a translated term. All other
        # commands and manual line/page/wait/pause order remain untouched.
        # Six individually bound clock greetings may omit exactly their GC-only
        # storage-location clause; the schema fixes its entire before/after text.
        delivery = lambda value: [t.data for t in tokenize(encode(value, info), info)
                                  if (t.kind == 'cmd' and t.data[1] != 0x50)
                                  or (t.kind == 'text' and t.data == b'\xcd')]
        before_delivery = delivery(before)
        omit_storage = record['complete_reference'].get('omit_startup_storage_location', False)
        if omit_storage:
            before_delivery = [command for command in before_delivery if command != b'\x7f\x28']
        if before_delivery != delivery(after):
            raise ValueError('Complete-reference span changes delivery or non-colour controls')
        parts.extend((text[previous_end:start], after))
        previous_end = start+len(before)
        changes.append({'operation': ('omit_startup_storage_location' if omit_storage
                                      else 'reviewed_native_wording_span'), 'character_offset': start,
                        'before_sha256': sha256(before.encode()), 'after_sha256': sha256(after.encode())})
    parts.append(text[previous_end:])
    return ''.join(parts), changes


def validate_content_candidate(id, source, candidate, matches):
    record = matches.get(id)
    if not record or 'complete_reference' not in record:
        return
    validate_content_approval(record)
    if (sha256(source) != record['source_sha256']
            or sha256(candidate) != record['complete_reference']['adapted_sha256']):
        raise ValueError('Complete-reference output differs from its reviewed payload')
