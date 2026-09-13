"""Install the compact key tray and attached controller sections on exact V2-08."""
import argparse
import json
import math
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from catalogue_names import Image
from editor_pixel_fix import flat_rows, jump
from keyboard_background_fix import donor
from keyboard_rc1_fix import metrics
import keyboard_v2 as v2
from letter_ui_fix import compile_part
from npc_mail_show import relocate_verified_data
from title_start_fix import reconstruct
from toolchain import IMAGE

ROOT=v2.ROOT
BASE_SHA='08aa1c4418848138803059a68de667f473f9da490d7c0866ee501c58b8d0896b'
EDITOR_SHA='74a81fd14005a48ab2a16a6f560aae48aee868066c76a57393352f1240ddd3ff'
REL_SHA='7890a5c797402f2ec7ac06df7f50eb1eccc3b3b6902089fa1c352be325eecda1'
VROM,RELOC,OWNER,RAM,PREFIX,CALL=v2.VROM,v2.RELOC,v2.OWNER,v2.RAM,v2.PREFIX,v2.CALL


def corner_texture():
    """Analytic quarter-circle: 8x8 coverage samples and a 16-level I4 mask."""
    pixels=bytearray()
    for y in range(16):
        for x in range(16):
            covered=sum(math.hypot(16-x-(sx+0.5)/8,16-y-(sy+0.5)/8)<=15.5
                        for sy in range(8) for sx in range(8))
            alpha=(covered*15+32)//64
            pixels.append(alpha)
    return bytes(pixels[i]<<4|pixels[i+1] for i in range(0,len(pixels),2))


def sources():
    result=v2.source_hashes()
    for name in ('tools/keyboard_v2_layout.py','overlays/keyboard_v2_layout/panel.c',
                 'overlays/keyboard_v2_layout/controls.c'):
        result[name]=sha256((ROOT/name).read_bytes())
    return result


def recover(data,rel):
    if sha256(data)!=EDITOR_SHA or sha256(rel)!=REL_SHA:
        raise ValueError('Changed V2-08 keyboard owner')
    prefix=bytearray(data[:PREFIX])
    struct.pack_into('>I',prefix,CALL,jump(RAM+25748,True))
    rows=[r for r in flat_rows(rel,len(data)) if (r&0xFFFFFF)<PREFIX]
    size=(24+4*len(rows)+15)&~15
    relocation=struct.pack('>5I',PREFIX,0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)
    relocation+=bytes(size-24-4*len(rows))+struct.pack('>I',size)
    if sha256(prefix)!=v2.RECOVERED_SHA or sha256(relocation)!=v2.SPEC['reloc_sha']:
        raise ValueError('Current keyboard input prefix differs')
    return bytes(prefix),relocation


def draw_source():
    helper,_=v2.draw_source()
    helper=helper.replace(b'/source/overlays/keyboard_v2/controls.c',
                          b'/source/overlays/keyboard_v2_layout/controls.c')
    helper=helper.replace(b'54+dx,116-dy',b'116+dx,116-dy')
    # No centred combination hint remains, so discard its unused helper.
    start=helper.index(b'static void centred_label(')
    end=helper.index(b'#include "/source/overlays/keyboard_v2_layout/controls.c"',start)
    helper=helper[:start]+helper[end:]
    return helper,(ROOT/'overlays/keyboard_v2_layout/panel.c').read_bytes()


