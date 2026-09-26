"""Add an isolated two-row code-entry mode to the accepted N64-style keyboard."""
import copy
import json
import struct

from aflib import CODE_RAM, by_vrom, sha256
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source
from letter_ui_fix import compile_part
from editor_pixel_fix import flat_rows, jump
from title_start_fix import reconstruct
from npc_mail_show import relocate_verified_data
from catalogue_names import Image
import keyboard_v2 as v2
import keyboard_v2_layout as layout

VROM, RELOC, OWNER, RAM = v2.VROM, v2.RELOC, v2.OWNER, v2.RAM
BASE_SHA='8927f2a00a2636816bfbb7f24b6f876f0ad080febf493c7f8cccbb6e5dbde944'
REL_SHA='4bf303b9cfd014e1cd9cf8187fb1735fad6bb950985081beeab9af9d2058981e'
REFERENCES={
    'src/game/m_passwordChk_ovl.c': 'f9f4035216bacc64a89d7a35345b1e175997f65ee19e678f7957396850122a19',
    'src/game/m_editor_ovl.c': 'e3d15e50af75a51fc7d7aec816c955204456c1a2436164774d7f74fbae2e1ae4',
}
SOURCES=('tools/v3_password_editor.py','tools/v3_furniture_install.py',
    'overlays/v3/password_editor.h','overlays/v3/password_editor.c',
    'overlays/v3/password_edit.c','overlays/v3/password_hash.c',
    'translations/provenance.json')


