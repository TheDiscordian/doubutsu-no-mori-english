"""Compose and render the trailer's original instrumental, without audio playback."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PPQ=480
TEMPO=500000
SOUNDFONT=Path('/usr/share/soundfonts/FluidR3_GM.sf2')


def vlq(n):
    result=[n&127]
    while n>>7:
        n>>=7;result.insert(0,(n&127)|128)
    return bytes(result)


def midi():
    events=[(0,b'\xff\x51\x03'+TEMPO.to_bytes(3,'big'))]
    def event(beat,raw): events.append((round(beat*PPQ),bytes(raw)))
    def note(ch,pitch,beat,length,velocity):
        assert 0<=pitch<=127 and length>0 and 1<=velocity<=127
        event(beat,[0x90|ch,pitch,velocity]);event(beat+length,[0x80|ch,pitch,0])
    # Nylon guitar, marimba, acoustic bass, warm electric piano, celesta,
    # and restrained brushed-kit percussion. All musical phrases are original.
    for ch,program,pan,volume in ((0,24,43,88),(1,12,72,91),(2,32,64,92),
                                 (3,4,78,67),(4,8,51,61),(9,0,64,73)):
        event(0,[0xC0|ch,program]);event(0,[0xB0|ch,10,pan])
        event(0,[0xB0|ch,7,volume]);event(0,[0xB0|ch,91,30])
    chords=[(36,[60,64,67,71,74]),(33,[60,64,67,69,71]),
            (38,[60,62,65,69,76]),(31,[59,62,65,69,76]),
            (29,[60,64,65,69,72]),(40,[59,62,64,67,74]),
            (38,[60,62,65,69,76]),(31,[59,62,65,69,76])]
    melody=[
        [67,72,76,79,76,74,72], [69,72,76,79,76,74,71],
        [69,74,77,76,74,72,69], [71,74,79,77,76,74,71],
        [72,76,81,79,76,74,72], [67,71,74,79,81,79,76],
        [69,72,77,76,74,72,69], [71,74,77,74,72,76,79]]
    starts=[0,0.75,1.25,1.75,2.5,3,3.5]
    lengths=[0.58,0.36,0.36,0.58,0.35,0.35,0.38]
    for bar in range(24):
        beat=bar*4;root,chord=chords[bar%8]
        if bar==23: root,chord=36,[60,64,67,69,74]
        # Light, syncopated strums with a tiny natural spread.
        for strum,vel in ((0,65),(1.5,57),(2.75,62)) if bar<23 else ((0,69),):
            for i,pitch in enumerate(chord[:4]):
                note(0,pitch,beat+strum+i*0.024,0.65 if bar<23 else 3.6,vel-i*2)
        for pitch in chord[1:]: note(3,pitch,beat+0.03,3.2 if bar<23 else 5.4,43)
        for pos,pitch in ((0,root),(1.5,root+12),(2.5,root+7),(3.5,root+12)):
            if bar==23 and pos:continue
            note(2,pitch,beat+pos,0.75 if bar<23 else 3.8,83 if pos==0 else 64)
        if 2<=bar<23:
            for i,(pitch,at,duration) in enumerate(zip(melody[(bar-2)%8],starts,lengths)):
                if 18<=bar<=19 and i%2:continue
                note(1,pitch,beat+at,duration,82+(i%3)*4)
            if bar%4==1:
                for i,pitch in enumerate(reversed(chord[-3:])):
                    note(4,pitch+12,beat+2.75+i*0.375,0.3,48)
        elif bar<2:
            for i,pitch in enumerate((72,76,79,76)):
                note(4,pitch,beat+i,0.72,60)
        else:
            for ch,pitch,velocity in ((1,84,91),(4,79,57),(4,88,46)):
                note(ch,pitch,beat,3.8,velocity)
        if 2<=bar<23:
            for pos,vel in ((0,77),(2,66)):
                note(9,36,beat+pos,0.12,vel)
            for pos in (1,3): note(9,37,beat+pos,0.10,62)
            for i in range(8):
                note(9,42,beat+i*0.5+(0.06 if i%2 else 0),0.08,39 if i%2 else 53)
            if bar in (9,17,21):
                for i in range(3):note(9,76+i%2,beat+3+i*0.25,0.10,54+i*5)
    # Let the resolving chord breathe; MIDI ends at fifty seconds.
    event(100,b'\xff\x2f\x00')
    events.sort(key=lambda e:(e[0],0 if e[1][0]&0xF0==0x80 else 1))
    track=bytearray();previous=0
    for tick,raw in events:track+=vlq(tick-previous)+raw;previous=tick
    return b'MThd'+struct.pack('>IHHH',6,0,1,PPQ)+b'MTrk'+struct.pack('>I',len(track))+track


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve()
    if not out.is_relative_to(ROOT/'build'):raise ValueError('Music outputs must stay in ignored build/')
    out.mkdir(parents=True,exist_ok=False)
    (out/'first-day-new-neighbours.mid').write_bytes(midi())
    env=dict(os.environ,SDL_AUDIODRIVER='dummy',PULSE_SERVER='unix:/nonexistent-af-music')
    render=subprocess.run(['fluidsynth','-ni','-a','file','-T','wav','-F',str(out/'music-raw.wav'),
        '-r','48000','-g','0.65',str(SOUNDFONT),str(out/'first-day-new-neighbours.mid')],
        env=env,check=True,capture_output=True,text=True,timeout=60)
    (out/'render.log').write_text(render.stdout+render.stderr)
    filters='atrim=0:50,afade=t=in:d=0.06,afade=t=out:st=48.5:d=1.5,loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json'
    result=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-i',str(out/'music-raw.wav'),
        '-af',filters,'-ar','48000','-c:a','pcm_s24le',str(out/'soundtrack.wav')],
        check=True,capture_output=True,text=True,timeout=60)
    (out/'mastering.log').write_text(result.stderr)
    (out/'SOUNDFONT-LICENSE.txt').write_bytes(Path('/usr/share/licenses/soundfont-fluid/COPYING').read_bytes())
    report={'title':'First Day, New Neighbours','composition':'Original melody and arrangement for this trailer',
        'tempo_bpm':120,'bars':24,'duration_seconds':50,'speaker_playback':False,
        'soundfont':SOUNDFONT.name,'soundfont_sha256':hashlib.sha256(SOUNDFONT.read_bytes()).hexdigest(),
        'soundfont_copyright':'Copyright (c) 2000-2002, 2008 Frank Wen',
        'soundfont_license':'MIT; full notice in SOUNDFONT-LICENSE.txt',
        'sources':{'tools/trailer_music.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'soundtrack_sha256':hashlib.sha256((out/'soundtrack.wav').read_bytes()).hexdigest(),
        'listening_review':'Not auditioned through physical audio output'}
    (out/'music.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
