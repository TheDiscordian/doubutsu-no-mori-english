"""Recorded ordinary controller input on the isolated current-ROM performance run."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time

from emulator_smoke import Keyboard
from v2_performance_smoke import ROM_SHA, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--display', required=True)
    parser.add_argument('--actions', default='[]', help='JSON key/duration or wait actions')
    parser.add_argument('--capture', required=True)
    args = parser.parse_args(); out = args.run.resolve()
    if not out.is_relative_to(ROOT/'build') or not re.fullmatch(r':[2-9][0-9]{2}', args.display):
        raise ValueError('Use an isolated test run and reserved X display')
    if json.loads((out/'run.json').read_text())['rom_sha256'] != ROM_SHA:
        raise ValueError('Ordinary performance check requires current V2-08')
    if not re.fullmatch(r'[a-z0-9-]+\.png', args.capture) or (out/args.capture).exists():
        raise ValueError('Choose a fresh simple capture name')
    actions = json.loads(args.actions)
    if not isinstance(actions, list) or len(actions) > 30:
        raise ValueError('Bounded controller action list required')
    duration = 0
    for action in actions:
        if set(action) == {'key', 'duration'}:
            if action['key'] not in ('a','b','Return','w','s','f','g','Up','Down','Left','Right','F5'):
                raise ValueError('Unsupported ordinary controller input')
            seconds = action['duration']
        elif set(action) == {'wait'}:
            seconds = action['wait']
        else:
            raise ValueError('Only controller input and waits are allowed')
        if not 0 <= seconds <= 20: raise ValueError('Action duration exceeds limit')
        duration += seconds
    if duration > 55: raise ValueError('Keep each live input batch below one minute')
    receipt = out/'ordinary-controls.jsonl'
    def record(value):
        recording = json.loads((out/'recording.json').read_text())
        latest = recording['markers'][-1]['seconds']
        origin = (out/'recording.json').stat().st_mtime-latest
        with receipt.open('a') as stream:
            stream.write(json.dumps({'approx_video_seconds':round(time.time()-origin,3), **value})+'\n')
    keyboard = Keyboard(args.display)
    for action in actions:
        record(action)
        if 'key' in action: keyboard.press(action['key'], action['duration'])
        else: time.sleep(action['wait'])
    subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-f','x11grab','-draw_mouse','0',
                    '-video_size','800x640','-i',args.display,'-frames:v','1',str(out/args.capture)],
                   check=True, timeout=10)
    record({'capture':args.capture})
    print(out/args.capture)


if __name__ == '__main__': main()
