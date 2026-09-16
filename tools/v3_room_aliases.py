"""Discover extra donor room representations without inventing new items.

The checked conversion functions supply ranges and parent IDs. These records
describe identity/dependencies, not implemented N64 placement or tool gameplay.
"""
import struct

from aflib import sha256, u32


FUNCTIONS = {
    'place': (0x760E4, 'mRmTp_Item1ItemNo2FtrItemNo_AtPlayerRoom', 640,
              '5228a779089eca94c3f751a814e169f74ff085a57626673c86d7d789fadd6c66'),
    'pickup': (0x76364, 'mRmTp_FtrItemNo2Item1ItemNo', 664,
               'a948f3ad02dcf0d9f967363bb22203091447edbb416345498564bb18efda353e'),
    'item_to_index': (0x775D0, 'mRmTp_FtrItemNo2FtrIdx', 68,
                      '78f4e2909f49abfd37c1e8617add178f1983c5183c5e3b43b7aeab89a4e81155'),
    'index_to_item': (0x77614, 'mRmTp_FtrIdx2FtrItemNo', 72,
                      'edf357ca53e07880d074757d2ea0dfb42ae6de89bdd48523565a1bf620797e4d'),
}
# Instruction locations in the complete reviewed functions, not item records.
# Each range expands automatically; the inverse must agree independently.
RANGES = (
    ('balloon', 0x150, 0x158, 0x16C, 0x134, 0x144, 0x15C, True, False),
    ('diary', 0x184, 0x18C, 0x19C, 0x16C, 0x174, 0x184, False, True),
    ('fan', 0x1AC, 0x1B4, 0x1C8, 0x198, 0x1A8, 0x1C0, True, True),
    ('pinwheel', 0x1D8, 0x1E0, 0x1F4, 0x1D4, 0x1E4, 0x1FC, True, True),
    ('golden-tool', 0x204, 0x20C, 0x220, 0x210, 0x220, 0x238, True, True),
    ('tool', 0x230, 0x238, 0x24C, 0x24C, 0x25C, 0x274, True, True),
)


def discover(source):
    """Bind both conversions, including rotations and worn-axe canonicalisation."""
    code, evidence = {}, {}
    for role, (address, symbol, size, digest) in FUNCTIONS.items():
        raw, receipt = source.function(address)
        if (receipt['symbol'] != symbol or len(raw) != size or sha256(raw) != digest
                or receipt['relocations']):
            raise ValueError('Changed donor room-alias function: ' + role)
        code[role], evidence[role] = raw, receipt

    def immediate(role, at, opcode):
        word = u32(code[role], at)
        if word >> 26 != opcode:
            raise ValueError('Changed room-alias immediate instruction')
        return word & 0xFFFF

    split = immediate('index_to_item', 0x18, 11)
    lower = immediate('index_to_item', 0x38, 14)
    upper = immediate('index_to_item', 0x24, 14)
    if (immediate('item_to_index', 0x34, 14) != split or
            -struct.unpack_from('>h', code['item_to_index'], 0x22)[0] != lower or
            -struct.unpack_from('>h', code['item_to_index'], 0x2E)[0] != upper):
        raise ValueError('Donor furniture index conversions disagree')

    def item_number(index):
        return lower + index * 4 if index < split else upper + (index - split) * 4

    rows = {}
    parents = set()
    for kind, lo, hi, target, back_lo, back_hi, back_parent, indexed, restricted in RANGES:
        first = immediate('place', lo, 10)
        last = immediate('place', hi, 10)
        destination = immediate('place', target, 14)
        inverse_first = immediate('pickup', back_lo, 11 if indexed else 10)
        inverse_last = immediate('pickup', back_hi, 11 if indexed else 10)
        if (last < first or last-first >= 16 or inverse_first != destination or
                inverse_last != destination + (last-first if indexed else (last-first)*4+3) or
                immediate('pickup', back_parent, 14) != first):
            raise ValueError('Donor room-alias ranges disagree: ' + kind)
        symbol = 'itemName_dummy' if kind == 'diary' else 'itemName_tool'
        names = source.raw(symbol)
        for i, parent in enumerate(range(first, last + 1)):
            display = item_number(destination+i) if indexed else destination+i*4
            if display in rows or parent in parents or display & 3:
                raise ValueError('Duplicate or non-canonical room alias')
            start = (parent & 255) * 16
            name_raw = names[start:start+16]
            if len(name_raw) != 16:
                raise ValueError('Room-alias parent escapes donor name table')
            name = name_raw.decode('ascii').rstrip(' ')
            if not name or name in ('DUMMY', 'dummy'):
                raise ValueError('Room alias has no actual parent name')
            rows[display] = dict(kind='room-display-alias', category=kind,
                display_item_id=f'{display:04X}', rotation_ids=[f'{display+r:04X}' for r in range(4)],
                parent_id=f'GAFE01-r0/item/{parent:04X}', parent_item_id=f'{parent:04X}',
                parent_name=name, parent_name_symbol=symbol, parent_name_index=parent & 255,
                parent_name_sha256=sha256(name_raw),
                placement_inputs=[f'{parent:04X}'], pickup_item_id=f'{parent:04X}',
                suppressed_by_no_convert_tools=restricted, native_identity='unreviewed',
                runtime_installed=False)
            parents.add(parent)

    # Donor placement loses the axe's wear-state identity; record that actual
    # asymmetry instead of treating seven worn axes as seven new furnishings.
    first = immediate('place', 0x25C, 10)
    last = immediate('place', 0x264, 10)
    target = immediate('place', 0x26C, 14)
    if first > last or last-first >= 16 or target not in rows or rows[target]['category'] != 'tool':
        raise ValueError('Changed worn-tool room alias')
    states = {f'{i:04X}' for i in range(first, last+1)}
    if states & {f'{i:04X}' for i in parents}:
        raise ValueError('Worn-tool states overlap canonical parent identities')
    rows[target]['placement_inputs'] += sorted(states)
    rows[target]['pickup_canonicalises_state'] = True
    return dict(format='AFV3-DONOR-ROOM-ALIASES-1', functions=evidence,
                scope='extra room representations: balloons, diaries, fans, pinwheels, and tools',
                rows=[rows[item] for item in sorted(rows)])


def pending_reason(alias):
    return (f"Room display of {alias['parent_name']} ({alias['parent_item_id']}); "
            'parent-item support and room placement/pickup integration are required, '
            'not a separate furniture acquisition route.')


def annotate_inventory(items, aliases):
    """Link existing donor inventory records; add no second selectable identity."""
    by_id = {row['donor_item_id']: row for row in items}
    if len(by_id) != len(items):
        raise ValueError('Duplicate donor inventory identity')
    for alias in aliases['rows']:
        display = by_id.get(alias['display_item_id'])
        parent = by_id.get(alias['parent_item_id'])
        if display is None or parent is None or parent['name_sha256'] != alias['parent_name_sha256']:
            raise ValueError('Room alias does not bind complete donor inventory')
        if display['selectable'] or parent['selectable']:
            raise ValueError('Research alias classification cannot enable imports')
        display.update(status='room_display_alias_pending_parent_support',
                       room_alias=alias, reason=pending_reason(alias))
        displays = parent.setdefault('room_display_ids', [])
        if alias['display_item_id'] not in displays:
            displays.append(alias['display_item_id'])
        for state in alias['placement_inputs'][1:]:
            if state not in by_id:
                raise ValueError('Missing donor worn-tool state')
            by_id[state].update(status='state_of_parent_item', canonical_parent_id=alias['parent_id'],
                               room_display_ids=[alias['display_item_id']])
