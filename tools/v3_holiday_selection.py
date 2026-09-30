"""Connect installed diary/event providers to optional composition as one category."""
import copy
import struct
import zlib

from aflib import by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT
from v3_import_storage import ROWS, ITEMS

FORMAT = 'AFV3-HOLIDAY-SELECTION-1'
SOURCES = ('tools/v3_holiday_selection.py', 'tools/v3_diary_selection.py',
    'tools/v3_holiday_active.py', 'tools/v3_creature_choices.py', 'tools/v3_optional_composition.py',
    'tools/v3_browser_composition.py', 'experimental/imports/composer.mjs', 'tools/v3_furniture_install.py')
CALENDAR = dict(id='holiday-calendar', name='Holiday calendar', binding='calendar_mode',
    symbol='af_holiday_calendar_choice', scope='Town events and diary calendars',
    description='N64 retains the original dates for shared holidays. GameCube uses the English GameCube dates. Imported holidays and their participants accompany selected diaries in either mode; original-only celebrations remain.')


def packets(e):
    n = e['npc_extra']
    return [n['packet'], e['holiday_fishing']['packet'], n['events']['sky']['packet'],
            n['events']['festivals']['packet']]+(
            [e['carried_items']['quest']['packet']] if e.get('carried_items', {}).get('quest') else [])


def location(e, ram, size):
    matches = [p for p in packets(e) if p['ram'] <= ram and ram+size <= p['ram']+p['bytes']]
    if len(matches) != 1:
        raise ValueError('Event binding has no unique installed packet')
    p = matches[0]
    return p, p['physical']+ram-p['ram']


def groups(image, report):
    """Declarative shared activation; never enable events for unrelated imports."""
    e = report.get('equipment_resources', {})
    selection = e.get('npc_extra', {}).get('events', {}).get('selection')
    if selection is None:
        return []
    if selection['format'] != FORMAT or not selection['installed']:
        raise ValueError('Unknown installed event selection')
    result = copy.deepcopy(selection['groups'])
    checked = set()
    for group in result:
        for field in group['fields']:
            p, at = location(e, field['ram'], 4)
            if p['id'] not in checked:
                if sha256(image[p['physical']:p['physical']+p['bytes']]) != p['sha256']:
                    raise ValueError('Changed complete event selection packet')
                checked.add(p['id'])
            if u32(image, at) != field['enabled']:
                raise ValueError('Changed installed event activation field')
            field.update(offset=at, before=image[at:at+4].hex())
    return result


def pipeline_allowed(group, report):
    """Retain complete independent gift/diary and spirit providers."""
    from v3_holiday_acquisition import providers_installed
    from v3_carried_selection import quest_items
    return ((group['id']=='diary-holidays' and providers_installed(report)) or
            (group['id']=='carried-quest' and bool(quest_items(report))))


def active(group, enabled, behaviours, *, scope='development', report=None):
    if scope == 'v3-pipeline' and not pipeline_allowed(group, report or {}):
        return False
    return bool(set(group['any_imports']) & set(enabled)) or any(
        behaviours.get(r['id']) == r['value'] for r in group['any_behaviours'])


def checksum_fields(image, report):
    e = report.get('equipment_resources', {})
    if not e.get('npc_extra', {}).get('events', {}).get('selection'):
        return []
    start = by_vrom(image)[BLOB].pstart+e['blob_offset']
    symbols = e['surface_bootstrap']['code']['symbols']
    # Fishing already has its CRC in creature_choices. These two additional
    # packets contain NPC flags, participant admission, and the calendar choice.
    result = []
    for p, name in ((e['npc_extra']['packet'], 'npc_extra_crc'),
                    (e['npc_extra']['events']['sky']['packet'], 'holiday_sky_crc')):
        at = start+symbols[name]-e['ram']
        if u32(image, at) != p['crc32'] or zlib.crc32(image[p['physical']:p['physical']+p['bytes']]) != p['crc32']:
            raise ValueError('Changed optional event startup checksum')
        result.append(dict(offset=at, before=image[at:at+4].hex(), start=p['physical'], length=p['bytes']))
    return result


