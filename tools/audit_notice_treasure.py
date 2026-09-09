#!/usr/bin/env python3
"""Review complete treasure notices against native selection and field meanings."""

import argparse
import json
from pathlib import Path
import struct
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse, verify_registered
from mail_format import Templates, format_letter
from mail_record import Record, Field
from mail_reference import BANK_HASHES, DECODER_SHA256, transcode
from notice_record import pack, unpack
from textbanks import Bank, banks

ROOT = Path(__file__).resolve().parents[1]
IDS = tuple(range(0x1F0, 0x202))
NATIVE_FIELDS = ((1, 2, 3, 4), (1, 3, 4), (2, 3), (1, 3, 4), (1, 3, 5),
                 (2, 3, 4), (1, 3), (1, 3, 4, 5), (1, 2, 4), (1, 3, 5),
                 (1, 3, 5), (1, 3, 4), (1, 2, 3, 4), (2, 3), (1, 2, 4),
                 (2, 3, 4), (2, 4), (2, 4))
GUARDS = (
    (0x800A5DF4, 0x800A5E58, '30b9e8a9e87197805686063dcce6358f76261b9ea876cd412b7faf7a21762af6'),
    (0x800A5E58, 0x800A5F08, '6311fb617183d51ba98866c308e525dc54cbbc8d41e6e168505b5ab7c9d9ab57'),
    (0x800A5F08, 0x800A62EC, 'e548281b85424af417431715461bd63d5806f4e15151fb90c0b263039917e53f'),
)
FUNCTIONS = {
    'mNtc_set_landname_string': (80, 'c035b7b7f053f6edd07075fb72a986503433ed02837a48d5bdb6e31864e92cbc'),
    'mNtc_set_treasure_string': (204, 'ecb7f84aed61ebcf4a3f1b230a3d7055f98e4e530cac197b606bff6f3cd048cd'),
    'mNtc_check_treasure': (864, '5fec24115dfe730244a0f43af0b73109747681ddeddff6fa4a360c1b64208541'),
}


def audit(native, catalog, root=ROOT):
    native = verified_rom(native)
    code = by_vrom(native)[CODE_VROM].extract(native)
    for start, end, digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError('Changed native treasure selector or field helper')
    # Original selection is 01F0 + personality*3 + random(3), not a relocated
    # event index. The formatter's output is the 96-byte body at sp+68h.
    for at, word in ((0x800A623C, 0x92C9000B), (0x800A6290, 0x01220019),
                     (0x800A629C, 0x256D01F0), (0x800A62A0, 0x0C024FC1),
                     (0x800A62A8, 0x0C02974C)):
        if struct.unpack_from('>I', code, at-CODE_RAM)[0] != word:
            raise ValueError('Changed native treasure identity or publication call')
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied treasure executable')
    for name, expected in FUNCTIONS.items():
        value = symbol_data(rel, symbols, name)
        if (len(value), sha256(value)) != expected:
            raise ValueError('Changed supplied treasure selector or field helper')
    identity = verify_registered(catalog)
    if identity['catalog'] != 4: raise ValueError('Treasure review requires complete glyph catalogue four')
    installed = parse(catalog)[1]
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256: raise ValueError('Changed supplied text decoder')
    tables = decoder_tables(decoder)
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    sources = {b.name: b.entries() for b in banks(native) if b.name in ('super', 'mail', 'ps')}
    parts = []
    for name, source in sources.items():
        data, table = ((directory/(name+suffix)).read_bytes() for suffix in ('_data.bin', '_data_table.bin'))
        if (sha256(data), sha256(table)) != BANK_HASHES[name]:
            raise ValueError('Changed supplied treasure bank')
        reference = Bank(name, 0, 0, data, table).entries()
        for number in IDS:
            value = transcode(reference[number], tables, extended_glyphs=True)
            old_fields = NATIVE_FIELDS[number-0x1F0] if name == 'mail' else ()
            new_fields = ((1, 2, 3) if number == 0x1F4 else (2, 4) if number == 0x1FE else old_fields)
            if name != 'mail': new_fields = ()
            if (value != installed[name][number]
                    or tuple(sorted(template_fields(source[number]))) != old_fields
                    or tuple(sorted(template_fields(value, extended_glyphs=True))) != new_fields):
                raise ValueError('Changed treasure source wording or field meaning')
            parts.append({'id': f'{name}:{number:04X}', 'source_sha256': sha256(source[number]),
                          'reference_sha256': sha256(reference[number]), 'encoded_sha256': sha256(value),
                          'native_fields': list(old_fields), 'reference_fields': list(new_fields)})
    cases = []
    for number in IDS:
        if number == 0x1F4: continue
        template = tuple(installed[name][number] for name in ('super', 'mail', 'ps'))
        fields = tuple(sorted(template_fields(template[1], extended_glyphs=True)))
        for capital in (False, True):
            # Preserve N64 numeric row/column coordinates; do not import the
            # donor's lettered vertical-acre conversion. Names exercise full
            # sixteen-byte fields, while town identity stays the native six.
            samples = {1: Field(b'ABCDEFGHIJKLMNOP'), 2: Field(b'abcdefghijklmnop', 1),
                       3: Field(b'5'), 4: Field(b'4'), 5: Field(b'TownXX')}
            value = Record(4, 0, (number,), tuple((i, samples[i]) for i in fields), capital)
            wire = pack(value)
            if unpack(wire, expected_catalog=4) != value:
                raise ValueError('Treasure snapshot loses full fields')
            letter = format_letter(value, Templates(4, 0, (number,)*3, template))
            if len(letter.body) > 1024: raise ValueError('Complete treasure body exceeds reader capacity')
            cases.append({'template': number, 'capital': int(capital), 'wire': wire.hex(),
                          'body': letter.body.hex(), 'body_bytes': len(letter.body)})
    return {'templates': list(IDS), 'reference_approved': [i for i in IDS if i != 0x1F4],
            'parts': parts, 'cases': cases, 'catalog': identity, 'installed': False,
            'native_adaptations': [{
                'template': 0x1F4, 'native_fields': [1, 3, 5], 'reference_fields': [1, 2, 3],
                'reason': 'The donor reveals the item where the native post gives only the row. '
                          'Retain the town treasure-hunt heading and undisclosed item.',
            }],
            'review_notes': {'01FE': 'The supplied English version omits the author signature; retain its complete wording.',
                            'coordinates': 'Native decimal row and column, not donor A-F row letters.',
                            'town': 'Original six-byte town identity without the Japanese village suffix.',
                            'names': 'Capture full villager and item fields and the selected item article.'},
            'status': 'Source review only; native-specific 01F4 text, creation, reader approval, '
                      'publication failure handling, and persistence remain'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog', type=Path, default=ROOT/'build/mail-glyph-resources/glyph-catalog.bin')
    parser.add_argument('--output', type=Path, default=ROOT/'build/audits/notice-treasure.json')
    args = parser.parse_args()
    result = audit(args.rom.read_bytes(), args.catalog.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'reference_bodies_approved': len(result['reference_approved']),
                      'native_adaptations': len(result['native_adaptations']),
                      'complete_field_cases': len(result['cases']), 'installed': False}))


if __name__ == '__main__': main()
