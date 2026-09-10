"""Install a bounded read-only English birthday renderer and its strings."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from artwork_chain import rebuild
from catalogue_names import Image,elf_inventory
from npc_mail_show import relocate_verified_data
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='23f9d9724827d0de3c91bd00a91349b04b0d45371d1930ef71cdbb95910e711e'
OWNER,RELOC,ASSET,RAM=0x79DA50,0x79E370,0xADD000,0x8089A350
START,END=0x334,0x740
NATIVE_HASHES={OWNER:'96c2b38dff3968ed6c138cfe83b5daceb8ff11b116a543ee6ac96f3ab58f10e8',
    RELOC:'976c3542d4cddf142d26c2b36562f50f5532c8ff92e8701e4720367f8ba0c736',
    ASSET:'e0f0c6847214f1c116448e2172c02639d379795f3e14531cbdb5094ad7a9c0a6'}
DRAW_SHA='d584bb146149cf1843294d9a6d9c77bf1b71e8a89938956fd83d780a5344880e'
PROMPT=b"When's your birthday?"
MONTHS=(b'January',b'February',b'March',b'April',b'May',b'June',b'July',b'August',
        b'September',b'October',b'November',b'December')
IMPORTS=((0x8089A6F4,0x800E041C,'af_birthday_scale'),
         (0x8089A710,0x800E0314,'af_birthday_translate'),
         (0x8089A72C,0x800E13C4,'af_birthday_matrix'),
         (0x8089A814,0x8009264C,'af_birthday_number'),
         (0x8089A89C,0x80090E98,'af_birthday_font'))


def strings():
    data=bytearray(512);data[:len(PROMPT)+1]=PROMPT+b'\0'
    for i,month in enumerate(MONTHS+(b'?',)):
        data[24+i*10:24+(i+1)*10]=month+bytes(10-len(month))
    data[0x9A:0x9C]=b'OK'
    return bytes(data)


def source(native):
    files=by_vrom(verified_rom(native));old={v:files[v].extract(native) for v in NATIVE_HASHES}
    if any(sha256(old[v])!=digest for v,digest in NATIVE_HASHES.items()):
        raise ValueError('Unknown native birthday owner, relocation, or assets')
    return old


def compiled(directory):
    from build_birthday_draw import FLAGS
    from toolchain import KNOWN_IMAGES
    draw=(directory/'draw.bin').read_bytes();profile=json.loads((directory/'draw.json').read_text())
    inventory=elf_inventory((directory/'relocations.txt').read_text(),ram=RAM)
    expected=[[at-RAM,4,target,name] for at,target,name in IMPORTS]
    paths=(ROOT/'overlays/birthday/draw.c',ROOT/'overlays/birthday/draw.ld')
    hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()) for p in paths}
    if (len(draw)!=800 or sha256(draw)!=DRAW_SHA or inventory!=expected
            or profile.get('sources')!=hashes or profile.get('sha256')!=DRAW_SHA
            or profile.get('ram')!=RAM+START or profile.get('bytes')!=800
            or profile.get('native_capacity')!=END-START or profile.get('toolchain_image') not in KNOWN_IMAGES
            or profile.get('flags')!=FLAGS or profile.get('fits_native_function') is not True
            or profile.get('stack_usage')!='/source/overlays/birthday/draw.c:45:6:af_birthday_draw\t136\tstatic\n'):
        raise ValueError('Changed birthday renderer compilation or source profile')
    for at,target,_ in IMPORTS:
        if struct.unpack_from('>I',draw,at-RAM-START)[0]!=0x0C000000|((target>>2)&0x3FFFFFF):
            raise ValueError('Unbound native birthday call')
    return draw,hashes


def replacements(native,draw):
    old=source(native)
    if len(draw)!=800 or sha256(draw)!=DRAW_SHA:raise ValueError('Unapproved birthday drawing instructions')
    owner=bytearray(old[OWNER]);owner[START:END]=draw+bytes(END-START-len(draw))
    sections=struct.unpack_from('>5I',old[RELOC])
    if sections!=(2272,64,0,16,41):raise ValueError('Changed native birthday sections')
    rows=list(struct.unpack_from('>41I',old[RELOC],20));kept=[];removed=[]
    for word in rows:
        section=word>>30
        if section not in (1,2):raise ValueError('Unknown birthday relocation section')
        at=(word&0xFFFFFF)+(sections[0] if section==2 else 0)
        (removed if START<=at<END else kept).append(word)
    if len(removed)!=6 or len(kept)!=35:raise ValueError('Unexpected replaced birthday relocation count')
    reloc=struct.pack('>5I',*sections[:4],35)+struct.pack('>35I',*kept)+bytes(28)+struct.pack('>I',192)
    asset=bytearray(old[ASSET]);asset[0x2DB8:0x2FB8]=strings()
    for load,offset,quad in ((0xAB8,0x2EB8,0x340),(0xB08,0x2DB8,0x380)):
        expected=struct.pack('>18I',0xFD900000,0x0C000000+offset,0xF5900000,0x07050150,
            0xE6000000,0,0xF3000000,0x0707F400,0xE7000000,0,0xF5800400,0x00F50150,
            0xF2000000,0x0007C03C,0x01004008,0x0C000000+quad,0x06000204,0x00020604)
        if old[ASSET][load:load+72]!=expected:raise ValueError('Changed native birthday suffix reader')
        asset[load:load+72]=bytes.fromhex('E000000000000000')*9
    changed={OWNER:bytes(owner),RELOC:reloc,ASSET:bytes(asset)}
    for base in (0x801A0010,0x802F8010,0x803F0010):
        before=relocate_verified_data(Image(RAM,2352,sections),old[OWNER],old[RELOC],base)
        after=relocate_verified_data(Image(RAM,2352,(*sections[:4],35)),changed[OWNER],reloc,base)
        if before[:START]!=after[:START] or before[END:]!=after[END:] or after[START:START+800]!=draw:
            raise ValueError('Birthday relocation changes unrelated code/state or its new renderer')
    return changed


def profile(changed,hashes):
    return {'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'native_sha256':{f'{v:08X}':d for v,d in NATIVE_HASHES.items()},
        'installed_sha256':{f'{v:08X}':sha256(b) for v,b in changed.items()},
        'renderer_sha256':DRAW_SHA,'sources':hashes,'prompt':PROMPT.decode(),
        'months':[m.decode() for m in MONTHS],'renderer_bytes':800,'native_function_bytes':1036,
        'stack_bytes':136,'relocation_count':35,'allocation_changed':False,'input_changed':False,
        'saved_format_changed':False,'status':'English birthday renderer installed; native/ordinary acceptance pending'}


def build(native,base,report,rel,symbols,directory):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Birthday screen requires the complete service-artwork baseline')
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256 or rel[DATA_BASE+0x7A6FC:DATA_BASE+0x7A6FC+len(PROMPT)]!=PROMPT:
        raise ValueError('Unknown English birthday source wording')
    draw,hashes=compiled(directory);changed=replacements(native,draw);files=by_vrom(base)
    if any(sha256(files[v].extract(base))!=digest for v,digest in NATIVE_HASHES.items()):
        raise ValueError('Birthday owner or asset already contains unrelated changes')
    image,patch,result=rebuild(native,base,report,changed)
    result['birthday_screen']=profile(changed,hashes)
    result['release_status']='Complete English birthday presentation; focused native acceptance pending'
    return image,patch,result


def measure_text(ledger,native,built,report):
    old=source(native);installed=report.get('birthday_screen')
    if installed:
        draw,hashes=compiled(ROOT/'build/birthday-draw-03');changed=replacements(native,draw)
        if installed!=profile(changed,hashes) or any(by_vrom(built)[v].extract(built)!=data for v,data in changed.items()):
            raise ValueError('Changed installed birthday translation or reader')
    for index,(offset,length,english) in enumerate(((0x8FC,10,PROMPT),(0x908,3,b'OK'))):
        identity=f'ui_birthday:{index:04X}'
        ledger.add(identity,old[OWNER][offset:offset+length])
        if installed:ledger.credit(identity,english,'birthday_screen')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/birthday-screen-01')
    a=p.parse_args();base=ROOT/'build/service-artwork-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),ROOT/'build/birthday-draw-03')
    a.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (a.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(a.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
