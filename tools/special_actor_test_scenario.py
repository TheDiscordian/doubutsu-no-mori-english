#!/usr/bin/env python3
"""Batch complete special-actor sequences, connected messages, and sound labels."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from runtime_module import module_command_info
from sequence_test_scenario import batch_scenario, SPECIAL_ACTOR_GROUPS
from shop_menu_test_scenario import scenario as menu_scenario
from topic_gap_test_scenario import combine_checkpoints

EXTRA_MESSAGES = ('message:14FD', 'message:09C8', 'message:072A', 'message:09CA')


def scenario(rom, source, edits, module=None):
    info = module_command_info(verified_rom(source))
    sequences = batch_scenario(rom, list(SPECIAL_ACTOR_GROUPS), module)
    menus, ids, labels = menu_scenario(rom, edits, info, message_ids=list(EXTRA_MESSAGES))
    return combine_checkpoints([sequences, menus]), {
        'sequences': list(SPECIAL_ACTOR_GROUPS), 'additional_messages': ids,
        'choice_ids': labels,
        'scope': 'Complete native cartridge loads, links, termination phases, and sound labels; '
                 'not ordinary actor traversal, gift/service outcomes, sound changes, or hardware acceptance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--source-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--module', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); rom = args.rom.read_bytes()
    actions, report = scenario(rom, args.source_rom.read_bytes(), json.loads(args.translations.read_text()),
                               json.loads(args.module.read_text()) if args.module else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'rom_sha256': sha256(rom), 'actions': len(actions),
                      'output': str(args.output), **report}, indent=2))


if __name__ == '__main__':
    main()
