#!/usr/bin/env python3
"""Restore complete English letters using actual cartridge DMA on the N64 CPU."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from mail_catalog import VROM, CONFIG_OFFSET, verify_registered, templates
from mail_format import format_letter
from mail_record import Record, pack
from mail_runtime_test_scenario import reference_fixtures, output_bytes
from runtime_module import verify_test_module, MODULE_RAM, MODULE_VROM
from runtime_layout import TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

WIRE = TEST_RETURN+0x10
WORK = TEST_RETURN+0x120
WORK_BYTES = 3552
OUTPUT = TEST_RETURN+0xF20
STACK_LOW = TEST_STACK-0xA00
EDGE = b'EDGE'*4


def scenario(rom, module, cases):
    verify_test_module(rom, module)
    files = by_vrom(rom)
    catalog = files[VROM].extract(rom)
    verify_registered(catalog)
    if files[MODULE_VROM].extract(rom)[CONFIG_OFFSET:CONFIG_OFFSET+4] != VROM.to_bytes(4, 'big'):
        raise ValueError('Native catalog test requires the configured cartridge resource')
    if WORK+WORK_BYTES+16 > OUTPUT-16 or OUTPUT+1040+16 >= STACK_LOW:
        raise ValueError('Catalog fixture buffers overlap')
    actions = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]
    def write(address, value):
        actions.append({'write': [f'{address:08X}', value.hex()]})
    def read(address, value):
        actions.append({'read': [f'{address:08X}', len(value)], 'expect': value.hex()})
    def call(address, args, result):
        actions.append({'call': {'address': address, 'arguments': args, 'expect_return': result}})
    write(STACK_LOW, EDGE)
    write(TEST_STACK+0x30, EDGE)
    def restore(record, success=True, skew=0):
        wire = pack(record)
        write(WIRE-16+skew, EDGE+wire+EDGE)
        write(WORK-16, EDGE+b'!'*WORK_BYTES+EDGE)
        write(OUTPUT-16, EDGE+b'!'*1040+EDGE)
        call(module['symbols']['af_mail_restore'], [OUTPUT, WIRE+skew, 122, WORK], int(success))
        value = output_bytes(record, templates(catalog, record)) if success else b'!'*1040
        read(OUTPUT-16, EDGE+value+EDGE)
        read(WIRE-16+skew, EDGE+wire+EDGE)
        read(WORK-16, EDGE)
        read(WORK+WORK_BYTES, EDGE)
        read(STACK_LOW, EDGE)
    for index, (_, record, parts, _) in enumerate(cases):
        record = replace(record, catalog=2)
        original = format_letter(record, replace(parts, catalog=2))
        if format_letter(record, templates(catalog, record)) != original:
            raise ValueError('Installed catalog output differs from verified reference')
        restore(record, skew=index % 8)
    for record in (Record(2, 0, (43,), ()), Record(2, 0, (982,), ()),
                   Record(4, 0, (0,), ()), Record(2, 1, (0, 0, 0, 0, 77), ())):
        restore(record, success=False)
    record = replace(cases[0][1], catalog=2)
    write(MODULE_RAM+CONFIG_OFFSET, bytes(4))
    restore(record, success=False)
    write(MODULE_RAM+CONFIG_OFFSET, VROM.to_bytes(4, 'big'))
    # Header corruption is tested through the real compiled validator without
    # changing the cartridge or invoking a decoder on an unknown catalog.
    write(WORK, catalog[:128])
    call(module['symbols']['af_mail_catalog_header_valid'], [WORK, 2], 1)
    for word in range(32):
        bad = bytearray(catalog[:128])
        bad[word*4+3] ^= 1
        write(WORK, bytes(bad))
        call(module['symbols']['af_mail_catalog_header_valid'], [WORK, 2], 0)
    read(STACK_LOW, EDGE)
    read(TEST_STACK+0x30, EDGE)
    read(GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
    actions += [{'load_state': True}, {'resume': True}, {'wait': 2}]
    read(WORK, bytes(4))
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--module', type=Path, default=Path('build/runtime-module/module.json'))
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--gc-data', type=Path, default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp', type=Path, default=Path('local/ac-decomp'))
    parser.add_argument('--rel', type=Path, default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = reference_fixtures(args.native_rom.read_bytes(), args.gc_data, args.decomp, args.rel)
    rom = args.rom.read_bytes()
    actions = scenario(rom, json.loads(args.module.read_text()), cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'rom_sha256': sha256(rom), 'actions': len(actions), 'reference_cases': len(cases)}))


if __name__ == '__main__':
    main()
