"""Install the shared password engine and checked lazy loader; no UI activation."""
import copy
import json
import struct
import zlib

from aflib import by_vrom, sha256
from v3_asset_loader import ROOT, BLOB, compile_part
from v3_equipment_runtime import RAM as EQUIPMENT_RAM, GUARD
from v3_furniture_pipeline import Source
import v3_password as codec
import v3_password_policy as policy

RAM, SIZE, BOOT, CACHE = 0x804C0000, 0x8000, 0x804B4D00, 0x804B4EF0
TABLES, POLICY, MAP = 0x2800, 0x3000, 0x5000
MATRIX_SHA = '22a5c233464f1779aa1d80944166b4ba4657b25392ff563cba7e9b02a04a2cc9'
SOURCES = ('tools/v3_password_runtime.py', 'tools/v3_asset_loader.py',
    'tools/v3_furniture_install.py', 'overlays/v3/password_runtime.c', 'overlays/v3/password_runtime.h',
    'overlays/v3/password_runtime.ld', 'overlays/v3/password_bootstrap.c',
    'overlays/v3/password_bootstrap.ld', 'translations/provenance.json') + codec.SOURCES + policy.SOURCES


def prepared(source, directory, lock):
    """Rebind existing verified results, without recompiling the donor oracle."""
    raw = (directory/'password-policy.json').read_bytes()
    receipt = json.loads(raw)
    generated, contract = policy.evaluator(source)
    matrix = (directory/'donor-permissions.bin').read_bytes()
    if (receipt['format'] != 'AFV3-PASSWORD-POLICY-1'
            or receipt['generated_source_sha256'] != sha256(generated.encode())
            or receipt['donor_matrix_sha256'] != sha256(matrix) or sha256(matrix) != MATRIX_SHA
            or any(receipt[k] != json.loads(json.dumps(v)) for k, v in contract.items())):
        raise ValueError('Changed prepared password source rules or permission matrix')
    permissions, ranges = policy.compact(matrix, contract)
    if (receipt['ranges'] != [list(r) for r in ranges]
            or receipt['sha256'] != sha256(permissions)
            or permissions != (directory/'password-policy.bin').read_bytes()):
        raise ValueError('Changed complete prepared permission packet')
    destinations, mapping = policy.destination_map(lock)
    if (mapping != receipt['destinations']
            or destinations != (directory/'password-destinations.bin').read_bytes()):
        raise ValueError('Prepared password destinations do not match the current build')
    tables, codec_contract = codec.discover(source)
    return tables, permissions, destinations, dict(codec=codec_contract,
        policy=contract, policy_preparation_sha256=sha256(raw),
        donor_matrix_sha256=sha256(matrix), destinations=mapping)


