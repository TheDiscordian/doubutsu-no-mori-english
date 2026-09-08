#!/usr/bin/env python3
"""Batch special dialogue, connected replies/labels, and original mood orders."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from actor_request_test_scenario import scenario as mood_scenario
from shop_menu_test_scenario import scenario as menu_scenario
from runtime_module import module_command_info
from topic_gap_test_scenario import combine_checkpoints

ROOT = Path(__file__).resolve().parents[1]
CONNECTED = '2041 2042 23EA 23EC 23ED 23EE 23EF 2514 2515 2516'.split()


def scenario(rom, source, edits):
    source = verified_rom(source)
    drafts = json.loads((ROOT/'translations/n64-special-followups.json').read_text())
    ids = [r['id'] for r in drafts]+['message:'+n for n in CONNECTED]+['message:203C']
    texts, ids, labels = menu_scenario(rom, edits, module_command_info(source), message_ids=ids)
    moods, mood_ids = mood_scenario(rom, source, edits, native_mood=True)
    actions = combine_checkpoints([texts, moods])
    return actions, {'messages': ids, 'choice_ids': labels, 'mood_messages': mood_ids,
                     'scope': 'Injected cartridge loads, native choice labels, and mood/timer order writes; '
                              'not normal sale, apology entry, rescue, reset, save, or hardware acceptance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--source-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); rom = args.rom.read_bytes()
    actions, report = scenario(rom, args.source_rom.read_bytes(), json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'rom_sha256': sha256(rom), 'actions': len(actions),
                      'output': str(args.output), **report}, indent=2))


if __name__ == '__main__':
    main()
