#!/usr/bin/env python3
"""Build and verify immutable, local-only English mail cartridge catalogs."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

from aflib import sha256, verified_rom
from audit_mail_templates import CLASSIC, COMPOSITE, template_fields
from mail_format import Templates
from mail_reference import load_reference

BANKS = CLASSIC+COMPOSITE
COUNTS = (982,)*3+(384,)*5
MAGIC, VERSION, SEMANTICS = 0x41464D4C, 1, 1
VROM, CONFIG_OFFSET, MAX_BYTES = 0x03000000, 0x44, 0x100000
HEADER_BYTES, ROW_BYTES, SOURCE_BYTES = 128, 16, 3104
REGISTRY = Path(__file__).resolve().parents[1]/'translations/mail_catalogs.json'


def align16(value):
    return (value+15) & ~15


def valid_part(data):
    if not isinstance(data, bytes) or len(data) > 1024 or 0x80 in data:
        raise ValueError('Unsupported catalog part length or extended glyph')
    return sum(1 << index for index in template_fields(data))


def resource(banks, catalog):
    if type(catalog) is not int or not 2 <= catalog < 0xFFFF:
        raise ValueError('Catalog ID is invalid or reserved for tests')
    if set(banks) != set(BANKS) or any(len(banks[name]) != count for name, count in zip(BANKS, COUNTS)):
        raise ValueError('Catalog requires all eight complete reference bank indices')
    data_start = HEADER_BYTES+16*len(BANKS)+ROW_BYTES*sum(COUNTS)
    directory, rows, payload = bytearray(), bytearray(), bytearray()
    table_offset = HEADER_BYTES+16*len(BANKS)
    for bank_index, (name, count) in enumerate(zip(BANKS, COUNTS)):
        directory.extend(struct.pack('>4I', bank_index, count, table_offset, 0))
        table_offset += count*ROW_BYTES
        for part in banks[name]:
            if part is None:
                rows.extend(struct.pack('>IHHII', 0, 0, 1, 0, 0))
                continue
            mask = valid_part(part)
            rows.extend(struct.pack('>IHHII', data_start+len(payload), len(part), 0,
                                    mask, zlib.crc32(part)))
            payload.extend(part.ljust(align16(len(part)), b'\0'))
    body = directory+rows+payload
    total = HEADER_BYTES+len(body)
    if total > MAX_BYTES:
        raise ValueError('Mail catalog exceeds cartridge resource reservation')
    header = struct.pack('>8I', MAGIC, VERSION, catalog, SEMANTICS, total, len(BANKS), HEADER_BYTES, ROW_BYTES)
    return header+hashlib.sha256(body).digest()+bytes(64)+body


def parse(data, *, expected_catalog=None):
    if len(data) < HEADER_BYTES or len(data) > MAX_BYTES or len(data) % 16:
        raise ValueError('Invalid mail catalog size')
    magic, version, catalog, semantics, total, count, directory, stride = struct.unpack_from('>8I', data)
    if (magic, version, semantics, total, count, directory, stride) != (
            MAGIC, VERSION, SEMANTICS, len(data), len(BANKS), HEADER_BYTES, ROW_BYTES):
        raise ValueError('Invalid mail catalog header')
    if not 2 <= catalog < 0xFFFF or expected_catalog is not None and catalog != expected_catalog:
        raise ValueError('Unknown mail catalog identity')
    if data[32:64] != hashlib.sha256(data[128:]).digest() or any(data[64:128]):
        raise ValueError('Invalid mail catalog hash or header padding')
    data_start = HEADER_BYTES+16*len(BANKS)+ROW_BYTES*sum(COUNTS)
    if len(data) < data_start:
        raise ValueError('Truncated mail catalog tables')
    banks, table_offset, payload_offset = {}, HEADER_BYTES+16*len(BANKS), data_start
    for index, (name, entries) in enumerate(zip(BANKS, COUNTS)):
        if struct.unpack_from('>4I', data, HEADER_BYTES+index*16) != (index, entries, table_offset, 0):
            raise ValueError('Invalid mail catalog directory')
        parts = []
        for row in range(entries):
            offset, size, flags, mask, crc = struct.unpack_from('>IHHII', data, table_offset+row*ROW_BYTES)
            if flags == 1 and (offset, size, mask, crc) == (0, 0, 0, 0):
                parts.append(None)
                continue
            end = offset+align16(size)
            if flags or offset != payload_offset or end > len(data) or size > 1024:
                raise ValueError('Invalid mail catalog row or payload range')
            part = data[offset:offset+size]
            if valid_part(part) != mask or zlib.crc32(part) != crc or any(data[offset+size:end]):
                raise ValueError('Invalid mail catalog part mask, CRC, or padding')
            parts.append(part)
            payload_offset = end
        banks[name] = parts
        table_offset += entries*ROW_BYTES
    if payload_offset != len(data):
        raise ValueError('Trailing unreferenced mail catalog data')
    return catalog, banks


def templates(data, record):
    catalog, banks = parse(data, expected_catalog=record.catalog)
    if type(record.kind) is not int or record.kind not in (0, 1):
        raise ValueError('Invalid mail catalog snapshot kind')
    names = COMPOSITE if record.kind else CLASSIC
    ids = record.templates if record.kind else record.templates*3
    if len(ids) != len(names):
        raise ValueError('Invalid mail catalog template selection')
    parts = []
    for name, index in zip(names, ids):
        if type(index) is not int or not 0 <= index < len(banks[name]) or banks[name][index] is None:
            raise ValueError('Unavailable mail catalog template')
        parts.append(banks[name][index])
    if sum(map(len, parts)) > SOURCE_BYTES:
        raise ValueError('Mail catalog source workspace overflow')
    return Templates(catalog, record.kind, ids, tuple(parts))


def identity(data):
    catalog, banks = parse(data)
    return {'catalog': catalog, 'format': VERSION, 'semantics': SEMANTICS, 'bytes': len(data),
            'sha256': sha256(data), 'payload_sha256': data[32:64].hex(),
            'counts': list(COUNTS), 'unavailable': {name: [i for i, part in enumerate(banks[name]) if part is None]
                                                   for name in BANKS}}


def verify_registered(data, registry=None):
    registry = json.loads(REGISTRY.read_text()) if registry is None else registry
    actual = identity(data)
    if registry.get('version') != 1 or not isinstance(registry.get('catalogs'), list):
        raise ValueError('Invalid immutable catalog registry')
    if any(not isinstance(item, dict) or type(item.get('catalog')) is not int
           or not 2 <= item['catalog'] < 0xFFFF for item in registry['catalogs']):
        raise ValueError('Invalid immutable catalog registry entry')
    ids = [item.get('catalog') for item in registry['catalogs']]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate immutable catalog identity')
    matches = [item for item in registry['catalogs'] if item.get('catalog') == actual['catalog']]
    if len(matches) != 1 or any(matches[0].get(key) != value for key, value in actual.items()):
        raise ValueError('Unregistered or changed immutable mail catalog')
    return actual


def install(rom, additions, module_report, directory):
    from runtime_module import MODULE_RAM, MODULE_VROM
    report = json.loads((directory/'catalog.json').read_text())
    data = (directory/'catalog.bin').read_bytes()
    actual = verify_registered(data)
    if (report.get('source_sha256') != sha256(rom) or report.get('registered') is not True
            or any(report.get(key) != value for key, value in actual.items())):
        raise ValueError('Stale, proposed, or mismatched mail catalog resource')
    if (not module_report or MODULE_VROM not in additions
            or not {'af_mail_restore', 'af_mail_catalog_header_valid'} <= module_report['symbols'].keys()):
        raise ValueError('Mail catalogs require a capable resident module')
    module = bytearray(additions[MODULE_VROM])
    original = bytearray(module)
    for offset, vrom in ((56, 0x02A00000), (60, 0x02C00000), (64, 0x02E00000)):
        value = struct.unpack_from('>I', original, offset)[0]
        if value and (value != vrom or value not in additions):
            raise ValueError('Unverified preceding module resource configuration')
        original[offset:offset+4] = bytes(4)
    if sha256(original) != module_report['module_sha256']:
        raise ValueError('Mail catalogs require unchanged verified module bytes')
    if module[CONFIG_OFFSET:CONFIG_OFFSET+4] != bytes(4) or VROM in additions:
        raise ValueError('Duplicate mail catalog configuration')
    struct.pack_into('>I', module, CONFIG_OFFSET, VROM)
    additions[MODULE_VROM], additions[VROM] = bytes(module), data
    return {**actual, 'source_sha256': sha256(rom), 'vrom': f'{VROM:08X}',
            'module_configuration_ram': f'{MODULE_RAM+CONFIG_OFFSET:08X}',
            'configured_module_sha256': sha256(module),
            'status': 'Experimental immutable reference catalog; generation/viewer/save hooks remain separate'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--catalog', type=int, default=2)
    parser.add_argument('--gc-data', type=Path, default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp', type=Path, default=Path('local/ac-decomp'))
    parser.add_argument('--rel', type=Path, default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--output', type=Path, default=Path('build/mail-catalog'))
    parser.add_argument('--propose-registration', action='store_true', help='Write local proposal only; never register or install it')
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    banks, reference = load_reference(args.gc_data, args.decomp, args.rel)
    data = resource(banks, args.catalog)
    details = identity(data) if args.propose_registration else verify_registered(data)
    report = {**details, 'source_sha256': sha256(rom), 'vrom': f'{VROM:08X}',
              'reference': reference, 'registered': not args.propose_registration,
              'status': 'Immutable reference parts only; native semantic matches and gameplay hooks remain required'}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'catalog.bin').write_bytes(data)
    (args.output/'catalog.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(details, indent=2))


if __name__ == '__main__':
    main()
