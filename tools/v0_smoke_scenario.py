"""Reuse existing ordinary gameplay scenarios without producing repeated images."""
import argparse
import json
from pathlib import Path
from mail_glyph_creator_scenario import without_captures

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/v0-boot-scenario.json')
    parser.add_argument('--phase', choices=('arrival', 'housing'), default='arrival')
    args = parser.parse_args()
    sources = ('runtime-choice', 'arrival-gameplay') if args.phase == 'arrival' else ('house-selection', 'house-inspection')
    actions = []
    if args.phase == 'housing':
        actions += [{'snapshot_player': True}, {'snapshot_inventory': True},
                    {'key': 'Return', 'duration': 0.08}, {'wait': 3}, {'snapshot_submenu': True},
                    {'key': 'Return', 'duration': 0.08}, {'wait': 3}]
    for name in sources:
        actions += without_captures(json.loads((ROOT/'tests'/(name+'-scenario.json')).read_text()))
    if args.phase == 'housing':
        actions += [{'snapshot_player': True}, {'snapshot_inventory': True}, {'snapshot_submenu': True}]
    actions += [{'read': ['8019C8D0', 16], 'expect': 'AF32C0DEAF32C0DEAF32C0DEAF32C0DE'}]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'output': str(args.output), 'actions': len(actions), 'screenshots': 0,
                      'phase': args.phase, 'scope': 'Existing ordinary input flow; not a save/restart claim'}))


if __name__ == '__main__':
    main()
