#!/usr/bin/env python3
"""Batch actual calendar preparation with contextual labels and answer branches."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from contextual_choice_test_scenario import scenario as choice_scenario
from dialogue_dates_test_scenario import scenario as date_scenario
from topic_gap_test_scenario import combine_checkpoints


def scenario(rom, source, module, edits):
    source = verified_rom(source)
    choices, ids, cases = choice_scenario(rom, source, edits)
    dates = date_scenario(rom, source, module, edits)
    return combine_checkpoints([dates, choices]), ids, cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--source-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions, ids, cases = scenario(rom, args.source_rom.read_bytes(),
        json.loads(args.module.read_text()), json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'rom_sha256': sha256(rom), 'actions': len(actions),
        'contextual_messages': ids, 'choice_cases': cases,
        'scope': 'Injected native calendar requests, date fields, quiz text, and answer branches; '
                 'not normal event selection, rewards, saves, or original hardware'}, indent=2))


if __name__ == '__main__':
    main()
