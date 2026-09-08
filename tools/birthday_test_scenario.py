#!/usr/bin/env python3
"""Batch birthday/date requests and contextual answers; optionally test NPC mail."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from calendar_quiz_test_scenario import scenario as calendar_scenario
from npc_mail_loader_test_scenario import scenario as loader_scenario
from topic_gap_test_scenario import combine_checkpoints


def scenario(rom, source, module, edits, *, include_npc_loader=False):
    source = verified_rom(source)
    calendar,ids,cases = calendar_scenario(rom,source,module,edits)
    parts = [calendar]
    if include_npc_loader:
        parts.append(loader_scenario(rom,source,module))
    return combine_checkpoints(parts),ids,cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--source-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module',type=Path,required=True)
    parser.add_argument('--translations',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--include-npc-loader',action='store_true',
                        help='Requires an isolated matching-ROM town checkpoint')
    args = parser.parse_args();rom = args.rom.read_bytes()
    actions,ids,cases = scenario(rom,args.source_rom.read_bytes(),json.loads(args.module.read_text()),
                               json.loads(args.translations.read_text()),
                               include_npc_loader=args.include_npc_loader)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'rom_sha256':sha256(rom),'actions':len(actions),'messages':ids,'choice_cases':cases,
        'npc_mail_loader_included':args.include_npc_loader,
        'scope':'Injected native birthday/calendar requests, complete field insertions, answer branches, '
                'and cartridge-created letters; not normal conversations, delivery, saves, or hardware'},indent=2))


if __name__ == '__main__': main()
