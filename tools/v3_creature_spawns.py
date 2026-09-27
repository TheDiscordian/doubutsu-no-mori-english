"""Complete donor fish calendars and native identity-preserving spawn records.

This is consumed by the fish category, not a per-species installer. The packed
calendar has no host/REL pointers; its offsets are checked before use on N64.
"""
import struct

from aflib import by_vrom, sha256, u32
from v3_creature_field import table
from v3_creature_items import source_records

MAGIC = 0x41465350
HEADER = 32
CALENDARS = 3 * 24 * 4 + 8
CAPACITY = 64
NATIVE_VROM, NATIVE_RAM = 0x8253C0, 0x8092DBC0


def calendars(source, native_rom):
    """Follow every half-month/time list; keep official weights and locations."""
    parents, _ = source_records(source)
    mapping = {r['source_index']: (int(r['item_id'], 16) & 255) + 4
               for r in parents if r['category'] == 'fish'}
    if len(mapping) != 9 or mapping.get(1) != 44:
        raise ValueError('Changed complete fish parent identities')
    mapping.update({i: i for i in range(32) if i not in mapping})
    mapping[44] = 35  # Source coastal salmon, not another carried species.
    receipts = {}

    def read(at, expected=None):
        name, start, n = source.containing(at, exact=True)
        if expected is not None and n != expected:
            raise ValueError('Changed complete fish calendar symbol: ' + name)
        raw, receipt = table(source, start, n, name)
        receipts[start] = receipt
        return raw, receipt['pointers']

    def lists(at):
        raw, refs = read(at, 32)
        result = []
        for time in range(4):
            p = time * 8
            count = raw[p]
            if raw[p+1:p+8] != bytes(7) or count > 32:
                raise ValueError('Changed fish time-list layout')
            target = refs.get(at+p+4)
            if not count:
                if target is not None:
                    raise ValueError('Unexpected empty fish list pointer')
                result.append([])
                continue
            if target is None:
                raise ValueError('Missing fish time-list pointer')
            values, dependencies = read(target, count*4)
            if dependencies:
                raise ValueError('Unexpected relocation inside spawn rows')
            rows = []
            for species, area, weight in struct.iter_unpack('>hBB', values):
                if species not in mapping or not 0 <= area <= 6 or not weight:
                    raise ValueError('Unsupported fish spawn identity, area, or weight')
                rows.append((mapping[species], area, weight))
            result.append(rows)
        if set(refs) != {at+t*8+4 for t in range(4) if raw[t*8]}:
            raise ValueError('Unexpected fish calendar pointer')
        return result

    schedule = []
    for name in ('r_month', 's_month', 'p_month'):
        at, n = source.symbol(name)
        raw, refs = read(at, 96)
        if raw != bytes(96):
            raise ValueError('Non-pointer fish month calendar')
        for term in range(24):
            target = refs.get(at+term*4)
            # The source has null pond lists outside their active seasons.
            schedule.extend(lists(target) if target is not None else [[] for _ in range(4)])
        if set(refs) - set(range(at, at+96, 4)):
            raise ValueError('Unexpected month calendar relocation')
    for name in ('f_event', 'f_island'):
        schedule.extend(lists(source.symbol(name)[0]))
    if len(schedule) != CALENDARS:
        raise ValueError('Incomplete full fish calendar')

    # Herabuna exists in N64 and is not the source brook trout. Preserve its
    # original monthly/time weights independently, including late September.
    owner = by_vrom(native_rom)[NATIVE_VROM].extract(native_rom)
    if sha256(owner) != 'a5673915b8af4a32e29368edaa6e0ffe0a63e59bcd6aef659ef918a7fb67b13d':
        raise ValueError('Changed native fish spawn owner')
    herabuna = []
    for term in range(24):
        for time in range(4):
            at = (0x809303A0 if term == 17 else 0x80930200+(term//2)*32) - NATIVE_RAM + time*8
            count, pointer = owner[at], u32(owner, at+4)
            start = pointer-NATIVE_RAM
            if count > 20 or not 0 <= start <= start+count*8 <= len(owner):
                raise ValueError('Unbounded native monthly fish list')
            found = [(area, weight) for species, area, weight, pad in
                     struct.iter_unpack('>IBBH', owner[start:start+count*8]) if species == 1]
            if len(found) != 1 or found[0][0] != 0:
                raise ValueError('Changed native herabuna identity/location')
            herabuna.append(found[0][1])

    env, _ = read(source.symbol('env_rate_table$517')[0], 28)
    transition, _ = read(source.symbol('rate$721')[0], 20)
    if struct.unpack('>7f', env) != (0.5, 0.75, 0.875, 1, 1, 1, 1):
        raise ValueError('Changed source environment weights')
    if transition != struct.pack('>5f', *(n/6 for n in (5, 4, 3, 2, 1))):
        raise ValueError('Changed source five-day transition weights')
    packed = bytearray(HEADER + CALENDARS*4)
    unique = {}
    for index, rows in enumerate(schedule):
        key = tuple(rows)
        if key not in unique:
            unique[key] = len(packed)
            for row in rows:
                packed.extend(struct.pack('>HBB', *row))
        struct.pack_into('>HH', packed, HEADER+index*4, unique[key], len(rows))
    herabuna_at = len(packed)
    packed.extend(bytes(herabuna))
    env_at = len(packed)
    packed.extend(env)
    transition_at = len(packed)
    packed.extend(transition)
    struct.pack_into('>8I', packed, 0, MAGIC, 1, len(packed), CALENDARS,
                     herabuna_at, env_at, transition_at, CAPACITY)
    max_rows = max(map(len, schedule)) * 2 + 2  # Both terms and native herabuna.
    if max_rows > CAPACITY or len(packed) > 65535:
        raise ValueError('Complete fish calendar exceeds runtime bounds')
    callbacks = [source.function(at)[1] for at in
        (0x12950C, 0x129574, 0x1296A8, 0x129780, 0x129B4C, 0x129BCC,
         0x129CB0, 0x129D38, 0x129D8C, 0x129E08, 0x129EC4, 0x129F18,
         0x129F70, 0x12A150, 0x12A1F8, 0x12A270, 0x12A2F0, 0x12A338,
         0x12A374, 0x12A490, 0x12A544, 0x12A6A0)]
    return bytes(packed), dict(format='AFV3-FISH-CALENDARS-1', bytes=len(packed),
        sha256=sha256(packed), calendars=schedule, native_herabuna_weights=herabuna,
        source_tables=list(receipts.values()), source_functions=callbacks,
        native_owner_sha256=sha256(owner), maximum_rows=max_rows,
        actor_mapping=mapping, installed=False)
