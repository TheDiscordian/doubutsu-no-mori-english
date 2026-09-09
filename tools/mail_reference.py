#!/usr/bin/env python3
"""Prepare source-verified local mail templates and exercise full-letter assembly.

Generated reference text is local-only. This bundle is not an approved catalog
and is not consumed by the ROM builder. Missing glyphs remain explicit failures.
"""

import argparse
from dataclasses import replace
import json
from pathlib import Path

from aflib import sha256, verified_rom
from audit_mail_templates import CLASSIC, COMPOSITE, reply_groups, reachable_fields, template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_format import Templates, format_letter, field_index
from mail_record import Field, Record, pack
from textbanks import Bank
from textcodec import ENCODE

DECODER_SHA256 = "a39f26143d26824209f5d944b0280ca1e2bfa544ffbeb5652df634fd7c790b90"
BANK_HASHES = {
    'super': ('f71c8a03917bba1ac273c7846e5b1b14a429ee097936040734a4f4cfdc502d02', 'dc1f34e4086e6860541258c2b5aed2bee46ca26dcc77efe13c7cd8726eb9e25e'),
    'mail': ('feb5a12a8a32fe374742a732db4c52f740c8307a755f2536087cf82fb1517776', '665f9b0e12b1ad2b9c2d5ad762c81562e24a5abaa31f74e830c12ec2e17965f0'),
    'ps': ('684da91c57da87179c86bc854b7b0d1fb7cbe2e18f8dfac81e73d879d2e52d21', '11f9748aa241901a82e30876771cd62983099f3207a829ff8924c9d2c9a58aba'),
    'superz': ('d4169bdd5aa71f532ef1debcc96d3db735117282216e081d0b5b66fb3d2deaa6', '0cb13975b98fea33ad1faa19a5feac33565c1c618bf0622180c20c02a8b2ac98'),
    'maila': ('186a16e81abc6b63354e06d76c8b76f7cd1c543c272f96cc575a46260f103ae6', 'e2abe4142c1f8dfdd942305b47b7b93df715203c98eb36e8b3949ab8a3ad0542'),
    'mailb': ('3daaf1ce0aeb35178d81d8109673ca3c7ecd736b95e2616da088863973f94f2d', 'd3e90b25777d3fcdb74484ca838f7d657e4deecf61b9bbe3fa7487b84bbb9436'),
    'mailc': ('14c37ef5811eecb8247fe9076a0019a2a64fcf8ee1a3e59912bab2804933fee1', 'd068736bc0b95db5da068e8407a33c637c0617b52305f1b2b1293b339db9ba89'),
    'psz': ('7a836f0644db1e7c17da6334194a28392446367d37ec07a0da6506c40e84c653', 'ca4f7b928ad1fd9401825f4cd2fcdb30c9bd7d75fcafb5c7ca022ca70e664d6c'),
    'string': ('1ca41141a2265ddd0b3bee22868f27fe3cd980f2caeb948e1d00e7910e0533cf', '1b61ef035cd276a575169a7473f62a8cd9b1b788abd713bbd972c016487079df'),
}
SEMANTIC_FUNCTIONS = {
    'mHandbill_clr_force_art': '31ed5e79b37f74d03010f1c85c2af5cfcbc49e95150c90359f7cbb368b8caf25',
    'mHandbill_clr_capital_flag': '31ed5e79b37f74d03010f1c85c2af5cfcbc49e95150c90359f7cbb368b8caf25',
    'mHandbill_load_init': '7c47cec2bb6979b1d0044106ef2e5337edfbc74ebd67e6976a8b96dd0d8509d6',
    'mHandbill_Put_String_FREE': '9e3c601a5d8dbdb03e6828274149731ef5bb046d22d378904167cc2550a01679',
    'mHandbill_Capital_Letter': '3bbd889893d55bcfbf24341e0d86105e602ced3800306af22ff353ad431f3f7e',
    'mMsg_Get_Length_String': '2cc9b56034319edb617bbee97046e2c0cb29d2ef5cffc0e36682f9d8932d04d4',
    'mFont_small_to_capital': 'a69427eba9ec1b65a8f135d5e9e2a2e885d6020f39640ac8cb463e457cb632a6',
    'mHandbill_Load_HandbillFromRom': 'a41b03a5f2c62deabe2aafb51a726afec7be634ef36526b0d3b2d6fe8cc26a44',
    'mHandbill_Load_HandbillFromRom2': 'c02fa16a9c93ed5f820bb80c5d26ab4453e13b774052102d223ad2a88ce151b4',
    'mHandbillz_load': '5a98fc2d3a4021461315c2f154197f2fc310ea6bd68ffce1df2c515aceba0aa4',
    'mHandbill_CheckSuperStringBorderAndCopy': 'a81b78f22b193ed6154ca4c05e0ee322d882747d184fb41ea67eb9f0d38653e3',
    'mHandbill_Change_ControlCode2': 'e94d91a72479ff7a291b101d8c899e5227f2fe066745a42167c257a2716f4431',
    'mHandbill_Cut_Article': '18ae1dd2eed9a1a5f3115ab11a5ff702b8bf6c11701da70c59a2db9c13b5ffd3',
}


