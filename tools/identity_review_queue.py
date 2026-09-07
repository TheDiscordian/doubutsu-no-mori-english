#!/usr/bin/env python3
"""Report complete same-ID comparisons under unchanged candidate rules; approve none."""

import argparse
from collections import Counter
import json
from pathlib import Path

from aflib import sha256, verified_rom
from gc_adapter import adapt_reference
from gc_text import plain
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode, tokenize
from text_coverage import index_edits
from textvalidate import expanded_bound, validate_entry


def review_rows(entries, references, installed, remaining, info):
    rows, excluded = [], Counter()
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    known = {f'message:{i:04X}' for i in range(len(entries))}
    if set(remaining)-known:
        raise ValueError('Unknown native identity-review ID')
    for number, native in enumerate(entries):
        id = f'message:{number:04X}'
        if id in installed:
            if installed[id].get('source_sha256') != sha256(native):
                raise ValueError('Stale identity-review candidate source: '+id)
            if id in remaining:
                if installed[id].get('reference_fallback') is True:
                    excluded['reference_rejection_has_original_fallback'] += 1
                else:
                    raise ValueError('Identity-review rejection already has a candidate: '+id)
            continue
        if remaining.get(id) != 'same_id_not_confirmed_by_legacy':
            continue
        reference = references.get(id)
        if reference and reference.get('id') != id:
            raise ValueError('Mismatched identity-review reference ID: '+id)
        if not reference or not plain(reference.get('text', '')).strip():
            excluded['no_visible_same_id_reference'] += 1
            continue
        native_text = decode(native, info)
        if not plain(native_text).strip():
            excluded['native_without_static_text_needs_flow_review'] += 1
            continue
        try:
            if sha256(encode(reference['text'], reference_info)) != reference.get('sha256'):
                excluded['reference_encoding_or_hash_requires_review'] += 1
                continue
            # Match the existing generator's policy ladder and stopping rule.
            # No animation, added-field, actor, controller, or sequence permits.
            for policy in ('presentation', 'reference_text', 'reference_delivery', 'reference_layout'):
                try:
                    text, changes = adapt_reference(reference['text'], native, info, policy, True)
                    candidate = encode(text, info)
                    validate_entry(native, candidate, info, 'message', policy, resident_runtime=True)
                    break
                except ValueError as exc:
                    if policy == 'reference_layout' or str(exc) != 'Control signature changed':
                        raise
        except ValueError as exc:
            excluded[str(exc)] += 1
            continue
        controls = lambda data: [t.data.hex().upper() for t in tokenize(data, info) if t.kind == 'cmd']
        rows.append({'native_id': id, 'source_sha256': sha256(native),
                     'reference_id': reference['id'], 'reference_sha256': reference['sha256'],
                     'candidate_sha256': sha256(candidate), 'control_policy': policy,
                     'expanded_bound': expanded_bound(candidate, info),
                     'review_status': 'native_meaning_and_context_review_required', 'approved': False,
                     'native_text': native_text, 'reference_text': reference['text'], 'adapted_text': text,
                     'native_commands': controls(native), 'candidate_commands': controls(candidate),
                     'adaptations': changes})
    return rows, dict(sorted(excluded.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--remaining', type=Path, required=True)
    parser.add_argument('--reference', type=Path, default=Path('build/gamecube/text/message.jsonl'))
    parser.add_argument('--output', type=Path, default=Path('build/identity-review'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    raw_edits, raw_remaining, raw_references = (p.read_bytes() for p in
                                               (args.translations, args.remaining, args.reference))
    installed = index_edits(json.loads(raw_edits))
    references, remaining = {}, {}
    for row in map(json.loads, raw_references.decode().splitlines()):
        if row['id'] in references:
            raise ValueError('Duplicate identity-review reference ID')
        references[row['id']] = row
    for row in map(json.loads, raw_remaining.decode().splitlines()):
        if row['id'] in remaining:
            raise ValueError('Duplicate identity-review rejection ID')
        remaining[row['id']] = row['reason']
    sources = next(b for b in banks(rom) if b.name == 'message').entries()
    rows, excluded = review_rows(sources, references, installed, remaining, module_command_info(rom))
    summary = {'source_rom_sha256': sha256(rom), 'translations_sha256': sha256(raw_edits),
               'remaining_file_sha256': sha256(raw_remaining), 'reference_file_sha256': sha256(raw_references),
               'review_records': len(rows), 'approved_records': 0, 'excluded': excluded,
               'scope': 'Read-only comparison pool under existing rules; topic, platform, and actor identity still require review'}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'queue.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows))
    (args.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