def refresh_receipts(e, records, payloads):
    """Preserve all shared packet and loaded-module identities after selection."""
    n = e['npc_extra']; events = n['events']
    for p in packets(e):
        if p['id'] not in payloads:
            continue
        data = payloads[p['id']]
        p.update(sha256=sha256(data), crc32=zlib.crc32(data))
        next(r for r in records if r['id'] == p['id'])['sha256'] = p['sha256']
    prefix = events['sky']['packet']; data = payloads.get(prefix['id'])
    if data is not None:
        for name in ('participants', 'exercise', 'calendar'):
            events[name]['packet'] = copy.deepcopy(prefix)
        part = events['participants']; at = part['loaded_code']['ram']-prefix['ram']
        part['code']['sha256'] = sha256(data[at:at+part['code']['bytes']])
        part['loaded_code']['sha256'] = part['code']['sha256']
        for batch in (*n.get('source_batches', []), n['variants'], events['exercise']):
            at = batch.get('ram', 0)-prefix['ram']
            if 0 <= at and at+batch['bytes'] <= len(data):
                batch['sha256'] = sha256(data[at:at+batch['bytes']])
        calendar = events['calendar']; at = calendar['ram']-prefix['ram']
        calendar['code']['sha256'] = sha256(data[at:at+calendar['code']['bytes']])
    e['holiday_state']['packet'] = copy.deepcopy(e['holiday_fishing']['packet'])
    carried = e.get('carried_items')
    if carried:
        carried['packet'] = copy.deepcopy(events['festivals']['packet'])
        quest = carried.get('quest')
        if quest and quest['packet']['id'] in payloads:
            p = quest['packet']; data = payloads[p['id']]
            for target in (carried['spawning'], carried['paper'].get('quantities'), quest.get('npc'), quest.get('rewards')):
                if target:target['packet'] = copy.deepcopy(p)
            if e.get('bank'):e['bank']['packet']=copy.deepcopy(p)
            at = quest['ram']-p['ram']
            quest['code']['sha256'] = sha256(data[at:at+quest['code']['bytes']])
            rewards=quest.get('rewards')
            if rewards:
                at=rewards['code']['ram']-p['ram']
                rewards['code']['sha256']=sha256(data[at:at+rewards['code']['bytes']])


def update_report(image, blob, report, selection):
    e = report['equipment_resources']; n = e.get('npc_extra', {})
    contract = n.get('events', {}).get('selection')
    if not contract:
        return
    enabled = set(selection['enabled'])
    states = {g['id']: active(g, enabled, selection.get('behaviours', {}),
                             scope=selection.get('scope', 'development'),report=report) for g in contract['groups']}
    contract['resolved_groups'] = states
    on = states['diary-holidays']
    n['record']['selected'] = n['lifecycle']['active'] = on
    n['events']['dispatch']['actor_active'] = on
    for name in ('participants', 'exercise', 'festivals'):
        n['events'][name]['registry']['enabled'] = on
    n['events']['participants']['events_active'] = n['events']['sky']['events_active'] = on
    live = e['holiday_fishing']['live']
    live['actors_active'] = live['service_admission'] = live['mail']['enabled'] = on
    e['holiday_fishing']['live_event_bound'] = on
    contract['calendar']['resolved'] = selection.get('behaviours', {}).get('holiday-calendar', 'N64')
    refresh_receipts(e, report['physical_resources'],
        {p['id']:image[p['physical']:p['physical']+p['bytes']] for p in packets(e)})
    d = e['diary_items']; d['selected'] = len(enabled & {r['id'] for r in d['rows']})
    for row, profile in zip(d['rows'], d['profiles'], strict=True):
        row['selected'] = profile['selected'] = row['id'] in enabled
        slot = profile['runtime_index']-1024
        profile['profile_record_sha256'] = sha256(blob[ROWS+slot*80:ROWS+(slot+1)*80])
        profile['item_record_sha256'] = sha256(blob[ITEMS+slot*32:ITEMS+(slot+1)*32])


