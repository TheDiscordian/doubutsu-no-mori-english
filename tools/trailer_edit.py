"""Edit a game-led private trailer to the cartridge's actual opening theme."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from html import escape
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ROM_SHA='259543536db43733d4a73ede05949ba52b1ce4ac3c557fc1c8e97b205856ad12'
FPS=30
TOTAL_FRAMES=1995
DURATION=TOTAL_FRAMES/FPS
# Every source is explicitly approved. No wildcard can admit the rejected name take.
FOOTAGE={'opening':'build/trailer-opening-01','kk':'build/trailer-kk-01',
         'keyboard':'build/trailer-keyboard-03','day':'build/trailer-daytime-02',
         'board':'build/trailer-board-02','map':'build/trailer-map-01',
         'nook_exterior':'build/trailer-nook-04','shop':'build/trailer-nook-08',
         'catalogue':'build/trailer-catalogue-03','bridge':'build/trailer-post-route-03',
         'post_exterior':'build/trailer-post-01','post':'build/trailer-post-02',
         'payment':'build/trailer-post-04'}
# Boundaries follow the original recording's approximately 118-BPM phrasing,
# quantised to video frames. K.K.'s actual words replace promotional copy.
CUTS=[
    {'source':'opening','start':0,'frames':367,'kind':'opening',
     'purpose':'Native N64 opening chime, train arrival, and animated English title'},
    {'source':'kk','start':28.5,'frames':122,'kind':'game',
     'purpose':'K.K. welcomes the player to living on their own'},
    {'source':'kk','start':44.8,'frames':122,'kind':'game','transition':'fade',
     'purpose':'You can do what you like, whenever you feel like it'},
    {'source':'keyboard','start':6.65,'frames':244,'kind':'game','transition':'circleopen',
     'purpose':'Enter Fae using the corrected English keyboard, with case switching'},
    {'source':'keyboard','start':25.9,'frames':122,'kind':'game',
     'purpose':'Rover reacts to the same name and laughs in English'},
    {'source':'map','start':3.0,'frames':61,'kind':'game','transition':'circleopen',
     'purpose':'Orient the town tour with the English map and player-home labels'},
    {'source':'nook_exterior','start':9.8,'frames':61,'kind':'game',
     'purpose':"Visit the translated Nook's Cranny storefront"},
    {'source':'shop','start':24.45,'frames':122,'kind':'game',
     'purpose':'Tom Nook offers the English shop choices beside the translated funds bubble'},
    {'source':'catalogue','start':11.7,'frames':122,'kind':'game','transition':'fade',
     'purpose':'Browse English catalogue names and Bells prices with a real selection change'},
    {'source':'bridge','start':5.3,'frames':61,'kind':'game','transition':'fade',
     'purpose':'Cross the river on the way to the next town service'},
    {'source':'post_exterior','start':10.0,'frames':61,'kind':'game',
     'purpose':'Show the English Post Office and Melody signs before going inside'},
    {'source':'post','start':17.1,'frames':61,'kind':'game',
     'purpose':'Pelly presents the English mail and deposit choices inside the post office'},
    {'source':'payment','start':6.7,'frames':122,'kind':'game','transition':'fade',
     'purpose':'Show the translated repayment amount entry and confirmation labels'},
    {'source':'day','start':8.5,'frames':61,'kind':'game','transition':'fade',
     'purpose':'Native inventory opens with English labels and item name'},
    {'source':'board','start':11.1,'frames':122,'kind':'game','transition':'fade',
     'purpose':'Read an actual translated notice on the bulletin board'},
    {'source':'opening','start':57.5,'frames':164,'kind':'ending','transition':'circleopen',
     'purpose':'Return to the English title over the final musical phrase'},
]
for cut in CUTS:cut['duration']=cut['frames']/FPS


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams',
                                               '-of','json',str(path)],text=True,timeout=20))


def artwork(cut):
    """Transparent, compact feature labels; never a replacement for game footage."""
    kind=cut['kind']
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">']
    def line(y,words,size=42,colour='#FFF9E8',weight=800):
        return (f'<text x="960" y="{y}" text-anchor="middle" font-family="DM Sans" '
                f'font-weight="{weight}" font-size="{size}" fill="{colour}">{escape(words)}</text>')
    if kind=='opening':
        parts+=['<rect x="590" y="40" width="740" height="82" rx="41" fill="#173A29" fill-opacity=".94"/>',
                line(95,'The N64 original, in English.',40)]
    elif kind=='ending':
        parts+=['<defs><linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">'
                '<stop offset="0" stop-color="#0E281F" stop-opacity="0"/>'
                '<stop offset=".4" stop-color="#0E281F" stop-opacity=".92"/>'
                '<stop offset="1" stop-color="#0E281F"/></linearGradient></defs>',
                '<rect x="0" y="825" width="1920" height="255" fill="url(#shade)"/>',
                line(944,'Animal Forest English',68),
                line(994,'Welcome home.',38,weight=600),
                line(1040,'V2 PREVIEW  •  EXPANSION PAK REQUIRED  •  UNOFFICIAL FAN TRANSLATION',22,weight=600),
                line(1069,'Game and music © Nintendo',17,weight=500)]
    parts.append('</svg>');return '\n'.join(parts)


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
        if cut['start']+cut['duration']+.3>report[cut['source']]['duration']:
            raise ValueError('Shot exceeds its approved footage: '+cut['purpose'])
    assert sum(c['frames'] for c in CUTS)==TOTAL_FRAMES
    return report


def render_music(out):
    """Keep the native opening intact; master only its level and closing tail."""
    source=ROOT/FOOTAGE['opening']/'footage.mkv'
    common=['ffmpeg','-nostdin','-hide_banner','-i',str(source),'-map','0:a','-t',str(DURATION)]
    measured=subprocess.run(common+['-af','loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json',
                                    '-f','null','-'],capture_output=True,text=True,check=True,timeout=60)
    (out/'music-measure.log').write_text(measured.stderr)
    data=json.loads(measured.stderr[measured.stderr.rfind('{'):measured.stderr.rfind('}')+1])
    mastering=('afade=t=out:st=65.8:d=0.7,loudnorm=I=-18:TP=-1.5:LRA=11:linear=true:'
               f"measured_I={data['input_i']}:measured_TP={data['input_tp']}:"
               f"measured_LRA={data['input_lra']}:measured_thresh={data['input_thresh']}:"
               f"offset={data['target_offset']}:print_format=json")
    result=subprocess.run(common+['-af',mastering,'-ar','48000','-c:a','pcm_s24le',str(out/'soundtrack.wav')],
                          capture_output=True,text=True,check=True,timeout=60)
    (out/'music-master.log').write_text(result.stderr)
    (out/'music.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),
        'source_sha256':sha(source),'description':'Native N64 opening chime and Doubutsu no Mori title theme',
        'copyright':'Nintendo; game recording remains local and private',
        'arrangement':'Original in-game sequence; no replacement composition or tempo alteration',
        'duration':DURATION,'output_sha256':sha(out/'soundtrack.wav'),
        'speaker_playback':False,'listening_review':'Not auditioned through physical audio outputs'},indent=2)+'\n')


def render_cut(index,cut,out):
    # Supply transition handles at the end, so all musical boundary frames stay fixed.
    frames=cut['frames']+(9 if index<len(CUTS)-1 and CUTS[index+1].get('transition') else 0)
    duration=frames/FPS
    source=ROOT/FOOTAGE[cut['source']]/'footage.mkv'
    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-filter_complex_threads','2',
             '-ss',str(cut['start']),'-i',str(source)]
    filters=['[0:v]crop=752:564:8:34,fps=30,setsar=1,settb=AVTB,setpts=PTS-STARTPTS,split=2[wide][native]',
             '[wide]scale=480:360:flags=bilinear,crop=480:270,gblur=sigma=18,eq=brightness=-0.14:saturation=0.8,'
             'scale=1920:1080:flags=bilinear[back]']
    filters+=['[native]scale=1440:1080:flags=lanczos[front]',
              '[back][front]overlay=240:0:shortest=1[scene]']
    result='scene'
    if cut['kind'] in ('opening','ending'):
        svg=out/f'{index:02d}.svg';png=out/f'{index:02d}.png'
        svg.write_text(artwork(cut))
        subprocess.run(['rsvg-convert',str(svg),'-o',str(png)],check=True,capture_output=True,timeout=20)
        command+=['-loop','1','-framerate','30','-i',str(png)]
        delay=8.6 if cut['kind']=='opening' else 2 if cut['kind']=='ending' else .4
        filters.append(f'[1:v]format=rgba,fade=t=in:st={delay}:d=0.3:alpha=1[label]')
        # A small settling movement, not repeated slide-deck transitions.
        filters.append(f"[{result}][label]overlay=0:'24*exp(-8*max(0,t-{delay}))':shortest=1[labelled]")
        result='labelled'
    if cut['kind']=='ending':
        filters.append(f'[{result}]fade=t=out:st={duration-.7}:d=0.7[fadeout]');result='fadeout'
    filters.append(f'[{result}]trim=end_frame={frames},format=yuv420p[v]')
    command+=['-filter_complex',';'.join(filters),'-map','[v]','-an','-frames:v',str(frames),
              '-c:v','libx264','-threads','4','-preset','medium','-crf','16',str(out/f'{index:02d}.mkv')]
    done=subprocess.run(command,capture_output=True,text=True,timeout=240)
    (out/f'{index:02d}.log').write_text(done.stderr)
    if done.returncode:raise RuntimeError(f'Shot {index} failed: '+done.stderr[-3000:])
    return index


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    if not out.is_relative_to(ROOT/'build'):raise ValueError('Trailer output must stay in ignored build/')
    footage=inputs();out.mkdir(parents=True,exist_ok=False)
    source_hashes={p:sha(ROOT/p) for p in ('tools/trailer_edit.py','tools/trailer_capture.py','tools/trailer_daytime.py')}
    (out/'edit.json').write_text(json.dumps({'cuts':CUTS,'footage':footage,'total_frames':TOTAL_FRAMES,
        'creative_direction':'Enter Animal Crossing through its opening, native music, and translated gameplay'},indent=2)+'\n')
    render_music(out)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for index in pool.map(lambda pair:render_cut(*pair,out),enumerate(CUTS)):
            print(f'Shot {index+1}/{len(CUTS)} rendered',flush=True)
    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','warning','-filter_complex_threads','2']
    for i in range(len(CUTS)):command+=['-i',str(out/f'{i:02d}.mkv')]
    command+=['-i',str(out/'soundtrack.wav')];filters=[]
    for i in range(len(CUTS)):filters.append(f'[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]')
    offset=0;previous='v0'
    for i in range(1,len(CUTS)):
        offset+=CUTS[i-1]['frames'];result=f'x{i}'
        transition=CUTS[i].get('transition')
        if transition:
            filters.append(f'[{previous}][v{i}]xfade=transition={transition}:duration=0.3:offset={offset/FPS}[{result}]')
        else:
            filters.append(f'[{previous}][v{i}]concat=n=2:v=1:a=0[{result}]')
        previous=result
    command+=['-filter_complex',';'.join(filters),'-map',f'[{previous}]','-map',f'{len(CUTS)}:a',
        '-t',str(DURATION),'-r','30','-c:v','libx264','-threads','4','-preset','slow','-crf','17',
        '-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-movflags','+faststart',
        '-metadata','title=Animal Forest English — Welcome to the Original Town',
        '-metadata','comment=Unofficial fan translation. Game and music © Nintendo. Private preview.',
        str(out/'Animal Forest English - Trailer.mp4')]
    joined=subprocess.run(command,capture_output=True,text=True,timeout=420)
    (out/'encode.log').write_text(joined.stderr)
    if joined.returncode:raise RuntimeError(joined.stderr[-4000:])
    final=out/'Animal Forest English - Trailer.mp4';info=probe(final)
    report={'output':str(final.relative_to(ROOT)),'sha256':sha(final),'bytes':final.stat().st_size,
            'rom_sha256':ROM_SHA,'duration':float(info['format']['duration']),
            'public_release':False,'speaker_playback':False,'approved_player_name':'Fae',
            'sources':source_hashes,
            'visual_review':'pending'}
    (out/'video.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
