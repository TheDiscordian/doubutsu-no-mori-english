"""Disposable summer-town fixture and read-only ordinary campsite observations."""
import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import struct
import time
from aflib import by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import BLOB,ROOT
from v3_cheri_gameplay_fixture import SOURCE_SHA
from v3_save_clothing import PROFILE,STATE
from v3_save_codec import BANK,PAYLOAD


def create(source,rom,report):
    if len(source)!=2*BANK or sha256(source)!=SOURCE_SHA:
        raise ValueError('Summer fixture requires the preserved source town')
    if sha256(rom)!=report['output_sha256'] or not report.get('tent_lamp'):
        raise ValueError('Summer fixture requires the current complete lamp cartridge')
    profile=bytes.fromhex(report['save_runtime']['profile_hex'])
    if len(profile)!=PROFILE or by_vrom(rom)[BLOB].extract(rom)[0x20:0x20+PROFILE]!=profile:
        raise ValueError('Changed installed import profile')
    spec=importlib.util.spec_from_file_location('v3_summer_save_reference',ROOT/'tests/test_v3_save_clothing.py')
    reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    state=profile+bytes(STATE-PROFILE);out=bytearray()
    for number in range(2):
        original=source[number*BANK:(number+1)*BANK]
        if original[4:8]!=b'NAFJ' or sum(struct.unpack('>'+str(PAYLOAD//2)+'H',original[:PAYLOAD]))&65535:
            raise ValueError('Invalid source bank')
        packed=reference.reference_pack(original,state)
        if any(original[i]!=packed[i] for i in range(PAYLOAD) if i not in (4,5,6,7,0x12,0x13)):
            raise ValueError('Summer fixture changes original town content')
        out.extend(packed)
    return bytes(out),dict(source_save_sha256=SOURCE_SHA,fixture_save_sha256=sha256(out),
        rom_sha256=sha256(rom),save_format=2,only_signature_checksum_and_profile_changed=True,
        seeded_campsite=False,seeded_camper=False,seeded_rewards=False,source_save_modified=False)


def snapshot(debug):
    def read(at,n):
        if at&3 or not 0x80000000<=at<=0x80800000-n:raise ValueError('Invalid campsite pointer')
        return debug.read_memory(at,n)
    def word(at):return int.from_bytes(read(at,4),'big')
    game=word(0x8010EF90);scene=word(0x80126EB4)
    grid=read(0x80126EA0+0x62A8,30*512);markers=[]
    for i,(fg,) in enumerate(struct.iter_unpack('>H',grid)):
        if fg not in (0x5849,0xF127):continue
        acre,unit=divmod(i,256);z,x=divmod(unit,16);bz,bx=divmod(acre,5)
        markers.append(dict(foreground=f'{fg:04X}',acre=[bx+1,bz+1],unit=[x,z],
                            world=[(bx+1)*640+x*40+20,(bz+1)*640+z*40+20]))
    structures=[];count,actor=struct.unpack('>II',read(game+0x1C7C,8));seen=set()
    if count>64:raise ValueError('Invalid structure actor count')
    for _ in range(count):
        if not actor or actor in seen:raise ValueError('Invalid structure actor chain')
        seen.add(actor);data=read(actor,0x174)
        if data[2]!=0:raise ValueError('Wrong structure actor category')
        if int.from_bytes(data[:2],'big')==0xCA:
            extra=read(actor+0x2B8,0x20)
            structures.append(dict(address=f'{actor:08X}',foreground=data[6:8].hex(),
                world=list(struct.unpack_from('>3f',data,0x28)),assets=f'{int.from_bytes(extra[:4],"big"):08X}',
                state_hex=extra.hex()))
        actor=int.from_bytes(data[0x158:0x15C],'big')
    if actor:raise ValueError('Structure chain exceeds declared count')
    return dict(read_only=True,scene=scene,game=f'{game:08X}',rtc=debug.read_memory(0x80136FBE,6).hex(),
        seconds=word(0x80136FB8),summer_event_index=debug.read_memory(0x804A2B00+70,1).hex(),
        markers=markers,tents=structures,camper_state=read(0x804A1A00,32).hex(),
        camper_animal=debug.read_memory(0x804A1A20,2).hex(),
        lamp_state=read(0x8046FFC0,36).hex())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored build directory')
    source=ROOT/'local/rc2-save-report-g3O4lU/test.flash'
    data,receipt=create(source.read_bytes(),args.rom.read_bytes(),json.loads((args.rom.parent/'build.json').read_bytes()))
    staged=datetime(2026,8,22,12,0);bcd=lambda n:(n//10)*16+n%10
    rtc=bytearray(b'\xFF'*32)
    rtc[16:24]=bytes((0,0,bcd(staged.hour)|128,bcd(staged.day),bcd((staged.weekday()+1)%7),
                     bcd(staged.month),bcd(staged.year%100),bcd(staged.year//100-19)))
    rtc[24:]=int(time.time()).to_bytes(8,'big');receipt.update(isolated_clock=staged.isoformat(),rtc_sha256=sha256(rtc))
    out.mkdir(parents=True);write_new(out/'test.flash',data);write_new(out/'test.rtc',rtc)
    write_new(out/'fixture.json',(json.dumps(receipt,indent=2)+'\n').encode())
    if sha256(source.read_bytes())!=SOURCE_SHA:raise ValueError('Source save changed')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
