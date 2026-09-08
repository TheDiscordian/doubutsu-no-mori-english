#!/usr/bin/env python3
"""Batch native topic text, contextual answers, and mood orders in one checkpoint."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from actor_request_test_scenario import scenario as mood_scenario
from contextual_choice_test_scenario import scenario as choice_scenario
from message_alias_test_scenario import scenario as text_scenario
from runtime_module import module_command_info

ROOT = Path(__file__).resolve().parents[1]
CONNECTED = '1D4F 1D50 2058 2059 25FE 25FF 2600 207A 2771 2772'.split()


def combine_checkpoints(parts):
    """Keep every body assertion and restore the shared machine exactly once."""
    prefix = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]
    restore = [{'load_state': True}, {'resume': True}, {'wait': 2}]
    if not parts:
        raise ValueError('A native batch requires at least one complete scenario')
    result, reads, restored_bytes = list(prefix), {}, {}
    for actions in parts:
        states = [i for i, action in enumerate(actions) if 'load_state' in action]
        if (actions[:3] != prefix or len(states) != 1
                or sum('save_state' in a for a in actions) != 1
                or actions[states[0]:states[0]+3] != restore):
            raise ValueError('Native batch checkpoint setup or restoration differs')
        end = states[0]
        if any('resume' in a or 'pause_game_thread' in a for a in actions[3:end]):
            raise ValueError('Native batch cannot resume between injected groups')
        result.extend(actions[3:end])
        for action in actions[end+3:]:
            if set(action) != {'read', 'expect'}:
                raise ValueError('Native batch has a non-read action after restoration')
            key = tuple(action['read'])
            address = int(key[0], 16)
            expected = bytes.fromhex(action['expect'])
            if len(expected) != key[1]:
                raise ValueError('Native batch restored-memory length differs')
            for offset, value in enumerate(expected):
                at = address+offset
                if at in restored_bytes and restored_bytes[at] != value:
                    raise ValueError('Native batch restored-memory expectations conflict')
                restored_bytes[at] = value
            reads[key] = action
    return result+restore+list(reads.values())


def scenario(rom, source, edits):
    source = verified_rom(source)
    info = module_command_info(source)
    choices, choice_ids, cases = choice_scenario(rom, source, edits)
    moods, mood_ids = mood_scenario(rom, source, edits, native_mood=True)
    drafts = json.loads((ROOT/'translations/n64-topic-gaps.json').read_text())
    wanted = {r['id'] for r in drafts} | {'message:'+id for id in CONNECTED}
    extra_ids = sorted(wanted-set(choice_ids)-set(mood_ids))
    texts = text_scenario(rom, edits, info, message_ids=extra_ids)
    actions = combine_checkpoints([choices, texts, moods])
    return actions, {'contextual_messages': choice_ids, 'choice_cases': cases,
                     'additional_messages': extra_ids, 'mood_messages': mood_ids,
                     'scope': 'Injected native loads, answer labels/selections/branches, and mood orders; '
                              'not normal conversations, item transfers, saving, or hardware acceptance'}


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