def install(image, prior, blob, original, output, directory, lock):
    old = prior['equipment_resources']
    if old.get('passwords'):
        raise ValueError('Password engine already installed')
    ep = bytearray(blob[old['blob_offset']:old['blob_offset']+old['bytes']])
    if (old['ram'] != EQUIPMENT_RAM or old['bytes'] != 0x12000
            or old['vrom'] != BLOB+old['blob_offset'] or sha256(ep) != old['sha256']
            or zlib.crc32(ep) != old['crc32'] or ep[-16:] != struct.pack('>4I', *([GUARD]*4))
            or not EQUIPMENT_RAM <= BOOT < CACHE < EQUIPMENT_RAM+len(ep)-16
            or any(ep[BOOT-EQUIPMENT_RAM:CACHE+4-EQUIPMENT_RAM])):
        raise ValueError('Changed equipment module or occupied password-loader reservation')
    # Scenery, rigs, scroll, and surfaces own the intervening address ranges.
    # Never enlarge the equipment packet across those separately loaded owners.
    packets = (old['scenery'], old['room_rigs']['packet'],
        old['room_rigs']['scrolling']['packet'], prior['room_surfaces']['items'])
    for r in packets:
        if not EQUIPMENT_RAM+len(ep) <= r['ram'] < r['ram']+r['bytes'] <= RAM:
            raise ValueError('Password reservation overlaps another live V3 packet')
    if RAM+SIZE > prior['furniture']['bank_pool']['start']:
        raise ValueError('Password module overlaps furniture banks')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    tables, permissions, destinations, source_report = prepared(source, directory, lock)
    defines = (f'AF_PW_TABLE_BYTES={len(tables)}', f'AF_PW_POLICY_BYTES={len(permissions)}',
        f'AF_PW_MAP_BYTES={len(destinations)}')
    code, compiled = compile_part('password_runtime', output/'password_runtime',
        extra_sources=('overlays/v3/password.c', 'overlays/v3/password_policy.c'), defines=defines)
    packet = bytearray(SIZE)
    parts = ((0, TABLES, code), (TABLES, POLICY, tables),
        (POLICY, MAP, permissions), (MAP, SIZE-16, destinations))
    for start, end, data in parts:
        if not data or start+len(data) > end:
            raise ValueError('Password code or complete table exceeds its reservation')
        packet[start:start+len(data)] = data
    packet[-16:] = struct.pack('>4I', *([0xAF5057DE]*4))
    blob.extend(bytes(-len(blob) % 16)); at = len(blob); blob.extend(packet)
    crc = zlib.crc32(packet)
    if not crc:
        raise ValueError('Zero password CRC collides with the cold cache state')
    loader, bootstrap = compile_part('password_bootstrap', output/'password_bootstrap',
        defines=(f'AF_PW_PACKET_VROM=0x{BLOB+at:X}u', f'AF_PW_PACKET_CRC=0x{crc:X}u'))
    if not loader or len(loader) > CACHE-BOOT:
        raise ValueError('Password bootstrap exceeds checked equipment padding')
    provenance = {r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    for key, text in (('title','V3 item codes'), ('code','Invalid password module')):
        entry = provenance['v3/password/diagnostic/'+key]['locales']['en']
        if (entry['credit'] != 'assistant' or entry['text'] != text
                or entry['encoded_sha256'] != sha256(text.encode()) or text.encode()+b'\0' not in loader):
            raise ValueError('Missing password diagnostic authorship or compiled text')
    ep[BOOT-EQUIPMENT_RAM:BOOT-EQUIPMENT_RAM+len(loader)] = loader
    blob[old['blob_offset']:old['blob_offset']+len(ep)] = ep
    # fqrand lives in the startup file, not the separately loaded game-code file.
    native = by_vrom(image)[0x1060].extract(image)
    rng = native[0x6D10:0x6DA0]
    if rng != by_vrom(original)[0x1060].extract(original)[0x6D10:0x6DA0]:
        raise ValueError('Changed complete native random generator')
    result = copy.deepcopy(old)
    result.update(sha256=sha256(ep), crc32=zlib.crc32(ep), additional_resident_bytes=SIZE)
    result['passwords'] = dict(format='AFV3-PASSWORD-RUNTIME-1', ram=RAM, bytes=SIZE,
        blob_offset=at, vrom=BLOB+at, crc32=crc, sha256=sha256(packet),
        code=compiled, bootstrap=dict(ram=BOOT, cache=CACHE, code=bootstrap),
        parts=[dict(offset=a, bytes=len(d), sha256=sha256(d)) for a, _, d in parts],
        source=source_report, rng=dict(start=0x8002C970, end=0x8002CA00, sha256=sha256(rng)),
        runtime_installed=True, live_selection_reader_installed=True, native_rng_installed=True,
        keyboard_installed=False, name_conversion_installed=False, acquisition_installed=False,
        ordinary_gameplay_tested=False, native_execution_tested=False,
        additional_resident_bytes=SIZE, saved_format_changed=False, saved_profile_changed=False,
        sources={p: sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return result