def build(native,base,out):
    verified_rom(native)
    if sha256(base)!=BASE_SHA: raise ValueError('Layout requires exact V2-08')
    before=sources(); files=by_vrom(base)
    old,old_rel=files[VROM].extract(base),files[RELOC].extract(base)
    prefix,relocation=recover(old,old_rel)
    frames,frame_report=donor((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    frame_report.update(native_panel_bounds=[52,128,236,204],
        adaptation='Unedited frame textures around the key grid only; separate code-drawn N64-style shells',
        controller_shells='Seven antialiased nine-slice grey shells, drawn before the key tray',
        corner_sha256=sha256(corner_texture()),corner_format='I4',corner_size=[16,16])
    artwork=v2.assets(native,base,out/'artwork'); origins,_=metrics(base)
    helper,panel=draw_source()
    controls=(ROOT/'overlays/keyboard_v2/controls.c').read_text()
    icon_renderer=controls[controls.index('static Gfx *af_v2_controls('):controls.index('static void af_v2_labels(')].encode()
    textures='\n'.join('static const unsigned char af_bg_frame_'+name+
        '[1024] __attribute__((aligned(8))) = {'+','.join(map(str,data))+'};'
        for name,data in zip(('a','b'),frames)).encode()+b'\n'
    textures+=('static const unsigned char af_bg_corner[128] __attribute__((aligned(8))) = {'+
               ','.join(map(str,corner_texture()))+'};\n').encode()
    metric_source=('static const signed char af_key_origins[258][2] = {'+
        ','.join('{'+f'{a},{b}'+'}' for a,b in struct.iter_unpack('>2b',origins))+'};\n').encode()
    recovered=reconstruct(native,base,{VROM:prefix,RELOC:relocation},resized=(VROM,RELOC))
    data,rel,compiled=compile_part('keyboard_layout',recovered,out/'editor',spec=v2.SPEC,
        source='/out/helper.c',generated={'helper.c':helper,'panel.inc':panel,
        'textures.inc':textures,'metrics.inc':metric_source,'icons.inc':icon_renderer},
        flags=('-D_LANGUAGE_C','-DF3DEX_GBI_2','-I/source/upstream/af/lib/ultralib/include',
               '-I/source/overlays/keyboard_grid','-I/out'))
    if any(hint in data[PREFIX:] for hint in (b'L+A:',b'L+Z:',b'Alter')):
        raise ValueError('Combination hints remain in the presentation')
    if set(compiled['touched_offsets'])!=set(range(CALL,CALL+4)):
        raise ValueError('Layout changes more than the existing drawing hook')
    for at in (0x80200010,0x80378010):
        previous=relocate_verified_data(Image(RAM,len(old),struct.unpack_from('>5I',old_rel)),old,old_rel,at)
        current=relocate_verified_data(Image(RAM,len(data),struct.unpack_from('>5I',rel)),data,rel,at)
        if previous[:CALL]!=current[:CALL] or previous[CALL+4:PREFIX]!=current[CALL+4:PREFIX]:
            raise ValueError('Layout changes input/editor behaviour after relocation')
    growth=((len(data)+63)&~63)-((PREFIX+63)&~63)
    if growth>8192: raise ValueError(f'Layout exceeds the existing suffix reservation: {growth}')
    owner=bytearray(files[OWNER].extract(base)); row=v2.SPEC['owner_at']
    if struct.unpack_from('>4I',owner,row)!=(VROM,VROM+len(old),RAM,RAM+len(old)):
        raise ValueError('Changed current keyboard allocation owner')
    code=files[CODE_VROM].extract(base)
    if struct.unpack_from('>I',code,0x800C4B10-CODE_RAM)[0]!=0x25CE7620:
        raise ValueError('Changed current keyboard pool reservation')
    struct.pack_into('>4I',owner,row,VROM,VROM+len(data),RAM,RAM+len(data))
    image=reconstruct(native,base,{VROM:data,RELOC:rel,OWNER:bytes(owner)},resized=(VROM,RELOC))
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image or sources()!=before:
        raise ValueError('Layout patch reconstruction or source consistency failed')
    return image,patch,{'build':'V2-10','output_sha256':sha256(image),'patch_sha256':sha256(patch),
        'baseline_sha256':BASE_SHA,'sources':before,'editor':compiled,'frame':frame_report,
        'native_artwork':artwork,'shared_growth_bytes':growth,'additional_pool_bytes':0,
        'input_code_changed':False,'save_format_changed':False,'key_positions_changed':False,
        'font_pixels_changed':False,'sound_code_changed':False,'combo_shortcuts_retained':True,
        'required_ram_bytes':0x800000,'toolchain_image':IMAGE,'native_validation':'pending'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/v2-keyboard-polish-10-final')
    args=parser.parse_args(); out=args.output.resolve()
    if not out.is_relative_to(ROOT/'build') or out.exists(): raise ValueError('Choose a fresh ignored output')
    out.mkdir(parents=True)
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/v2-performance-fix-08/Animal Forest English V2.z64').read_bytes(),out)
    for name,data in {'Animal Forest English V2.z64':image,'Animal Forest English V2.ups':patch,
                      'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (out/name).open('xb') as stream: stream.write(data)
    print(json.dumps({k:report[k] for k in ('output_sha256','patch_sha256','shared_growth_bytes')},indent=2))


if __name__=='__main__':main()
