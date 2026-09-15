"""Generate browser selection rules from the checked installed import records.

Exports are unserved, ignored development artifacts. This does not update web/,
the Pages recipe, or either running V2 patcher.
"""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import struct
import zlib

from aflib import by_vrom, n64_checksum, sha256, verified_rom
import v3_optional_composition as composition
from v3_save_runtime import profile_bytes

ROOT = composition.ROOT
FILES = ('composer.mjs', 'worker.mjs')


def rules(image, report):
    """Compile a small, data-only plan; there are no browser item allowlists."""
    pinned = (composition.BASE/'build.json').read_bytes()
    if (sha256(image) != composition.BASE_SHA or sha256(pinned) != composition.REPORT_SHA or
            json.loads(pinned) != report):
        raise ValueError('Browser rules require the complete pinned cartridge and report')
    catalog = composition.catalogue(image, report)
    files = by_vrom(image)
    blob = files[composition.BLOB]
    module = files[composition.MODULE]
    if blob.pend or module.pend:
        raise ValueError('Selection resources must be uncompressed')
    entries, slots = [], {}

    def field(at, size):
        if type(at) is not int or not 0 <= at <= len(image) - size or size <= 0:
            raise ValueError('Selection field outside the cartridge')
        return {'offset': at, 'before': image[at:at + size].hex()}

    def disable(at, size, value=None):
        return {**field(at, size), 'after': (bytes(size) if value is None else value).hex()}

    for key, row in catalog.items():
        villagers = [row] if row['kind'] == 'villager' else []
        furniture = [row] if row['kind'] == 'furniture' else []
        shirts = []
        off = [disable(blob.pstart + row['enable_offset'], row['enable_bytes'])]
        if row['kind'] == 'villager':
            off.append(disable(blob.pstart + row['town_flag_offset'], 1))
        elif row['kind'] == 'clothing':
            furniture.append({'item_id': row['display_item_id'],
                              'runtime_index': row['display_runtime_index']})
            shirts.append(row['source_record'])
            off.append(disable(blob.pstart + row['display_enable_offset'], 4))
        for item in furniture:
            index = item['runtime_index']
            if index in slots:
                raise ValueError('Two selection options own the same furniture identity')
            slots[index] = key
        profile = profile_bytes(villagers, furniture, shirts)
        entries.append({'id': key, 'name': row['name'], 'kind': row['kind'],
                        'dependencies': row['dependencies'], 'profile_hex': profile.hex(),
                        'disable': off})

    # Reuse the authoritative HRA write generator, assigning each disabled row
    # to the option that owns its fixed furniture/mannequin runtime identity.
    import v3_hra as hra
    entry = files[hra.NEW_VROM]
    scoring, _ = composition.scoring_selection(image, report, catalog, set())
    scoring_by_offset = {row['offset']: row for row in scoring}
    options = {row['id']: row for row in entries}
    for row in report['hra']['imports']:
        at = entry.pstart + report['hra']['metadata_address'] - hra.RAM + row['runtime_index'] * 4
        patch = scoring_by_offset.pop(at)
        options[slots[row['runtime_index']]]['disable'].append(
            {key: patch[key] for key in ('offset', 'before', 'after')})
    if scoring_by_offset:
        raise ValueError('Unassigned scoring changes')

    # Derive append-only ordering/count operations from the offline composer's
    # checked empty tables. This keeps native addresses and row encodings in
    # that existing implementation, not in a second browser-side item system.
    table_writes, _ = composition.catalogue_selection(image, report, set())
    packed = []
    cat = report['catalogue']
    for kind, width, rows, ordering, count_label in (
            ('furniture', 4, cat['imports'], 'selected furniture ordering',
             'selected furniture iteration/search/completion count'),
            ('clothing', 2, cat['clothing']['imports'], 'selected clothing ordering',
             'selected clothing iteration/completion count')):
        table = next(row for row in table_writes if row['purpose'] == ordering)
        before, empty = bytes.fromhex(table['before']), bytes.fromhex(table['after'])
        start = len(before) - len(rows) * width
        if before[:start] != empty[:start] or any(empty[start:]):
            raise ValueError('Changed selected catalogue suffix contract')
        members = []
        for i, row in enumerate(rows):
            donor = row['donor_item_id'] if kind == 'clothing' else row['item_id']
            key = composition.item_key(int(donor, 16))
            if catalog[key]['kind'] != kind:
                raise ValueError('Catalogue option has the wrong item class')
            members.append({'id': key, 'hex': before[start + i * width:start + (i + 1) * width].hex()})
        counts = []
        for row in table_writes:
            if row['purpose'] == count_label:
                counts.append({**field(row['offset'], 4), 'base': int(row['after'], 16)})
                if int(row['before'], 16) != counts[-1]['base'] + len(members):
                    raise ValueError('Catalogue count is not a bounded additive count')
        packed.append({**field(table['offset'] + start, len(rows) * width),
                       'width': width, 'rows': members, 'counts': counts})
    if len(table_writes) != len(packed) + sum(len(row['counts']) for row in packed):
        raise ValueError('Unassigned catalogue changes')

    crcs = []
    for at, start, length in ((blob.pstart + 0xF8, blob.pstart + composition.PACKAGE, composition.PACKAGE_SIZE),
                              (module.pstart + composition.CONFIG + 8, blob.pstart, composition.PREFIX_SIZE)):
        value = field(at, 4)
        if int(value['before'], 16) != zlib.crc32(image[start:start + length]):
            raise ValueError('Changed source resident checksum')
        crcs.append({**value, 'start': start, 'length': length})
    if struct.unpack_from('>2I', image, 0x10) != n64_checksum(image):
        raise ValueError('Changed source cartridge checksum')
    return {'format': 'AFV3-BROWSER-COMPOSITION-1', 'donor': 'GAFE01-r0',
            'runtime_abi': report['runtime_abi'], 'base_sha256': sha256(image), 'base_size': len(image),
            'base_report_sha256': composition.REPORT_SHA,
            'stable_sha256': composition.STABLE_SHA, 'stable_size': composition.STABLE.stat().st_size,
            'experimental': True, 'web_patcher_enabled': False,
            'options': entries, 'profile': field(blob.pstart + 0x20, 192), 'tables': packed,
            'crc32': crcs, 'header': field(0x10, 8)}