def verify_semantics(rel, symbols):
    for name, expected in SEMANTIC_FUNCTIONS.items():
        if sha256(symbol_data(rel, symbols, name)) != expected:
            raise ValueError(f"Unexpected English mail implementation: {name}")
    return dict(SEMANTIC_FUNCTIONS)


def transcode(data, tables, *, extended_glyphs=False):
    """Keep all mail commands; translate only exact supported glyph identities."""
    output, pos = bytearray(), 0
    while pos < len(data):
        byte = data[pos]
        if byte == 0x7F:
            if pos+1 >= len(data):
                raise ValueError("Truncated reference mail command")
            opcode = data[pos+1]
            if opcode not in (0x74, 0x75):
                field_index(opcode)
            if tables['CONT_SIZES'][opcode] != 2:
                raise ValueError("Unexpected reference mail command length")
            output.extend(data[pos:pos+2])
            pos += 2
        else:
            if extended_glyphs:
                from mail_glyph_codes import ADVANCES
                if byte in ADVANCES:
                    output.extend((0x80,byte))
                    pos += 1
                    continue
            glyph = tables['CHAR_MAP'][byte]
            if glyph not in ENCODE:
                raise ValueError(f"Unrepresentable mail glyph at {pos}: GC {byte:02X} {glyph!r}")
            output.append(ENCODE[glyph])
            pos += 1
    return bytes(output)


def load_reference(directory, decomp, rel_path, *, extended_glyphs=False):
    decoder = decomp/'tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256:
        raise ValueError("Unexpected English decoder source")
    tables = decoder_tables(decoder)
    symbols = (decomp/'config/GAFE01_00/foresta/symbols.txt').read_text()
    semantics = verify_semantics(rel_path.read_bytes(), symbols)
    if extended_glyphs:
        from extended_glyphs import source_atlas
        source_atlas(rel_path.read_bytes(),symbols,decoder,mail=True)
    banks, report = {}, {}
    for name, expected in BANK_HASHES.items():
        data = (directory/(name+'_data.bin')).read_bytes()
        table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data), sha256(table)) != expected:
            raise ValueError(f"Unexpected English {name} bank")
        entries = Bank(name, 0, 0, data, table).entries()
        if name == 'string':
            if entries[0x738:0x73C] != [b'a', b'an', b'the', b'some']:
                raise ValueError("Unexpected English mail articles")
            continue
        converted, rows = [], []
        for index, entry in enumerate(entries):
            row = {'id': index, 'source_sha256': sha256(entry), 'source_bytes': len(entry)}
            try:
                encoded = transcode(entry, tables,extended_glyphs=extended_glyphs)
                row.update(n64_hex=encoded.hex(), n64_sha256=sha256(encoded),
                           fields=sorted(template_fields(encoded,extended_glyphs=extended_glyphs)), status='reference_only_not_approved')
            except ValueError as error:
                encoded = None
                row.update(error=str(error), status='requires_glyph_or_command_support')
            converted.append(encoded)
            rows.append(row)
        banks[name] = converted
        report[name] = {'data_sha256': expected[0], 'table_sha256': expected[1], 'entries': rows,
                       'converted': sum(entry is not None for entry in converted), 'total': len(entries)}
    return banks, {'banks': report, 'semantic_functions': semantics, 'decoder_sha256': DECODER_SHA256,
                   'article_bank_sha256': BANK_HASHES['string'],
                   'status': 'Local references only; no approved catalog or runtime installation'}


