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


def insect_calendars(source):
    """Extract the whole insect schedule, extras, and group sizes from the REL.

    Type 41 is the source's explicit no-spawn weight, not an animal. Type 40
    belongs to Wisp's event and is not silently added to ordinary populations.
    Island lists are retained without inventing an island in the N64 town.
    """
    from v3_creature_field import named_table
    receipts = {}

    def read(name, size):
        raw, receipt = named_table(source, name, size)
        receipts[receipt['offset']] = receipt
        return raw, receipt

    schedule = []
    for name, count in (('l_insect_month', 72), ('l_insect_island', 6)):
        raw, receipt = read(name, count*8)
        at = receipt['offset']; refs = receipt['pointers']
        if set(refs) != set(range(at+4, at+count*8, 8)):
            raise ValueError('Incomplete insect calendar pointers')
        for i in range(count):
            size = raw[i*8]
            if raw[i*8+1:i*8+8] != bytes(7) or not 1 <= size <= 21:
                raise ValueError('Changed insect time-list layout')
            name2, start, n = source.containing(refs[at+i*8+4], exact=True)
            if n != size*8:
                raise ValueError('Changed complete insect spawn rows')
            rows, row_receipt = read(name2, n)
            if row_receipt['pointers']:
                raise ValueError('Unexpected pointer in insect spawn row')
            values = []
            for actor, area, weight, pad in struct.iter_unpack('>IBBH', rows):
                if (actor > 41 or actor == 40 or area > 13 or not weight or pad or
                        (actor == 41) != (area == 13)):
                    raise ValueError('Changed insect identity/area/weight')
                values.append((actor, area, weight))
            schedule.append(values)
    extra, _ = read('additional_data$559', 36)
    extras = list(struct.iter_unpack('>IB3xf', extra))
    if extras != [(38, 8, 1.0), (38, 9, 1.0), (28, 9, 1.0)]:
        raise ValueError('Changed ant/cockroach food spawns')
    birth, _ = read('l_insect_birth_sum', 82)
    if list(struct.iter_unpack('>BB', birth)) != [
            (6, 3) if i in (10, 27) else (1, 0) for i in range(41)]:
        raise ValueError('Changed complete insect group sizes')
    packed = bytearray(32+78*4)
    unique = {}
    for i, rows in enumerate(schedule):
        key = tuple(rows)
        if key not in unique:
            unique[key] = len(packed)
            for row in rows:
                packed.extend(struct.pack('>HBB', *row))
        struct.pack_into('>HH', packed, 32+i*4, unique[key], len(rows))
    extra_at = len(packed)
    for actor, area, weight in extras:
        packed.extend(struct.pack('>HBB', actor, area, int(weight)))
    birth_at = len(packed); packed.extend(birth)
    struct.pack_into('>8I', packed, 0, 0x41464953, 1, len(packed), 78,
                     extra_at, birth_at, 41, CAPACITY)
    maximum = max(len(schedule[m*6+t])+len(schedule[((m+1)%12)*6+t])+3
                  for m in range(12) for t in range(6))
    if maximum > CAPACITY or len(packed) > 65535:
        raise ValueError('Insect schedule exceeds shared plan capacity')
    callbacks = [source.function(at)[1] for at, names in source.functions.items()
                 if any(name.startswith('aSOI_') for name, _ in names)]
    return bytes(packed), dict(format='AFV3-INSECT-CALENDARS-1', bytes=len(packed),
        sha256=sha256(packed), calendars=schedule, additional_spawns=extras,
        group_sizes=list(struct.iter_unpack('>BB', birth)), maximum_rows=maximum,
        source_tables=list(receipts.values()), source_functions=callbacks,
        installed=False)


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
