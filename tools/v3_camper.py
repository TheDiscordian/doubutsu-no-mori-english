"""Install an independent camper Animal and native reader; keep patchers V2."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256,
                   verified_rom, fix_checksum, make_ups, apply_ups)
from apply_translation import write_new
from v3_asset_loader import ROOT, BLOB, MODULE, STARTUP, CONFIG, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, replace_checked, jump
from v3_campsite_calendar import PACKAGE_SIZE

BASE = ROOT / 'build/v3-campsite-calendar-runtime-02'
BASE_SHA = '90279325c2c9c0b316e9705e741d4e1f7313c80b88df93e18736d0d84be35b6d'
REPORT_SHA = 'b687603059f655afe7293887d265a66cbc8e868c91c8dddc68378ec5c2c4fedd'
ABI, OWNER, OWNER_SIZE = 74, 0x804A1A00, 0x560
REGISTER, READER, TRAMPOLINE = 0x804A2D00, 0x804A29A0, 0x804A1F60
NPC_INFO = 0x800AB3A0


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build directory')
    native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE / 'build.json').read_bytes()
    if (sha256(base), sha256(raw)) != (BASE_SHA, REPORT_SHA):
        raise ValueError('Changed complete native calendar base')
    prior, files = json.loads(raw), by_vrom(base)
    blob = bytearray(files[BLOB].extract(base))
    package = blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    if (sha256(package) != prior['campsite_calendar']['package_sha256']
            or struct.unpack_from('>4I',blob,0xF0) !=
                (BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)
            or package[-16:] != bytes.fromhex('AFACC0DE')*4):
        raise ValueError('Changed checked package')
    output.mkdir(parents=True)
    register, registration = compile_part('camper',output/'register')
    reader, reading = compile_part('camper_reader',output/'reader')
    if len(register) > 0x2F0 or len(reader) > 0x160:
        raise ValueError('Camper code exceeds its independent reservations')
    code = bytearray(files[CODE_VROM].extract(base))
    old = bytes.fromhex('27bdffe8afa5001c')
    at = NPC_INFO-CODE_RAM
    if code[at:at+8] != by_vrom(native)[CODE_VROM].extract(native)[at:at+8]:
        raise ValueError('Native NPC attachment already changes')
    hook = struct.pack('>2I',jump(READER),0)
    replace_checked(code,at,old,hook)
    trampoline = old + struct.pack('>2I',jump(NPC_INFO+8),0)
    owner = bytearray(OWNER_SIZE)
    struct.pack_into('>4I',owner,0,0x41464341,1,OWNER_SIZE,0xD08F)
    owner[-16:] = bytes.fromhex('AFCA11ED')*4
    # The Animal is contiguous. Each allocation has an independently reviewed
    # end; no index, packet, code, or original package guard is overwritten.
    placements = ((OWNER,owner,TRAMPOLINE),(TRAMPOLINE,trampoline,0x804A1FF0),
                  (READER,reader,0x804A2B00),(REGISTER,register,0x804A2FF0))
    for address,data,end in placements:
        at = PACKAGE+address-PACKAGE_RAM
        if address+len(data)>end or any(blob[at:at+len(data)]):
            raise ValueError(f'Occupied camper reservation at {address:08X}')
        blob[at:at+len(data)] = data
    startup, startup_report = compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB+PACKAGE}','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module = bytearray(files[MODULE].extract(base)); old_startup = prior['startup']
    if (sha256(module[STARTUP:STARTUP+old_startup['bytes']]) != old_startup['sha256']
            or any(module[STARTUP+old_startup['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed or insufficient startup reservation')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    package = blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',blob,0xF0,BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    result = bytearray(base)
    for vrom,data in ((BLOB,blob),(MODULE,module),(CODE_VROM,code)):
        entry = files[vrom]
        if entry.pend or len(data)!=entry.size: raise ValueError('Camper changes an allocation')
        result[entry.pstart:entry.pstart+len(data)] = data
    fix_checksum(result); result = bytes(result)
    if len(by_vrom(result))!=3389 or result[DMA_START:DMA_END]!=base[DMA_START:DMA_END]:
        raise ValueError('Camper changes the DMA directory')
    patch = make_ups(native,result)
    if apply_ups(native,patch)!=result: raise ValueError('Camper patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-camper',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(result),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        startup=startup_report,native_test='pending current camper owner/reader test')
    for section in ('construction','garden','western','western_large','accessory_runtime','camping',
                    'tent_model','fire','import_storage','campsite','campsite_exterior','campsite_calendar'):
        report[section]['package_sha256'] = sha256(package)
    at = PACKAGE+0x804A1000-PACKAGE_RAM
    report['campsite']['packet_sha256'] = sha256(blob[at:at+0x1000])
    report['camper'] = dict(registration=registration,reader=reading,owner=OWNER,owner_bytes=OWNER_SIZE,
        animal=OWNER+0x20,animal_bytes=0x528,greeted=OWNER+0x10,
        owner_sha256=sha256(owner),trampoline=TRAMPOLINE,trampoline_hex=trampoline.hex(),
        hook=dict(address=NPC_INFO,before=old.hex(),after=hook.hex()),
        package_bytes=PACKAGE_SIZE,package_sha256=sha256(package),additional_resident_bytes=0,
        additional_heap_bytes=0,native_alias_slots=5,saved_format_changed=False,saved_profile_changed=False,
        npc_reader_installed=True,manager_installed=False,acquisition_installed=False,
        web_patcher_enabled=False,not_a_playtest_handoff=True,
        pending=['event-manager activation and greeting-state transitions',
                 'remaining masked NPC/conversation readers, English flow, rewards, and lighting',
                 'ordinary appearance, tent entry, exit, and persistence'])
    write_new(output/'animal-forest-v3-asset-loader.z64',result)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    report = build(args.output)
    print(json.dumps({key:report[key] for key in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
