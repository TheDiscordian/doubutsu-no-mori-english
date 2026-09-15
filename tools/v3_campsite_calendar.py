"""Install the native summer calendar/index; preserve both V2 web patchers."""
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
from v3_campsite_event import donor_schedule, native_contracts

BASE = ROOT / 'build/v3-campsite-exterior-runtime-01'
BASE_SHA = '61d9bec4ac698420f20df7a062b13d8bf3619989fc78b357245d6ade4589abdf'
REPORT_SHA = '24fa37a4cd3bb5b5ace06cc10bfedf001b29a0ac2c0e905618f1a60c741fbc8b'
ABI, OLD_SIZE, PACKAGE_SIZE = 73, 0x2F010, 0x30000
EVENT_CODE, CALENDAR_CODE = 0x804A2100, 0x804A2740
INDEX, PACKET = 0x804A2B00, 0x804A2C00

# Reviewed HI/LO consumers of the private index, not similarly encoded
# pointers to the END of event_today. The offset-16 entries belong to the
# original masked-NPC event and must move along with every generic reader.
INDEX_READERS = (
    (0x8007E18C, 0x8007E194, 0), (0x8007E1E0, 0x8007E1E8, 0),
    (0x8007E280, 0x8007E28C, 0), (0x8007E2C8, 0x8007E2D8, 0),
    (0x8007E3FC, 0x8007E400, 0), (0x8007E530, 0x8007E53C, 0),
    (0x8007EF68, 0x8007EF74, 0), (0x8007F28C, 0x8007F294, 0),
    (0x8007F8F4, 0x8007F900, 16), (0x8007F934, 0x8007F93C, 16),
    (0x8007FCB8, 0x8007FCC0, 0), (0x8007FD40, 0x8007FD48, 0),
    (0x8007FDB4, 0x8007FDBC, 0), (0x8007FE0C, 0x8007FE14, 0),
    (0x8007FE80, 0x8007FE88, 0), (0x8007FEBC, 0x8007FEC4, 0),
    (0x8007FF14, 0x8007FF1C, 0), (0x8008009C, 0x800800A4, 0),
)
RETAINED_INDEX_FORMS = {
    0x8007E614, 0x8007E65C, 0x8007E660, 0x8007E664, 0x8007E668,
    0x8007E698, 0x8007F118, 0x80081864,
}