def install(base, prior, blob, core, output):
    """Admit the complete installed provider family and all sixteen diary styles."""
    del core
    from v3_diary_selection import bindings
    from v3_holiday_active import refresh_dispatch
    from v3_npc_registry import TABLE
    import v3_physical_resources as physical
    rows = bindings(base, prior)
    e = copy.deepcopy(prior['equipment_resources']); n = e['npc_extra']; events = n['events']
    if (len(rows) != 16 or not n.get('optional_dialogue', {}).get('installed') or
            events.get('selection') or not events['festivals']['native_services_bound'] or
            events['participants']['unbound_services'] or
            not e['holiday_fishing']['live']['mail']['installed']):
        raise ValueError('Incomplete connected diary/event implementation')
    records = copy.deepcopy(prior['physical_resources']); physical.verify(base, records)
    work = output/'event-selection'; work.mkdir()
    write = refresh_dispatch(base, n, records, work/'dispatcher', {},
                             events['dispatch']['provider_defines'])
    payloads = {p['id']: bytearray(base[p['physical']:p['physical']+p['bytes']]) for p in packets(e)}
    payloads[n['packet']['id']] = bytearray(write[1])

    def read(ram, size):
        p, _ = location(e, ram, size)
        return payloads[p['id']][ram-p['ram']:ram-p['ram']+size]

    fields = []
    def enable(ram, before, value, disabled, label):
        p, _ = location(e, ram, 4); at = ram-p['ram']
        data = payloads[p['id']]
        if u32(data, at) != before:
            raise ValueError('Changed event activation predecessor: '+label)
        struct.pack_into('>I', data, at, value)
        fields.append(dict(ram=ram, enabled=value, disabled=disabled, purpose=label))

    # Validate the actual native descriptors/callbacks before opening allocation.
    table = n['packet']['ram']+TABLE
    if struct.unpack('>4I', read(table, 16)) != (0x41464E58, 1, 5, 44):
        raise ValueError('Incomplete special-character directory')
    special_names = set()
    for i in range(5):
        ram = table+16+44*i; row = read(ram, 44)
        name, profile = struct.unpack_from('>HH', row)
        descriptor = u32(row, 24); actor = u32(read(descriptor, 32), 20)
        native = read(actor, 36)
        callbacks = struct.unpack_from('>5I', native, 16)
        # Tortimer's native NPC constructor installs its drawing callback from
        # the complete Ctor record; its ActorProfile drawing slot stays null.
        if name in (0xD090, 0xD092):
            symbols = n['lifecycle']['code']['symbols']
            valid_callbacks = callbacks == tuple(symbols['af_holiday_npc_'+key] if key else 0
                for key in ('ctor', 'dtor', 'init', None, 'save'))
        else:
            valid_callbacks = all(callbacks[:4])
        if (struct.unpack_from('>H', native)[0] != profile or
                struct.unpack_from('>H', native, 8)[0] != name or
                u32(native, 12) != u32(row, 8) or not valid_callbacks):
            raise ValueError('Incomplete actual special-character lifecycle')
        special_names.add(name)
        enable(ram+4, 0, 3, 1, f'optional special character {name:04X}')
    if special_names != {0xD090, 0xD091, 0xD092, 0xD0AE, 0xD0B3}:
        raise ValueError('Changed complete event character set')

    # The current complete registry supersedes the smaller early preparations.
    symbols = events['festivals']['code']['symbols']
    count = events['festivals']['registry']['owner_count']
    names = {0xD074, 0xD03D}; profiles = set()
    for i in range(count):
        r = struct.unpack('>4H4B2I', read(symbols['af_hp_records']+20*i, 20))
        native = read(r[8], 36)
        size = u32(native, 12)
        if (not all(struct.unpack_from('>4I', native, 16)) or not 372 <= size <= 2400 or
                (r[5] and (r[6] != 3 or size < 2364)) or
                (not r[5] and not (r[6] == 7 or r[6] == 4 and size == 372))):
            raise ValueError('Incomplete actual participant lifecycle')
        names.update(range(r[0], r[0]+r[5])); profiles.add(struct.unpack_from('>H', native)[0])
    decoration = events['dispatch']['bindings']['af_decor_actor_records']
    for i in range(18):
        row = struct.unpack('>6H5I', read(decoration+32*i, 32))
        if not all(row[7:]) or row[6] & ~31:
            raise ValueError('Incomplete complete decoration providers')
        names.add(row[0])
    code = events['dispatch']['code']['symbols']
    need_count = u32(read(code['af_holiday_identity_need_count'], 4), 0)
    effects = {p['source_id'] for p in events['sky']['source']['profiles']} | {118}
    for i in range(need_count):
        kind, source = struct.unpack('>2H', read(code['af_holiday_identity_needs']+4*i, 4))
        if source not in (names if kind == 0 else profiles if kind == 1 else effects if kind == 2 else set()):
            raise ValueError(f'Unbound complete event dependency: {kind}/{source:04X}')
    enable(symbols['af_hp_available'], 0, 1, 0, 'complete holiday participants')
    services = events['dispatch']['bindings']['af_holiday_decoration_ready']
    if services != e['holiday_fishing']['live']['code']['symbols']['af_hf_services_ready'] or not all(
            struct.unpack('>18I', read(services+4, 72))):
        raise ValueError('Incomplete shared event service directory')
    enable(services, 7, 31, 7, 'fishing and Harvest services')

    d = e['diary_items']
    for r, p in zip(d['rows'], d['profiles'], strict=True):
        row = rows[r['id']]; at = row['enable_offset']; slot = row['display_runtime_index']-1024
        if blob[ITEMS+slot*32+7] != 0:
            raise ValueError('Changed inactive diary metadata')
        struct.pack_into('>I', blob, at, 1); blob[ITEMS+slot*32+7] = 1
        blob[0x20+row['profile_byte']] |= row['profile_mask']
        r.update(ready=True, selected=True); p['selected'] = True
        p['profile_record_sha256'] = sha256(blob[ROWS+slot*80:ROWS+(slot+1)*80])
        p['item_record_sha256'] = sha256(blob[ITEMS+slot*32:ITEMS+(slot+1)*32])
    d.update(selected=16, pending=['ordinary shop stock', 'native diary UI/save verification'])
    events['selection'] = dict(format=FORMAT, installed=True, native_execution_verified=False,
        groups=[dict(id='diary-holidays', any_imports=sorted(rows), any_behaviours=[
            dict(id='holiday-calendar', value='GameCube'), dict(id='tournament-measurements', value='GameCube')],
            fields=fields)], calendar=dict(CALENDAR, ram=events['calendar']['code']['symbols'][CALENDAR['symbol']],
                default='N64', values=dict(N64=0, GameCube=1)),
        actual_owner_requirements=need_count, saved_format_changed=False)
    n.update(actor_callbacks_bound=True); n['record'].update(implemented=True, selected=True)
    n['lifecycle']['active'] = True
    events['calendar'].update(actor_admission_bound=True, choice_exposed=True)
    events['dispatch']['actor_active'] = True
    for family in ('participants', 'exercise', 'festivals'):
        events[family]['registry']['enabled'] = True
    events['participants']['events_active'] = events['sky']['events_active'] = True
    live = e['holiday_fishing']['live']
    live.update(service_admission=True, actors_active=True); live['mail']['enabled'] = True
    e['holiday_fishing']['live_event_bound'] = True
    refresh_receipts(e, records, payloads)
    writes = []
    for p in packets(e):
        old = next(r for r in prior['physical_resources'] if r['id'] == p['id'])
        if old['sha256'] != p['sha256']:
            r = next(r for r in records if r['id'] == p['id'])
            writes.append((dict(r, previous_sha256=old['sha256']), bytes(payloads[p['id']])))
    saved = copy.deepcopy(prior['save_runtime'])
    saved.update(profile_hex=blob[0x20:0xE0].hex(), profile_sha256=sha256(blob[0x20:0xE0]))
    n['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return e, {}, dict(physical_resources=records, save_runtime=saved), writes
