"""Reuse existing ordinary gameplay scenarios without producing repeated images."""
import argparse
import json
from pathlib import Path
from mail_glyph_creator_scenario import without_captures

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/v0-boot-scenario.json')
    args = parser.parse_args()
    actions = without_captures(json.loads((ROOT/'tests/runtime-choice-scenario.json').read_text()))
    actions += without_captures(json.loads((ROOT/'tests/arrival-gameplay-scenario.json').read_text()))
    actions += [{'read': ['8019C8D0', 16], 'expect': 'AF32C0DEAF32C0DEAF32C0DEAF32C0DE'}]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'output': str(args.output), 'actions': len(actions), 'screenshots': 0,
                      'scope': 'Existing name/town/train/arrival flow; not a save/restart claim'}))


if __name__ == '__main__':
    main()
