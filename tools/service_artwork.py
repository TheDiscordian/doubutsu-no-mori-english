"""Install supplied mailbox and repayment labels in existing asset allocations."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from artwork_chain import rebuild
from building_artwork import donor_texture_pointers
from map_artwork import Donor,compile_commands
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,pack4,model_texture_shape

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='67f72b69017452be3ec83e05a513502fd58752bd0cf96b000a182fee4f880a58'
MAIL,REPAY=0xA7C000,0xACC000
NATIVE_HASHES={MAIL:'675e45d3a2b53151fecf8316e48bb39d099c15994cc4c71485002108a345eaa6',
              REPAY:'d04e4d7008026baea0793c7d9b97511eda3e95a71474dacdaeb5e66f51cc9c2f'}
MAIL_DONOR=Donor(0x4ABCC0,0x4AD8D8,8)
# name, donor, width, original texture, destination, load, quad, old width
ROWS=(('cash',Donor(0x4D8C00,0x4DB578,8),64,0x1288,0x1288,0x8E0,0x180,96),
      ('payment',Donor(0x4D8A00,0x4DB590,8),64,0x1588,0x2A08,0x890,0x140,96),
      ('owe',Donor(0x4D7F00,0x4DB5A8,8),96,0x2A08,0x1588,0x7E0,0x40,48),
      ('bells',Donor(0x4D8E00,0x4DB550,8),32,0x2088,0x2088,0x830,0x80,32))


def commands(directory):
    return compile_commands(directory,ROOT/'overlays/service_artwork/labels.c',
                            tuple((row[0],56) for row in ROWS))


def expected_load(offset,width):
    mask={32:5,64:6,96:0}[width];mode=0x90200+(mask<<4);line=width//16
    return struct.pack('>14I',0xFD900000,0x0C000000+offset,0xF5900000,0x07000000+mode,
        0xE6000000,0,0xF3000000,0x07000000+((width*4-1)<<12)+(2048+line-1)//line,
        0xE7000000,0,0xF5800000+(line<<9),0x00F00000+mode,0xF2000000,((width-1)*4<<12)+60)


def source_pixels(rel,donor,width):
    if model_texture_shape(rel[DATA_BASE+donor.gc_model:DATA_BASE+donor.gc_model+8])!=(width,16,4,0):
        raise ValueError('English service-label dimensions changed')
    return pack4(untile(rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+width*8],width,16,4))


def readers(data,offset):
    pointer=struct.pack('>I',0x0C000000+offset)
    return [at for at in range(len(data)-3) if data[at:at+4]==pointer]


def patch_assets(native,rel,symbols,compiled):
    verified_rom(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Unexpected English service artwork source')
    files=by_vrom(native);old={v:files[v].extract(native) for v in NATIVE_HASHES}
    if any(sha256(old[v])!=digest for v,digest in NATIVE_HASHES.items()):
        raise ValueError('Changed native mailbox/repayment assets')
    if set(compiled)!={row[0] for row in ROWS}:raise ValueError('Unexpected service load inventory')
    for owner,at,v in ((0x789B60,0x984,MAIL),(0x79B120,0xDD8,REPAY)):
        if files[owner].extract(native)[at:at+8]!=struct.pack('>2I',v,v+len(old[v])):
            raise ValueError('Native service asset binding changed')
    pointers=donor_texture_pointers(rel,(MAIL_DONOR,)+tuple(row[1] for row in ROWS))
    changed={v:bytearray(data) for v,data in old.items()};records=[]
    mail=source_pixels(rel,MAIL_DONOR,64)
    if old[MAIL][0x960:0x9A8]!=bytes.fromhex('FD9000000C0035B0F590000007050160E600000000000000'
        'F3000000070FF200E700000000000000F580080000F50160F2000000000FC03C'
        '010040080C0003D00600020400020604'):
        raise ValueError('Native mailbox heading reader changed')
    changed[MAIL][0x35B0:0x37B0]=mail
    records.append({'label':'Mail','gc_texture':f'{MAIL_DONOR.gc:08X}',
        'texture_vrom':'00A7F5B0','width':64,'height':16,'texture_sha256':sha256(mail)})
    b=old[REPAY];data=changed[REPAY]
    # Reuse only the two reviewed existing regions, retaining the border's pixels.
    if readers(b,0x2B88)!=[0xA84] or b[0xA80:0xA88]!=bytes.fromhex('FD9000000C002B88'):
        raise ValueError('Unaccounted native repayment border reader')
    data[0x1288:0x1888]=bytes(1536);data[0x2A08:0x2C08]=bytes(512)
    data[0x1488:0x1508]=b[0x2B88:0x2C08]
    struct.pack_into('>I',data,0xA84,0x0C001488)
    for name,donor,width,original,target,load,quad,old_width in ROWS:
        if (readers(b,original)!=[load+4]
                or b[load:load+8]!=struct.pack('>2I',0xFD900000,0x0C000000+original)
                or b[load+48:load+56]!=struct.pack('>2I',0xF2000000,((old_width-1)*4<<12)+60)):
            raise ValueError('Native repayment label reader changed')
        count=12 if name=='bells' else 4
        if b[load+56:load+64]!=struct.pack('>2I',0x01000000+(count<<12)+(count*2),0x0C000000+quad):
            raise ValueError('Native repayment label vertex reader changed')
        expected=expected_load(target,width)
        if compiled[name]!=expected:raise ValueError('Compiled service load differs from native GBI')
        value=source_pixels(rel,donor,width)
        data[target:target+len(value)]=value;data[load:load+56]=expected
        if name!='bells':
            for at in range(quad,quad+64,16):
                x,y,z,flag,s,t,*colour=struct.unpack_from('>3hH2h4B',b,at)
                if x not in (-12-old_width*3//4,-12) or flag or s not in (0,old_width*32) or t not in (0,512):
                    raise ValueError('Native repayment label geometry changed')
                struct.pack_into('>h',data,at,-12 if x==-12 else -12-width*3//4)
                struct.pack_into('>h',data,at+8,s*width//old_width)
        records.append({'label':name,'gc_texture':f'{donor.gc:08X}',
            'texture_vrom':f'{REPAY+target:08X}','width':width,'height':16,'texture_sha256':sha256(value)})
    changed={v:bytes(data) for v,data in changed.items()}
    if any(len(changed[v])!=len(old[v]) for v in old):raise ValueError('Service artwork allocation changed')
    return changed,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'native_asset_sha256':{f'{v:08X}':d for v,d in NATIVE_HASHES.items()},
        'asset_sha256':{f'{v:08X}':sha256(data) for v,data in changed.items()},'labels':records,
        'donor_texture_pointers':{f'{k:08X}':f'{v:08X}' for k,v in pointers.items()},
        'command_source_sha256':sha256((ROOT/'overlays/service_artwork/labels.c').read_bytes()),
        'allocation_changed':False,'cpu_code_changed':False,'saved_format_changed':False,
        'border_pixels_preserved':True,'status':'English mailbox/repayment images installed; ordinary acceptance pending'}


def build(native,base,report,rel,symbols,compiled):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Service artwork requires the complete catalogue baseline')
    files=by_vrom(base)
    if any(sha256(files[v].extract(base))!=digest for v,digest in NATIVE_HASHES.items()):
        raise ValueError('Service assets already contain unrelated changes')
    changed,profile=patch_assets(native,rel,symbols,compiled)
    image,patch,result=rebuild(native,base,report,changed)
    result['service_artwork']=profile
    result['release_status']='English mailbox/repayment controls with prior fixes; ordinary acceptance pending'
    return image,patch,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/service-artwork-01')
    args=parser.parse_args();base=ROOT/'build/catalogue-artwork-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
        commands(ROOT/'build/service-artwork-commands'))
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
