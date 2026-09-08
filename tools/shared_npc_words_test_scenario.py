#!/usr/bin/env python3
"""Batch both consumers of the shared English words with separate checkpoints."""

import argparse
import json
from pathlib import Path

from aflib import sha256
from npc_mail_loader_test_scenario import scenario as mail_scenario
from resident_word_test_scenario import scenario as resident_scenario


def scenario(rom, native, report, edits):
    if (not report.get('shared_npc_words') or not report.get('npc_mail_loader')
            or report.get('output_sha256') != sha256(rom)):
        raise ValueError('Shared-word batch requires the exact configured shared-word ROM build')
    # The resident test deliberately changes message-window fields. Restore its
    # checkpoint before starting the independent native metadata comparisons.
    return resident_scenario(rom, native, report, edits)+mail_scenario(rom, native, report['runtime_module'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module', type=Path, required=True, help='Complete configured build.json')
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(), args.native_rom.read_bytes(), json.loads(args.module.read_text()),
                       json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'random_words': 288, 'original_letter_comparisons': 48,
                      'successive_letters': 8, 'rejected_letters': 8, 'output': str(args.output)}))


if __name__ == '__main__': main()
