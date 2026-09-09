#!/usr/bin/env python3
"""Batch installed glyph creators against original native choices and delivery."""

import argparse
import json
from pathlib import Path

from academy_score_scenario import scenario as score_scenario
from mother_letter_scenario import scenario as mother_scenario
from npc_mail_loader_test_scenario import scenario as npc_scenario
from villager_event_scenario import scenario as event_scenario
from topic_gap_test_scenario import combine_checkpoints


def scenario(native,built,report):
    if report['runtime_module']['npc_mail_loader']['overlay'].get('mail_glyphs') is not True:
        raise ValueError('Complete glyph creator integration is required')
    batches = [mother_scenario(native,built,report),event_scenario(native,built,report),
               score_scenario(native,built,report),npc_scenario(built,native,report['runtime_module'])]
    # Each native test restores its own live save/globals and allocations. One
    # outer checkpoint also restores scratch and resumes the original thread.
    return combine_checkpoints(batches)


def without_captures(actions):
    result = []
    for action in actions:
        value = {k:v for k,v in action.items() if k!='capture'}
        if 'actions' in value: value['actions'] = without_captures(value['actions'])
        if value: result.append(value)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/mail-glyph-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--boot-output',type=Path,help='Also prepare the existing boot-to-town scenario without screenshots')
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    if args.boot_output:
        root = Path(__file__).resolve().parents[1]
        boot = without_captures(json.loads((root/'tests/runtime-choice-scenario.json').read_text()))
        args.boot_output.parent.mkdir(parents=True,exist_ok=True)
        args.boot_output.write_text(json.dumps(boot,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'creator_batches':4,'cartridge_loading':True,
                      'save_round_trip':False,'hardware_validation':False}))


if __name__ == '__main__': main()
