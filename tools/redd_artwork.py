"""Port Redd's English summer sign without disturbing snow or existing colours."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from artwork_chain import rebuild
from building_artwork import Texture,donor_texture_pointers,palette_equivalent,model_refs,PALETTES_SHA
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,pack4,rgb5a3,model_texture_shape
from nookington_sign import OBJECT,NEW_OBJECT

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '7ec5ba6eb5a68e15a3c89ab37111cf758a5b02241a1f51291cebf174b64ef6ad'
PALETTES = 0xD5B000
DONOR = Texture('obj_s_yamishop_t1_tex_txt',0xD5F0C8,0x50EF80,0xD5BA48,0x50E760,
                0x50F800,0x420,0x50FC70,0x88)


def patch_assets(native,prior,rel,symbols):
    verified_rom(native)
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English Redd source')
    files = by_vrom(native)
    original = files[OBJECT].extract(native)
    if len(prior) != len(original) or prior[:0x3440] != original[:0x3440]:
        raise ValueError('Redd native summer/winter source region changed')
    pointers = donor_texture_pointers(rel,(DONOR,))
    model = rel[DATA_BASE+DONOR.gc_model:DATA_BASE+DONOR.gc_model+DONOR.model_bytes]
    if model_texture_shape(model) != (128,32,2,0):
        raise ValueError('Redd source texture shape changed')
    refs,uses = model_refs(prior,DONOR,rel[DATA_BASE+DONOR.gc_vertices:DATA_BASE+DONOR.gc_vertices+DONOR.vertex_bytes])
    if refs != ['00D5E518','00D5E6F8'] or uses != 31:
        raise ValueError('Redd main/door texture bindings changed')
    # Both summer colour textures; the independent window texture is intensity only.
    used = {v for b in prior[0x8C8:0x18C8] for v in (b>>4,b&15)}
    if 13 in used or 14 in used:
        raise ValueError('English reds would recolour existing native summer pixels')
    pal_table = files[0xD5D000].extract(native)
    if sha256(pal_table) != '76ff36c9a7ccd0ad3def96bf3125e1db4fe8e5cdbf1cea2a9f98c96ac505c052':
        raise ValueError('Native palette ownership table changed')
    refs_pal = [(i*4,v) for i,(v,) in enumerate(struct.iter_unpack('>I',pal_table))
                if v < 0x06000A68 and v+32 > 0x06000A48]
    if refs_pal != [(0x108,0x06000A48)]:
        raise ValueError('Summer Redd palette is shared by another seasonal reader')
    pals = files[PALETTES].extract(native)
    if sha256(pals) != PALETTES_SHA:
        raise ValueError('Native building palette file changed')
    gc_palette = rel[DATA_BASE+DONOR.gc_palette:DATA_BASE+DONOR.gc_palette+32]
    new_palette = bytearray(pals)
    for i in (13,14):
        rgba = rgb5a3(struct.unpack_from('>H',gc_palette,i*2)[0])
        if rgba[3] != 255:raise ValueError('New Redd lettering must use opaque palette colours')
        value = (rgba[0]>>3)<<11 | (rgba[1]>>3)<<6 | (rgba[2]>>3)<<1 | 1
        struct.pack_into('>H',new_palette,0xA48+i*2,value)
    if new_palette[0xA62:0xA66] != bytes.fromhex('E04181CF'):
        raise ValueError('English Redd red colours changed')
    samples = untile(rel[DATA_BASE+DONOR.gc:DATA_BASE+DONOR.gc+2048],128,32,4)
    palette_equivalent(bytes(new_palette[0xA48:0xA68]),gc_palette,set(samples)|used)
    winter = pack4(untile(rel[DATA_BASE+0x510720:DATA_BASE+0x510F20],128,32,4))
    if prior[0x2AE8:0x32E8] != winter:
        raise ValueError('Winter snowy tent differs from the retained donor')
    converted = pack4(samples)
    changed = prior[:0x10C8]+converted+prior[0x18C8:]
    return changed,bytes(new_palette),{'version':1,'source_rel_sha256':REL_SHA256,
        'source_symbols_sha256':SYMBOLS_SHA256,'texture_vrom':'00D5F0C8',
        'donor_texture_offset':'0050EF80','texture_sha256':sha256(converted),
        'object_sha256':sha256(changed),'palettes_sha256':sha256(new_palette),
        'new_summer_palette_indices':[13,14],'previously_unused_indices':True,
        'exclusive_palette_table_offset':'0108','palette_changed_bytes':4,
        'matched_vertex_uses':uses,'native_texture_references':refs,
        'donor_texture_pointers':{f'{k:08X}':f'{v:08X}' for k,v in pointers.items()},
        'winter_retained':True,'allocation_changed':False,'models_changed':False,
        'status':'English summer sign installed; snowy winter retained; ordinary appearance pending'}


def build(native,base,report,rel,symbols):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Redd artwork requires the complete police/signs/grid baseline')
    files = by_vrom(base)
    prior = files[OBJECT].extract(base)
    changed,palette,profile = patch_assets(native,prior,rel,symbols)
    if sha256(files[PALETTES].extract(base)) != PALETTES_SHA:
        raise ValueError('Installed building palettes have unrelated changes')
    expanded = files[NEW_OBJECT].extract(base)
    if expanded[:len(prior)] != prior or sha256(expanded) != report['police_artwork']['streamed_object_sha256']:
        raise ValueError('Current streamed building source differs from the complete police profile')
    new_expanded = changed+expanded[len(prior):]
    profile.update(streamed_object_vrom=f'{NEW_OBJECT:08X}',streamed_object_sha256=sha256(new_expanded))
    image,patch,result = rebuild(native,base,report,{OBJECT:changed,NEW_OBJECT:new_expanded,PALETTES:palette})
    result.update(redd_artwork=profile,release_status='English police/Redd/shop signs and grid; further native acceptance pending')
    return image,patch,result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/redd-artwork-01')
    args=parser.parse_args();baseline=ROOT/'build/police-artwork-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(),json.loads((baseline/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':report['output_sha256'],'patch_sha256':report['patch_sha256']}))


if __name__=='__main__':main()
