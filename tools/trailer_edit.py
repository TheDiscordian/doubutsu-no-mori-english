"""Build the private fifty-second trailer from explicitly approved footage."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from html import escape
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ROM_SHA='259543536db43733d4a73ede05949ba52b1ce4ac3c557fc1c8e97b205856ad12'
# Explicit allowlist: the rejected mistyped-name take is never an input.
FOOTAGE={'title':'build/trailer-title-01','town':'build/trailer-town-02',
         'keyboard':'build/trailer-keyboard-02','explore':'build/trailer-explore-01'}
CUTS=[
    {'kind':'intro','duration':4},
    {'kind':'hero','source':'title','start':12.5,'duration':4},
    {'kind':'feature','source':'town','start':51.8,'duration':6,'number':'01',
     'eyebrow':'A LITTLE ESCAPE','lines':['Your town.','Your pace.'],
     'detail':['The Nintendo 64 original.','A new English welcome.']},
    {'kind':'feature','source':'keyboard','start':21.5,'duration':6,'number':'02',
     'eyebrow':'FAMILIAR FACES','lines':['Say','hello.'],
     'detail':['Conversations with character.','And plenty of personality.']},
    {'kind':'feature','source':'town','start':61.2,'duration':4,'number':'03',
     'eyebrow':'LITTLE EVERYDAY JOYS','lines':['Little finds.','Big plans.'],
     'detail':['English menus.','Original charm.']},
    {'kind':'feature','source':'keyboard','start':4.6,'duration':6,'number':'04',
     'eyebrow':'MAKE IT PERSONAL','lines':['Make it','yours.'],
     'detail':['An English keyboard,','with N64 character.']},
    {'kind':'keyboard','source':'keyboard','start':15.4,'duration':4},
    {'kind':'feature','source':'explore','start':8.3,'duration':6,'number':'05',
     'eyebrow':'STAY A LITTLE LONGER','lines':['One more','little stroll.'],
     'detail':['Quiet nights.','A town to call home.']},
    {'kind':'hero','source':'title','start':22,'duration':4},
    {'kind':'outro','duration':6},
]
MUSIC=ROOT/'build/trailer-music-01/soundtrack.wav'
FONT='/usr/share/fonts/noto/NotoSans-Black.ttf'
SERIF='/usr/share/fonts/noto/NotoSerifDisplay-Black.ttf'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams',
                                               '-of','json',str(path)],text=True,timeout=20))


def text(x,y,s,size=36,colour='#183E31',family='Noto Sans',weight=700,anchor='start'):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" fill="{colour}">{escape(s)}</text>')


def artwork(cut):
    dark=cut['kind'] in ('intro','hero','outro')
    bg='#163E32' if dark else '#F4EDDD'; ink='#F4EDDD' if dark else '#163E32'
    shapes=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">',
        '<defs><pattern id="paper" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="3" cy="4" r="1" fill="#9B986E" opacity=".16"/></pattern>',
        '<path id="leaf" d="M0 0 C-75-15-105-105-95-165 C-5-165 55-75 0 0Z"/></defs>',
        f'<rect width="1920" height="1080" fill="{bg}"/><rect width="1920" height="1080" fill="url(#paper)"/>']
    for x,y,angle,scale in ((180,1000,-30,2),(1840,220,140,2.6),(1800,1060,55,1.5),(80,170,-90,1.2)):
        shapes.append(f'<use href="#leaf" transform="translate({x} {y}) rotate({angle}) scale({scale})" fill="#91BA64" opacity=".16"/>')
    kind=cut['kind']
    if kind=='feature':
        shapes.extend(['<rect x="562" y="94" width="1296" height="972" rx="12" fill="#163E32" opacity=".12"/>',
                       '<rect x="552" y="78" width="1296" height="972" rx="12" fill="#FFFDF6"/>',
                       '<circle cx="114" cy="158" r="34" fill="#E9BC4B"/>',
                       text(114,171,cut['number'],34,anchor='middle'),
                       text(76,240,cut['eyebrow'],22),
                       '<rect x="76" y="269" width="96" height="6" rx="3" fill="#CD7548"/>'])
        for i,line in enumerate(cut['lines']):shapes.append(text(72,428+i*107,line,78,family='Noto Serif Display',weight=900))
        for i,line in enumerate(cut['detail']):shapes.append(text(78,697+i*47,line,28,weight=400))
        shapes.append(text(78,1000,'ANIMAL FOREST ENGLISH / V2',18))
    elif kind=='hero':
        for i,line in enumerate(['THE','N64','ORIGINAL.']):shapes.append(text(34,418+i*52,line,29,ink))
        for i,line in enumerate(['NOW','IN','ENGLISH.']):shapes.append(text(1698,418+i*52,line,29,ink))
        shapes.append(text(36,998,'FAN PROJECT',17,ink))
        shapes.append(text(1700,998,'V2 PREVIEW',17,ink))
    elif kind=='keyboard':
        shapes.append(text(960,97,'ENGLISH KEYS. N64 SOUL.',55,anchor='middle',weight=900))
        shapes.append('<rect x="116" y="162" width="1688" height="848" rx="18" fill="#FFFDF6"/>')
    elif kind=='intro':
        shapes.extend(['<rect x="650" y="184" width="620" height="60" rx="30" fill="#E9BC4B"/>',
                       text(960,225,'ONE LITTLE CARTRIDGE.',28,anchor='middle'),
                       text(960,972,'THE NINTENDO 64 ORIGINAL • AN ENGLISH FAN TRANSLATION',25,ink,anchor='middle')])
    elif kind=='outro':
        shapes.extend([text(960,180,'DOUBUTSU NO MORI  /  NINTENDO 64',27,ink,anchor='middle'),
                       text(960,370,'ANIMAL FOREST',132,ink,'Noto Serif Display',900,'middle'),
                       text(960,530,'ENGLISH',150,'#E9BC4B','Noto Sans',900,'middle'),
                       '<rect x="733" y="578" width="454" height="54" rx="27" fill="#F4EDDD"/>',
                       text(960,613,'UNOFFICIAL FAN TRANSLATION',22,anchor='middle'),
                       text(960,906,'V2 PREVIEW • EXPANSION PAK REQUIRED',25,ink,anchor='middle'),
                       text(960,997,'Game footage © Nintendo. Unofficial fan project.',19,ink,weight=400,anchor='middle')])
    shapes.append('</svg>');return '\n'.join(shapes)


def inputs():
    report={}
    for key,directory in FOOTAGE.items():
        folder=ROOT/directory;run=json.loads((folder/'run.json').read_text())
        if run['rom_sha256']!=ROM_SHA:raise ValueError('Footage uses another cartridge')
        info=probe(folder/'footage.mkv')
        report[key]={'directory':directory,'sha256':sha(folder/'footage.mkv'),
                     'recording_sha256':sha(folder/'recording.json'),'duration':float(info['format']['duration'])}
    rows=json.loads((ROOT/FOOTAGE['keyboard']/'results.json').read_text())
    names=[r['text_hex'] for r in rows if 'text_hex' in r]
    if names!=['466165202020']:raise ValueError('Only the corrected Fae keyboard take is approved')
    for cut in CUTS:
        if 'source' in cut and cut['start']+cut['duration']+.25>report[cut['source']]['duration']:
            raise ValueError('Shot exceeds its approved footage')
    return report


def render_cut(index,cut,out):
    duration=cut['duration']+(0.25 if index<len(CUTS)-1 else 0)
    svg=out/f'{index:02d}.svg';png=out/f'{index:02d}.png'
    svg.write_text(artwork(cut))
    subprocess.run(['rsvg-convert',str(svg),'-o',str(png)],check=True,capture_output=True,timeout=20)
    args=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-filter_complex_threads','2',
          '-loop','1','-framerate','30','-i',str(png)]
    filters=['[0:v]format=yuv420p,setsar=1,settb=AVTB[bg]'];result='bg'
    if 'source' in cut:
        args+=['-ss',str(cut['start']),'-i',str(ROOT/FOOTAGE[cut['source']]/'footage.mkv')]
        if cut['kind']=='feature':
            crop='752:564:8:34';size='1264:948';x,y=568,90
        elif cut['kind']=='keyboard':
            crop='576:288:96:292';size='1664:832';x,y=128,170
        else:
            crop='752:564:8:34';size='1440:1080';x,y=240,0
        filters.append(f'[1:v]crop={crop},scale={size}:flags=lanczos,setsar=1,fps=30,settb=AVTB,setpts=PTS-STARTPTS[game]')
        filters.append(f'[bg][game]overlay={x}:{y}:shortest=1[composed]');result='composed'
    if cut['kind']=='intro':
        filters.append(f"[{result}]drawtext=fontfile={SERIF}:text='N64 roots.':fontsize=154:fontcolor=0xF4EDDD:x=(w-tw)/2:y=410-45*exp(-7*t):alpha='min(1,t*4)',"
            f"drawtext=fontfile={SERIF}:text='A new welcome.':fontsize=135:fontcolor=0xE9BC4B:x=(w-tw)/2:y='624+55*exp(-7*max(0,t-0.5))':alpha='min(1,max(0,t-0.5)*4)'[type]")
        result='type'
    if cut['kind']=='outro':
        filters.append(f"[{result}]drawtext=fontfile={SERIF}:text='Make yourself at home.':fontsize=62:fontcolor=0xF4EDDD:x=(w-tw)/2:y=733+28*exp(-6*t):alpha='min(1,t*3)',fade=t=out:st=5.55:d=0.45[type]")
        result='type'
    filters.append(f'[{result}]trim=duration={duration},fps=30,format=yuv420p[v]')
    args+=['-filter_complex',';'.join(filters),'-map','[v]','-an','-t',str(duration),
           '-c:v','libx264','-threads','4','-preset','medium','-crf','16',str(out/f'{index:02d}.mkv')]
    completed=subprocess.run(args,capture_output=True,text=True,timeout=180)
    (out/f'{index:02d}.log').write_text(completed.stderr)
    if completed.returncode:raise RuntimeError(f'Shot {index} failed: '+completed.stderr[-3000:])
    return index


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    if not out.is_relative_to(ROOT/'build'):raise ValueError('Trailer output must stay in ignored build/')
    footage=inputs();out.mkdir(parents=True,exist_ok=False)
    (out/'edit.json').write_text(json.dumps({'cuts':CUTS,'footage':footage,'music_sha256':sha(MUSIC)},indent=2)+'\n')
    with ThreadPoolExecutor(max_workers=2) as pool:
        for index in pool.map(lambda pair:render_cut(*pair,out),enumerate(CUTS)):
            print(f'Shot {index+1}/{len(CUTS)} rendered',flush=True)
    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','warning','-filter_complex_threads','2']
    for i in range(len(CUTS)):command+=['-i',str(out/f'{i:02d}.mkv')]
    command+=['-i',str(MUSIC)];filters=[]
    for i in range(len(CUTS)):filters.append(f'[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]')
    offset=0;previous='v0';transitions=['fade','smoothleft','fade','wipeleft','smoothleft','circleopen','fade','smoothleft','fade']
    for i in range(1,len(CUTS)):
        offset+=CUTS[i-1]['duration'];result=f'x{i}'
        filters.append(f'[{previous}][v{i}]xfade=transition={transitions[i-1]}:duration=0.25:offset={offset}[{result}]')
        previous=result
    command+=['-filter_complex',';'.join(filters),'-map',f'[{previous}]','-map',f'{len(CUTS)}:a',
        '-t','50','-r','30','-c:v','libx264','-threads','4','-preset','slow','-crf','17',
        '-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-movflags','+faststart',
        '-metadata','title=Animal Forest English — Make Yourself at Home',
        '-metadata','comment=Unofficial fan translation. Private trailer; no public release authorised.',
        str(out/'Animal Forest English - Trailer.mp4')]
    joined=subprocess.run(command,capture_output=True,text=True,timeout=300)
    (out/'encode.log').write_text(joined.stderr)
    if joined.returncode:raise RuntimeError(joined.stderr[-4000:])
    final=out/'Animal Forest English - Trailer.mp4';info=probe(final)
    report={'output':str(final.relative_to(ROOT)),'sha256':sha(final),'bytes':final.stat().st_size,
            'rom_sha256':ROM_SHA,'duration':float(info['format']['duration']),
            'public_release':False,'speaker_playback':False,'approved_player_name':'Fae',
            'sources':{p:sha(ROOT/p) for p in ('tools/trailer_edit.py','tools/trailer_music.py','tools/trailer_capture.py')},
            'visual_review':'pending'}
    (out/'video.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
