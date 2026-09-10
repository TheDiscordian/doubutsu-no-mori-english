"""Prepare the bounded installed classic-loader native scenario."""
import argparse
import json
from pathlib import Path
from aflib import by_vrom
from classic_letters import verify_installation


def scenario(native, built, report):
    verify_installation(built, native, report)
    files = by_vrom(built)
    request = {'module': report['runtime_module'], 'font_blob': files[0x03400000].extract(built).hex(),
               'catalog': files[0x030A0000].extract(built).hex()}
    return [{'wait': 8}, {'read': ['80000318', 4], 'expect': '00400000'},
            {'save_state': True}, {'pause_game_thread': True}, {'test_classic_letters': request},
            {'load_state': True}, {'resume': True}, {'wait': 2},
            {'read': ['8019B000', 4], 'expect': '00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=Path('build/classic-letters-pilot'))
    parser.add_argument('--output', type=Path, default=Path('build/classic-letter-scenario.json'))
    args = parser.parse_args()
    actions = scenario(Path('local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
