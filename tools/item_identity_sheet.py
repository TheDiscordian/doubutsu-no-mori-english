#!/usr/bin/env python3
"""Inspect cached first-generation item identity evidence; never approve by index.

Reads stored XLSX cell values only. Formulas, links, and macros are not executed.
Downloaded evidence stays ignored; explicit reviewed approvals bind local ROM
and supplied English bytes, not a mutable online sheet.
"""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from aflib import sha256

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
SHEET_SHA = '7fcfb2d7ac3c30c3c69650ed61ae253c9589be0fba4b3aff09a334770da32be0'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/13sRAcj9YbP9_i-u0Kg6S7ycHbaOQx1jFG4lYLm2DJ4c/edit'


def sheet_rows(path, name):
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read('xl/workbook.xml'))
        selected = [r for r in root.findall(NS+'sheets/'+NS+'sheet') if r.get('name') == name]
        if len(selected) != 1: raise ValueError('Expected one named worksheet')
        links = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target = [r.get('Target') for r in links if r.get('Id') == selected[0].get(REL+'id')]
        if len(target) != 1 or '..' in PurePosixPath(target[0]).parts:
            raise ValueError('Invalid worksheet relationship')
        member = target[0].lstrip('/') if target[0].startswith('/') else 'xl/'+target[0]
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            for row in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall(NS+'si'):
                shared.append(''.join(t.text or '' for t in row.iter(NS+'t')))
        for row in ET.fromstring(archive.read(member)).findall(NS+'sheetData/'+NS+'row'):
            result = {}
            for cell in row.findall(NS+'c'):
                address = cell.get('r', '')
                match = re.fullmatch(r'([A-Z]+)[1-9][0-9]*', address)
                if not match or match[1] in result: raise ValueError('Invalid or duplicate cell')
                value = cell.findtext(NS+'v', '')
                if cell.get('t') == 's':
                    index = int(value)
                    if not 0 <= index < len(shared): raise ValueError('Invalid shared string')
                    value = shared[index]
                elif cell.get('t') == 'inlineStr':
                    value = ''.join(t.text or '' for t in cell.iter(NS+'t'))
                result[match[1]] = value
            yield int(row.get('r')), result


def identity_queue(path, inventory, references, remaining):
    if sha256(path.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed identity worksheet; review before using a new snapshot')
    cells = list(sheet_rows(path, 'Items'))
    for column, label in {'A': 'Row ID', 'C': 'ID (AF)', 'E': 'ID (AC)',
                          'H': 'Name (AF)', 'J': 'Name (English)', 'CJ': 'Texture (AF)',
                          'CX': 'Texture (AC)'}.items():
        if cells[0][1].get(column) != label: raise ValueError('Changed identity columns')
    indexed = {}
    for row, cell in cells[1:]:
        if re.fullmatch('[0-9A-F]{4}', cell.get('C', '')):
            indexed.setdefault(int(cell['C'], 16), []).append((row, cell))
    result = []
    for pending in sorted(remaining.glob('item_*-remaining.jsonl')):
        bank = pending.name.removesuffix('-remaining.jsonl')
        source = {r['id']: r for r in map(json.loads, (inventory/(bank+'.jsonl')).read_text().splitlines())}
        family = 'furniture' if bank == 'item_10' else bank
        refs = list(map(json.loads, (references/(family+'.jsonl')).read_text().splitlines()))
        for item in map(json.loads, pending.read_text().splitlines()):
            index = int(item['id'].split(':')[1], 16)
            if bank == 'item_10' and index % 4: continue
            number = (0x1000 if bank == 'item_10' else int(bank[5:], 16)*256)+index
            native = source[item['id']]
            row = {'id': item['id'], 'source_sha256': native['source_sha256'],
                   'native_name': native['source'].rstrip(' '), 'sheet_sha256': SHEET_SHA,
                   'status': 'needs_review'}
            matches = indexed.get(number, [])
            if len(matches) != 1:
                row['reason'] = 'missing_or_ambiguous_native_sheet_id'
            else:
                position, match = matches[0]
                row.update(sheet_row=position, sheet_item=match['A'], sheet_native=match['H'],
                           sheet_english=match['J'], sheet_gc_id=match['E'], notes=match.get('V', ''),
                           native_notes=match.get('HX', ''), english_notes=match.get('HZ', ''))
                row['visual_changes'] = [key for key, other in (('CG', 'CQ'), ('CJ', 'CX'))
                                         if match.get(key, '-') != match.get(other, '-')]
                refs_matching = [r for r in refs if r['text'] == match['J'] and r['text'].strip()]
                if len(refs_matching) == 1:
                    ref = refs_matching[0]
                    row.update(reference_id=ref['id'], reference_sha256=ref['source_sha256'])
                if row['native_name'] != match['H']:
                    row['reason'] = 'native_name_differs_from_sheet'
                elif len(refs_matching) != 1:
                    row['reason'] = 'missing_or_ambiguous_complete_reference'
                elif row['visual_changes']:
                    row['reason'] = 'version_specific_visual_reference'
                elif not match['J'].isascii():
                    row['reason'] = 'requires_accented_item_support'
                else:
                    row['reason'] = 'exact_bilingual_identity_requires_review'
            result.append(row)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('build/item-identity-megasheet.xlsx'))
    parser.add_argument('--sheet', default='Items')
    parser.add_argument('--head', type=int)
    parser.add_argument('--queue', action='store_true')
    parser.add_argument('--inventory', type=Path, default=Path('build/inventory'))
    parser.add_argument('--references', type=Path, default=Path('build/gamecube/names'))
    parser.add_argument('--remaining', type=Path, default=Path('build/native-items-resource'))
    args = parser.parse_args()
    if args.queue:
        for row in identity_queue(args.input, args.inventory, args.references, args.remaining):
            print(json.dumps(row, ensure_ascii=False))
        return
    for index, (number, row) in enumerate(sheet_rows(args.input, args.sheet)):
        if args.head is not None and index >= args.head: break
        print(json.dumps({'row': number, 'cells': row}, ensure_ascii=False))


if __name__ == '__main__': main()
