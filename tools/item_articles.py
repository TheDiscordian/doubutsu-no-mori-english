"""Bind complete installed item names to supplied English article metadata."""

import argparse
import json
from pathlib import Path
import struct
import zlib

from aflib import sha256, verified_rom
from extended_items import COUNTS, WIDTH, resource as name_resource
from gc_names import symbol_data
from native_item_names import load_names as native_names

ROOT = Path(__file__).resolve().parents[1]
REL_HASH = '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
SYMBOL_HASH = 'e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'
NAMES_HASH = '69e7bf2e099e652463deecd3a1416f09774c9b4b4810bfc3cfd104956eff4add'
# Immutable name/article profiles share the unchanged version-one wire layout.
# Register only complete source reconstructions, never self-reported checksums.
DATA_HASH = '639aaeb04f49e5c5e06daaae7c395bd4691fb68f3ec0d3ddd018e0946e04686d'
SHEET_NAMES_HASH = 'e64c6e93659af310860458964ef02690f3cc1d5914e896070a004b453ea47bcd'
SHEET_DATA_HASH = 'eee68e48d3a6f5e68cfc23288c2776402a46958a37206477cc4f72e1b2d5c4c1'
PROFILES = {NAMES_HASH: DATA_HASH, SHEET_NAMES_HASH: SHEET_DATA_HASH}
LEGACY_GENERATOR_SHA256 = 'c913ac8565b1dcdc6d4dbd0a7bf8d7229653cf409d0473271df7e478bae666ca'
COUNT = sum(COUNTS[:-1])+COUNTS[-1]//4
HEADER = struct.pack('>4I', 0x41464941, 1, COUNT, 5)+bytes.fromhex(NAMES_HASH)
SIZE = (len(HEADER)+5*COUNT+15)&~15
UNKNOWN = 255
ARTICLES = ('Paper', 'Money', 'Tool', 'Fish', 'Cloth', 'Etc', 'Carpet', 'Wall',
            'Fruit', 'Plant', 'MiniDisk', 'Diary', 'Ticket', 'Insect', 'Hukubukuro', 'Kabu')
NAMES = ('paper', 'money', 'tool', 'fish', 'cloth', 'etc', 'carpet', 'wall',
         'fruit', 'plant', 'minidisk', 'dummy', 'ticket', 'insect', 'hukubukuro', 'kabu')


