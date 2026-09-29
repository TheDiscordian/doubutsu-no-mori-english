"""Independent carried-family selection using installed shared readers and saves."""
import copy
import struct
import zlib

from aflib import by_vrom, sha256, u32
from v3_asset_loader import ROOT, BLOB
from v3_carried_runtime import TABLE, RAM
from v3_registry import CARRIED_ITEMS

FORMAT = 'AFV3-CARRIED-SELECTION-1'
READY = 0x7D  # Sign boards belong to the V4 Able Sisters/custom-design feature.


def options(image, report):
    d = report.get('equipment_resources', {}).get('carried_items', {})
    selection = d.get('optional_selection')
    if not selection:
        return {}
    p = d['packet']; raw = image[p['physical']:p['physical']+p['bytes']]
    at = TABLE-p['ram']; table = raw[at:at+d['table_bytes']]
    if (selection['format'] != FORMAT or not selection['installed'] or
            sha256(raw) != p['sha256'] or sha256(table) != d['table_sha256'] or
            struct.unpack_from('>8I', table) != (0x41464350, 1, 26, 32, READY, READY, 0, 0) or
            (d['ready_mask'], d['selected_mask']) != (READY, READY)):
        raise ValueError('Changed complete carried selection binding')
    result = {}
    if len(d['rows']) != 26:
        raise ValueError('Incomplete carried state family')
    for index, row in enumerate(d['rows']):
        fields = struct.unpack_from('>3H4BHI16s', table, 32+index*32)
        if (fields != (CARRIED_ITEMS[int(row['donor_item_id'], 16)],
                int(row['donor_item_id'], 16), CARRIED_ITEMS[int(row['parent_item_id'], 16)],
                row['family'], row['state_index'], row['native_category'], 0, row['price'],
                row['icon'], row['name'].encode('ascii').ljust(16, b' ')) or
                row['id'] != 'GAFE01-r0/item/'+row['parent_item_id'] or
                row['native_item_id'] != f'{fields[0]:04X}' or
                row['native_parent_id'] != f'{fields[2]:04X}' or
                row['ready'] != bool(READY & (1 << row['family'])) or row['selected'] != row['ready']):
            raise ValueError('Changed carried state identity or source name')
        if row['state_index'] or not READY & (1 << row['family']):
            continue
        result[row['id']] = dict(id=row['id'], name=row['name'], kind='carried',
            item_id=row['native_parent_id'], family=row['family'], dependencies=[],
            carried_mask=1 << row['family'])
    if sorted(result) != selection['identities'] or len(result) != 6:
        raise ValueError('Incomplete carried parent selections')
    return result


def masks(image, report):
    """Each physical word has one owner and a set of independent option bits."""
    rows = options(image, report)
    if not rows:
        return []
    e = report['equipment_resources']; d = e['carried_items']
    from v3_holiday_selection import location
    result = []
    for ram, members in ((TABLE+20, [dict(id=k, mask=r['carried_mask']) for k, r in rows.items()]),
            (e['holiday_items']['table_ram']+12,
             [dict(id=k, mask=r['carried_mask'] >> 2) for k, r in rows.items() if r['family'] in (2, 3)])):
        p, at = location(e, ram, 4)
        if sha256(image[p['physical']:p['physical']+p['bytes']]) != p['sha256']:
            raise ValueError('Changed carried/event selection packet')
        full = sum(r['mask'] for r in members)
        if u32(image, at) != full:
            raise ValueError('Changed carried/event selected mask')
        result.append(dict(offset=at, before=image[at:at+4].hex(), members=members))
    return result


def checksum_fields(image, report):
    if not report.get('equipment_resources', {}).get('carried_items', {}).get('optional_selection'):
        return []
    e = report['equipment_resources']; p = e['carried_items']['packet']
    boot = e['surface_bootstrap']['code']['symbols']
    at = by_vrom(image)[BLOB].pstart+e['blob_offset']+boot['holiday_festivals_crc']-e['ram']
    if u32(image, at) != p['crc32'] or zlib.crc32(image[p['physical']:p['physical']+p['bytes']]) != p['crc32']:
        raise ValueError('Changed carried startup checksum')
    return [dict(offset=at, before=image[at:at+4].hex(), start=p['physical'], length=p['bytes'])]


def update_report(image, report, enabled):
    e = report['equipment_resources']; d = e.get('carried_items', {})
    if not d.get('optional_selection'):
        return
    mask = sum(1 << r['family'] for r in d['rows'] if not r['state_index'] and r['id'] in enabled)
    d['selected_mask'] = mask
    d['optional_selection']['selected_identities'] = sorted(set(enabled) & set(d['optional_selection']['identities']))
    for r in d['rows']:
        r['selected'] = bool(mask & (1 << r['family']))
    for record, p, start in ((d, d['packet'], RAM),
            (e['holiday_items'], e['holiday_fishing']['packet'], e['holiday_items']['ram'])):
        raw = image[p['physical']:p['physical']+p['bytes']]
        at = record['table_ram']-p['ram']
        record['table_sha256'] = sha256(raw[at:at+record['table_bytes']])
        record['sha256'] = sha256(raw[start-p['ram']:start-p['ram']+record['bytes']])
    e['holiday_items']['selected'] = sum(r['selected'] for r in d['rows'] if r['family'] in (2, 3))
    d['quest']['npc']['selectable'] = True
    d['quest']['npc']['selected'] = bool(mask & 64)
    d['quest']['available'] = bool(mask & 64)
    for r in e['npc_extra']['prepared_characters'].values():
        if r.get('callback_family')=='Ev_Ghost':r['active'] = bool(mask & 64)