def generated(source, image):
    from extended_glyphs import untile_i4, FONT_SHA256
    from font import get_glyph, pack_pixels
    from keyboard_background_fix import donor
    from keyboard_rc1_fix import metrics
    title=source.raw('title_str$485')
    if title!=b'Enter a secret code.': raise ValueError('Changed complete donor code-entry title')
    raw=source.raw('FONT_nes_tex_font1')
    if sha256(raw)!=FONT_SHA256: raise ValueError('Changed complete donor font')
    glyph=get_glyph(untile_i4(raw,192,256),0xD1)
    texture=pack_pixels([p for row in glyph for p in row+[0]*4])
    entry={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    en=entry['v3/password/editor/title']['locales']['en']
    if en['credit']!='official' or en['text'].encode()!=title or en['encoded_sha256']!=sha256(title):
        raise ValueError('Missing official keyboard title provenance')
    for path,digest in REFERENCES.items():
        if sha256((ROOT/'local/ac-decomp'/path).read_bytes())!=digest:
            raise ValueError('Changed donor keyboard behaviour source: '+path)
    helper,panel=layout.draw_source()
    helper=helper.replace(b'#include "editor.h"',b'#include "editor.h"\n#include "/source/overlays/v3/password_editor.h"')
    helper=helper.replace(b'static void text(',b'#include "password-assets.inc"\n#include "/source/overlays/v3/password_hash.c"\n\nstatic void text(',1)
    needle=b'    af_hboard_font_line(game,s,length,'
    if helper.count(needle)!=1:raise ValueError('Changed accepted renderer font call')
    helper=helper.replace(needle,b"    if (length==1 && s[0]=='#' && af_pw_editor_active(af_grid_context.submenu)) {\n        af_pw_hash_draw(graph,x,y,r,g,b);return;\n    }\n"+needle)
    needle=b'code=af_grid_key(&cell,af_grid_tables,newline,apology);'
    if helper.count(needle)!=1:raise ValueError('Changed accepted renderer key selection')
    helper=helper.replace(needle,b'code=af_pw_editor_key(&cell,af_grid_tables,newline,apology);')
    needle=b'            metric=code<256 ? code : code==AF_GRID_SUN ? 256u : 257u;'
    if helper.count(needle)!=1:raise ValueError('Changed accepted renderer metrics')
    helper=helper.replace(needle,b"            if (code=='#' && af_pw_editor_active(submenu)) {\n                text(graph,game,glyph,1,x+2,y,selected,0,1);continue;\n            }\n"+needle)
    helper+=b'\n#include "/source/overlays/v3/password_editor.c"\n'
    frames,_=donor(source.rel,source.symbols.encode())
    textures='\n'.join('static const unsigned char af_bg_frame_'+name+
        '[1024] __attribute__((aligned(8))) = {'+','.join(map(str,data))+'};'
        for name,data in zip(('a','b'),frames))+'\n'
    textures+='static const unsigned char af_bg_corner[128] __attribute__((aligned(8))) = {'+','.join(map(str,layout.corner_texture()))+'};\n'
    origins,_=metrics(image)
    metric_source='static const signed char af_key_origins[258][2] = {'+','.join('{'+f'{a},{b}'+'}' for a,b in struct.iter_unpack('>2b',origins))+'};\n'
    controls=(ROOT/'overlays/keyboard_v2/controls.c').read_text()
    icons=controls[controls.index('static Gfx *af_v2_controls('):controls.index('static void af_v2_labels(')]
    assets='static const unsigned char af_pw_title[] = {'+','.join(map(str,title))+'};\n'
    assets+='static const unsigned char af_pw_hash[128] __attribute__((aligned(8))) = {'+','.join(map(str,texture))+'};\n'
    return {'helper.c':helper,'panel.inc':panel,'textures.inc':textures.encode(),
        'metrics.inc':metric_source.encode(),'icons.inc':icons.encode(),'password-assets.inc':assets.encode()},dict(
        title_symbol='title_str$485',title_data_offset=0x8482C,title_sha256=sha256(title),
        font_symbol='FONT_nes_tex_font1',font_sha256=sha256(raw),hash_glyph_code=0xD1,
        hash_texture_sha256=sha256(texture),references=REFERENCES)


def install(image, prior, core, original, output):
    if prior.get('password_editor'):raise ValueError('Code-entry mode already installed')
    if not prior['equipment_resources'].get('passwords'):raise ValueError('Missing shared password engine')
    files=by_vrom(image);old=files[VROM].extract(image);rel=files[RELOC].extract(image)
    if sha256(old)!=BASE_SHA or sha256(rel)!=REL_SHA:raise ValueError('Changed accepted keyboard owner')
    # Replace only the prior presentation suffix; preserve its entire native,
    # English editing, controls, and runtime context prefix.
    prefix=bytearray(old[:v2.PREFIX]);struct.pack_into('>I',prefix,v2.CALL,jump(RAM+25748,True))
    rows=[r for r in flat_rows(rel,len(old)) if r&0xFFFFFF<v2.PREFIX]
    n=(24+len(rows)*4+15)&~15
    previous_rel=struct.pack('>5I',len(prefix),0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)+bytes(n-24-len(rows)*4)+struct.pack('>I',n)
    if sha256(prefix)!=v2.SPEC['sha'] or sha256(previous_rel)!=v2.SPEC['reloc_sha']:
        raise ValueError('Changed retained keyboard editor/input prefix')
    symbols=struct.unpack_from('>40H',old,27776+320)
    cell=next(i for i,c in enumerate(symbols) if c==0xFFFF)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated_files,reference=generated(source,image)
    spec=copy.deepcopy(v2.SPEC)
    spec['imports'].update(af_pw_previous_init=0x8088B2AC,af_pw_previous_update=0x80886724,
        af_pw_previous_input=0x8088C62C,af_pw_done=0x808860A0,af_pw_feedback=0x8088596C,
        af_pw_sound=0x800D1A9C,af_grid_editor_prepare=0x8088B278)
    spec['calls']={0x80888484:('af_pw_editor_init',0x8088B2AC),
        RAM+v2.CALL:('af_pw_editor_draw',RAM+25748),
        0x8088B0CC:('af_pw_editor_key',0x8088AC9C)}
    recovered=reconstruct(original,image,{VROM:bytes(prefix),RELOC:previous_rel},resized=(VROM,RELOC))
    data,new_rel,compiled=compile_part('password_editor',recovered,output/'password_editor',
        spec=spec,source='/out/helper.c',generated=generated_files,
        flags=('-D_LANGUAGE_C','-DF3DEX_GBI_2','-I/source/upstream/af/lib/ultralib/include',
            '-I/source/overlays/keyboard_grid','-I/out',f'-DAF_PW_HASH_COLUMN={cell%10}',f'-DAF_PW_HASH_ROW={cell//10}'))
    data=bytearray(data);dispatch=0x8088883C-RAM
    if (struct.unpack_from('>I',data,dispatch)[0]!=0x80886724 or
            (0x42000000|dispatch) not in flat_rows(new_rel,len(data))):
        raise ValueError('Changed native per-frame editor dispatch')
    struct.pack_into('>I',data,dispatch,RAM+compiled['symbols']['af_pw_editor_update'])
    allowed=set(compiled['touched_offsets'])|set(range(dispatch,dispatch+4))
    for base in (0x80200010,0x80370010):
        a=relocate_verified_data(Image(RAM,len(old),struct.unpack_from('>5I',rel)),old,rel,base)
        b=relocate_verified_data(Image(RAM,len(data),struct.unpack_from('>5I',new_rel)),data,new_rel,base)
        if any(a[i]!=b[i] for i in range(v2.PREFIX) if i not in allowed):
            raise ValueError('Code-entry changes unrelated existing editor behaviour')
    data=bytes(data);compiled.update(overlay_sha256=sha256(data),touched_offsets=sorted(allowed))
    owner=bytearray(files[OWNER].extract(image));at=spec['owner_at']
    if struct.unpack_from('>4I',owner,at)!=(VROM,VROM+len(old),RAM,RAM+len(old)):
        raise ValueError('Changed keyboard allocation descriptor')
    struct.pack_into('>4I',owner,at,VROM,VROM+len(data),RAM,RAM+len(data))
    # This HI/LO pair is the shared arena's editor term, including previously
    # reserved growth for other menus. Add only this editor's aligned increase.
    high,low=0x800C4AFC-CODE_RAM,0x800C4B10-CODE_RAM
    if (struct.unpack_from('>I',core,high)[0],struct.unpack_from('>I',core,low)[0])!=(0x3C0E808A,0x25CE8FE0):
        raise ValueError('Changed shared menu allocation term')
    growth=((len(data)+63)&~63)-((len(old)+63)&~63)
    if not 0<growth<=0x4000 or len(data)>RELOC-VROM:raise ValueError('Code-entry exceeds bounded owner growth')
    bound=0x80898FE0+growth
    struct.pack_into('>I',core,high,0x3C0E0000|((bound+0x8000)>>16))
    struct.pack_into('>I',core,low,0x25CE0000|(bound&0xFFFF))
    changes={VROM:data,RELOC:new_rel,OWNER:bytes(owner)}
    receipt=dict(format='AFV3-PASSWORD-EDITOR-1',vrom=VROM,reloc=RELOC,ram=RAM,
        compiled=compiled,source=reference,hash_cell=cell,mode=5,caller_bytes=28,
        additional_menu_pool_bytes=growth,previous_pool_bound=0x80898FE0,pool_bound=bound,
        owner_resizes=[dict(vrom=v,previous_bytes=files[v].size,previous_sha256=sha256(files[v].extract(image)),
            bytes=len(d),sha256=sha256(d)) for v,d in changes.items() if v in (VROM,RELOC)],
        installed=True,shop_route_installed=False,ordinary_gameplay_tested=False,native_execution_tested=False,
        saved_format_changed=False,sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    # Preserve final installed bytes, not only the pre-dispatch compiler output.
    (output/'password_editor/installed.bin').write_bytes(data)
    (output/'password_editor/installed.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return changes,{'password_editor':receipt}