def build(rom, names, report, rel, symbols, originals):
    verified_rom(rom)
    if sha256(rel) != REL_HASH or sha256(symbols.encode()) != SYMBOL_HASH:
        raise ValueError('Changed supplied GameCube article source or symbol map')
    if (report.get('source_sha256') != sha256(rom) or report.get('data_sha256') != sha256(names)
            or sha256(names) not in PROFILES or name_resource(rom, report['edits']) != names):
        raise ValueError('Articles require the complete approved item-name resource')
    approved = native_names()
    expected_originals = {row['translation'] for row in approved.values()}
    if (not isinstance(originals, dict) or set(originals) != expected_originals
            or any(not isinstance(row, dict) or type(row.get('article')) is not int
                   or not 0 <= row['article'] <= 4 or not isinstance(row.get('reason'), str)
                   or not row['reason'].strip() for row in originals.values())):
        raise ValueError('Every native-specific name requires an explicit article approval')
    donor = {'furniture': (symbol_data(rel, symbols, 'ftrName_table'),
                            symbol_data(rel, symbols, 'ftrArt'))}
    for index, (name, article) in enumerate(zip(NAMES, ARTICLES)):
        donor[f'item_{0x20+index:02X}'] = (symbol_data(rel, symbols, 'itemName_'+name),
                                         symbol_data(rel, symbols, 'itemArt_'+article))
    edits = {row['id']: row for row in report['edits']}
    output, rows, slot = bytearray(HEADER[:16]+bytes.fromhex(sha256(names))), [], 0
    for group, count in zip((*range(0x20, 0x30), 0x10), COUNTS):
        for index in range(0, count, 4 if group == 0x10 else 1):
            copies = 4 if group == 0x10 else 1
            ids = [f'item_{group:02X}:{index+i:04X}' for i in range(copies)]
            fields = [names[32+(slot+i)*WIDTH:32+(slot+i+1)*WIDTH] for i in range(copies)]
            if len(set(fields)) != 1 or len({id in edits for id in ids}) != 1:
                raise ValueError('Furniture rotations require identical complete names and approval')
            name, article, references = fields[0], UNKNOWN, []
            for id in ids:
                edit = edits.get(id)
                if edit is None:
                    continue
                provenance = edit['provenance']
                reference = provenance['reference_id']
                if reference.startswith('native:'):
                    key = reference[len('native:'):]
                    row = approved.get(key)
                    if row is None or edit['translation'] != row['translation']:
                        raise ValueError('Unknown native-specific article identity')
                    choice = originals[row['translation']]['article']
                else:
                    family, number = reference.split(':'); number = int(number, 16)
                    if family not in donor:
                        raise ValueError('Unknown supplied item article family')
                    source, articles = donor[family]
                    field = source[number*WIDTH:(number+1)*WIDTH]
                    if (len(field) != WIDTH or field != name or number >= len(articles)
                            or sha256(field) != provenance['reference_sha256']):
                        raise ValueError('Item article does not match the complete English donor name')
                    choice = articles[number]
                if not 0 <= choice <= 4 or (article != UNKNOWN and article != choice):
                    raise ValueError('Invalid or conflicting item article')
                article = choice
                references.append(reference)
            output.extend(bytes([article])+struct.pack('>I', zlib.crc32(name) if article != UNKNOWN else 0))
            rows.append({'id': ids[0], 'slots': copies, 'article': article,
                         'name_sha256': sha256(name), 'references': references})
            slot += copies
    output.extend(bytes(SIZE-len(output)))
    data = bytes(output)
    return data, {'version': 1, 'data_sha256': sha256(data), 'bytes': len(data),
                  'names_sha256': sha256(names), 'rom_sha256': sha256(rom),
                  'rel_sha256': sha256(rel), 'symbols_sha256': sha256(symbols.encode()),
                  'original_articles': originals,
                  'known_slots': sum(r['slots'] for r in rows if r['article'] != UNKNOWN),
                  'unknown_slots': sum(r['slots'] for r in rows if r['article'] == UNKNOWN),
                  'entries': rows}


def verify(data):
    names_hash = data[16:48].hex()
    expected = PROFILES.get(names_hash)
    if len(data) != SIZE or data[:16] != HEADER[:16] or expected is None or sha256(data) != expected:
        raise ValueError('Changed or unapproved complete item article profile')
    return names_hash


def verify_names(names, configured_vrom, expected_names_hash=NAMES_HASH):
    if (configured_vrom != 0x02A00000 or PROFILES.get(expected_names_hash) is None
            or sha256(names) != expected_names_hash):
        raise ValueError('Treasure articles require their exact complete installed item names')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--names', type=Path, default=ROOT/'build/native-items-resource')
    parser.add_argument('--rel', type=Path, default=ROOT/'build/gamecube/files/foresta.rel.szs.decoded')
    parser.add_argument('--symbols', type=Path, default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-treasure/articles')
    parser.add_argument('--audit-only', action='store_true', help='Report reconstructed identity without approving or writing it')
    args = parser.parse_args()
    data, report = build(args.rom.read_bytes(), (args.names/'names.bin').read_bytes(),
                         json.loads((args.names/'names.json').read_text()), args.rel.read_bytes(),
                         args.symbols.read_text(), json.loads((ROOT/'translations/n64-item-articles.json').read_text()))
    if args.audit_only:
        print(json.dumps({k: v for k, v in report.items() if k not in ('entries', 'original_articles')}, indent=2))
        return
    verify(data)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'articles.bin').write_bytes(data)
    (args.output/'articles.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('entries', 'original_articles')}, indent=2))


if __name__ == '__main__': main()
