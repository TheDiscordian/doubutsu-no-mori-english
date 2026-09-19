"""Create a copied-town item playtest fixture, never changing the source save."""
import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import struct
import time

from aflib import sha256
from apply_translation import write_new
from v3_cheri_gameplay_fixture import SOURCE_SHA
from v3_save_clothing import PROFILE, STATE
from v3_save_codec import BANK, PAYLOAD

ROOT = Path(__file__).resolve().parents[1]


def snapshot(debug, rom_path):
    """Compare the ordinary player's active garment bank without executing code."""
    from aflib import by_vrom
    from v3_asset_loader import BLOB
    rom_path = Path(rom_path)
    rom = rom_path.read_bytes()
    report = json.loads((rom_path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing'].get('wearing'):
        raise ValueError('Clothing snapshot requires the checked current cartridge')

    def pointer(at, size):
        value = int.from_bytes(debug.read_memory(at, 4), 'big')
        if value % 4 or not 0x80000000 <= value <= 0x80400000-size:
            raise ValueError('Invalid ordinary clothing pointer')
        return value

    game, private = pointer(0x8010EF90, 0x1914), pointer(0x80136FD8, 0xBD0)
    active, first, second = struct.unpack('>3I', debug.read_memory(0x8010C0D0, 12))
    if active not in (0, 1) or not 0 <= first < 73 or not 0 <= second < 73:
        raise ValueError('Invalid active native clothing bank')
    index = (first, second)[active]
    bank = debug.read_memory(game+0x110+84*index, 84)
    if struct.unpack_from('>H', bank)[0] != 14 or struct.unpack_from('>I', bank, 16)[0] != 512:
        raise ValueError('Active bank is not the native clothing texture')
    texture = pointer(game+0x110+84*index+4, 544)
    expected = by_vrom(rom)[BLOB].extract(rom)[0xF000:0xF220]
    actual = debug.read_memory(texture, 544)
    if actual != expected or debug.read_memory(private+0xA76, 4) != bytes.fromhex('10BF34BF'):
        raise ValueError('Ordinary player garment identity or complete artwork mismatch')
    return {'ordinary_clothing_snapshot': {'active_buffer': active, 'bank_index': index,
        'texture_pointer': f'{texture:08X}', 'texture_palette_bytes': 544,
        'artwork_sha256': sha256(actual), 'cloth_id': '10BF', 'cloth_item': '34BF',
        'assertion': 'passed', 'read_only': True}}


def create(source, rom, report, *, shop_stock=False, equipment_item=None, event_shop=False):
    if len(source) != 2*BANK or sha256(source) != SOURCE_SHA:
        raise ValueError('Clothing fixture requires the preserved copied source town')
    if sha256(rom) != report['output_sha256']:
        raise ValueError('Item fixture requires its exact checked cartridge')
    profile = bytes.fromhex(report['save_runtime']['profile_hex'])
    if len(profile) != PROFILE:
        raise ValueError('Invalid item fixture profile')
    item = 0x34BF
    parent = None
    if event_shop:
        from aflib import by_vrom
        from v3_asset_loader import BLOB
        equipment = report.get('equipment_resources', {})
        if (shop_stock or equipment_item is not None or not equipment.get('optional_selection') or
                not equipment.get('event_acquisition', {}).get('acquisition_installed')):
            raise ValueError('Event fixture requires complete selected acquisition, not seeded goods')
        blob = by_vrom(rom)[BLOB].extract(rom); at = equipment['blob_offset']
        if (blob[0x20:0x20+PROFILE] != profile or sha256(blob[at:at+equipment['bytes']]) != equipment['sha256'] or
                not any(profile[r['profile_byte']] & r['profile_mask'] for r in equipment['parent_readers']['rows'])):
            raise ValueError('Event fixture has no selected complete parent or changed reader bindings')
        item = None
    elif equipment_item is None:
        if not report['clothing'].get('wearing') or not profile[183] & 0x80:
            raise ValueError('Current profile does not include the full imported garment')
    else:
        from aflib import by_vrom
        from v3_asset_loader import BLOB
        equipment = report.get('equipment_resources', {})
        if shop_stock or not equipment.get('optional_selection'):
            raise ValueError('Equipment fixture needs installed parent selection and a pocket, not shop stock')
        rows = equipment['parent_readers']['rows']
        parent = next((r for r in rows if int(r['item_id'], 16) == equipment_item), None)
        blob = by_vrom(rom)[BLOB].extract(rom)
        at = equipment['blob_offset']
        if (parent is None or blob[0x20:0x20+PROFILE] != profile or
                sha256(blob[at:at+equipment['bytes']]) != equipment['sha256'] or
                not profile[parent['profile_byte']] & parent['profile_mask']):
            raise ValueError('Equipment parent is absent, disabled, or has changed installed bindings')
        item = equipment_item
    spec = importlib.util.spec_from_file_location('v3_clothing_save_reference', ROOT/'tests/test_v3_save_clothing.py')
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    state = bytearray(profile+bytes(STATE-PROFILE))
    if parent is not None:
        index = (int(parent['display_item_id'], 16)-0x3000)//4
        if not 0 <= index < 1024 or (parent['profile_byte'], parent['profile_mask']) != (32+index//8, 1 << (index & 7)):
            raise ValueError('Equipment collection/profile identity mismatch')
        state[PROFILE+index//8] |= 1 << (index & 7)
    elif not shop_stock and not event_shop:
        state[PROFILE+512+23] = 0x80
    output, records = bytearray(), []
    for number in range(2):
        bank = bytearray(source[number*BANK:(number+1)*BANK])
        if bank[4:8] != b'NAFJ' or sum(struct.unpack('>'+str(PAYLOAD//2)+'H', bank[:PAYLOAD])) & 0xFFFF:
            raise ValueError('Source town bank is invalid')
        if event_shop:
            wallet = 0x20+0x38
            balance = struct.unpack_from('>I', bank, wallet)[0]
            struct.pack_into('>I', bank, wallet, 10000)
            records.append({'bank': number, 'saved_offset': wallet,
                            'wallet_before': balance, 'wallet_after': 10000})
        elif shop_stock:
            # Native shop goods start at saved ED22 / live 80135BC2. The
            # preserved town's third entry is its clothing slot, not a pocket.
            slot = 0xED26
            before = bytes(bank[slot:slot+2])
            if before != bytes.fromhex('2474'):
                raise ValueError('Unexpected original shop clothing entry')
            bank[slot:slot+2] = struct.pack('>H', item)
            records.append({'bank': number, 'shop_goods_index': 2, 'saved_offset': slot,
                            'before': before.hex(), 'after': '34bf'})
            wallet = 0x20+0x38
            balance = struct.unpack_from('>I', bank, wallet)[0]
            struct.pack_into('>I', bank, wallet, 1000)
            records.append({'bank': number, 'saved_offset': wallet,
                            'wallet_before': balance, 'wallet_after': 1000})
        else:
            slot, conditions = 0x20+0x14, 0x20+0x34
            before = bytes(bank[slot:slot+2])
            condition_before = struct.unpack_from('>I', bank, conditions)[0]
            bank[slot:slot+2] = struct.pack('>H', item)
            struct.pack_into('>I', bank, conditions, condition_before & ~3)
            records.append({'bank': number, 'pocket_offset': slot, 'before': before.hex(), 'after': f'{item:04x}',
                            'condition_before': condition_before, 'condition_after': condition_before & ~3})
        output.extend(reference.reference_pack(bank, state))
    return bytes(output), {'source_save_sha256': SOURCE_SHA, 'rom_sha256': sha256(rom),
        'fixture_save_sha256': sha256(output), 'player_slot': 0,
        'pocket_slot': None if shop_stock or event_shop else 0, 'seeded_shop_stock': shop_stock,
        'event_shop': event_shop, 'item': f'{item:04X}' if item is not None else None,
        'seeded_ownership': not shop_stock and not event_shop, 'save_format': 2, 'field_changes': records,
        'villagers_and_other_items_retained': True, 'ordinary_acquisition_tested': False,
        'source_save_modified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--shop-stock', action='store_true',
                        help='Seed shop clothing and 1,000 Bells; preserve pockets and zero imported ownership')
    parser.add_argument('--equipment-item', type=lambda value: int(value, 16),
                        help='Seed this selected equipment parent in the first pocket using its installed records')
    parser.add_argument('--event-shop', action='store_true',
                        help='Set up an isolated festival-night town with money, no imported items, and no ownership')
    args = parser.parse_args()
    source = ROOT/'local/rc2-save-report-g3O4lU/test.flash'
    image, receipt = create(source.read_bytes(), args.rom.read_bytes(),
                            json.loads((args.rom.parent/'build.json').read_text()), shop_stock=args.shop_stock,
                            equipment_item=args.equipment_item, event_shop=args.event_shop)
    rtc = (ROOT/'build/v3-identity-arrival-01/test.rtc').read_bytes()
    if args.shop_stock or args.event_shop:
        # Clothing uses the source stock's calendar day; the event uses a
        # festival Saturday. Change only Ares's disposable RTC, not the host.
        staged = datetime(2026, 8, 29, 20, 0, 0) if args.event_shop else datetime(2026, 9, 10, 12, 0, 0)
        if args.event_shop and staged.weekday() != 5:
            raise ValueError('Festival clock must be a Saturday in August')
        def bcd(value): return (value//10)*16+value%10
        rtc = bytearray(b'\xff'*32)
        rtc[16:24] = bytes([bcd(staged.second), bcd(staged.minute), bcd(staged.hour)|0x80,
                           bcd(staged.day), bcd((staged.weekday()+1)%7), bcd(staged.month),
                           bcd(staged.year%100), bcd(staged.year//100-19)])
        rtc[24:32] = int(time.time()).to_bytes(8, 'big')
        receipt['isolated_clock'] = staged.isoformat()
    if len(rtc) != 32: raise ValueError('Invalid retained daytime RTC')
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(args.output/'test.flash', image)
    write_new(args.output/'test.rtc', rtc)
    receipt['rtc_sha256'] = sha256(rtc)
    write_new(args.output/'fixture.json', (json.dumps(receipt, indent=2)+'\n').encode())
    if sha256(source.read_bytes()) != SOURCE_SHA: raise ValueError('Source town unexpectedly changed')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__': main()
