"""Decode and inspect a finished trailer silently; produce local review frames."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def run(command):
    return subprocess.run(command,capture_output=True,text=True,check=True,timeout=90)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    args=parser.parse_args();directory=args.directory.resolve()
    if not directory.is_relative_to(ROOT/'build'):raise ValueError('Use an ignored local build')
    final=directory/'Animal Forest English - Trailer.mp4'
    review=directory/'review';review.mkdir(exist_ok=False)
    base=['ffmpeg','-nostdin','-hide_banner','-i',str(final)]
    decoded=run(base+['-v','error','-f','null','-'])
    (review/'decode.log').write_text(decoded.stderr)
    music=run(base+['-vn','-af','loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
    (review/'audio.log').write_text(music.stderr)
    levels=json.loads(music.stderr[music.stderr.rfind('{'):music.stderr.rfind('}')+1])
    # Time labels are review-only. None are added to the deliverable.
    run(base+['-vf',"fps=1,scale=384:216,drawtext=fontfile=/usr/share/fonts/noto/NotoSans-Bold.ttf:"
         "text='%{pts\\:hms}':fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7:x=6:y=6,tile=5x4",
         '-fps_mode','vfr',str(review/'timeline-%02d.png')])
    edit=json.loads((directory/'edit.json').read_text());at=0;boundaries=[]
    for cut in edit['cuts'][:-1]:
        at+=cut['frames'];boundaries.append(at/30)
    for index,seconds in enumerate(boundaries):
        run(['ffmpeg','-nostdin','-v','error','-ss',str(seconds-.10),'-i',str(final),
             '-vf','fps=10,scale=480:270,tile=4x1','-frames:v','1',
             str(review/f'transition-{index+1:02d}.png')])
    seconds_at=0;midpoints=[]
    for cut in edit['cuts']:
        midpoints.append(round(seconds_at+cut['frames']/60,1))
        seconds_at+=cut['frames']/30
    for seconds in sorted(set([10,66,*midpoints])):
        run(['ffmpeg','-nostdin','-v','error','-ss',str(seconds),'-i',str(final),
             '-frames:v','1',str(review/f'frame-{seconds:05.1f}.png')])
    report={'video_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),
            'full_decode':'passed','duration':seconds_at,'transition_times':boundaries,
            'full_frame_review_times':sorted(set([10,66,*midpoints])),
            'audio_integrated_lufs':levels['input_i'],'audio_true_peak_dbtp':levels['input_tp'],
            'physical_playback':False,'visual_inspection':'pending; inspect generated frames'}
    (review/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