def install(base, prior, output, directory):
    """Admit the connected six-family batch without rebuilding any game assets."""
    from v3_holiday_selection import packets, location, refresh_receipts
    import v3_physical_resources as physical
    e = copy.deepcopy(prior['equipment_resources']); d = e['carried_items']
    npc = d['quest']['npc']; events = e['npc_extra']['events']
    if (d.get('optional_selection') or d['ready_mask'] or d['selected_mask'] or
            directory.resolve() != ROOT/d['prepared'] or
            not all(d.get(k) for k in ('actions', 'storage', 'eating', 'interactions', 'spawning')) or
            not d['paper']['quantities']['installed'] or not npc['installed'] or npc['unbound_services'] or
            not npc['registry']['independent_gate'] or not npc.get('save_services') or
            not e['holiday_items'].get('controls') or not events.get('exercise') or
            prior['save_codec']['format_version'] != 19):
        raise ValueError('Incomplete carried gameplay/save implementation')
    records = copy.deepcopy(prior['physical_resources']); physical.verify(base, records)
    payloads = {p['id']: bytearray(base[p['physical']:p['physical']+p['bytes']]) for p in packets(e)}
    def word(ram, before, after):
        p, _ = location(e, ram, 4); at = ram-p['ram']; raw = payloads[p['id']]
        if u32(raw, at) != before:
            raise ValueError('Changed inactive carried selection word')
        struct.pack_into('>I', raw, at, after)
    word(TABLE+16, 0, READY); word(TABLE+20, 0, READY)
    word(e['holiday_items']['table_ram']+12, 0, 3)
    quest = d['quest']; available = quest['availability_address']
    if available != quest['code']['symbols']['af_cw_available']:
        raise ValueError('Changed carried quest availability binding')
    ghost = [r for r in e['npc_extra']['prepared_characters'].values() if r.get('callback_family')=='Ev_Ghost']
    if len(ghost)!=1 or not ghost[0]['actor_installed']:
        raise ValueError('Missing complete Wisp character allocation')
    character = e['npc_extra']['packet']['ram']+ghost[0]['flags_offset']
    word(available, 0, 1); word(character, 0, 3)
    for row in d['rows']:
        row['ready'] = row['selected'] = bool(READY & (1 << row['family']))
    d.update(ready_mask=READY, selected_mask=READY,
        optional_selection=dict(format=FORMAT, installed=True,
            identities=sorted({r['id'] for r in d['rows'] if r['ready']}),
            selected_identities=sorted({r['id'] for r in d['rows'] if r['ready']}),
            native_gameplay_verified=False, deferred=['GAFE01-r0/item/251E']),
        pending=['ordinary combined gameplay/save verification', 'V4 Able Sisters sign-board designs'])
    e['holiday_items'].update(ready_mask=3, selected=14)
    e['holiday_items']['pending'] = ['ordinary combined gameplay/save verification']
    npc['native_services_bound'] = True
    npc['pending'] = ['ordinary gameplay and save/travel']
    d['quest']['pending'] = ['ordinary Wisp gameplay and native save/travel verification']
    for key in ('field_creatures', 'spawning'):
        d[key]['selectable'] = True
        d[key]['pending'] = ['ordinary carried-creature gameplay verification']
    # Exercise cards and cutlery need the same complete holiday providers as
    # diaries, but neither import requires selecting a diary. Wisp is independent.
    group = next(g for g in events['selection']['groups'] if g['id'] == 'diary-holidays')
    group['any_imports'] = sorted(set(group['any_imports']) | {
        r['id'] for r in d['rows'] if r['family'] in (2, 3)})
    events['selection']['groups'].append(dict(id='carried-quest',
        any_imports=[r['id'] for r in d['rows'] if r['family']==6 and not r['state_index']],
        any_behaviours=[], fields=[
            dict(ram=available, enabled=1, disabled=0, purpose='complete carried quest services'),
            dict(ram=character, enabled=3, disabled=1, purpose='optional Wisp character')]))
    refresh_receipts(e, records, payloads)
    assembled = bytearray(base)
    writes = []
    for p in packets(e):
        old = next(r for r in prior['physical_resources'] if r['id'] == p['id'])
        if old['sha256'] != p['sha256']:
            r = next(r for r in records if r['id'] == p['id'])
            raw = bytes(payloads[p['id']]); assembled[p['physical']:p['physical']+p['bytes']] = raw
            writes.append((dict(r, previous_sha256=old['sha256']), raw))
    temporary = dict(equipment_resources=e)
    update_report(assembled, temporary, d['optional_selection']['identities'])
    d['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in (
        'tools/v3_carried_selection.py', 'tools/v3_optional_composition.py',
        'tools/v3_browser_composition.py', 'experimental/imports/composer.mjs')})
    options(assembled, temporary); masks(assembled, temporary)
    warning = (prior['save_warning']+' Carried-item saves require every carried family selected when the save was written; '
        'builds with no carried-family admission (including ABI 368) cannot load them. '
        'Removing a family is not a save migration. Keep a separate V3 test save and its selection profile.')
    return e, {}, dict(physical_resources=records, save_warning=warning), writes
