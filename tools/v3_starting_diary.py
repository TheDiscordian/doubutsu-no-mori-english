"""Optional source-verified diary and orange box in newly initialised houses.

The native starting-room function still creates its cassette player and room
surfaces. Its return branches to a small tail which places the donor box at
[1][1] in the main layer, and the carried diary in the secondary layer. It does
not run when loading saved houses and never reads or writes player pockets.
"""
import struct

from aflib import by_vrom, CODE_RAM, CODE_VROM, sha256
from v3_asset_loader import BLOB, ROOT

HOOK = 0x800947B8
WRAPPER, SETTING = 0xBF60, 0xBFB0
BOX = 'GAFE01-r0/item/30F8'
DONOR_ROOM_SHA = '0f47f6a3e8307f11c60c3a4c5637587277b9bc0103789f395352cfc2ba4aade8'
CONTRACTS = (
    (0x80094520, 0x80094690, 'f567fa8e97fffe0beec1b6177054c2c2eff4f0b36325d67ddc2621eda7aaa61a'),
    (0x80094744, 0x800947C0, '82b7d2e308804f16ed877b60a8db56efe68f5d0f210f3b494a0f9ccd30f50368'),
    (0x800853CC, 0x80085490, '19b5811a5327c05b78cecba7afc09e5f437d2f2eaac7528a1e9cd60f2e84267d'),
    (0x800869F0, 0x80086B00, 'b009db990859d318e26057565607cbf28ee8d495c037c5101cd48faa0dff42ad'),
)


def dependencies(report):
    """Only the real installed source box is a starting-house dependency."""
    diary = report.get('equipment_resources', {}).get('diary_items', {})
    if not diary.get('rows') or not all(row.get('ready') for row in diary['rows']):
        return []
    box = next((row for row in report['furniture']['imports'] if row['id'] == BOX), None)
    if not box or (box['name'], box['item_id'], box['runtime_index'],
            box['profile']['profile_symbol'], box['profile']['profile_sha256']) != (
            'orange box', '30F8', 1086, 'iam_nog_mikanbox',
            'cd44a07ecf105caf8842468bf78a8a94f0938ad3fb1377924077e272e787d357'):
        raise ValueError('Starting house needs the complete installed source orange box')
    return [BOX]


def wrapper(item):
    # a3 remains common-data base + masked house index * 0xB48 in the exact
    # native room initializer. Both readers retain their 512-byte layers.
    return struct.pack('>6I', 0x340830F8, 0xA4E835E2,
        0x34080000 | item, 0xA4E837E2, 0x03E00008, 0)


def option(image, report):
    required = dependencies(report)
    if not required:
        return None
    from v3_diary_selection import bindings
    diaries = bindings(image, report)
    first = report['equipment_resources']['diary_items']['rows'][0]
    key, item = first['id'], int(first['item_id'], 16)
    if key not in diaries or not diaries[key]['selectable'] or first['style'] != 0 or item != 0x2B10:
        raise ValueError('Starting diary requires the complete selectable first style')
    from v3_furniture_pipeline import Source
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    donor, function = source.function(0x42E14)
    if function['symbol'] != 'mHm_SetDefaultPlayerRoomData' or sha256(donor) != DONOR_ROOM_SHA:
        raise ValueError('Changed complete donor starting-room initializer')
    files = by_vrom(image); core = files[CODE_VROM]
    if core.pend:
        raise ValueError('Starting diary requires uncompressed native code')
    for lo, hi, digest in CONTRACTS:
        data = image[core.pstart+lo-CODE_RAM:core.pstart+hi-CODE_RAM]
        if sha256(data) != digest:
            raise ValueError('Changed complete native house initializer/layer reader')
    e = report['equipment_resources']; p = e['creature_fish']['world']['packet']
    start = files[BLOB].pstart+p['blob_offset']; code = wrapper(item)
    travel = e['creature_fish']['world']['creature_travel']
    if (travel['ram']+travel['code']['bytes'] > p['ram']+WRAPPER or
            p['ram']+SETTING+4 > travel['visitor_ram'] or
            any(image[start+WRAPPER:start+SETTING+4])):
        raise ValueError('Starting-house tail reservation is occupied')
    at = core.pstart+HOOK-CODE_RAM
    before = bytes.fromhex('03e0000800000000')
    if image[at:at+8] != before:
        raise ValueError('Changed native starting-room return')
    after = struct.pack('>2I', 0x08000000 | ((p['ram']+WRAPPER) >> 2 & 0x3FFFFFF), 0)
    return dict(id='starting-diary', name='Start with a diary', scope='Newly created starting houses only',
        description='Place the college-rule diary on the orange box inside each starting house. Saved houses and pockets are unchanged.',
        default='N64', values=dict(N64=0, GameCube=1), offset=start+SETTING, before='00000000',
        required_imports=[key, *required],
        patches=[dict(offset=start+WRAPPER, before=bytes(len(code)).hex(), after=code.hex()),
                 dict(offset=at, before=before.hex(), after=after.hex())],
        source=dict(symbol=function['symbol'], sha256=DONOR_ROOM_SHA,
            reference='ACreTeam/ac-decomp@09ca8e8b5b24e6ab44047ee980cf0088ad7ecb4c:src/game/m_home.c',
            main_cell=[1,1], secondary_cell=[1,1], native_main_offset=0x35E2,
            native_secondary_offset=0x37E2, native_hook=HOOK, tail_ram=p['ram']+WRAPPER))