def assembly_cases(banks, rom):
    """Cover all classic triples, diagonal replies, and every reply part choice.

    Cross combinations are not exhaustive. Exact largest-field-union witnesses
    supplement single-part variations. Unsupported glyph rows remain rejected.
    Catalog FFFF is a test identity, never a release assignment.
    """
    requests = [(0, (i,)) for i in range(len(banks['mail']))]
    selections = {tuple([i]*5) for i in range(384)}
    for starts in reply_groups(rom):
        for start in starts:
            for part in range(5):
                for index in range(start, start+32):
                    ids = [start]*5
                    ids[part] = index
                    selections.add(tuple(ids))
            entries = [[(i, template_fields(data)) for i in range(start, start+32)
                        if (data := banks[name][i]) is not None] for name in COMPOSITE]
            states = reachable_fields(entries)
            largest = max(map(len, states))
            for mask, ids in states.items():
                if len(mask) == largest:
                    selections.add(ids)
    requests.extend((1, ids) for ids in sorted(selections))
    for kind, ids in requests:
        names = COMPOSITE if kind else CLASSIC
        part_ids = ids if kind else ids*3
        parts = tuple(banks[name][index] for name, index in zip(names, part_ids))
        label = f"{kind}:"+','.join(f'{index:04X}' for index in ids)
        if any(part is None for part in parts):
            yield label, None, None, 'unrepresentable_reference_glyph'
            continue
        fields = frozenset().union(*(template_fields(part) for part in parts))
        width = 10 if not kind and ids == (1,) else 16
        record = Record(0xFFFF, kind, ids, tuple((i, Field(b'x'*width, 4)) for i in sorted(fields)))
        templates = Templates(record.catalog, kind, part_ids, parts)
        # Record 0001 at width ten is a formatter probe, not proof that its
        # actual sources fit. The maximum-width snapshot audit still rejects it.
        limitation = 'requires_actual_field_bounds' if width == 10 else None
        for capital in (False, True):
            yield label+f':capital={int(capital)}', replace(record, initial_capital=capital), templates, limitation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--gc-data', type=Path, default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp', type=Path, default=Path('local/ac-decomp'))
    parser.add_argument('--rel', type=Path, default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--output', type=Path, default=Path('build/mail-reference'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    banks, report = load_reference(args.gc_data, args.decomp, args.rel)
    cases = []
    for label, record, templates, limitation in assembly_cases(banks, rom):
        row = {'case': label, 'limitation': limitation}
        if record is not None:
            letter = format_letter(record, templates)
            wire = pack(record)
            parts = (letter.header, letter.body, letter.footer)
            row.update(snapshot_used=wire[2], snapshot_sha256=sha256(wire),
                       lengths=list(map(len, parts)), header_split=letter.header_split,
                       output_sha256=sha256(b''.join(parts)), final_capital=letter.final_capital)
        cases.append(row)
    report['assembly_cases'] = cases
    report['native_source_sha256'] = sha256(rom)
    assembled = [case for case in cases if 'lengths' in case]
    report['summary'] = {
        'reference_entries': sum(bank['total'] for bank in report['banks'].values()),
        'transcoded_entries': sum(bank['converted'] for bank in report['banks'].values()),
        'entries_requiring_glyph_support': sum(bank['total']-bank['converted'] for bank in report['banks'].values()),
        'assembled_cases': len(assembled),
        'rejected_cases': len(cases)-len(assembled),
        'probe_cases_requiring_actual_field_bounds': sum(case['limitation'] == 'requires_actual_field_bounds' for case in assembled),
        'max_header_body_footer_bytes': [max(case['lengths'][i] for case in assembled) for i in range(3)],
        'max_total_output_bytes': max(sum(case['lengths']) for case in assembled),
        'scope': 'All classic triples and specified composite probes, two initial capital states; not every composite combination',
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'reference.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
