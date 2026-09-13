"""Measure frozen game pictures in a bounded interval of ordinary K.K. footage."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from v2_performance_smoke import ROM_SHA, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--start', type=float, required=True)
    parser.add_argument('--duration', type=float, required=True)
    args = parser.parse_args(); out = args.run.resolve()
    if (not out.is_relative_to(ROOT/'build') or args.start < 0
            or not 1 <= args.duration <= 300 or (out/'freeze-review.json').exists()):
        raise ValueError('Choose an unreviewed isolated run and bounded video interval')
    if json.loads((out/'run.json').read_text())['rom_sha256'] != ROM_SHA:
        raise ValueError('Performance review requires current V2-08')
    source = out/'footage.mkv'
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format',
        '-show_streams','-of','json',str(source)], text=True, timeout=15))
    if args.start+args.duration > float(probe['format']['duration']):
        raise ValueError('Requested interval extends beyond the completed recording')
    metadata = out/'freeze-metadata.txt'
    # Crop out the emulator, cursor, and changing VPS counter before measuring.
    filters = f'crop=752:564:8:34,freezedetect=n=0.001:d=0.5,metadata=mode=print:file={metadata}'
    result = subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','info',
        '-ss',str(args.start),'-i',str(source),'-t',str(args.duration),'-an',
        '-vf',filters,'-f','null','-'], text=True, capture_output=True, timeout=90)
    (out/'freeze-review.log').write_text(result.stderr)
    result.check_returncode()
    events = re.findall(r'lavfi\.freezedetect\.(freeze_start|freeze_duration|freeze_end)=([0-9.]+)', metadata.read_text())
    counts = re.findall(r'frame=\s*(\d+)',result.stderr)
    frames = int(counts[-1]) if counts else 0
    if frames < (args.duration-.1)*30:
        raise ValueError('Video analysis did not cover the complete interval')
    report = {'rom_sha256':ROM_SHA,'footage_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'interval_start_seconds':args.start,'interval_duration_seconds':args.duration,
        'analysed_frames':frames,'game_crop':[8,34,752,564],'noise_tolerance':0.001,
        'minimum_freeze_seconds':0.5,'events':events,
        'no_half_second_freezes':not events,'hardware_test':False,'audio_audition':False}
    (out/'freeze-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