def patch_index(code, native, entries):
    changes = []
    def patch(address, before, after, purpose):
        replace_checked(code, address - CODE_RAM, before, after)
        changes.append(dict(address=address, before=before.hex(), after=after.hex(), purpose=purpose))
    found = set()
    for address in range(0x8007D140, 0x80081E48, 4):
        word = struct.unpack_from('>I', native, address - CODE_RAM)[0]
        if word >> 26 in (9, 0x20, 0x24, 0x28) and 0xA098 <= (word & 65535) <= 0xA0DE:
            found.add(address)
    if found != {lo for _, lo, _ in INDEX_READERS} | RETAINED_INDEX_FORMS:
        raise ValueError('Native event-index address forms need review: ' + repr(sorted(found)))
    for hi, lo, offset in INDEX_READERS:
        high, low = (struct.unpack_from('>I', native, a - CODE_RAM)[0] for a in (hi, lo))
        register = (high >> 16) & 31
        if (high >> 26 != 15 or high & 65535 != 0x8014
                or low & 65535 != 0xA098 + offset or (low >> 21) & 31 != register):
            raise ValueError('Changed reviewed native index HI/LO binding')
        for address, before, after in (
            (hi, high, (high & 0xFFFF0000) | ((INDEX + offset + 0x8000) >> 16)),
            (lo, low, (low & 0xFFFF0000) | ((INDEX + offset) & 65535))):
            patch(address, struct.pack('>I', before), struct.pack('>I', after), 'expanded 71-type event index')
    for address in (0x8007F640, 0x8007F660):
        patch(address, bytes.fromhex('24110046'), bytes.fromhex('24110047'), 'include camper in native cleanup')
    for address, original, name in (
        (0x8007F7B4, 0x8007E60C, 'af_v3_campsite_today_init'),
        (0x8007F630, 0x8007F2D8, 'af_v3_campsite_before_cleanup')):
        before = struct.pack('>I', jump(original, link=True))
        patch(address, before, struct.pack('>I', jump(entries[name], link=True)), name)
    return changes


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh ignored build directory')
    native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    contracts = native_contracts(native)
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE / 'build.json').read_bytes()
    if sha256(base) != BASE_SHA or sha256(raw) != REPORT_SHA:
        raise ValueError('Changed complete campsite-exterior base')
    prior, files = json.loads(raw), by_vrom(base)
    row = donor_schedule((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    blob = bytearray(files[BLOB].extract(base))
    old_package = blob[PACKAGE:PACKAGE + OLD_SIZE]
    if (sha256(old_package) != prior['campsite']['package_sha256']
            or struct.unpack_from('>4I', blob, 0xF0) !=
                (BLOB + PACKAGE, OLD_SIZE, zlib.crc32(old_package), PACKAGE_RAM)
            or any(blob[PACKAGE + OLD_SIZE:PACKAGE + PACKAGE_SIZE])
            or PACKAGE + PACKAGE_SIZE > len(blob) or PACKAGE_RAM + PACKAGE_SIZE > 0x80500000):
        raise ValueError('Changed package or occupied expansion reservation')
    output.mkdir(parents=True)
    event, event_report = compile_part('campsite_event', output / 'event')
    calendar, compiled = compile_part('campsite_calendar', output / 'calendar')
    if EVENT_CODE + len(event) > CALENDAR_CODE or CALENDAR_CODE + len(calendar) > INDEX:
        raise ValueError('Camper event code does not fit its checked reservation')
    packet = bytearray(0x100)
    struct.pack_into('>4I', packet, 0, 0x41464345, 1, 70, INDEX)
    packet[0x20:0x2C] = row
    struct.pack_into('>6I', packet, 0x40, compiled['symbols']['af_v3_campsite_decode_date'], 0x8007DD84,
        compiled['symbols']['af_v3_campsite_add_today'], compiled['symbols']['af_v3_campsite_one_time'], PACKET+0x20, 70)
    packet[-16:] = bytes.fromhex('AFC7CA1E') * 4
    for address, data in ((EVENT_CODE,event), (CALENDAR_CODE,calendar),
                           (INDEX,b'\xFF'*128), (PACKET,packet)):
        at = PACKAGE + address - PACKAGE_RAM
        if any(blob[at:at+len(data)]) or at < PACKAGE+OLD_SIZE or at+len(data) > PACKAGE+PACKAGE_SIZE-16:
            raise ValueError('Camper calendar overlaps existing checked data')
        blob[at:at+len(data)] = data
    blob[PACKAGE+PACKAGE_SIZE-16:PACKAGE+PACKAGE_SIZE] = old_package[-16:]
    struct.pack_into('>I', blob, PACKAGE+8, PACKAGE_SIZE)
    code = bytearray(files[CODE_VROM].extract(base))
    hooks = patch_index(code, by_vrom(native)[CODE_VROM].extract(native), compiled['symbols'])
    startup, startup_report = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB+PACKAGE}', 'AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1', 'AF_V3_CAMPER_CALENDAR=1'))
    module = bytearray(files[MODULE].extract(base)); old = prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']]) != old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup) > CONFIG-STARTUP):
        raise ValueError('Changed or insufficient startup reservation')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG-STARTUP-len(startup))
    package = blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    struct.pack_into('>4I',blob,0xF0,BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    result = bytearray(base)
    for vrom, data in ((BLOB,blob), (MODULE,module), (CODE_VROM,code)):
        entry = files[vrom]
        if entry.pend or len(data) != entry.size: raise ValueError('Calendar changes a physical allocation')
        result[entry.pstart:entry.pstart+len(data)] = data
    fix_checksum(result); result = bytes(result)
    if len(by_vrom(result)) != 3389 or result[DMA_START:DMA_END] != base[DMA_START:DMA_END]:
        raise ValueError('Calendar changes the DMA directory')
    patch = make_ups(native,result)
    if apply_ups(native,patch) != result: raise ValueError('Calendar reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-campsite-calendar', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        startup=startup_report, native_test='pending current native calendar integration')
    for section in ('construction','garden','western','western_large','accessory_runtime','camping',
                    'tent_model','fire','import_storage','campsite','campsite_exterior'):
        report[section]['package_sha256'] = sha256(package)
        if 'package_bytes' in report[section]: report[section]['package_bytes'] = PACKAGE_SIZE
    report['accessory_runtime'].update(active_package_bytes=PACKAGE_SIZE,
        active_package_vrom=f'{BLOB+PACKAGE:08X}')
    report['campsite_calendar'] = dict(event_code=event_report, code=compiled, hooks=hooks,
        native_contracts=contracts, index=INDEX, index_bytes=128, event_type=70,
        native_event_types_retained=70, original_today_capacity=16, today_capacity=16,
        packet=PACKET, packet_sha256=sha256(packet), package_bytes=PACKAGE_SIZE,
        package_sha256=sha256(package), additional_resident_bytes=PACKAGE_SIZE-OLD_SIZE,
        ordinary_heap_growth=0, saved_format_changed=False, saved_profile_changed=False,
        web_patcher_enabled=False, calendar_installed=True, manager_installed=False,
        acquisition_installed=False, not_a_playtest_handoff=True,
        pending=['event-manager callbacks and full visitor identity/default/greeting state',
                 'English conversation flow, selected camping rewards, and lighting',
                 'ordinary tent entry, exit, appearance, and persistence'])
    write_new(output/'animal-forest-v3-asset-loader.z64',result)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = build(args.output)
    print(json.dumps({key:report[key] for key in ('build','runtime_abi','output_sha256','campsite_calendar')},indent=2))
