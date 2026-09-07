#!/usr/bin/env python3
"""Execute resident mail codecs/assembly on the N64 CPU with isolated fixtures."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import sha256
from mail_record import Field, Record, pack
from mail_format import Templates, format_letter
from runtime_layout import TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from runtime_module import verify_test_module

RECORD = TEST_RETURN+0x120
WIRE = TEST_RETURN+0x320
TEMPLATES = TEST_RETURN+0x420
SOURCE = TEST_RETURN+0x520
OUTPUT = TEST_RETURN+0xB20
STACK_LOW = TEST_STACK-0x1000
EDGE = b'EDGE'*4


def record_bytes(record):
    """The o32 structure has explicit two-byte trailing alignment padding."""
    pack(record)
    ids = record.templates+(0,)*(5-len(record.templates))
    fields = dict(record.fields)
    data = struct.pack('>HBBI5H', record.catalog, record.kind, record.initial_capital,
                       sum(1 << i for i in fields), *ids)
    for index in range(20):
        field = fields.get(index, Field(b''))
        data += bytes((len(field.text), field.article))+field.text.ljust(16, b'\0')
    return data+b'\0\0'


def template_bytes(templates):
    data, raw = struct.pack('>II', templates.catalog, templates.kind), b''
    for identity, part in zip(templates.ids, templates.parts):
        data += struct.pack('>IIHH', SOURCE+len(raw), len(part), identity, 0)
        raw += part
    data += bytes(12*(5-len(templates.parts)))
    if len(data) != 68 or len(raw) > OUTPUT-SOURCE-32:
        raise ValueError('Native mail templates exceed fixture memory')
    return data, raw


def output_bytes(record, templates):
    letter = format_letter(record, templates)
    h, b, f = letter.header, letter.body, letter.footer
    offsets = (0, len(h), len(h)+len(b)) if record.kind else (0, len(h)+len(f), len(h))
    text = h+b+f if record.kind else h+f+b
    return struct.pack('>7HBB', *offsets, len(h), len(b), len(f), letter.header_split,
                       letter.final_capital, 0)+text.ljust(1024, b'\0')


def fixtures():
    for index in range(20):
        opcode = 0x24+index if index < 10 else 0x36+index-10
        record = Record(1, 0, (7,), ((index, Field(b'full field value', index % 5)),), bool(index % 2))
        yield record, Templates(1, 0, (7,)*3, (b'To \xcd!', bytes((0x7F, opcode))+b'\xcd', b'End'))
    for width in range(17):
        record = Record(1, 1, (0, 1, 2, 3, 4), ((0, Field(b'x'*width, width % 5)),), bool(width % 2))
        yield record, Templates(1, 1, record.templates,
            (b'To \xcd', b'\x7f\x75\x7f', b'\x74\x7f\x24', b'!\xcd\xcd', b'\x7f\x24'))
    for capital in (False, True):
        record = Record(1, 1, (0, 32, 64, 96, 383),
                        tuple((i, Field(b'x'*16, 4)) for i in range(6)), capital)
        yield record, Templates(1, 1, record.templates,
            (b'\xcd', b'\x7f\x24\x7f\x25', b'\x7f\x26\x7f\x27', b'\x7f\x28\x7f\x29\xcd', b'End'))
    record = Record(1, 0, (7,), ((0, Field(b' ')),))
    for parts in ((b'\xcd', b'\x7f\x75\x7f\x24after\xcd', b'End'),
                  (b'So, \xcd...\xcd', b'', b''),
                  (b'H', b'x'*1022, b'F')):
        yield record, Templates(1, 0, (7,)*3, parts)


def reference_fixtures(native_rom, directory, decomp, rel):
    """Select deterministic reference boundaries and long-output witnesses."""
    from aflib import verified_rom
    from mail_reference import load_reference, assembly_cases
    banks, _ = load_reference(directory, decomp, rel)
    choices = {}
    def keep(key, score, case):
        if key not in choices or score > choices[key][0]:
            choices[key] = (score, case)
    for label, record, templates, limitation in assembly_cases(banks, verified_rom(native_rom)):
        if record is None:
            continue
        result = format_letter(record, templates)
        lengths = (len(result.header), len(result.body), len(result.footer))
        case = (label, record, templates, limitation)
        key = record.kind, record.initial_capital
        keep(('first', key), tuple(-i for i in record.templates), case)
        keep(('last', key), record.templates, case)
        for index, length in enumerate(lengths+(sum(lengths),)):
            keep(('length', key, index), length, case)
        if record.kind:
            keep(('reply', record.templates[0]//32, record.initial_capital), sum(lengths), case)
        elif record.templates == (1,):
            keep(('bounded_probe', key), 1, case)
    selected = {case[0]: case for _, case in choices.values()}
    if not 1 <= len(selected) <= 64:
        raise ValueError('Unexpected native reference probe count')
    return [selected[label] for label in sorted(selected)]


class Scenario:
    def __init__(self, rom, module):
        verify_test_module(rom, module)
        self.module = module
        self.actions = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]
        self.write(STACK_LOW, EDGE)
        self.write(TEST_STACK+0x30, EDGE)

    def write(self, address, data):
        self.actions.append({'write': [f'{address:08X}', data.hex()]})

    def read(self, address, data):
        self.actions.append({'read': [f'{address:08X}', len(data)], 'expect': data.hex()})

    def guarded(self, address, data):
        self.write(address-16, EDGE+data+EDGE)

    def check(self, address, data):
        self.read(address-16, EDGE+data+EDGE)

    def call(self, symbol, arguments, result):
        self.actions.append({'call': {'address': self.module['symbols'][symbol],
                                     'arguments': arguments, 'expect_return': result}})

    def finish(self):
        self.read(STACK_LOW, EDGE)
        self.read(TEST_STACK+0x30, EDGE)
        self.read(GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
        self.actions.extend([{'load_state': True}, {'resume': True}, {'wait': 2}])
        self.read(RECORD, bytes(4))
        return self.actions

    def codec(self):
        for number, (record, _) in enumerate(fixtures()):
            wire = WIRE+number % 8
            self.guarded(RECORD, record_bytes(record))
            self.guarded(wire, b'!'*122)
            self.call('af_mail_record_pack', [wire, 122, RECORD], 1)
            self.check(wire, pack(record))
            self.check(RECORD, record_bytes(record))
            self.guarded(RECORD, b'!'*380)
            self.call('af_mail_record_unpack', [RECORD, wire, 122, record.catalog], 1)
            self.check(RECORD, record_bytes(record))
            self.check(wire, pack(record))
        record = Record(1, 0, (7,), ((0, Field(b'word')),), True)
        wire = pack(record)
        self.guarded(RECORD, b'!'*380)
        for index in range(122):
            corrupt = bytearray(wire)
            corrupt[index] ^= 1
            self.guarded(WIRE, bytes(corrupt))
            self.call('af_mail_record_unpack', [RECORD, WIRE, 122, 1], 0)
            self.check(RECORD, b'!'*380)
        self.guarded(WIRE, wire)
        for size, catalog in ((121, 1), (123, 1), (122, 0), (122, 2), (122, 65536)):
            self.call('af_mail_record_unpack', [RECORD, WIRE, size, catalog], 0)
            self.check(RECORD, b'!'*380)
        self.guarded(RECORD, record_bytes(record))
        self.guarded(WIRE, b'!'*122)
        for capacity, pointer in ((121, RECORD), (122, 0)):
            self.call('af_mail_record_pack', [WIRE, capacity, pointer], 0)
            self.check(WIRE, b'!'*122)
        # Both codec directions can stage through overlapping structures.
        self.call('af_mail_record_pack', [RECORD, 122, RECORD], 1)
        self.read(RECORD, wire)
        self.call('af_mail_record_unpack', [RECORD, RECORD, 122, 1], 1)
        self.check(RECORD, record_bytes(record))
        return self.finish()

    def format_case(self, record, templates, *, reject=False, alias=False):
        self.guarded(WIRE, pack(record))
        self.guarded(RECORD, b'!'*380)
        self.call('af_mail_record_unpack', [RECORD, WIRE, 122, record.catalog], 1)
        self.check(RECORD, record_bytes(record))
        descriptors, raw = template_bytes(templates)
        self.guarded(TEMPLATES, descriptors)
        self.guarded(SOURCE, raw)
        content = record_bytes(record).ljust(1040, b'!') if alias else b'!'*1040
        self.guarded(OUTPUT, content)
        pointer = OUTPUT if alias else RECORD
        self.call('af_mail_format', [OUTPUT, pointer, TEMPLATES], int(not reject))
        self.check(OUTPUT, content if reject else output_bytes(record, templates))
        self.check(RECORD, record_bytes(record))
        self.check(TEMPLATES, descriptors)
        self.check(SOURCE, raw)
        self.read(STACK_LOW, EDGE)

    def formatter(self):
        for record, templates in fixtures():
            self.format_case(record, templates)
        record, templates = next(fixtures())
        self.format_case(record, templates, alias=True)
        self.format_case(record, replace(templates, parts=(b'H', b'x'*1023, b'F')), reject=True)
        self.format_case(record, replace(templates, catalog=2), reject=True)
        self.format_case(record, replace(templates, ids=(8, 8, 8)), reject=True)
        self.format_case(record, replace(templates, parts=(b'\xcd', b'\x80', b'')), reject=True)
        # Every command is executed on the resident C parser. Invalid commands
        # return failure without touching output; valid field commands use
        # explicitly captured empty fields rather than missing data.
        record = Record(1, 0, (7,), tuple((i, Field(b'')) for i in range(20)))
        self.guarded(RECORD, record_bytes(record))
        allowed = {*range(0x24, 0x2E), *range(0x36, 0x40), 0x74, 0x75}
        for opcode in range(256):
            templates = Templates(1, 0, (7,)*3, (b'\xcd', bytes((0x7F, opcode)), b'End'))
            descriptors, raw = template_bytes(templates)
            if opcode == 0:
                self.guarded(TEMPLATES, descriptors)
            self.guarded(SOURCE, raw)
            self.guarded(OUTPUT, b'!'*1040)
            self.call('af_mail_format', [OUTPUT, RECORD, TEMPLATES], int(opcode in allowed))
            self.check(OUTPUT, output_bytes(record, templates) if opcode in allowed else b'!'*1040)
        self.check(RECORD, record_bytes(record))
        self.check(TEMPLATES, descriptors)
        return self.finish()


def scenario(rom, module, suite, references=()):
    builder = Scenario(rom, module)
    if suite == 'codec':
        return builder.codec()
    if suite == 'format':
        return builder.formatter()
    if suite == 'reference' and 1 <= len(references) <= 64:
        for _, record, templates, _ in references:
            builder.format_case(record, templates)
        return builder.finish()
    raise ValueError('Unknown native mail suite')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--module', type=Path, default=Path('build/runtime-module/module.json'))
    parser.add_argument('--suite', choices=('codec', 'format', 'reference'), required=True)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--gc-data', type=Path, default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp', type=Path, default=Path('local/ac-decomp'))
    parser.add_argument('--rel', type=Path, default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    references = reference_fixtures(args.native_rom.read_bytes(), args.gc_data, args.decomp, args.rel) if args.suite == 'reference' else ()
    actions = scenario(rom, json.loads(args.module.read_text()), args.suite, references)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'rom_sha256': sha256(rom), 'suite': args.suite, 'actions': len(actions),
                      'references': [{'case': label, 'limitation': limit} for label, _, _, limit in references]}))


if __name__ == '__main__':
    main()
