"""Inventory verified V3 donor identities; this does not install game content."""

import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from aflib import ROM_SHA256, sha256, verified_rom, yaz0_decode
from gamecube import Disc, rarc_files
from gc_names import symbol_data
from gc_text import decoder_tables, decode_gc
from textbanks import banks

ROOT = Path(__file__).resolve().parents[1]
DONOR = 'GAFE01-r0'
NATIVE_NPC_COUNT = 216
GC_NPC_COUNT = 236
GC_NPC_STORAGE_COUNT = 238  # Includes two development characters, not imports.
SYMBOLS_SHA = 'e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'
DECODER_SHA = 'a39f26143d26824209f5d944b0280ca1e2bfa544ffbeb5652df634fd7c790b90'
REL_SHA = '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
DONOR_FILES = {
    'forest_2nd.arc': (4132608, 'b3d784fbb993e83f65ce4b904db2cd6e42f6cf08e8467a77f2c8614d395e362a'),
    'foresta.rel.szs': (6137393, 'e9e24735808ec0bdf32fb8d327e2b846b6b6bc64f7d70010eff96d1c67336688'),
}
PERSONALITIES = ('normal', 'peppy', 'lazy', 'jock', 'cranky', 'snooty')
GROWTH = ('starter', 'move_in', 'islander')
ITEM_GROUPS = (
    'paper', 'money', 'tool', 'fish', 'cloth', 'etc', 'carpet', 'wall',
    'fruit', 'plant', 'minidisk', 'dummy', 'ticket', 'insect', 'hukubukuro', 'kabu',
)


def checked(data, size, digest, label):
    if len(data) != size or sha256(data) != digest:
        raise ValueError(f'{label}: unsupported size or SHA-256')
    return data


def read_donor(path):
    """Read only pinned resources from the actual disc, without extracting assets."""
    with Disc(path) as disc:
        if disc.header[:8] != b'GAFE01\x00\x00':
            raise ValueError('V3 requires GAFE01 disc 0, revision 0')
        entries = disc.files()
        paths = [entry['path'] for entry in entries]
        if len(paths) != len(set(paths)):
            raise ValueError('Duplicate GameCube resource path')
        files = {entry['path']: entry for entry in entries}
        result = {}
        for name, (size, digest) in DONOR_FILES.items():
            entry = files.get(name)
            if not entry or entry['size'] != size:
                raise ValueError(f'{name}: missing or unsupported resource size')
            result[name] = checked(disc.read(entry['offset'], size), size, digest, name)
    result['rel'] = checked(yaz0_decode(result['foresta.rel.szs']), 15640056, REL_SHA, 'Decoded REL')
    return result


def fixed_records(data, width, count=None):
    if width <= 0 or len(data) % width or (count is not None and len(data) != count * width):
        raise ValueError('Unexpected fixed-record size or count')
    return [data[i:i + width] for i in range(0, len(data), width)]


def villager_rows(names, defaults, personalities, growth, tables):
    """Keep actual donor identity and islander role; do not invent town support."""
    names = fixed_records(names, 8, GC_NPC_COUNT)
    defaults = fixed_records(defaults, 6, GC_NPC_STORAGE_COUNT)
    fixed_records(personalities, 1, GC_NPC_STORAGE_COUNT)
    fixed_records(growth, 1, GC_NPC_STORAGE_COUNT)
    result = []
    for index in range(NATIVE_NPC_COUNT, GC_NPC_COUNT):
        if personalities[index] >= len(PERSONALITIES) or growth[index] >= len(GROWTH):
            raise ValueError('Unsupported villager personality or growth permission')
        cloth, catchphrase, umbrella = struct.unpack_from('>HHb', defaults[index])
        if not 0x2400 <= cloth < 0x24FF or not 0 <= umbrella < 32:
            raise ValueError('Unsupported default villager clothing or umbrella')
        text = decode_gc(names[index], tables).rstrip(' ')
        if not text or '{' in text:
            raise ValueError('Unresolved villager name encoding')
        result.append({
            'id': f'{DONOR}/villager/{index:04X}',
            'donor_actor_id': f'{0xE000 + index:04X}',
            'name': text,
            'name_sha256': sha256(names[index]),
            'default_sha256': sha256(defaults[index]),
            'personality': PERSONALITIES[personalities[index]],
            'donor_role': GROWTH[growth[index]],
            'donor_clothing_id': f'{cloth:04X}',
            'donor_catchphrase_index': catchphrase,
            'donor_umbrella_index': umbrella,
            'native_identity': 'absent_from_original_roster',
            'target_actor_id': None,
            'status': 'identified_not_ported',
            'selectable': False,
        })
    return result


