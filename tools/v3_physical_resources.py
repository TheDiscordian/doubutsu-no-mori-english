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


def retire_packet_copies(rom,prior,copies):
    """Reclaim declared old startup packets with a live replacement at the same RAM.

    Each copy names its retained predecessor receipt and current replacement.
    Both hashes and RAM extents are checked, and the actual installed startup
    table must load the replacement, never the obsolete physical copy.
    """
    import struct
    from v3_asset_loader import BLOB
    records=prior['physical_resources'];verify(rom,records)
    e=prior['equipment_resources'];boot=e['surface_bootstrap']['code']
    blob=by_vrom(rom)[BLOB].extract(rom)
    at=e['blob_offset']+boot['symbols']['packets']-e['ram']
    # This API belongs to the installed shared nineteen-packet owner. Refuse an
    # unrelated startup shape instead of interpreting arbitrary words as rows.
    if boot['bytes']!=688:raise ValueError('Changed complete startup packet reader')
    live=[struct.unpack_from('>5I',blob,at+i*20)[:3] for i in range(19)]
    retired=[];seen=set()
    for old,current in copies:
        row=next((r for r in records if r['id']==old['id']),None)
        if (row is None or row['id'] in seen or any(row[k]!=old[k] for k in ('physical','bytes','sha256')) or
                sha256(rom[current['physical']:current['physical']+current['bytes']])!=current['sha256'] or
                not current['ram']<=old['ram']<old['ram']+old['bytes']<=current['ram']+current['bytes'] or
                (current['ram'],current['physical']|0x80000000,current['bytes']) not in live or
                any((physical&0x7FFFFFFF)<old['physical']+old['bytes'] and
                    old['physical']<(physical&0x7FFFFFFF)+size for _,physical,size in live)):
            raise ValueError('Old physical packet still has an active or unchecked owner')
        seen.add(row['id']);retired.append(dict(row,replaced_by=current['id'],ram=old['ram']))
    staged=bytearray(rom)
    for row in retired:staged[row['physical']:row['physical']+row['bytes']]=bytes(row['bytes'])
    retained=[r for r in records if r['id'] not in seen]
    verify(staged,retained)
    return staged,retained,retired


def grow_backwards(rom,records,identity,data):
    """Grow one owned resource into its preceding checked free space.

    Return a replacement write; the original cartridge is never modified here.
    The writer must verify the exact predecessor and the added zero-filled span.
    """
    verify(rom,records)
    matches=[r for r in records if r['id']==identity]
    if len(matches)!=1:raise ValueError('Ambiguous physical resource growth')
    old=matches[0];end=old['physical']+old['bytes'];start=end-len(data)
    if (not data or len(data)&15 or len(data)<=old['bytes'] or start<0x100000 or
            any(rom[start:old['physical']]) or
            overlaps([r for r in records if r['id']!=identity],start,end) or
            any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                for e in by_vrom(rom).values() if e.pstart!=0xFFFFFFFF)):
        raise ValueError('No checked adjacent space for complete physical resource growth')
    return dict(id=identity,physical=start,bytes=len(data),sha256=sha256(data),
        previous_physical=old['physical'],previous_bytes=old['bytes'],previous_sha256=old['sha256'])


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
