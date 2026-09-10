"""Install supplied English town-tune controls without changing native tune data."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from artwork_chain import rebuild
from building_artwork import donor_texture_pointers
from map_artwork import Donor,compile_commands
from notice_artwork import source_pixels,expected_load
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,pack4,model_texture_shape

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='96d2b253bdf727bf537c416d49fdd0a0eb70abfe0be8a0c8ade9dafbd46de941'
VROM=0xAD1000
NATIVE_SHA='a1644c0082cf2ae0cafc5a9d21290838a55863f2a787ec285ec3b3b6bd99ece6'
ROWS=(('Play',Donor(0x4A2500,0x4A40B8,8),0x67C8,0x3F80,0x3550),
      ('Erase',Donor(0x4A2900,0x4A4098,8),0x6C48,0x3F30,0x3510))
OKAY=Donor(0x4A4980,0x4A9310,8)
OKAY_LOAD=bytes.fromhex('FD9000000C0043C8F590000007090250E600000000000000'
    'F30000000707F400E700000000000000F580040000F90250F20000000007C03C')


def commands(directory):
    return compile_commands(directory,ROOT/'overlays/tune_artwork/labels.c',(('okay',56),))


def patch_assets(native,rel,symbols,compiled):
    verified_rom(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Unexpected English town-tune artwork source')
    pointers=donor_texture_pointers(rel,tuple(row[1] for row in ROWS)+(OKAY,))
    old=by_vrom(native)[VROM].extract(native)
    if sha256(old)!=NATIVE_SHA or compiled!={'okay':OKAY_LOAD}:
        raise ValueError('Unexpected native town-tune asset or compiled load')
    data=bytearray(old);records=[]
    for name,donor,target,load,quad in ROWS:
        if model_texture_shape(rel[DATA_BASE+donor.gc_model:DATA_BASE+donor.gc_model+8])!=(64,16,3,1):
            raise ValueError('English town-tune label shape changed')
        if (old[load:load+56]!=expected_load(target,64,False)
                or old[load+56:load+64]!=struct.pack('>2I',0x01004008,0x0C000000+quad)):
            raise ValueError('Native town-tune label reader changed')
        vertices=list(struct.iter_unpack('>3hH2h4B',old[quad:quad+64]))
        if (max(v[0] for v in vertices)-min(v[0] for v in vertices)!=64
                or max(v[1] for v in vertices)-min(v[1] for v in vertices)!=16
                or {v[4] for v in vertices}!={0,2048} or {v[5] for v in vertices}!={0,512}):
            raise ValueError('Native town-tune label sampling changed')
        value=source_pixels(rel,donor,64);data[target:target+1024]=value
        records.append({'label':name,'gc_texture':f'{donor.gc:08X}',
            'texture_vrom':f'{VROM+target:08X}','format':'IA8','width':64,'height':16,
            'texture_sha256':sha256(value)})
    if model_texture_shape(rel[DATA_BASE+OKAY.gc_model:DATA_BASE+OKAY.gc_model+8])!=(32,16,4,0):
        raise ValueError('English OK label shape changed')
    if old[0x4118:0x4160]!=bytes.fromhex('FD9000000C0043C8F590000007050160E600000000000000'
        'F3000000070FF200E700000000000000F580080000F50160F2000000000FC03C'
        '010040080C0036500600020400020604'):
        raise ValueError('Native finish-label reader changed')
    value=pack4(untile(rel[DATA_BASE+OKAY.gc:DATA_BASE+OKAY.gc+256],32,16,4))
    data[0x43C8:0x45C8]=value+bytes(256);data[0x4118:0x4150]=OKAY_LOAD
    for at in range(0x3650,0x3690,16):
        x,y,z,flag,s,t,*colour=struct.unpack_from('>3hH2h4B',old,at)
        if x not in (75,135) or y not in (-49,-64) or z or s not in (0,2048) or t not in (0,512):
            raise ValueError('Native finish-label quad changed')
        struct.pack_into('>h',data,at,90 if x==75 else 120)
        struct.pack_into('>h',data,at+8,s//2)
    records.append({'label':'OK','gc_texture':f'{OKAY.gc:08X}',
        'texture_vrom':'00AD53C8','format':'I4','width':32,'height':16,'texture_sha256':sha256(value)})
    data=bytes(data)
    return data,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'asset_vrom':f'{VROM:08X}','native_asset_sha256':NATIVE_SHA,'asset_sha256':sha256(data),
        'labels':records,'donor_texture_pointers':{f'{k:08X}':f'{v:08X}' for k,v in pointers.items()},
        'command_source_sha256':sha256((ROOT/'overlays/tune_artwork/labels.c').read_bytes()),
        'allocation_changed':False,'cpu_code_changed':False,'saved_melody_changed':False,
        'native_button_icons_preserved':True,'status':'English tune controls installed; ordinary acceptance pending'}


def build(native,base,report,rel,symbols,compiled):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Town-tune artwork requires the complete bulletin-board artwork baseline')
    if sha256(by_vrom(base)[VROM].extract(base))!=NATIVE_SHA:
        raise ValueError('Town-tune asset already contains unrelated changes')
    data,profile=patch_assets(native,rel,symbols,compiled)
    image,patch,result=rebuild(native,base,report,{VROM:data})
    result['tune_artwork']=profile
    result['release_status']='English tune/notice controls with all prior fixes; ordinary screen acceptance pending'
    return image,patch,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/tune-artwork-01')
    args=parser.parse_args();base=ROOT/'build/notice-artwork-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
        commands(ROOT/'build/tune-artwork-commands'))
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
