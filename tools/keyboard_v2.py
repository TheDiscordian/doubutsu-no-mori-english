"""Build the private N64-inspired keyboard from the preserved V1 Final cartridge."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from catalogue_names import Image
from editor_pixel_fix import flat_rows, jump
from keyboard_background_fix import ROOT, RAM, donor
from keyboard_grid_labels import encode_label
from keyboard_rc1_fix import (VROM, RELOC, OWNER, PREFIX, SPEC as PREVIOUS_SPEC,
                              draw_source as previous_draw, metrics)
from letter_ui_fix import compile_part
from npc_mail_show import relocate_verified_data
from texture_preview import decode, png_rgba
from title_start_fix import reconstruct
from toolchain import IMAGE

BASE_SHA = '0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf'
EDITOR_SHA = 'd2af4fc07a2602120b650fd488ee5950d349f1abe73a27e2209ac717efa6d03c'
RELOC_SHA = '2e8988e434f538305fe64210f5ead26b0045102a45f1be85a36a4a5720327e9e'
RECOVERED_SHA = '649bc5f566bff529357b697b810d2b314641a55cf4953d74206a39e39d5bcf4b'
ART_VROM = 0xA40000
ART_SHA = '39b26c60392e75e5988f25788e1eac2cc3996583bdbc3ccb7d50de809cbf2b76'
NATIVE_ART_SHA = '0445bb9fdb4634ccfe31cce544695a98c471a77266d94455390868324bf87f17'
CALL = 0x808882D8-RAM
SPEC = dict(PREVIOUS_SPEC, vrom=VROM, reloc=RELOC, sha=RECOVERED_SHA,
            imports=dict(PREVIOUS_SPEC['imports'], af_grid_get_button=0x80078D78))
BOTTOM = b'D-pad: Move   L+A: Alter   L+Z: ABC'

# Offsets are bound to native pointer tables and the actual RDP materials.
# Tuple: name, editor table offset, released/pressed, dimensions, format, texture-load command.
ASSETS = (
    ('button_mask',0x370C,0x14E48,0x16C48,32,32,'i4',0xC80),
    ('start',0x3714,0x13648,0x15448,32,32,'rgba16',0xCE0),
    ('b',0x371C,0x13E48,0x15C48,32,32,'rgba16',0xD78),
    ('a',0x3724,0x14648,0x16448,32,32,'rgba16',0xC48),
    ('c_right',0x372C,0x5F48,0x5E48,16,16,'ia8',0xED8),
    ('c_left',0x3734,0x6148,0x6048,16,16,'ia8',0xF40),
    ('c_up',0x373C,0x6348,0x6248,16,16,'ia8',0xFA8),
    ('c_down',0x3744,0x6548,0x6448,16,16,'ia8',0x1010),
    ('z',0x374C,0xCE48,0xC648,32,64,'ia8',0x11E8),
    ('shoulder',0x3754,0x8E48,0x8648,64,32,'ia8',0x13F0),
    ('stick',0x3788,0xD648,None,64,64,'ia8',0x1610),
)


def source_hashes():
    names = ('tools/keyboard_v2.py','overlays/keyboard_v2/controls.c',
             'tools/keyboard_rc1_fix.py','overlays/keyboard_rc1/panel.c',
             'overlays/keyboard_grid/draw.c','overlays/keyboard_grid/editor.h',
             'overlays/keyboard_grid/core.h','overlays/hboard/editor.h',
             'runtime/hboard_editor.h','tools/keyboard_background_fix.py',
             'tools/letter_ui_fix.py','tools/texture_preview.py')
    return {p:sha256((ROOT/p).read_bytes()) for p in names}


def recover(data, relocation):
    if sha256(data)!=EDITOR_SHA or sha256(relocation)!=RELOC_SHA:
        raise ValueError('V2 requires the V1 Final editor, including its later space/input fixes')
    prefix=bytearray(data[:PREFIX])
    if struct.unpack_from('>I',prefix,CALL)[0]!=0x0C22327A:
        raise ValueError('Changed V1 Final drawing hook')
    struct.pack_into('>I',prefix,CALL,jump(RAM+25748,True))
    rows=[r for r in flat_rows(relocation,len(data)) if (r&0xFFFFFF)<PREFIX]
    size=(24+len(rows)*4+15)&~15
    rel=(struct.pack('>5I',PREFIX,0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)
         +bytes(size-24-len(rows)*4)+struct.pack('>I',size))
    if sha256(prefix)!=RECOVERED_SHA or sha256(rel)!=SPEC['reloc_sha']:
        raise ValueError('Recovered current input/editor prefix does not match')
    return bytes(prefix),rel


def assets(native, base, out):
    original=by_vrom(native); current=by_vrom(base)
    art=original[ART_VROM].extract(native); installed=current[ART_VROM].extract(base)
    editor=original[0x78CB80].extract(native)
    if sha256(art)!=NATIVE_ART_SHA or sha256(installed)!=ART_SHA:
        raise ValueError('Changed source or installed keyboard artwork')
    # The complete native ROM is verified by the caller. Bind each texture reader too.
    out.mkdir(parents=True,exist_ok=False); report=[]
    for name,table,released,pressed,w,h,fmt,command in ASSETS:
        addresses=(released,) if pressed is None else (released,pressed)
        if struct.unpack_from('>'+str(len(addresses))+'I',editor,table)!=tuple(0x0C000000+a for a in addresses):
            raise ValueError('Changed native controller texture table: '+name)
        load=struct.unpack_from('>2I',art,command)
        expected_segment=9 if fmt=='rgba16' or name=='shoulder' else 8
        if load!=(0xFD100000 if fmt=='rgba16' else 0xFD900000 if fmt=='i4' else 0xFD700000,
                  expected_segment<<24):
            raise ValueError('Changed controller texture load: '+name)
        tile=struct.unpack_from('>2I',art,command+40)
        size=struct.unpack_from('>2I',art,command+48)
        if tile[0]>>24!=0xF5 or size[0]>>24!=0xF2 or (
                ((size[1]>>12)&4095)//4+1,(size[1]&4095)//4+1)!=(w,h):
            raise ValueError('Changed controller dimensions: '+name)
        bits={'i4':4,'ia8':8,'rgba16':16}[fmt]; hashes=[]
        for index,at in enumerate(addresses):
            raw=art[at:at+w*h*bits//8]
            if installed[at:at+len(raw)]!=raw: raise ValueError('Controller artwork is no longer native')
            hashes.append(sha256(raw))
            (out/f'{name}-{index}.png').write_bytes(png_rgba(w,h,decode(raw,w,h,fmt),4))
        report.append(dict(name=name,table=f'{table:05X}',offsets=[f'{a:05X}' for a in addresses],
                           size=[w,h],format=fmt,sha256=hashes,texture_command=f'{command:05X}'))
    return report


def draw_source():
    source=previous_draw().decode()
    old_panel=(ROOT/'overlays/keyboard_rc1/panel.c').read_text()
    if sha256(old_panel.encode())!='f876b937dac8eb6899e8ec4ecdeb145f24b0bb3ee8e874d6066990c970289bc5':
        raise ValueError('Changed accepted GC panel source')
    panel=old_panel.replace('225,205,225,255','225,225,225,255').replace('160,90,245,255','105,110,115,255')
    changes={
        '#include "/source/overlays/keyboard_rc1/panel.c"':'#include "panel.inc"',
        'void af_bg_editor_draw(':'#include "/source/overlays/keyboard_v2/controls.c"\n\nvoid af_bg_editor_draw(',
        '!space(graph,4096)':'!space(graph,8192)',
        '    gDPPipeSync(g++);\n    gDPSetCombineLERP':'    g=af_v2_controls(g,dx,dy);\n    gDPPipeSync(g++);\n    gDPSetCombineLERP',
        '    label(graph,game,"L: Case   Z: Page   L+Z: ABC",110+dx,117-dy);':'    af_v2_labels(graph,game,dx,dy);',
        '    centred_label(graph,game,"A: Type   B: Del   R: Space   Start: Done",160+dx,200-dy);':'',
        '    centred_label(graph,game,"Move: Stick/D-pad   Cursor: C   L+A: Alter",160+dx,212-dy);':'',
    }
    for old,new in changes.items():
        if source.count(old)!=1: raise ValueError('Missing unique V2 presentation edit: '+old)
        source=source.replace(old,new,1)
    return source.encode(),panel.encode()


def build(native, base, rel, symbols, out):
    verified_rom(native)
    if sha256(base)!=BASE_SHA: raise ValueError('V2 requires the exact V1 Final baseline')
    sources=source_hashes(); files=by_vrom(base)
    original=files[VROM].extract(base); original_rel=files[RELOC].extract(base)
    prefix,prior_rel=recover(original,original_rel)
    artwork=assets(native,base,out/'artwork')
    frames,frame_report=donor(rel,symbols); origins,_=metrics(base)
    helper,panel=draw_source()
    textures='\n'.join('static const unsigned char af_bg_frame_'+name+
        '[1024] __attribute__((aligned(8))) = {'+','.join(str(v) for v in data)+'};'
        for name,data in zip(('a','b'),frames)).encode()+b'\n'
    metric_source=('static const signed char af_key_origins[258][2] = {'+
        ','.join('{'+f'{a},{b}'+'}' for a,b in struct.iter_unpack('>2b',origins))+'};\n').encode()
    recovered=reconstruct(native,base,{VROM:prefix,RELOC:prior_rel},resized=(VROM,RELOC))
    data,relocation,compiled=compile_part('keyboard_v2',recovered,out/'editor',spec=SPEC,
        source='/out/helper.c',generated={'helper.c':helper,'panel.inc':panel,
                                         'textures.inc':textures,'metrics.inc':metric_source},
        flags=('-D_LANGUAGE_C','-DF3DEX_GBI_2','-I/source/upstream/af/lib/ultralib/include',
               '-I/source/overlays/keyboard_grid','-I/out'))
    data=bytearray(data)
    if data[PREFIX:].count(BOTTOM+b'\0')!=1: raise ValueError('Changed V2 control hints')
    at=data.index(BOTTOM+b'\0',PREFIX); data[at:at+len(BOTTOM)]=encode_label(BOTTOM)
    data=bytes(data); allowed=set(range(CALL,CALL+4))
    if set(compiled['touched_offsets'])!=allowed: raise ValueError('V2 changes more than its drawing hook')
    for address in (0x80200010,0x80378010):
        before=relocate_verified_data(Image(RAM,len(original),struct.unpack_from('>5I',original_rel)),
                                      original,original_rel,address)
        after=relocate_verified_data(Image(RAM,len(data),struct.unpack_from('>5I',relocation)),
                                     data,relocation,address)
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before[:PREFIX],after[:PREFIX]))):
            raise ValueError('V2 changes retained editor behaviour at runtime')
    growth=((len(data)+63)&~63)-((PREFIX+63)&~63)
    if growth>8192 or len(data)>RELOC-VROM: raise ValueError('V2 exceeds the existing keyboard reservation')
    owner=bytearray(files[OWNER].extract(base)); code=files[CODE_VROM].extract(base)
    if struct.unpack_from('>4I',owner,SPEC['owner_at'])!=(VROM,VROM+len(original),RAM,RAM+len(original)):
        raise ValueError('Changed V1 Final editor allocation')
    if struct.unpack_from('>I',code,0x800C4B10-CODE_RAM)[0]!=0x25CE7620:
        raise ValueError('Changed existing keyboard memory reservation')
    struct.pack_into('>4I',owner,SPEC['owner_at'],VROM,VROM+len(data),RAM,RAM+len(data))
    image=reconstruct(native,base,{VROM:data,RELOC:relocation,OWNER:bytes(owner)},resized=(VROM,RELOC))
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image or source_hashes()!=sources:
        raise ValueError('V2 patch reconstruction or source retention failed')
    compiled['overlay_sha256']=sha256(data)
    (out/'editor/image.bin').write_bytes(data)
    (out/'editor/image.json').write_text(json.dumps(compiled,indent=2)+'\n')
    return image,patch,dict(version=2,baseline_sha256=BASE_SHA,source_sha256=sha256(native),
        output_sha256=sha256(image),patch_sha256=sha256(patch),sources=sources,editor=compiled,
        native_artwork=artwork,frame=frame_report,frame_colours=[[225,225,225],[105,110,115]],
        shared_growth_bytes=growth,existing_pool_extra_bytes=8192,additional_pool_bytes=0,
        key_positions_changed=False,font_pixels_changed=False,sound_code_changed=False,
        input_code_changed=False,save_format_changed=False,required_ram_bytes=0x800000,
        toolchain_image=IMAGE,public_release=False,native_tests='pending',hardware_tests='pending')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=ROOT/'build/v1-final/Animal Forest English V1 Final.z64')
    p.add_argument('--output',type=Path,default=ROOT/'build/v2-keyboard-01'); a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),a.base.read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),a.output)
    for name,data in {'Animal Forest English V2 Development.z64':image,
                      'Animal Forest English V2 Development.ups':patch,
                      'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (a.output/name).open('xb') as target: target.write(data)
    print(json.dumps({k:report[k] for k in ('output_sha256','patch_sha256','shared_growth_bytes')},indent=2))


if __name__=='__main__': main()
