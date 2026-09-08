#!/usr/bin/env python3
"""Audit exact reserve labels separately from dialogue and continuation approvals."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from aflib import sha256, verified_rom
from placeholder_text import native_label
from reference_sequences import load_sequences, message_targets, validate_sequences
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode
from text_coverage import index_edits
from textvalidate import validate_entry


def audit(entries, edits, info, *, resident_runtime=False):
    groups = load_sequences()
    allocation = {member['id']: name for name, group in groups.items() for member in group['members']}
    permits = validate_sequences(list(edits.values()), entries, info, groups, resident_runtime=resident_runtime)
    incoming = defaultdict(list)
    for number, source in enumerate(entries):
        for target in set(message_targets(source, info)):
            incoming[target].append(f'message:{number:04X}')
    rows = []
    for number, source in enumerate(entries):
        definition = native_label(source, info)
        if definition is None:
            continue
        id = f'message:{number:04X}'
        row = {'id': id, 'source_sha256': sha256(source), 'kind': definition.kind,
               'english_label': definition.english, 'english_label_alternatives': definition.alternatives,
               'native_message_script_incoming': incoming[number], 'reachability': 'not_established',
               'sequence_allocation': allocation.get(id), 'status': 'missing_candidate'}
        edit = edits.get(id)
        if edit is not None:
            if edit['source_sha256'] != row['source_sha256']:
                raise ValueError(f'Stale placeholder candidate: {id}')
            candidate = encode(edit['translation'], info)
            row['candidate_sha256'] = sha256(candidate)
            try:
                validate_entry(source, candidate, info, 'message', edit.get('control_policy', 'exact'),
                               resident_runtime=resident_runtime, sequence_permit=permits.get(id))
            except ValueError as exc:
                row.update(status='invalid_candidate', reason=str(exc))
            else:
                row['status'] = 'approved_sequence_member' if id in permits else 'english_label_candidate'
        elif id in allocation:
            row['status'] = 'allocated_sequence_not_installed'
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--resident-runtime', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('build/placeholder-audit'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    raw = args.translations.read_bytes()
    entries = next(b for b in banks(rom) if b.name == 'message').entries()
    rows = audit(entries, index_edits(json.loads(raw)), module_command_info(rom),
                 resident_runtime=args.resident_runtime)
    summary = {'schema': 1, 'rom_sha256': sha256(rom), 'translations_sha256': sha256(raw),
               'native_labels': len(rows), 'kinds': dict(Counter(r['kind'] for r in rows)),
               'statuses': dict(Counter(r['status'] for r in rows)),
               'with_native_message_script_incoming': sum(bool(r['native_message_script_incoming']) for r in rows),
               'completion_claim': False,
               'scope': 'Exact native label recognition and candidate controls/hashes. '
                        'Incoming references cover native message-script targets only; '
                        'not executable/table callers, indirect flow, runtime execution, or final wording review.'}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'labels.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    (args.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
