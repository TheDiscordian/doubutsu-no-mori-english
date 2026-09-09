#!/usr/bin/env python3
"""Bind initial bulletin-board text and controls to the supplied native sources."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from audit_mail_templates import template_fields
from gc_text import decoder_tables
from mail_catalog import parse, verify_registered
from mail_format import Templates, format_letter
from mail_record import Record, Field
from mail_reference import BANK_HASHES, DECODER_SHA256, transcode
from notice_record import pack, unpack
from textbanks import Bank, banks

ROOT = Path(__file__).resolve().parents[1]
INITIAL_IDS = tuple(range(0x1E, 0x22))
SCOPED_IDS = INITIAL_IDS + tuple(range(0x1A4, 0x1CD)) + tuple(range(0x1F0, 0x202))
NATIVE_BODY_HASHES = (
    'df06dfe0b9dd3b3d1ab5a557ca39bda15d21fd22e2acc53b15498c1924c54577',
    'd8e4f03c7d4e557c0f82eb081efb591435a31d656d91fa149d0d7d325fa02501',
    '671976ca421811b8c901c9b2ec6c75846eaf34b238121dfb2cb4b9b3fd4e5da4',
    '02d18cd5ef30a888ec7ec762ca59956ce622438c1caaf9311c40833585e0c9f7',
)
ENCODED_BODY_HASHES = (
    '34224b8906c9b70f79289d20ce35b1961ab37820a46ca65b24eb66c8e4f8c50f',
    'd1954827407d388e099091c93942d53ef74fe93a3a56300d3224d1755bb02c18',
    'da2e4abfa6c26630f9f38eff368ac233bc8e2fae06597c374e7637d052d2fafd',
    '6d51fae4941774c3f135b362987f12e156a4a0ea2dfe33d73cb47c5a85cff99c',
)
OVERLAY_VROM, OVERLAY_RAM = 0x797A50, 0x80894250
OVERLAY_HASH = 'b7f501e8efe2761f0f0e6fd4c18bd648ceae48658cbfe0f350d8a8386a8f7cb7'
INIT_HASH = '1fa0a689e509bf025a7eac40d9d4a1e73a8681523fea021593559b54384cf599'
READ_CONTROL_HASH = 'bda6eb0b4479eb456d61b1f88ae3d7acbde5b756cc98a47fd5e02d13ebd6b559'


def initial_body(record, catalog_banks):
    """Independent complete-body model for the immutable first notice profile."""
    pack(record)
    if (record.catalog != 4 or record.templates[0] not in INITIAL_IDS or record.fields):
        raise ValueError('Unapproved initial notice template or fields')
    number = record.templates[0]
    parts = tuple(catalog_banks[name][number] for name in ('super', 'mail', 'ps'))
    if parts[0] != b'\xcd' or parts[2] != b'':
        raise ValueError('Unexpected initial notice header or footer')
    if sha256(parts[1]) != ENCODED_BODY_HASHES[number-0x1E]:
        raise ValueError('Changed complete initial notice body')
    letter = format_letter(record, Templates(4, 0, (number,)*3, parts))
    if letter.header or letter.footer:
        raise ValueError('Initial notice unexpectedly displays mail sections')
    body = letter.body
    if number == 0x21:
        if body[81:88] != b'C Stick' or body.count(b'C Stick') != 1:
            raise ValueError('Changed notice controller span')
        body = body[:81] + b'C Buttons' + body[88:]
    return body


def audit(native, catalog, root=ROOT):
    native = verified_rom(native)
    files = by_vrom(native)
    code = files[CODE_VROM].extract(native)
    overlay = files[OVERLAY_VROM].extract(native)
    if (sha256(overlay) != OVERLAY_HASH
            or sha256(code[0x800A5BC4-CODE_RAM:0x800A5CB0-CODE_RAM]) != INIT_HASH
            or struct.unpack_from('>4I', code, 0x8010B4A0-CODE_RAM) != INITIAL_IDS
            or sha256(overlay[0x310:0x5C4]) != READ_CONTROL_HASH):
        raise ValueError('Changed native notice initializer, identities, or controls')
    # Actual native trigger arguments, not the donor's C Stick description.
    controls = {0x80894594: 0x24040002, 0x808945D4: 0x24040001,
                0x8089460C: 0x24040004, 0x80894654: 0x24040008,
                0x8089467C: 0x34048000, 0x808946FC: 0x24044000,
                0x80894708: 0x24041000}
    for address, word in controls.items():
        if struct.unpack_from('>I', overlay, address-OVERLAY_RAM)[0] != word:
            raise ValueError('Changed native notice button mask')
    identity = verify_registered(catalog)
    if identity['catalog'] != 4:
        raise ValueError('Initial notices require immutable glyph catalogue four')
    installed = parse(catalog)[1]
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256:
        raise ValueError('Changed supplied text decoder')
    tables = decoder_tables(decoder)
    original = {b.name: b.entries() for b in banks(native) if b.name in ('super', 'mail', 'ps')}
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    approvals = []
    for name in original:
        data, table = ((directory/(name+suffix)).read_bytes()
                       for suffix in ('_data.bin', '_data_table.bin'))
        if (sha256(data), sha256(table)) != BANK_HASHES[name]:
            raise ValueError('Changed supplied notice reference bank')
        reference = Bank(name, 0, 0, data, table).entries()
        for number in INITIAL_IDS:
            value = transcode(reference[number], tables, extended_glyphs=True)
            if (value != installed[name][number] or template_fields(value, extended_glyphs=True)
                    or template_fields(original[name][number])):
                raise ValueError('Changed notice source fields or complete reference')
            if name == 'mail' and sha256(original[name][number]) != NATIVE_BODY_HASHES[number-0x1E]:
                raise ValueError('Changed Japanese initial notice identity')
            approvals.append({'id': f'{name}:{number:04X}',
                              'source_sha256': sha256(original[name][number]),
                              'reference_sha256': sha256(reference[number]),
                              'encoded_sha256': sha256(value), 'bytes': len(value)})
    cases = []
    for number in INITIAL_IDS:
        for capital in (False, True):
            record = Record(4, 0, (number,), (), capital)
            wire, body = pack(record), initial_body(record, installed)
            if unpack(wire, expected_catalog=4) != record:
                raise ValueError('Initial notice snapshot mismatch')
            cases.append({'template': number, 'capital': int(capital), 'wire': wire.hex(),
                          'body_sha256': sha256(body), 'body_bytes': len(body),
                          'visible_lines': len(body.rstrip(b'\xcd').split(b'\xcd'))})
    feasibility = []
    for number in SCOPED_IDS:
        fields = sorted(set().union(*(template_fields(installed[name][number], extended_glyphs=True)
                                      for name in ('super', 'mail', 'ps'))))
        record = Record(4, 0, (number,), tuple((i, Field(b'X'*16, 4)) for i in fields))
        wire = pack(record)
        if unpack(wire, expected_catalog=4) != record:
            raise ValueError('Notice maximum-field snapshot mismatch')
        feasibility.append({'template': number, 'fields': fields, 'used_bytes': 4+wire[6],
                            'semantic_approval': number in INITIAL_IDS})
    return {'profile': 1, 'catalog': identity, 'source_sha256': sha256(native),
            'native_overlay_sha256': OVERLAY_HASH, 'native_init_sha256': INIT_HASH,
            'native_read_control_sha256': READ_CONTROL_HASH,
            'button_masks': {f'{a:08X}': f'{w & 0xFFFF:04X}' for a, w in controls.items()},
            'parts': approvals, 'cases': cases, 'feasibility': feasibility,
            'message_bytes': 96, 'post_bytes': 104, 'timestamp_offset': 96,
            'installed': False,
            'status': 'Initial-body source binding and lossless codec; native creation, reader, editor/tag discrimination, and persistence remain'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog', type=Path, default=ROOT/'build/mail-glyph-resources/glyph-catalog.bin')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-foundation/approval.json')
    args = parser.parse_args()
    report = audit(args.rom.read_bytes(), args.catalog.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'initial_bodies': 4, 'cases': len(report['cases']),
                      'scoped_templates_fit': len(report['feasibility']),
                      'max_saved_bytes': max(r['used_bytes'] for r in report['feasibility']),
                      'installed': False}))


if __name__ == '__main__':
    main()
