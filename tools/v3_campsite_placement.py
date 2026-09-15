"""Add native tent placement/removal classification; preserve the V2 patchers."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256,
                   verified_rom, fix_checksum, make_ups, apply_ups)
from apply_translation import write_new
from gc_names import rel_sections
from v3_asset_loader import ROOT, BLOB, MODULE, STARTUP, CONFIG, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, replace_checked, jump
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_art import verify_sources
from v3_villager_art import data_pointers

BASE = ROOT / 'build/v3-camper-runtime-02'
BASE_SHA = 'bd2fd28f02f1b667c1038e4ffc1121026d4660d94847afa53eaa03d53c35849f'
REPORT_SHA = 'c41c4b3e21cb13ffe3b44232844de7211092a32a7da5ee73a8c3727024bdb3c1'
ABI, CODE, CLEANUP = 75, 0x804A2A70, 0x804A2C80
CLASS_TABLE, NATIVE_CLASS_COUNT = 0x8010699C, 68
NATIVE_CLEANUP, NATIVE_CLEANUP_COUNT = 0x80104FE0, 19


def donor_contract():
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    verify_sources(rel, symbols)
    data = rel_sections(rel)[5][0]
    classes = rel[data+0x6B38:data+0x6B8B]
    functions = data_pointers(rel, 0x6B8C, 48, expected_section=1)
    areas = rel[data+0x6BC8:data+0x6BF8]
    if (len(classes) != 83 or classes[73] != 10 or classes[41] != 10
            or functions[0x6B8C+10*4] != functions[0x6B8C+5*4]
            or areas[10*4:11*4] != bytes(4)):
        raise ValueError('Changed donor tent/igloo 3x3 lot-restoration contract')
    return dict(class_sha256=sha256(classes), area_sha256=sha256(areas),
        donor_tent_class=10, native_tent_class=8, donor_tent_item=0x5849,
        donor_igloo_same_class=True, reserved_lot_restored_on_remove=True,
        structure_area_origin_only=True)


def patch_native(code, original, symbols):
    hooks = []
    def patch(address, before, after, purpose):
        replace_checked(code, address-CODE_RAM, before, after)
        hooks.append(dict(address=address, before=before.hex(), after=after.hex(), purpose=purpose))
    # Both native consumers of the biased building-class table; preserve all
    # original inputs, rather than shifting the base of a partially valid table.
    found = {CODE_RAM+at for at in range(0, 0x800FCD70-CODE_RAM, 4)
             if struct.unpack_from('>I', original, at)[0] in (0x9063119C, 0x9084119C)}
    if found != {0x8008D4A8, 0x8008D5BC}:
        raise ValueError('Changed native building-class consumer inventory')
    for address, before, name in (
        (0x8008D4A8, '9063119c8faa0064', 'af_v3_tent_set_class'),
        (0x8008D5BC, '9084119c3c0b8010', 'af_v3_tent_area_class')):
        patch(address, bytes.fromhex(before), struct.pack('>2I', jump(symbols[name]), 0), name)
    # Native finish removes temporary event structures before ordinary save.
    # Keep all nineteen originals and append the tent; do not reuse the padding
    # that precedes the live count word in the original resident data.
    patch(0x8007FBCC, bytes.fromhex('3c198010'), struct.pack('>I', 0x3C190000 | ((CLEANUP+0x8000)>>16)),
          'expanded native event-structure cleanup table high')
    patch(0x8007FBD0, bytes.fromhex('27394fe0'), struct.pack('>I', 0x27390000 | (CLEANUP&65535)),
          'expanded native event-structure cleanup table low')
    patch(0x80105008, struct.pack('>I',19), struct.pack('>I',20), 'include tent in ordinary event cleanup')
    return hooks


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored build directory')
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw)) != (BASE_SHA,REPORT_SHA):
        raise ValueError('Changed complete camper owner base')
    prior,files = json.loads(raw),by_vrom(base)
    contract = donor_contract()
    blob = bytearray(files[BLOB].extract(base))
    package = blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    if (sha256(package) != prior['camper']['package_sha256']
            or struct.unpack_from('>4I',blob,0xF0) !=
                (BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)):
        raise ValueError('Changed checked package')
    original = by_vrom(native)[CODE_VROM].extract(native)
    code = bytearray(files[CODE_VROM].extract(base))
    start = CLASS_TABLE-CODE_RAM
    classes = original[start:start+NATIVE_CLASS_COUNT]
    if (classes[0x29] != 8 or code[start:start+NATIVE_CLASS_COUNT] != classes
            or code[0x801069E0-CODE_RAM:0x80106A3C-CODE_RAM] !=
                original[0x801069E0-CODE_RAM:0x80106A3C-CODE_RAM]
            or struct.unpack_from('>I',code,0x801069E0+8*4-CODE_RAM)[0] != 0x8008D12C
            or code[0x80106A14+8*4-CODE_RAM:0x80106A14+9*4-CODE_RAM] != bytes(4)):
        raise ValueError('Changed native 3x3 placement, removal, or area binding')
    start = NATIVE_CLEANUP-CODE_RAM
    cleanup = original[start:start+NATIVE_CLEANUP_COUNT*2]
    if (code[start:start+len(cleanup)] != cleanup
            or struct.unpack('>19H',cleanup) != tuple(range(0x5826,0x5839))):
        raise ValueError('Changed original temporary-structure cleanup list')
    cleanup += struct.pack('>H',0x5849)
    output.mkdir(parents=True)
    helpers,compiled = compile_part('campsite_placement',output/'placement',
        primary_source='overlays/v3/campsite_placement.S')
    if len(helpers)>0x90 or CODE < prior['camper']['reader']['symbols']['af_v3_camper_npc_info']+prior['camper']['reader']['bytes']:
        raise ValueError('Tent classifier overlaps the complete camper reader')
    for address,data,end in ((CODE,helpers,0x804A2B00),(CLEANUP,cleanup,0x804A2CF0)):
        at = PACKAGE+address-PACKAGE_RAM
        if address+len(data)>end or any(blob[at:at+len(data)]):
            raise ValueError('Occupied tent placement reservation')
        blob[at:at+len(data)] = data
    hooks = patch_native(code,original,compiled['symbols'])
    startup,startup_report = compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB+PACKAGE}','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module = bytearray(files[MODULE].extract(base)); old = prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']]) != old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed or insufficient startup reservation')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    package = blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',blob,0xF0,BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    result = bytearray(base)
    for vrom,data in ((BLOB,blob),(MODULE,module),(CODE_VROM,code)):
        entry = files[vrom]
        if entry.pend or len(data)!=entry.size: raise ValueError('Tent placement changes an allocation')
        result[entry.pstart:entry.pstart+len(data)] = data
    fix_checksum(result); result = bytes(result)
    if len(by_vrom(result))!=3389 or result[DMA_START:DMA_END]!=base[DMA_START:DMA_END]:
        raise ValueError('Tent placement changes the DMA directory')
    patch = make_ups(native,result)
    if apply_ups(native,patch)!=result: raise ValueError('Tent placement reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-campsite-placement',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(result),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        startup=startup_report,native_test='pending current native tent placement/removal')
    for section in ('construction','garden','western','western_large','accessory_runtime','camping',
                    'tent_model','fire','import_storage','campsite','campsite_exterior','campsite_calendar','camper'):
        report[section]['package_sha256'] = sha256(package)
    at = PACKAGE+0x804A2C00-PACKAGE_RAM
    report['campsite_calendar']['packet_sha256'] = sha256(blob[at:at+0x100])
    report['campsite_placement'] = dict(code=compiled,hooks=hooks,donor=contract,
        cleanup=CLEANUP,cleanup_bytes=len(cleanup),cleanup_sha256=sha256(cleanup),
        native_cleanup_rows_retained=19,cleanup_rows=20,native_classes_retained=68,
        package_bytes=PACKAGE_SIZE,package_sha256=sha256(package),additional_resident_bytes=0,
        additional_heap_bytes=0,saved_format_changed=False,saved_profile_changed=False,
        manager_installed=False,acquisition_installed=False,web_patcher_enabled=False,
        not_a_playtest_handoff=True,
        pending=['event-manager and complete masked camper/conversation integration',
                 'native full placement/removal, ordinary tent entry, exit, and persistence'])
    sources = ('tools/v3_campsite_placement.py','tools/v3_asset_loader.py',
        'overlays/v3/campsite_placement.S','overlays/v3/campsite_placement.ld')
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in sources})
    write_new(output/'animal-forest-v3-asset-loader.z64',result)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    report = build(parser.parse_args().output)
    print(json.dumps({key:report[key] for key in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