def build(output, *, recipes=False, disc=None):
    out = output.resolve()
    if not out.is_relative_to(ROOT/'build') or out.exists():
        raise ValueError('Choose a fresh ignored build/ output; never a served site')
    image, report = composition.inputs()
    plan = rules(image, report)
    raw = composition.canonical(plan)
    site = out/'site'
    data = site/'data'
    data.mkdir(parents=True)
    (data/'composition.json').write_bytes(raw)
    for name in FILES:
        target = site/'experimental/imports'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/'experimental/imports'/name, target)
    (site/'web').mkdir()
    shutil.copyfile(ROOT/'web/core.mjs', site/'web/core.mjs')
    manifest = {'format': 'AFV3-BROWSER-BUNDLE-1', 'experimental': True,
                'web_patcher_enabled': False, 'plan': {'file': 'composition.json',
                'size': len(raw), 'sha256': sha256(raw)}}
    if recipes:
        from build_portal import donor_resources, make_recipe, SAVE_NOTE
        native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        resources, donors = donor_resources(disc or ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        stable = composition.STABLE.read_bytes()
        if sha256(stable) != composition.STABLE_SHA:
            raise ValueError('Changed no-import V2 baseline')
        for label, target in (('v2', stable), ('v3', image)):
            recipe, stats = make_recipe(native, target, donors)
            compressed = gzip.compress(recipe, compresslevel=9, mtime=0)
            folder = data/label
            folder.mkdir()
            (folder/'patch.afwp.gz').write_bytes(compressed)
            manifest[label] = {'format': 1, 'build': 'V2-11' if label == 'v2' else f'V3-ABI-{plan["runtime_abi"]}',
                'public_release': False, 'source_sha256': sha256(native), 'source_size': len(native),
                'output_sha256': sha256(target), 'output_size': len(target),
                'output_name': 'Animal Crossing N64 - Development.z64',
                'disc_id': 'GAFE01', 'disc_revision': 0, 'resources': resources,
                'recipe': {'file': 'patch.afwp.gz', 'size': len(compressed), 'sha256': sha256(compressed),
                           'decoded_size': len(recipe), 'decoded_sha256': sha256(recipe)},
                'requirements': {'expansion_pak': True, 'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc': True},
                'save_compatibility': SAVE_NOTE, 'stats': stats}
    (data/'manifest.json').write_bytes(composition.canonical(manifest))
    receipt = {'format': 'AFV3-BROWSER-EXPORT-1', 'base_sha256': plan['base_sha256'],
               'base_report_sha256': composition.REPORT_SHA, 'runtime_abi': plan['runtime_abi'],
               'options': len(plan['options']), 'recipes_included': recipes,
               'experimental': True, 'served': False, 'web_patcher_enabled': False,
               'files': {str(p.relative_to(site)): sha256(p.read_bytes())
                         for p in sorted(site.rglob('*')) if p.is_file()}}
    (out/'build.json').write_bytes(composition.canonical(receipt))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recipes', action='store_true', help='Include two-game reconstruction recipes in the unserved export')
    parser.add_argument('--disc', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output, recipes=args.recipes, disc=args.disc), indent=2))
