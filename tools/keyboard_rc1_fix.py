"""Correct RC1 keyboard corner UVs, visible key alignment, hints, and pages."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from catalogue_names import Image
from editor_pixel_fix import flat_rows, jump
from extended_font_cartridge import ACCENT_RESOURCE_HASH
from extended_glyphs import validate_resource
from font import FONT_VROM, ATLAS_OFFSET, ATLAS_SIZE, WIDTH_TABLE, pixels, get_glyph
from keyboard_background_fix import ROOT, RAM, SPEC as OLD_SPEC, DRAW_SHA, donor
from keyboard_grid_labels import LABELS, encode_label
from letter_ui_fix import compile_part
from npc_mail_show import relocate_verified_data
from title_assets import DATA_BASE
from title_start_fix import reconstruct
from toolchain import IMAGE

BASE_SHA = '40d2478cdea8cbb808ae1d1dd7e65184bb9efe11215524a6411efff3efc15378'
VROM, RELOC, OWNER, PREFIX = 0x3E70000, 0x3E80000, 0x7749C0, 30272
OLD_SHA = '945617d1c357f82d319370acecb8182c360ff134c18456570336aab08011abfc'
OLD_REL_SHA = '43d83bdcb1dd5b95809f363a8628aa82825798b80f63871fe1729a63fb8986a7'
FONT_SHA = '7e4fdb93f1b0109e3d609434163d8c31174ef6699b7d439aef1a8305a18d2798'
SPEC = dict(OLD_SPEC, vrom=VROM, reloc=RELOC)
TABLE = 27776
PAGE_WORDS = ((0x8088AC0C-RAM, 0x2C630003, 0x2C630002),
              (0x8088B074-RAM, 0x24030003, 0x24030002))
HINTS = (b'A: Type   B: Del   R: Space   Start: Done', LABELS[1][1])


def source_hashes():
    paths = ['tools/keyboard_rc1_fix.py', 'overlays/keyboard_rc1/panel.c',
             'overlays/keyboard_grid/draw.c', 'overlays/keyboard_grid/core.c',
             'overlays/keyboard_grid/core.h', 'overlays/keyboard_grid/editor.h',
             'overlays/hboard/editor.h', 'runtime/hboard_editor.h']
    return {p: sha256((ROOT/p).read_bytes()) for p in paths}


def recover(data, relocation):
    if sha256(data) != OLD_SHA or sha256(relocation) != OLD_REL_SHA:
        raise ValueError('Changed RC1 keyboard owner or relocation')
    prefix = bytearray(data[:PREFIX]); at = 0x808882D8-RAM
    if struct.unpack_from('>I', prefix, at)[0] != jump(RAM+30600, True):
        raise ValueError('Changed owned background call')
    struct.pack_into('>I', prefix, at, jump(RAM+25748, True))
    rows = [r for r in flat_rows(relocation, len(data)) if (r & 0xFFFFFF) < PREFIX]
    size = (24+len(rows)*4+15) & ~15
    rel = (struct.pack('>5I', PREFIX, 0, 0, 0, len(rows))+
           struct.pack('>'+str(len(rows))+'I', *rows)+bytes(size-24-len(rows)*4)+struct.pack('>I', size))
    if sha256(prefix) != SPEC['sha'] or sha256(rel) != SPEC['reloc_sha']:
        raise ValueError('Recovered keyboard differs from its verified complete prefix')
    return bytes(prefix), rel


def combined_symbols(prefix):
    original = prefix[TABLE:TABLE+480]
    if sha256(original) != 'de0934289f9ee4f86cdadd87df63fe2eba0ab0b7d5cdb76949bd98ab7c54c0a7':
        raise ValueError('Changed supported keyboard tables')
    codes = struct.unpack('>240H', original)
    ordered = list(dict.fromkeys(c for c in codes[160:] if c not in (0xFFFF, 0xCD, 0x20)))
    if len(ordered) != 22: raise ValueError('Changed distinct supported symbol count')
    # Keep Return and Space in their familiar last-column rows. The old marks
    # storage remains unreachable so every following owned address stays fixed.
    page = ordered+[0xFFFF]*(40-len(ordered)); page[29]=0xCD; page[39]=0x20
    if set(page) != set(codes[160:]): raise ValueError('Combined page loses a supported symbol')
    return struct.pack('>40H', *page), page


def placement(glyph):
    ink = [(x, y, v) for y, row in enumerate(glyph) for x, v in enumerate(row) if v]
    if not ink: return [0, 0], None
    left, right = min(p[0] for p in ink), max(p[0] for p in ink)
    top, bottom = min(p[1] for p in ink), max(p[1] for p in ink)
    total = sum(v for _, _, v in ink)
    centre = sum(x*v for x, _, v in ink)/total
    # Quarter-pixel optical centring, constrained by the complete visible ink.
    x4 = max(4*(1-left), min(4*(14-right), round(4*(7.5-centre))))
    # Keep punctuation's baseline relationships. Lift only low marks which
    # otherwise touch/escape the bottom edge; full-height symbols stay intact.
    y = max(1-top, min(0, 14-bottom)) if bottom-top < 14 else -top
    if not 0 <= left+x4/4 <= right+x4/4 < 16 or not 0 <= top+y <= bottom+y < 16:
        raise ValueError('Key label cannot fit without cutting its pixels')
    return [x4, y*4], {'bounds': [left, top, right, bottom], 'ink_centre_x': centre,
                      'origin': [x4/4, y]}


def metrics(base):
    files = by_vrom(base); font = files[FONT_VROM].extract(base)
    if sha256(font) != FONT_SHA: raise ValueError('Changed installed keyboard font')
    atlas = pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
    # These two complete extended glyphs are already installed for apologies.
    extended = files[0x3400000].extract(base)
    starts = [i for i in range(len(extended)-1599) if extended[i:i+4] == b'AFGX']
    if len(starts) != 1: raise ValueError('Ambiguous installed extended font')
    at = starts[0]; resource = extended[at:at+1600]
    validate_resource(resource, mail=True, accents=True)
    if sha256(resource) != ACCENT_RESOURCE_HASH: raise ValueError('Changed installed extended pixels')
    glyphs = [get_glyph(atlas, c) for c in range(256)]
    ext_atlas = pixels(resource[64:])
    for c in (0xA7, 0xBA): glyphs.append(get_glyph(ext_atlas, resource[32:48].index(c)))
    placements, profiles = zip(*(placement(g) for g in glyphs))
    data = b''.join(struct.pack('>2b', *p) for p in placements)
    return data, {str(c if c < 256 else (0x80A7, 0x80BA)[c-256]): p
                  for c, p in enumerate(profiles) if p is not None}


def draw_source():
    data = (ROOT/'overlays/keyboard_grid/draw.c').read_text()
    if sha256(data.encode()) != DRAW_SHA: raise ValueError('Changed retained keyboard drawing source')
    start = data.index('static Gfx *rectangle('); end = data.index('void af_grid_editor_draw(', start)
    data = data[:start]+'''static void centred_label(void *graph, void *game, const char *s, float centre, float y) {
    int length=0, width=0, advance;
    while (length<64 && s[length]) {
        advance=af_hboard_code_width((unsigned char)s[length],1);
        if (advance<1 || advance>12) {af_grid_context.error=4;return;}
        width+=advance; ++length;
    }
    if (length==64 || width>280) {af_grid_context.error=4;return;}
    label(graph,game,s,centre-width*0.375f,y);
}

'''+data[end:]
    changes = {
        'void af_grid_editor_draw(': 'void af_bg_editor_draw(',
        'g=rectangle(g,': 'g=af_bg_panel(g,',
        'apology,newline,width;': 'apology,newline;\n    unsigned int metric;',
        '            width=code>255 ? 12 : af_hboard_code_width(code,1);\n'
        '            if (width<1 || width>12) {ctx->error=4;continue;}':
        '            metric=code<256 ? code : code==AF_GRID_SUN ? 256u : 257u;',
        'x+(16-width)*0.5f,y+1,selected,disabled,1.0f);':
        'x+af_key_origins[metric][0]*0.25f,y+af_key_origins[metric][1]*0.25f,selected,disabled,1.0f);',
        'ctx->state.page==1 ? "Symbols" : ctx->state.page==2 ? "Marks" :':
        'ctx->state.page ? "Symbols" :',
        'label(graph,game,"'+HINTS[0].decode()+'",51+dx,202-dy);':
        'centred_label(graph,game,"'+HINTS[0].decode()+'",160+dx,200-dy);',
        'label(graph,game,"'+HINTS[1].decode()+'",51+dx,215-dy);':
        'centred_label(graph,game,"'+HINTS[1].decode()+'",160+dx,212-dy);',
    }
    for old, new in changes.items():
        if data.count(old) != 1: raise ValueError('Missing unique keyboard drawing edit: '+old)
        data = data.replace(old, new, 1)
    return ('#include "/source/overlays/keyboard_rc1/panel.c"\n#include "metrics.inc"\n'+data).encode()


def core_source():
    data = (ROOT/'overlays/keyboard_grid/core.c').read_text()
    for old, new in (('s->page<3', 's->page<2'), ('(s->page+1u)%3u', '(s->page+1u)%2u')):
        if data.count(old) != 1: raise ValueError('Changed source page-count binding')
        data = data.replace(old, new)
    return data.encode()


def build(native, base, rel, symbols, out):
    verified_rom(native)
    if sha256(base) != BASE_SHA: raise ValueError('Keyboard requires the complete RC1 text/HUD follow-up')
    sources = source_hashes(); files = by_vrom(base)
    prefix, prior_rel = recover(files[VROM].extract(base), files[RELOC].extract(base))
    frames, artwork = donor(rel, symbols)
    # Bind all sixteen actual donor vertices, including the one-pixel offset
    # and the lower-right's negative T direction missed by the earlier review.
    vertices = list(struct.iter_unpack('>3hH2h4B', rel[DATA_BASE+0x41FFF0:DATA_BASE+0x4200F0]))
    expected = [(-105,-82,0,1024),(-15,-82,2048,1024),(-15,-46,2048,0),(-105,-46,0,0),
                (-15,-45,2048,0),(75,-45,0,0),(75,-9,0,1024),(-15,-9,2048,1024),
                (-15,-45,2048,1024),(-15,-81,2048,0),(75,-45,0,1024),(75,-81,0,0),
                (-105,-10,0,0),(-105,-46,0,1024),(-15,-10,2048,0),(-15,-46,2048,1024)]
    if [(x,y,s,t) for x,y,z,flag,s,t,*rgba in vertices] != expected:
        raise ValueError('Changed GC frame corner geometry or UV orientation')
    artwork.update(native_panel_bounds=[42,111,278,227], right_pair_y_offset=-2,
                   lower_right_st=[2048,1024], lower_right_direction=[-1,-1],
                   adaptation='Corrected donor corner directions/offset; control hints centred inside visible alpha')
    origins, glyphs = metrics(base); page, codes = combined_symbols(prefix)
    texture_source = '\n'.join('static const unsigned char af_bg_frame_'+name+
        '[1024] __attribute__((aligned(8))) = {'+','.join(str(v) for v in data)+'};'
        for name, data in zip(('a', 'b'), frames)).encode()+b'\n'
    metric_source = ('static const signed char af_key_origins[258][2] = {'+
                     ','.join('{'+f'{a},{b}'+'}' for a,b in struct.iter_unpack('>2b',origins))+'};\n').encode()
    # Recover only for compilation; the finished image is installed into the
    # actual predecessor so its text/HUD fixes and every other resource persist.
    recovered = reconstruct(native, base, {VROM: prefix, RELOC: prior_rel}, resized=(VROM,RELOC))
    data, relocation, compiled = compile_part('keyboard_rc1', recovered, out/'editor', spec=SPEC,
        source='/out/helper.c', generated={'helper.c':draw_source(), 'textures.inc':texture_source,
                                         'metrics.inc':metric_source},
        flags=('-D_LANGUAGE_C','-DF3DEX_GBI_2','-I/source/upstream/af/lib/ultralib/include',
               '-I/source/overlays/keyboard_grid','-I/out'))
    data = bytearray(data); allowed = set(compiled['touched_offsets'])
    rows = flat_rows(relocation, len(data))
    for at, old, new in PAGE_WORDS:
        if struct.unpack_from('>I', data, at)[0] != old or any(at <= (r&0xFFFFFF) < at+4 for r in rows):
            raise ValueError('Changed non-relocated page-count instruction')
        struct.pack_into('>I',data,at,new); allowed.update(range(at,at+4))
    table_at=TABLE+320
    if any(table_at <= (r&0xFFFFFF) < table_at+80 for r in rows):
        raise ValueError('Unexpected relocation inside supported-symbol values')
    data[table_at:table_at+80]=page; allowed.update(range(table_at,table_at+80))
    for _, label in LABELS:
        if data[PREFIX:].count(label+b'\0') != 1: raise ValueError('Changed complete native control hint')
        at=data.index(label+b'\0', PREFIX); data[at:at+len(label)]=encode_label(label)
    data=bytes(data)
    for address in (0x80200010,0x80378010):
        before=relocate_verified_data(Image(RAM,PREFIX,struct.unpack_from('>5I',prior_rel)),prefix,prior_rel,address)
        after=relocate_verified_data(Image(RAM,len(data),struct.unpack_from('>5I',relocation)),data,relocation,address)
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,after))):
            raise ValueError('Keyboard changes retained editing behaviour at runtime')
    growth=((len(data)+63)&~63)-((PREFIX+63)&~63)
    if growth>8192 or len(data)>RELOC-VROM: raise ValueError('Keyboard exceeds existing reserved memory')
    owner=bytearray(files[OWNER].extract(base)); code=files[CODE_VROM].extract(base)
    if struct.unpack_from('>4I',owner,SPEC['owner_at']) != (VROM,VROM+35392,RAM,RAM+35392):
        raise ValueError('Changed preceding keyboard owner metadata')
    if struct.unpack_from('>I',code,0x800C4B10-CODE_RAM)[0] != 0x25CE7620:
        raise ValueError('Changed existing shared keyboard memory reservation')
    struct.pack_into('>4I',owner,SPEC['owner_at'],VROM,VROM+len(data),RAM,RAM+len(data))
    image=reconstruct(native,base,{VROM:data,RELOC:relocation,OWNER:bytes(owner)},resized=(VROM,RELOC))
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image or source_hashes()!=sources:
        raise ValueError('Keyboard patch or source retention failed')
    compiled.update(overlay_sha256=sha256(data), touched_offsets=sorted(allowed),
                    final_relocation_bases=['80200010','80378010'])
    (out/'editor/image.bin').write_bytes(data)
    (out/'editor/image.json').write_text(json.dumps(compiled,indent=2)+'\n')
    return image,patch,{'version':1,'source_sha256':sha256(native),'baseline_sha256':BASE_SHA,
        'output_sha256':sha256(image),'patch_sha256':sha256(patch),'sources':sources,'editor':compiled,
        'artwork':artwork,'key_metrics':glyphs,'font_sha256':FONT_SHA,'symbol_page':codes,
        'page_count':2,'distinct_supported_symbols':24,'shared_growth_bytes':growth,
        'existing_pool_extra_bytes':8192,'additional_pool_bytes':0,'toolchain_image':IMAGE,
        'rom_bytes':len(image),'required_ram_bytes':0x800000,'save_format_changed':False,
        'font_pixels_changed':False,'sound_code_changed':False,'fixed_issues':['V1-14'],
        'hardware_retest':'pending','native_tests':'pending'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=ROOT/'build/v1rc1-text-hud-fix-01')
    p.add_argument('--output',type=Path,default=ROOT/'build/v1rc1-keyboard-fix-01'); a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (a.base/'animal-forest-title-preview.z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),a.output)
    for name,data in {'animal-forest-title-preview.z64':image,'animal-forest-title-preview.ups':patch,
                      'fixes.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (a.output/name).open('xb') as target: target.write(data)
    print(json.dumps({k:report[k] for k in ('output_sha256','patch_sha256','shared_growth_bytes')},indent=2))


if __name__=='__main__': main()
