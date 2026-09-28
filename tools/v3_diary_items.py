"""Install shared carried readers/artwork for the entire diary category.

This continues the installed diary menus and storage. It does not enable styles
before room artwork, catalogue/scoring, and the other consumers are connected.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, MODULE_RAM, compile_part
from v3_category_runtime import rebase_art
from v3_console_disk_install import reservations
from v3_diaries import discover
from v3_diary_install import GUARD, checked_file
from v3_import_storage import jump
from v3_registry import DIARY_PARENT_REGISTRY_VERSION, diary_parent_identity
import v3_physical_resources as physical

RAM, SIZE, TABLE, ICON, ART = 0x806E0000, 0x4000, 0x2000, 0x2300, 0x2600
SOURCES = ('tools/v3_diary_items.py', 'tools/v3_registry.py', 'tools/v3_furniture_install.py',
    'tools/v3_room_goods.py', 'tools/v3_asset_loader.py', 'tools/v3_creature_items.py',
    'overlays/v3/diary_items.c', 'overlays/v3/diary_items.h', 'overlays/v3/diary_items.ld',
    'overlays/v3/creature_icon.S', 'overlays/v3/item_categories.c',
    'overlays/v3/diary_room.c', 'overlays/v3/surface_bootstrap.c',
    'tools/v3_furniture_capacity.py', 'translations/provenance.json')


def records(source):
    prepared = discover(source)
    if source.raw('item1_B_tableNo') != bytes([17])*16:
        raise ValueError('Changed complete donor diary category table')
    rows = []
    for style, r in enumerate(prepared['rows']):
        donor = int(r['parent_item_id'], 16)
        if donor != 0x2B00+style or r['display_item_id'] != f'{0x30FC+4*style:04X}':
            raise ValueError('Changed complete diary identity relationship')
        rows.append(dict(id=r['parent_id'], donor_item_id=r['parent_item_id'],
            item_id=f'{diary_parent_identity(donor):04X}', display_item_id=r['display_item_id'],
            style=style, name=r['parent_name'], name_sha256=r['parent_name_sha256'],
            name_source_symbol=r['parent_name_symbol'], name_source_index=r['parent_name_index'],
            price=r['price'], native_category=44, source_category=17, source=r,
            ready=False, selected=False))
    return rows, prepared


def encode(rows):
    if len(rows) != 16:
        raise ValueError('Diary readers require the entire fixed category')
    table = bytearray(struct.pack('>4I', 0x41464449, 1, 16, 24))
    for style, r in enumerate(rows):
        name = r['name'].encode('ascii').ljust(16, b' ')
        item = diary_parent_identity(int(r['donor_item_id'], 16))
        if (r['style'] != style or item != 0x2B10+style or r['item_id'] != f'{item:04X}' or
                r['display_item_id'] != f'{0x30FC+style*4:04X}' or
                len(name) != 16 or sha256(name) != r['name_sha256'] or r['native_category'] != 44):
            raise ValueError('Changed diary identity, official name, or category')
        table.extend(struct.pack('>HHHBB', item, 0x30FC+style*4, r['price'], 44, style)+name)
    return bytes(table)


def pocket_icon(source):
    from title_assets import pack4, untile
    from v3_villager_art import native_palette
    a, n = source.symbol('item_tex_data_table$779')
    t, size = source.symbol('etc2_tex_table$774')
    p = source.pointers(t, size)
    if (n != 64 or source.pointers(a, n).get(a+11*4) != t or size != 128 or
            source.raw('etc2_tex_table$774') != bytes(size) or set(p) != set(range(t, t+size, 4))):
        raise ValueError('Changed complete diary pocket icon binding')
    pair = [p[t], p[t+4]]
    if any(p[t+i*8+lane*4] != pair[lane] for i in range(16) for lane in range(2)):
        raise ValueError('Donor diaries no longer share one pocket icon')
    data = bytearray(struct.pack('>2I', RAM+ICON+32, RAM+ICON+64)+bytes(24))
    resources = []
    for at, name, count, kind in ((pair[0], 'inv_mwin_nittki_pal', 32, 'palette'),
                                  (pair[1], 'inv_mwin_nittki_tex', 512, 'texture')):
        if source.containing(at, exact=True) != (name, at, count) or source.pointers(at, count):
            raise ValueError('Incomplete diary icon resource')
        raw = source.raw(name)
        converted = native_palette(raw) if kind == 'palette' else pack4(untile(raw, 32, 32, 4))
        resources.append(dict(symbol=name, source_offset=at, source_sha256=sha256(raw),
            bytes=count, offset=len(data), ram=RAM+ICON+len(data), sha256=sha256(converted)))
        data.extend(converted)
    return bytes(data), dict(table=t, table_bytes=size, pointers=p, resources=resources,
        width=32, height=32, format_native='CI4/RGBA5551', shared_styles=16)


def carried(source, directory, prepared):
    from v3_furniture_pipeline import prepare_material_pair
    r = prepared['carried_artwork']
    data = checked_file(directory, r['file'], r['sha256'], r['bytes'])
    parts = [(name, *source.symbol(name)) for name in
        ('obj_item_diaryT_mat_model', 'obj_item_diaryT_gfx_model')]
    model = prepare_material_pair(source, parts)
    if (r['resources'] != model[2] or data[:len(model[1])] != model[1] or
            (directory/'carried/commands.c').read_text() != model[5]):
        raise ValueError('Changed complete carried diary resources or commands')
    for m in r['models']:
        spec = model[4][m['layer']]; at, size = m['native_offset'], m['bytes']
        if (m['symbol'] != spec['symbol'] or m['source_sha256'] != spec['source_sha256'] or
                m['source_parts'] != spec['source_parts'] or sha256(data[at:at+size]) != m['output_sha256']):
            raise ValueError('Changed shared carried diary model')
    r = dict(r, compiled_models=r['models'], model_offsets=r['offsets'])
    data, fixes = rebase_art(data, r, RAM+ART)
    r.update(ram=RAM+ART, source_category=17, native_category=44, installed_sha256=sha256(data),
        pointer_relocations=fixes, installed=True, source_preparation=str(directory.relative_to(ROOT)))
    return data, r


def rebind_ui(base, prior, equipment, output):
    """Relink the changed surface predicate, preserving all installed exports."""
    from v3_diary_ui import resident, SOURCES as UI_SOURCES
    from v3_furniture_install import inputs
    old = equipment['diaries']; directory = ROOT/old['prepared']['core']
    prepared = json.loads((directory/'diaries.json').read_bytes())
    # Event preparation validates the pristine caller from the actual immutable
    # pre-install cartridge; the installed UI and bindings are checked below.
    original, original_report = inputs(ROOT/prepared['base_lock'])
    compiled = resident(output/'diary-ui', prepared, ROOT/old['prepared']['screen'], original, original_report)
    before = old['ui_compiled']; p = old['packets']['ui']
    raw = bytearray(base[p['physical']:p['physical']+p['bytes']])
    data = (output/'diary-ui/code.bin').read_bytes()
    if (sha256(raw) != p['sha256'] or sha256(raw[:before['bytes']]) != before['sha256'] or
            compiled['symbols'] != before['symbols'] or compiled['bindings'] != before['bindings'] or
            compiled['bytes'] != before['bytes']):
        raise ValueError('Diary identity rebind changes installed UI addresses or dependencies')
    start = before['symbols']['af_diary_on_surface']-p['ram']
    end = min(v-p['ram'] for v in before['symbols'].values() if v-p['ram'] > start)
    if data[:start] != raw[:start] or data[end:] != raw[end:before['bytes']]:
        raise ValueError('Diary identity rebind changes unrelated UI code')
    changes = [dict(offset=i, before=raw[i:i+4].hex(), after=data[i:i+4].hex())
               for i in range(start, end, 4) if raw[i:i+4] != data[i:i+4]]
    if not changes:
        raise ValueError('Diary UI carried identity was not rebound')
    raw[:len(data)] = data
    record = dict(p, sha256=sha256(raw), crc32=zlib.crc32(raw))
    old.update(ui_compiled=compiled, carried_identity_patches=changes,
        carried_registry_version=DIARY_PARENT_REGISTRY_VERSION)
    old['packets']['ui'] = record
    old['sources'].update({s: sha256((ROOT/s).read_bytes()) for s in UI_SOURCES})
    return dict(record, previous_sha256=p['sha256']), bytes(raw)


def categories(base, equipment, blob, core, output, art):
    """One category entry serves ground, police storage, and handover."""
    e = equipment; at = e['blob_offset']; data = bytearray(blob[at:at+e['bytes']])
    if sha256(data) != e['sha256']:
        raise ValueError('Changed shared equipment packet')
    c = e['item_categories']; old = c['code']; offset = c['code_offset']
    if sha256(data[offset:offset+old['bytes']]) != old['sha256']:
        raise ValueError('Changed category entry')
    flags = [s[2:] for s in old['flags'] if s.startswith('-D')]
    flags.append(f'AF_V3_DIARY_CATEGORY_QUERY=0x{e["diary_items"]["code"]["symbols"]["af_diary_item_type"]:X}u')
    code, compiled = compile_part('item_categories', output/'diary-categories', defines=flags)
    if len(code) > c['map_offset']-offset or compiled['symbols'] != old['symbols']:
        raise ValueError('Diary category changes existing entry or exceeds code reservation')
    data[offset:c['map_offset']] = code.ljust(c['map_offset']-offset, b'\0')
    pos = c['map_offset']+16+17
    if data[pos] or any(r['source_category'] == 17 for r in c['objects']):
        raise ValueError('Diary category overwrites an existing mapping')
    data[pos] = 44
    for row in c['tables']:
        start, n = row['offset'], row['bytes']; pos = start+44*4
        if sha256(data[start:start+n]) != row['sha256'] or u32(data, pos):
            raise ValueError('Changed or occupied diary graphics category')
        struct.pack_into('>I', data, pos, (art['ram'] & 0x1FFFFFFF)+art['model_offsets'][row['role']])
        row['sha256'] = sha256(data[start:start+n])
    c.update(code=compiled, map_sha256=sha256(data[c['map_offset']:c['map_offset']+c['map_bytes']]))
    c['objects'].append(dict(art, handover_police_installed=True, ground_installed=True, runtime_installed=True))
    # The category tables already reserve 71 entries. Scenery owns the space
    # after the old descriptors: append a complete new descriptor bank after
    # that retained bank, rather than growing into or moving its resources.
    files = by_vrom(base); owners = {}
    ground = e['ground_categories']; cfg = ground['config_offset']
    if sha256(data[cfg:cfg+ground['config_bytes']]) != ground['config_sha256']:
        raise ValueError('Changed complete ground descriptor configuration')
    for variant, row in enumerate(ground['owners']):
        cap = row['capacity']; rel = bytearray(files[row['reloc']].extract(base))
        scenery = next(r for r in e['scenery']['owners'] if r['vrom'] == row['vrom'])
        pos = row['allocation_descriptor']-CODE_RAM+12
        old_resident = scenery['resident_bytes']
        if (sha256(rel) != scenery['output_reloc_sha256'] or
                u32(rel, 12) != old_resident-files[row['vrom']].size or
                u32(core, pos) != row['ram']+old_resident or
                scenery['bank_offset']+scenery['bank_bytes'] != old_resident or
                u32(data, cfg+variant*36+24) != cap['parts_offset']):
            raise ValueError('Changed seasonal diary descriptor allocation')
        empty = (old_resident+15) & ~15; parts = empty+32
        resident = (parts+52*len(c['objects'])+15) & ~15
        if resident >= 0x20000:
            raise ValueError('Invalid seasonal diary descriptor growth')
        growth = resident-old_resident
        cap.update(resident_bytes=resident, bss_bytes=u32(rel, 12)+growth,
            empty_offset=empty, parts_offset=parts)
        struct.pack_into('>I', data, cfg+variant*36+24, parts)
        struct.pack_into('>I', rel, 12, cap['bss_bytes'])
        struct.pack_into('>I', core, pos, row['ram']+resident)
        row.update(output_reloc_sha256=sha256(rel), diary_descriptor_growth=growth)
        owners[row['reloc']] = bytes(rel)
    ground['config_sha256'] = sha256(data[cfg:cfg+ground['config_bytes']])
    blob[at:at+len(data)] = data; e.update(sha256=sha256(data), crc32=zlib.crc32(data))
    return owners


def install(base, prior, blob, core, module, output):
    from v3_furniture_pipeline import Source
    from v3_furniture_install import provenance_patch
    from v3_furniture_icon import VROM as MENU, RAM as MENU_RAM
    e = copy.deepcopy(prior['equipment_resources'])
    if not e.get('diaries') or e.get('diary_items'):
        raise ValueError('Diary carried path requires installed menus/storage and no previous items')
    if any(a < RAM+SIZE and RAM < b for a, b in reservations(prior)):
        raise ValueError('Diary item packet overlaps a retained RAM allocation')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rows, discovered = records(source); table = encode(rows); icon, icons = pocket_icon(source)
    attribution = provenance_patch(rows, ('tools/v3_diary_items.py', 'tools/v3_diaries.py'))
    if attribution:
        write_new(output/'provenance.patch', attribution.encode())
    directory = ROOT/e['diaries']['prepared']['core']
    prepared = json.loads((directory/'diaries.json').read_bytes())
    if prepared['rows'] != discovered['rows']:
        raise ValueError('Changed prepared diary identities')
    # Native category B has a single type-21 entry. Additions must not alias it.
    native = u32(core, 0x8010B334-CODE_RAM+11*4)
    if not CODE_RAM <= native < CODE_RAM+len(core) or core[native-CODE_RAM] != 21:
        raise ValueError('Changed preserved native category-B identity')
    art, artwork = carried(source, directory, prepared)
    writes = [rebind_ui(base, prior, e, output)]
    hooks = [dict(kind=h['kind'], address=h['address'], before=h['after'], prior=h['target'],
                  symbol='af_diary_item_'+h['kind']) for h in e['creature_items']['hooks']]
    display = copy.deepcopy(prior['clothing'])
    for kind, h in zip(('record', 'owned'), display['display']['readers']['collection_hooks']):
        hooks.append(dict(kind=kind, address=h['entry'], before=h['after'], prior=h['target'],
            symbol='af_diary_item_'+kind))
    bindings = {'af_diary_prior_'+h['kind']: h['prior'] for h in hooks}
    bindings.update(af_diary_native_selected=e['diaries']['ui_compiled']['symbols']['af_diary_native_selected'],
        af_diary_prior_icon=e['creature_fish']['world']['compiled']['symbols']['af_v3_creature_icon_hook'])
    bindings.update({k: e['collection']['code']['symbols'][k] for k in
        ('af_v3_require_save_state', 'af_v3_save_collect', 'af_v3_save_halt')})
    code, compiled = compile_part('diary_items', output/'diary-items',
        extra_sources=('overlays/v3/creature_icon.S',), defines=('AF_DIARY_ICON=1', 'AF_V3_CLOTHING_PROFILE=1'),
        link_symbols=bindings)
    packet = bytearray(SIZE)
    for offset, data, limit in ((0, code, TABLE), (TABLE, table, ICON), (ICON, icon, ART), (ART, art, SIZE-16)):
        if offset+len(data) > limit:
            raise ValueError('Diary item packet exceeds its bounded regions')
        packet[offset:offset+len(data)] = data
    packet[-16:] = GUARD
    for h in hooks:
        if h['address'] >= 0x80460000:
            owner, origin = blob, 0x80460000
        else:
            owner, origin = (module, MODULE_RAM) if h['address'] >= MODULE_RAM else (core, CODE_RAM)
        at = h['address']-origin
        if owner[at:at+8] != bytes.fromhex(h['before']):
            raise ValueError('Changed diary predecessor: '+h['kind'])
        target = compiled['symbols'][h['symbol']]; after = struct.pack('>2I', jump(target), 0)
        owner[at:at+8] = after; h.update(target=target, after=after.hex())
        if h['kind'] in ('record', 'owned'):
            previous = display['display']['readers']['collection_hooks'][0 if h['kind'] == 'record' else 1]
            previous.update(diary_prior_target=previous['target'], target=target, after=after.hex())
    files = by_vrom(base); menu = bytearray(files[MENU].extract(base))
    pos = 0x8085C968-MENU_RAM
    before = struct.pack('>2I', jump(bindings['af_diary_prior_icon']), 0)
    if menu[pos:pos+8] != before:
        raise ValueError('Changed predecessor pocket icon branch')
    after = struct.pack('>2I', jump(compiled['symbols']['af_diary_icon_hook']), 0)
    menu[pos:pos+8] = after
    icon_hook = dict(vrom=MENU, address=0x8085C968, ram=MENU_RAM, before=before.hex(), after=after.hex())
    records_rom = copy.deepcopy(prior.get('physical_resources', [])); staging = bytearray(base)
    for record, data in writes:
        records_rom = [dict(record) if r['id'] == record['id'] else r for r in records_rom]
        staging[record['physical']:record['physical']+len(data)] = data
    record = physical.allocate(staging, records_rom, packet, 'diary-items-GAFE01-r0')
    records_rom.append(record); writes.append((record, bytes(packet)))
    e['diary_items'] = dict(format='AFV3-DIARY-ITEMS-1', registry=DIARY_PARENT_REGISTRY_VERSION,
        rows=rows, code=compiled, hooks=hooks, icon_hook=icon_hook, artwork=artwork, icons=icons,
        packet=dict(record, ram=RAM, crc32=zlib.crc32(packet), storage='physical-ROM'),
        table_offset=TABLE, table_sha256=sha256(table), table_bytes=len(table),
        additional_resident_bytes=SIZE, selected=0, saved_format_changed=False,
        native_execution_tested=False, pending=['loose-room drawing', 'cover profiles and catalogue/scoring',
            'participation callers', 'selection and connected native verification'],
        sources={s: sha256((ROOT/s).read_bytes()) for s in SOURCES})
    owners = categories(base, e, blob, core, output, artwork); owners[MENU] = bytes(menu)
    e['pocket_icons']['owner_sha256'] = sha256(menu)
    for name, data in (('diary-items.bin', packet), ('diary-ui.bin', writes[0][1])):
        write_new(output/name, bytes(data))
    return e, owners, dict(clothing=display, physical_resources=records_rom), writes
