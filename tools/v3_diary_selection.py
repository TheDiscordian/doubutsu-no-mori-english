"""Bind the complete installed diary category without enabling unfinished gameplay."""
import struct

from aflib import by_vrom, sha256
from v3_asset_loader import BLOB
from v3_diary_items import encode, TABLE
from v3_import_storage import ITEMS, ROWS, ROWS_RAM
from v3_registry import diary_parent_identity

PENDING = ('Tortimer event participation and ordinary diary acquisition remain '
           'unfinished; native diary UI/save execution is unverified.')


def catalogue_key(row):
    donor = int(row['donor_parent_item_id'], 16)
    item = diary_parent_identity(donor)
    index = 1087 + donor - 0x2B00
    key = f'GAFE01-r0/item/{donor:04X}'
    if (row['parent_item_id'] != f'{item:04X}' or row['selection_id'] != key or
            row['item_id'] != f'{0x30FC + 4*(donor-0x2B00):04X}' or
            row['runtime_index'] != index or row['catalogue_index'] != index+1024 or
            row['mode'] != 0 or row['representation'] != 'diary'):
        raise ValueError('Changed diary parent/cover catalogue binding')
    return key


def bindings(image, report):
    """One shared bit/enable word controls a carried style and all cover rotations.

    These are prepared bindings, not selectable choices. Promotion requires the
    remaining gameplay implementation, not merely changing a report boolean.
    """
    d = report.get('equipment_resources', {}).get('diary_items')
    if not d or not d.get('catalogue'):
        return {}
    if (d['format'] != 'AFV3-DIARY-ITEMS-1' or d['selected'] != 0 or
            len(d['rows']) != 16 or len(d['profiles']) != 16):
        raise ValueError('Changed inactive diary category contract')
    files = by_vrom(image)
    blob = files[BLOB].extract(image)
    p = d['packet']; packet = image[p['physical']:p['physical']+p['bytes']]
    table = encode(d['rows'])
    if (sha256(packet) != p['sha256'] or packet[TABLE:TABLE+len(table)] != table or
            blob[0x20:0xE0].hex() != report['save_runtime']['profile_hex']):
        raise ValueError('Changed diary readers or saved profile')
    covers = {r['item_id']: r for r in d['catalogue']['imports']}
    if len(covers) != 16:
        raise ValueError('Incomplete diary catalogue category')
    result = {}
    for style, (r, profile) in enumerate(zip(d['rows'], d['profiles'], strict=True)):
        cover = 0x30FC+style*4; slot = (cover-0x3000)//4; index = 1024+slot
        at = ROWS+slot*80; metadata = blob[ITEMS+slot*32:ITEMS+(slot+1)*32]
        byte, mask = 32+slot//8, 1 << (slot & 7)
        cat = covers.get(f'{cover:04X}')
        if (not cat or catalogue_key(cat) != r['id'] or r['ready'] is not False or
                r['selected'] is not False or profile['selected'] is not False or
                profile['item_id'] != r['display_item_id'] or
                profile['parent_item_id'] != r['item_id'] or profile['runtime_index'] != index or
                profile['profile_ram'] != ROWS_RAM+slot*80+8 or
                struct.unpack_from('>HHI', blob, at) != (index, cover, 0) or
                blob[at+8:at+76].hex() != profile['profile_hex'] or any(blob[at+76:at+80]) or
                sha256(blob[at:at+80]) != profile['profile_record_sha256'] or
                sha256(metadata) != profile['item_record_sha256'] or
                int.from_bytes(metadata[28:30], 'big') != diary_parent_identity(0x2B00+style) or
                blob[0x20+byte] & mask):
            raise ValueError('Changed inactive diary carried/display/save binding')
        owner = next((f for f in files.values() if
            f.vstart <= profile['object_vrom'] < profile['object_vrom']+profile['object_bytes'] <= f.vend), None)
        if owner is None:
            raise ValueError('Diary artwork has no DMA owner')
        art = owner.extract(image); start = profile['object_vrom']-owner.vstart
        if sha256(art[start:start+profile['object_bytes']]) != profile['object_sha256']:
            raise ValueError('Changed installed diary cover artwork')
        result[r['id']] = dict(id=r['id'], name=r['name'], kind='diary', item_id=r['item_id'],
            display_item_id=r['display_item_id'], display_runtime_index=index,
            dependencies=[], enable_offset=at+4, enable_bytes=4,
            enable_ram=ROWS_RAM+slot*80+4, profile_byte=byte, profile_mask=mask,
            selectable=False, reason=PENDING)
    return result
