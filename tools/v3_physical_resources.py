"""Checked ROM-only resources outside the full native DMA directory."""
from aflib import by_vrom, sha256

SOURCES = ('tools/v3_physical_resources.py',)


def verify(rom, records):
    """Treat even zero-filled bytes inside a declared resource as occupied."""
    occupied = [(e.pstart, e.pend or e.pstart+e.size) for e in by_vrom(rom).values()
                if e.pstart != 0xFFFFFFFF]
    names = set()
    for row in records:
        start, size = row['physical'], row['bytes']
        if (not isinstance(row['id'], str) or row['id'] in names or
                type(start) is not int or type(size) is not int or
                start & 15 or size & 15 or not 0 < size or
                not 0x100000 <= start < start+size <= len(rom) <= 0x4000000 or
                any(a < start+size and start < b for a, b in occupied) or
                sha256(rom[start:start+size]) != row['sha256']):
            raise ValueError('Changed, overlapping, or invalid physical ROM resource')
        occupied.append((start, start+size))
        names.add(row['id'])


def overlaps(records, start, end):
    return any(r['physical'] < end and start < r['physical']+r['bytes'] for r in records)


def allocate(rom, records, data, name, *, best_fit=False):
    verify(rom, records)
    if len(rom) != 0x4000000 or not data or len(data) & 15 or any(r['id'] == name for r in records):
        raise ValueError('Physical resource needs complete aligned data and a new identity')
    # Allocate downward from the cartridge end. Shared owner appends keep their
    # ordinary lower tail and explicitly skip these independent reservations.
    occupied = [(e.pstart, e.pend or e.pstart+e.size) for e in by_vrom(rom).values()
                if e.pstart != 0xFFFFFFFF]
    occupied += [(r['physical'], r['physical']+r['bytes']) for r in records]
    limit = len(rom); candidates=[]
    for first, last in sorted(occupied, reverse=True)+[(0, 0)]:
        start = (limit-len(data)) & ~15
        if start >= max(last, 0x100000) and not any(rom[start:limit]):
            row=dict(id=name, physical=start, bytes=len(data), sha256=sha256(data))
            if not best_fit:return row
            candidates.append((limit-max(last,0x100000),row))
        limit = min(limit, first)
    if candidates:return min(candidates,key=lambda pair:pair[0])[1]
    raise ValueError('No checked cartridge space for the complete physical resource')
