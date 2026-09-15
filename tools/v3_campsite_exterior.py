"""Install the additive enterable campsite actor; do not publish either patcher."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256, verified_rom, fix_checksum, make_ups, apply_ups
from apply_translation import write_new
from gc_names import rel_sections
from v3_asset_loader import ROOT, BLOB, MODULE, STARTUP, CONFIG, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, END, jump, replace_checked
from v3_furniture_art import verify_sources
from v3_villager_art import data_pointers

BASE = ROOT / 'build/v3-campsite-runtime-03'
BASE_SHA = 'fc8a8682c58f61841f23996bacccf2daa98eefda2c6f9e65aa4e472713834ea9'
REPORT_SHA = '1295caaa47575b241ce5cbfe5fbb3d9448f6e21af6e970d5ed7171baf256d2d2'
ABI, PACKAGE_SIZE = 72, 0x2F010
ENTRY, PACKET = 0x804A0360, 0x804A1800
STRUCTURE, STRUCTURE_RAM, RELOC = 0x8CB690, 0x809E7ED0, 0x8CD350


def actor_packet(rel, symbols, entries):
    verify_sources(rel, symbols)
    base = rel_sections(rel)[5][0]
    profile = rel[base + 0x79C40:base + 0x79C64]
    door = rel[base + 0x79C94:base + 0x79CA8]
    grid = rel[base + 0x79CA8:base + 0x79CE7]
    expected_grid = bytes.fromhex('64030101070700640a0a0a0a0a0064030707010100'
        '64030101070700640a0a0a0a0a006403070701010064030303030300640a0a0a0a0a0064030303030300')
    if (profile.hex() != '00f301000000080058490003000002dc0000000000000000000000000000000000000000'
            or door.hex() != '00000033040000000078000000dc000001000000' or grid != expected_grid
            or data_pointers(rel, 0x79C94, 20) or data_pointers(rel, 0x79CA8, 63)):
        raise ValueError('Changed complete donor tent profile, entry door, or nine-cell collision')
    packet = bytearray(0x1F0)
    struct.pack_into('>4I', packet, 0, 0x41465445, 1, 0xCA, 0x5849)
    # Resident actor: no separate overlay allocation or mutable alias to an
    # existing descriptor. C9 remains the native no-demo sentinel.
    struct.pack_into('>8I', packet, 0x20, 0,0,0,0,0,PACKET + 0x40,0,0)
    # Native item/structure category 0; GC category 1 and Dolphin TA bit 0800
    # do not carry native semantics. Native keep bank and pool size are retained.
    struct.pack_into('>HHIHH6I', packet, 0x40, 0xCA, 0, 0, 0x5849, 3, 0x2D8,
        entries['af_v3_campsite_exterior_ct'], entries['af_v3_campsite_exterior_dt'],
        entries['af_v3_campsite_exterior_init'], entries['af_v3_campsite_exterior_dw'], 0)
    packet[0x80:0x94] = door
    struct.pack_into('>I', packet, 0x80, 35)
    packet[0xA0:0xDF] = grid
    packet[-16:] = bytes.fromhex('AFC7E17E') * 4
    return bytes(packet)


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh ignored build directory')
    native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE / 'build.json').read_bytes()
    if sha256(base) != BASE_SHA or sha256(raw) != REPORT_SHA:
        raise ValueError('Changed complete campsite scene-loader base')
    prior, files = json.loads(raw), by_vrom(base)
    output.mkdir(parents=True)
    callbacks, compiled = compile_part('campsite_exterior', output / 'callbacks')
    rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    packet = actor_packet(rel, symbols, compiled['symbols'])
    blob = bytearray(files[BLOB].extract(base)); old_blob_size = len(blob)
    old_package = blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
    if (sha256(old_package) != prior['campsite']['package_sha256']
            or struct.unpack_from('>4I', blob, 0xF0) !=
                (BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(old_package), PACKAGE_RAM)):
        raise ValueError('Changed complete checked campsite package')
    for address, data in ((ENTRY, callbacks), (PACKET, packet)):
        at = PACKAGE + address - PACKAGE_RAM
        if any(blob[at:at + len(data)]) or at < PACKAGE or at + len(data) >= PACKAGE + PACKAGE_SIZE - 16:
            raise ValueError('Campsite actor overlaps another checked resident resource')
        blob[at:at + len(data)] = data
    if ENTRY + len(callbacks) > 0x804A1000 or PACKET + len(packet) > 0x804A1FF0:
        raise ValueError('Campsite actor exceeds reserved scene code/data')
    changes = []
    def patch(owner, ram, address, before, after, reason):
        replace_checked(owner, address - ram, before, after)
        changes.append({'address':address,'before':before.hex(),'after':after.hex(),'purpose':reason})
    code = bytearray(files[CODE_VROM].extract(base))
    old = bytes.fromhex('3c0f801025ef0c90000671408d09000001cf8021')
    new = struct.pack('>5I', jump(ENTRY, link=True),0x00C02025,0x00408025,0x8FA80070,0x8D090000)
    patch(code,CODE_RAM,0x80057E4C,old,new,'additive resident actor descriptor with preserved saved arguments')
    structure = bytearray(files[STRUCTURE].extract(base)); reloc = files[RELOC].extract(base)
    setup = compiled['symbols']['af_v3_campsite_structure_setup']
    patch(structure,STRUCTURE_RAM,0x809E93F8,struct.pack('>I',0x3C0F809F),
          struct.pack('>I',0x3C0F0000 | ((setup + 0x8000) >> 16)), 'structure setup callback high address')
    patch(structure,STRUCTURE_RAM,0x809E9400,struct.pack('>I',0x25EF8E24),
          struct.pack('>I',0x25EF0000 | (setup & 65535)), 'structure setup callback low address')
    sections = struct.unpack_from('>5I',reloc)
    if sum(sections[:3]) != len(structure) or struct.unpack_from('>I',reloc,len(reloc)-4)[0] != len(reloc):
        raise ValueError('Changed complete structure relocation dimensions')
    keep, removed = [], []
    for word, in struct.iter_unpack('>I',reloc[20:20 + sections[4]*4]):
        section, off = word >> 30, word & 0xFFFFFF
        if section not in (1,2,3) or off & 3 or off >= sections[section-1]:
            raise ValueError('Invalid structure relocation')
        address = STRUCTURE_RAM + sum(sections[:section-1]) + off
        (removed if address in (0x809E93F8,0x809E9400) else keep).append(word)
    if removed != [0x45001528,0x46001530] or any(reloc[20 + sections[4]*4:-4]):
        raise ValueError('Changed structure setup pointer relocation ownership')
    updated_reloc = bytearray(reloc)
    struct.pack_into('>I',updated_reloc,16,len(keep))
    updated_reloc[20:-4] = struct.pack('>' + str(len(keep)) + 'I',*keep) + bytes(len(reloc)-24-4*len(keep))
    moves = []
    for vrom, data in ((STRUCTURE,structure),(RELOC,updated_reloc)):
        blob.extend(bytes(-len(blob)%16)); at=len(blob); blob.extend(data)
        moves.append({'vrom':vrom,'bytes':len(data),'blob_offset':at,
            'physical':files[BLOB].pstart+at,'sha256':sha256(data)})
    startup, startup_report = compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB+PACKAGE}','AF_V3_WESTERN_LARGE=1','AF_V3_CAMPSITE=1'))
    module=bytearray(files[MODULE].extract(base)); old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed or insufficient startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    package=blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    struct.pack_into('>4I',blob,0xF0,BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    start,end=files[BLOB].pstart+old_blob_size,files[BLOB].pstart+len(blob)
    if (BLOB+len(blob)>END or end>len(base) or any(base[start:end])
            or any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                   for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)):
        raise ValueError('Campsite actor storage overlaps a live resource')
    result=bytearray(base)
    for v,data in ((BLOB,blob),(MODULE,module),(CODE_VROM,code)):
        entry=files[v]
        if entry.pend or (v!=BLOB and len(data)!=entry.size): raise ValueError('Changed owner encoding/size')
        result[entry.pstart:entry.pstart+len(data)]=data
    struct.pack_into('>I',result,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in moves:
        struct.pack_into('>4I',result,DMA_START+files[row['vrom']].index*16,
            row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    fix_checksum(result); result=bytes(result)
    if len(by_vrom(result))!=3389 or result[DMA_END-16:DMA_END]!=bytes(16):
        raise ValueError('Campsite changes DMA count/terminator')
    patch_data=make_ups(native,result)
    if apply_ups(native,patch_data)!=result: raise ValueError('Cartridge patch reconstruction failed')
    report=copy.deepcopy(prior)
    report.update(build='v3-campsite-exterior',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(result),patch_sha256=sha256(patch_data),blob_sha256=sha256(blob),
        blob_bytes=len(blob),blob_file_bytes=len(blob),startup=startup_report,
        native_test='pending current complete exterior integration')
    for section in ('construction','garden','western','western_large','accessory_runtime','camping',
                    'tent_model','fire','import_storage','campsite'):
        report[section]['package_sha256']=sha256(package)
    report['import_storage']['remaining_bytes']=END-BLOB-len(blob)
    report['campsite']['packet_sha256']=sha256(blob[PACKAGE+0x2E000:PACKAGE+0x2F000])
    report['campsite']['pending']=['summer event','camper registration and English conversations',
        'selected rewards','scene lighting and floor sounds','ordinary entry/exit, GPU appearance, and persistence']
    report['campsite_exterior']={'code':compiled,'packet_ram':PACKET,'packet_bytes':len(packet),
        'packet_sha256':sha256(packet),'actor_id':'00CA','foreground_id':'5849','dummy_id':'F127',
        'actor_bytes':0x2D8,'asset_allocation_bytes':0x1E60,'additional_resident_bytes':0,
        'hooks':changes,'resource_moves':moves,'removed_relocations':removed,
        'original_igloo_unchanged': files[0x8D3D00].extract(base)==by_vrom(native)[0x8D3D00].extract(native),
        'event_installed':False,'acquisition_installed':False,'web_patcher_enabled':False,
        'saved_format_changed':False,'saved_profile_changed':False,'not_a_playtest_handoff':True}
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in (
        'tools/v3_campsite_exterior.py','tools/v3_asset_loader.py','overlays/v3/campsite_exterior.c',
        'overlays/v3/campsite_exterior.ld')})
    write_new(output/'animal-forest-v3-asset-loader.z64',result)
    write_new(output/'asset-loader.ups',patch_data)
    write_new(output/'build.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    result=build(parser.parse_args().output)
    print(json.dumps({k:result[k] for k in ('runtime_abi','output_sha256','patch_sha256')},indent=2))
