#!/usr/bin/env python3
"""Quick, read-only coverage of distinct English GameCube import candidates.

Use the existing identity worksheet and current build receipts, not a progress
checklist. This is content-weighted pipeline coverage, not remaining work hours
or release readiness. See docs/IMPORT_PROGRESS.md for the counting rules.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from aflib import sha256
from item_identity_sheet import SHEET_SHA, sheet_rows

ROOT = Path(__file__).resolve().parents[1]
DONOR = 'GAFE01-r0'
KINDS = {'Furniture': 'furniture', 'Clothing': 'clothing', 'Carpet': 'flooring',
         'Wallpaper': 'wallpaper', 'Stationery': 'stationery', 'Diary': 'diaries',
         'Fish': 'fish', 'Insect': 'bugs', 'Gyroid': 'gyroids', 'Fossil': 'fossils',
         'Tool': 'equipment', 'Umbrella': 'equipment', 'Balloon': 'equipment',
         'Pinwheel': 'equipment', 'Fan': 'equipment', 'Music': 'music'}


def current_lock():
    """Follow the already-maintained proposal pointer, never a stale counter pin."""
    progress = (ROOT/'docs/PROGRESS.md').read_text()
    match = re.search(r'The current proposal.*?`(build/[^`]+/build-lock\.json)`',
                      progress, re.S)
    if not match:
        raise ValueError('Current proposal not found; specify --base-lock')
    return ROOT/match[1]


def canonical_item(item):
    # Donor m_name_table.h: paper quantity, axe wear, exercise-card stamps,
    # and spirit instances are states of a single item, not extra imports.
    if item >> 8 == 0x20:
        return 0x2000 + (item & 63)
    if 0x223D <= item <= 0x2243:
        return 0x2201
    if 0x2523 <= item <= 0x252F:
        return 0x2523
    if 0x2D28 <= item <= 0x2D2C:
        return 0x2D28
    return item


def item_key(item):
    return f'{DONOR}/item/{canonical_item(item):04X}'


def candidate_rows(cells, representations, excluded):
    """Inventory all categories, including ones without an implemented importer."""
    result = {}
    for number, row in cells:
        value = row.get('E', '')
        if not re.fullmatch('[0-9A-F]{4}', value):
            continue
        item = int(value, 16)
        if (item in representations or item in excluded or canonical_item(item) != item
                or row.get('HG') != '1'
                or any(row.get(k, '-') != '-' for k in ('C', 'H', 'CG', 'CJ'))):
            continue
        key = item_key(item)
        if key in result:
            raise ValueError('Ambiguous worksheet identity: '+key)
        result[key] = dict(id=key, name=row['J'], kind=KINDS.get(row.get('HR'), 'other'),
                           evidence=f'identity worksheet row {number}')
    return result


def installed_rows(report, selectable):
    """Read completed integrations; partial preparation gets no completion credit."""
    done = {key: 'installed selectable integration' for key in selectable}
    staged = report.get('staged_furniture', {})
    if staged.get('deferred_resources'):
        raise ValueError('Staged furniture has unresolved resources; inspect before counting')
    for row in staged.get('rows', []):
        # The shared installer only publishes these profiles after the complete
        # room behaviour is bound. Acquisition/catalogue/scoring can remain off.
        if row.get('profile_installed') and row.get('item_record_installed') and row.get('room_runtime'):
            done[row['id']] = 'installed room behaviour and item profile; acquisition pending'
    surfaces = report.get('room_surfaces', {})
    selection = surfaces.get('optional_selection', {})
    if (surfaces.get('menu', {}).get('surface_options_enabled')
            and surfaces.get('save', {}).get('surface_options_enabled')
            and surfaces.get('sound', {}).get('runtime_installed')):
        # These reasons belong to the existing surface selector, not a new
        # manually maintained completion list. Unknown reasons remain pending.
        for key, reason in selection.get('pending', {}).items():
            if reason in ('HomePage delivery', 'Harvest rewards'):
                done[key] = 'installed surface integration; '+reason+' pending'
    return done


def summarise(candidates, done, selectable):
    if set(done)-candidates.keys():
        raise ValueError('Completed identities absent from denominator')
    counts = {kind: dict(imported=0, total=0) for kind in sorted(set(KINDS.values()) | {'villagers', 'other'})}
    rows = []
    for key, row in sorted(candidates.items()):
        counts[row['kind']]['total'] += 1
        counts[row['kind']]['imported'] += key in done
        rows.append(dict(row, imported=key in done, selectable=key in selectable,
                         reason=done.get(key, 'no completed integration in this build')))
    total, imported = len(rows), len(done)
    return dict(donor=DONOR, imported=imported, total=total, remaining=total-imported,
                percent=round(imported*100/total, 1) if total else None,
                selectable=len(set(selectable)&candidates.keys()), categories=counts, rows=rows)


def measure(lock):
    import v3_optional_composition as composition
    from v3_furniture_pipeline import Source
    from v3_room_aliases import discover as aliases
    from v3_room_representations import discover as special
    from v3_clothing_batch import representations as clothes
    from v3_creature_items import source_records as creatures
    from v3_import_catalog import NATIVE_NPC_COUNT, GC_NPC_COUNT

    composition.use_build_lock(lock)
    image, report = composition.inputs()
    selectable = composition.catalogue(image, report)
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                    (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    sheet = ROOT/'build/item-identity-megasheet.xlsx'
    if sha256(sheet.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed identity worksheet')
    cells = list(sheet_rows(sheet, 'Items'))
    if any(cells[0][1].get(k) != v for k, v in
           {'C': 'ID (AF)', 'E': 'ID (AC)', 'HG': 'Obtainable (AC)', 'HR': 'Type'}.items()):
        raise ValueError('Changed identity worksheet columns')
    display = {int(r['display_item_id'], 16) for r in aliases(source)['rows']} | set(clothes(source))
    display |= {int(r['source_display_item_id'], 16) for r in creatures(source)[0]}
    excluded = {int(r['item_id'], 16) for r in special(source)['rows']}
    # User-created umbrella slots are not eight fixed donor appearances.
    excluded.update(range(0x2224, 0x222C))
    candidates = candidate_rows(cells[1:], display, excluded)
    worksheet = {item_key(int(r['E'], 16)): r for _, r in reversed(cells[1:])
                 if re.fullmatch('[0-9A-F]{4}', r.get('E', ''))}
    for index in range(NATIVE_NPC_COUNT, GC_NPC_COUNT):
        key = f'{DONOR}/villager/{index:04X}'
        candidates[key] = dict(id=key, name=selectable.get(key, {}).get('name', f'Villager {index:04X}'),
                               kind='villagers', evidence='donor roster minus original roster')

    # Existing import records include reviewed artwork variants (e.g. cherry
    # shirt), plus supported hidden donor items. Keep these in scope even when
    # the worksheet lists an N64 counterpart or marks the item unobtainable.
    known = list(selectable.values()) + report.get('staged_furniture', {}).get('rows', [])
    for row in known:
        key = row['id']
        if not key.startswith(DONOR+'/'):
            raise ValueError('Non-English-GameCube identity in build: '+key)
        if key in candidates:
            continue
        fields = worksheet.get(key, {})
        kind = KINDS.get(fields.get('HR'), row.get('kind', 'other'))
        candidates[key] = dict(id=key, name=row['name'], kind=kind,
                               evidence='existing reviewed import record')
    result = summarise(candidates, installed_rows(report, selectable), selectable)
    result.update(build_lock=str(lock.resolve().relative_to(ROOT)), runtime_abi=report['runtime_abi'],
                  rom_sha256=report['output_sha256'], worksheet_sha256=SHEET_SHA,
                  metric='distinct-content importing coverage approximation; not release readiness')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock', type=Path, help='Override the current proposal in docs/PROGRESS.md')
    parser.add_argument('--json', action='store_true', help='Include every counted identity and its evidence')
    args = parser.parse_args()
    try:
        result = measure(args.base_lock or current_lock())
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Cannot measure import coverage: {error}\n')
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"GameCube importing: {result['percent']}% ({result['imported']}/{result['total']} distinct additions)")
    for kind, count in result['categories'].items():
        value = f"{count['imported']}/{count['total']}" if count['total'] else 'no additional identities found'
        print(f'  {kind:12} {value}')
    print(f"Remaining: {result['remaining']}; selectable now: {result['selectable']}.")
    print('Item-weighted approximation. Acquisition and playtesting are separate; partial artwork is not completion.')
    print(f"Build: ABI {result['runtime_abi']}; {result['build_lock']}")


if __name__ == '__main__':
    main()
