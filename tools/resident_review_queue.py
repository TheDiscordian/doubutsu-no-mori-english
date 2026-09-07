#!/usr/bin/env python3
"""Prepare local-only expression-difference reviews; never approve or install text."""

import argparse
from collections import Counter
import json
from pathlib import Path

from aflib import sha256, verified_rom
from gc_adapter import adapt_reference
from gc_text import plain
from reference_animations import ResidentAnimationPermit, verify_native_consumer
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode, tokenize
from text_coverage import index_edits
from textvalidate import expanded_bound, validate_entry


def review_rows(entries, references, installed, info):
    """Hypothetical command compatibility does not establish actor/topic identity."""
    rows, excluded = [], Counter()
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    for number, native in enumerate(entries):
        id = f'message:{number:04X}'
        if id in installed:
            if installed[id].get('source_sha256') != sha256(native):
                raise ValueError('Review input contains a stale installed source: '+id)
            excluded['already_has_candidate'] += 1
            continue
        reference = references.get(id)
        if not reference or not plain(reference.get('text', '')).strip():
            excluded['no_visible_same_id_reference'] += 1
            continue
        native_text = decode(native, info)
        if not plain(native_text).strip():
            excluded['native_without_static_text_needs_flow_review'] += 1
            continue
        try:
            original_reference = encode(reference['text'], reference_info)
        except ValueError as exc:
            excluded[str(exc)] += 1
            continue
        if reference.get('id') != id:
            raise ValueError('Review input contains a mismatched English reference ID: '+id)
        if sha256(original_reference) != reference.get('sha256'):
            # Some English glyphs do not re-encode to the same native bytes.
            # A changed or stale reference has the same uncertainty here.
            # Neither case may enter this complete-hash-bound review pool.
            excluded['reference_encoding_or_hash_requires_review'] += 1
            continue
        try:
            text, adaptations = adapt_reference(reference['text'], native, info, 'reference_layout', True,
                                                 retain_resident_animations=True)
            candidate = encode(text, info)
            hypothetical = ResidentAnimationPermit(sha256(native), sha256(candidate), 'native_resident_talk')
            validate_entry(native, candidate, info, 'message', 'reference_layout', resident_runtime=True,
                           animation_permit=hypothetical)
        except ValueError as exc:
            excluded[str(exc)] += 1
            continue
        def controls(data):
            return [t.data.hex().upper() for t in tokenize(data, info) if t.kind == 'cmd']
        rows.append({'native_id': id, 'source_sha256': sha256(native),
                     'reference_id': reference['id'], 'reference_sha256': reference['sha256'],
                     'candidate_sha256': sha256(candidate), 'expanded_bound': expanded_bound(candidate, info),
                     'review_status': 'native_actor_and_topic_review_required', 'approved': False,
                     'native_text': native_text, 'reference_text': reference['text'], 'adapted_text': text,
                     'native_commands': controls(native), 'candidate_commands': controls(candidate),
                     'adaptations': adaptations})
    return rows, dict(sorted(excluded.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--reference', type=Path, default=Path('build/gamecube/text/message.jsonl'))
    parser.add_argument('--output', type=Path, default=Path('build/resident-review'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    verify_native_consumer(rom)
    raw_edits, raw_references = args.translations.read_bytes(), args.reference.read_bytes()
    installed = index_edits(json.loads(raw_edits))
    references = {}
    for reference in map(json.loads, raw_references.decode().splitlines()):
        if reference['id'] in references:
            raise ValueError('Duplicate English reference ID')
        references[reference['id']] = reference
    entries = next(b for b in banks(rom) if b.name == 'message').entries()
    rows, excluded = review_rows(entries, references, installed, module_command_info(rom))
    summary = {'source_rom_sha256': sha256(rom), 'translations_sha256': sha256(raw_edits),
               'reference_file_sha256': sha256(raw_references), 'review_records': len(rows),
               'approved_records': 0, 'excluded': excluded,
               'scope': 'Read-only review pool; special actors and changed topics are not approved by command compatibility'}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'queue.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows))
    (args.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
