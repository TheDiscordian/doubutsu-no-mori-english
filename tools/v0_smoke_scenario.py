"""Reuse existing ordinary gameplay scenarios without producing repeated images."""
import argparse
import json
from pathlib import Path
from mail_glyph_creator_scenario import without_captures

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/v0-boot-scenario.json')
    parser.add_argument('--phase', choices=('arrival', 'housing', 'import-load', 'import-save'), default='arrival')
    args = parser.parse_args()
    actions = []
    if args.phase.startswith('import-'):
        # Reuse normal controller-driven loading/saving of the disposable town.
        # This does not replay the exhausted direct-allocation FlashRAM fixture.
        sources = ['v3_equipment_reload_gameplay']
        if args.phase == 'import-save':
            sources.append('v3_equipment_save_gameplay')
        for name in sources:
            existing = json.loads((ROOT/'tests/scenarios'/(name+'.json')).read_text())
            for action in without_captures(existing):
                if action.get('read') == ['8046C0DA', 1]:
                    # Old two-fan profile mask, not valid for select-all.
                    continue
                if action.get('read') == ['8046C350', 16]:
                    action['read'][0] = '8046C4E0'
                if action.get('snapshot_player'):
                    actions += [{'snapshot_message': True}, {'save_state': True},
                        {'read': ['80400000', 16], 'expect': 'AF53434EAF53434EAF53434EAF53434E'},
                        {'read': ['8044FFF0', 16], 'expect': 'AF53434EAF53434EAF53434EAF53434E'},
                        {'read': ['80400010', 8], 'expect': '7373000000000010'}]
                actions.append(action)
        actions += [
            {'read': ['8046C004', 4], 'expect': '00000000'},
            {'read': ['804E3000', 16], 'expect': '4146504200000000AF53B0DEAF53B0DE'},
            {'read': ['804F3010', 16], 'expect': 'AF53B0DEAF53B0DEAF53B0DEAF53B0DE'},
            {'read': ['806A90B0', 16], 'expect': 'AF4355DEAF4355DEAF4355DEAF4355DE'},
            {'save_state': True}, {'command': 'g'}]
        sources = ()
    else:
        sources = (('runtime-choice', 'arrival-gameplay') if args.phase == 'arrival'
                   else ('house-selection', 'house-inspection'))
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
                      'phase': args.phase, 'scope': 'Existing ordinary input flow; execution and chip inspection required for save/restart evidence'}))


if __name__ == '__main__':
    main()