def item_rows(data, tables, *, base, furniture):
    """Describe donor name addresses, not inferred N64 matches or new-item counts."""
    records = fixed_records(data, 16)
    maximum = 1024 if furniture else 256
    if len(records) > maximum:
        raise ValueError('Item group exceeds its donor ID range')
    if (furniture and base not in (0x1000, 0x3000)) or (
            not furniture and base not in range(0x2000, 0x3000, 0x100)):
        raise ValueError('Unsupported donor item group')
    rows = []
    for index, record in enumerate(records):
        item_id = base + index * (4 if furniture else 1)
        name = decode_gc(record, tables).rstrip(' ')
        rows.append({
            'id': f'{DONOR}/item/{item_id:04X}',
            'donor_item_id': f'{item_id:04X}',
            'donor_name_index': index,
            'name': name,
            'name_sha256': sha256(record),
            'rotation_ids': [f'{item_id + r:04X}' for r in range(4)] if furniture else [],
            'native_identity': 'unreviewed',
            'target_item_id': None,
            'status': 'identity_and_behaviour_review_required',
            'selectable': False,
        })
    return rows


def build_catalog(n64_path, disc_path, decomp):
    rom = verified_rom(n64_path.read_bytes())
    symbols_path = decomp / 'config/GAFE01_00/foresta/symbols.txt'
    decoder_path = decomp / 'tools/msg_tool.py'
    symbol_bytes = symbols_path.read_bytes()
    if sha256(symbol_bytes) != SYMBOLS_SHA or sha256(decoder_path.read_bytes()) != DECODER_SHA:
        raise ValueError('V3 requires the pinned GameCube symbols and decoder')
    symbols = symbol_bytes.decode('utf-8')
    tables = decoder_tables(decoder_path)
    donor = read_donor(disc_path)
    members = list(rarc_files(donor['forest_2nd.arc']))
    if len({name for name, _ in members}) != len(members):
        raise ValueError('Duplicate donor archive member')
    names_path = 'data/npc_name_str_table.bin'
    members = dict(members)
    if names_path not in members:
        raise ValueError('Missing donor villager names')
    rel = donor['rel']
    villagers = villager_rows(members[names_path],
                             symbol_data(rel, symbols, 'npc_def_list'),
                             symbol_data(rel, symbols, 'npc_looks_table'),
                             symbol_data(rel, symbols, 'npc_grow_list'), tables)
    native_banks = {bank.name: bank for bank in banks(rom)}
    items, groups = [], []
    specs = [(f'itemName_{name}', 0x2000 + i * 0x100, False) for i, name in enumerate(ITEM_GROUPS)]
    specs += [('ftrName_table', 0x1000, True), ('ftrName2_table', 0x3000, True)]
    for symbol, base, furniture in specs:
        data = symbol_data(rel, symbols, symbol)
        rows = item_rows(data, tables, base=base, furniture=furniture)
        items.extend(rows)
        native = native_banks.get(f'item_{base >> 8:02X}')
        native_slots = len(native.entries()) if native else 0
        if furniture and native:
            if (native_slots - 1) % 4:
                raise ValueError('Unexpected native furniture rotation/filler layout')
            native_slots = (native_slots - 1) // 4
        groups.append({
            'symbol': symbol, 'donor_id_base': f'{base:04X}',
            'donor_name_records': len(rows), 'donor_name_table_sha256': sha256(data),
            'native_name_records': native_slots,
            'comparison': 'storage_counts_only_not_new_content_count',
        })
    all_ids = [r['id'] for r in villagers + items]
    if len(set(all_ids)) != len(all_ids):
        raise ValueError('Duplicate V3 donor identity')
    from v3_furniture_pipeline import Source
    from v3_room_aliases import discover, annotate_inventory
    aliases = discover(Source(rel, symbol_bytes))
    annotate_inventory(items, aliases)
    return {
        'format': 'AFV3-INVENTORY-1',
        'status': 'research_inventory_not_patch_or_supported_options',
        'donor': DONOR, 'source_sha256': ROM_SHA256,
        'source_resources': [{'path': path, 'size': size, 'sha256': digest}
                             for path, (size, digest) in DONOR_FILES.items()],
        'rel_decoded_sha256': REL_SHA, 'symbols_sha256': SYMBOLS_SHA,
        'decoder_sha256': DECODER_SHA,
        'summary': {
            'native_villagers': NATIVE_NPC_COUNT, 'donor_villagers': GC_NPC_COUNT,
            'additional_villager_identities': len(villagers),
            'additional_villagers_by_donor_role': dict(Counter(r['donor_role'] for r in villagers)),
            'donor_item_name_records': len(items), 'new_item_identities': None,
            'selectable_imports': 0,
        },
        'villagers': villagers, 'item_groups': groups, 'items': items, 'room_aliases': aliases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n64', type=Path, default=ROOT / 'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--disc', type=Path, default=ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--decomp', type=Path, default=ROOT / 'local/ac-decomp')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new inventory output file; existing results are preserved')
    catalog = build_catalog(args.n64, args.disc, args.decomp)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        output.write(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), **catalog['summary']}, indent=2))


if __name__ == '__main__':
    main()
