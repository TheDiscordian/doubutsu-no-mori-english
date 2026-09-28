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


def install_room(base, prior, blob, core, output, directory):
    """Use every real cover in rooms and ordinary DMA-backed preview profiles."""
    from v3_furniture_pipeline import Source, PreparedAssets, prepare
    from v3_furniture_install import profile, owner_tail_storage
    from v3_furniture_capacity import checked as model_capacity
    from v3_resource_capacity import checked_limit
    from v3_import_storage import ROWS, ITEMS, slot, ROWS_RAM
    from v3_player_actions import native_references
    from v3_room_goods import VROM, RELOC, RAM as GOODS_RAM, TABLE_AT, TABLE_BYTES, TABLE_SHA
    from npc_mail_show import relocate_verified_data
    from types import SimpleNamespace
    e = copy.deepcopy(prior['equipment_resources']); d = e['diary_items']; goods = e['room_goods']
    if d.get('room_art'):
        raise ValueError('Complete diary room artwork is already installed')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT/'build'):
        raise ValueError('Diary covers require ignored complete prepared assets')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    prepared = json.loads((directory/'art.json').read_bytes())
    assets = {r['item_id']: r for r in prepared['objects']}
    cache = PreparedAssets(source, [directory]); files = by_vrom(base)
    old, old_rel = files[VROM].extract(base), files[RELOC].extract(base)
    if (sha256(old) != goods['binding']['owner_sha256'] or
            sha256(old_rel) != goods['binding']['relocation_sha256']):
        raise ValueError('Changed complete native loose-item predecessor')
    groups, absolute, relocations, _, _ = native_references(old, old_rel,
        expected_sections=(0xFB0, 0x2E0, 0x10, 0x10))
    # Keep native BSS at its linked offsets by materializing it as zero data.
    # The additional table and complete models follow it, never overwrite it.
    table_at = 0x12B0; count = 50; target_vrom, target_rel = 0x1A50000, 0x1A60000
    data = bytearray(old+bytes(16)+old[0xFB0:0xFB0+34*20]+bytes(17*20))
    data.extend(bytes(-len(data)%16)); first_model = len(data)
    s4 = source.sections[4][0]; table = source.rel[s4+TABLE_AT:s4+TABLE_AT+TABLE_BYTES]
    if sha256(table) != TABLE_SHA:
        raise ValueError('Changed complete donor room model table')
    limit, bank = checked_limit(base, prior), model_capacity(base, prior)
    profiles, fixes, added_relocations = [], [], []
    for style, parent in enumerate(d['rows']):
        item = parent['display_item_id']; r = assets[item]; donor = 0x2B00+style
        current = prepare(source, int(item, 16))
        if cache.reuse(source, item, current) is None:
            raise ValueError('Changed prepared diary cover: '+item)
        raw = (directory/r['object_file']).read_bytes(); offset = len(data)
        matches = [i for i in range(0, len(table), 40) if struct.unpack_from('>HH', table, i) == (donor, donor)]
        if len(matches) != 1 or u32(table, matches[0]+36) != 1:
            raise ValueError('Unsupported complete diary room drawing row')
        at = TABLE_AT+matches[0]
        pointers = [source.section_relocations.get((4, at+4+i*4)) for i in range(8)]
        if table[matches[0]+4:matches[0]+36] != bytes(32):
            raise ValueError('Unrelocated diary room model pointer')
        models = []
        for lane in range(4):
            pointer, alternate = pointers[lane*2:lane*2+2]
            if pointer != alternate:
                raise ValueError('Diary source room/shop modes have different artwork')
            if pointer is None:
                models.append(0);continue
            layers = [k for k,v in r['profile']['models'].items() if v[1] == pointer[3]]
            if pointer[:3] != (1,u32(source.rel,0),5) or len(layers) != 1:
                raise ValueError('Room model is absent from complete cover preparation')
            models.append(GOODS_RAM+offset+r['model_offsets'][layers[0]])
        # Validate every resource reference, including interior vertex loads.
        used = set()
        for model in r['models']:
            a, n = model['native_offset'], model['bytes']
            if sha256(raw[a:a+n]) != model['output_sha256']:
                raise ValueError('Changed complete cover drawing commands')
            for word_at in range(a, a+n, 8):
                op = raw[word_at]; pointer = u32(raw, word_at+4)
                if op not in (1, 0xFD):
                    if pointer>>24 == 6:
                        raise ValueError('Unbound non-resource diary pointer')
                    continue
                off = pointer & 0xFFFFFF
                resources = [x for x in r['resources'] if x['native_offset'] <= off < x['native_offset']+x['bytes']]
                if pointer>>24 != 6 or len(resources) != 1:
                    raise ValueError('Unbound complete cover resource')
                resource = resources[0]
                if (op == 1 and (resource['kind'] != 'vertices' or
                        off+((u32(raw, word_at)>>12)&255)*16 > resource['native_offset']+resource['bytes']) or
                        op == 0xFD and resource['kind'] not in ('texture', 'palette')):
                    raise ValueError('Cover resource reference exceeds its source')
                used.add(resource['native_offset'])
                fixes.append((offset+word_at+4, pointer, offset+off))
        if used != {x['native_offset'] for x in r['resources']}:
            raise ValueError('Cover room binding omits a source resource')
        data.extend(raw)
        row_at = table_at+(34+style)*20
        struct.pack_into('>HH4I', data, row_at, 0x2B10+style, 0x2B10+style,*models)
        added_relocations.extend(0xC2000000|(row_at+4+lane*4-0x1290) for lane,value in enumerate(models) if value)
        cover = int(item, 16); index = 1087+style; s = slot(cover)
        if (any(blob[ROWS+s*80:ROWS+(s+1)*80]) or any(blob[ITEMS+s*32:ITEMS+(s+1)*32]) or
                blob[0x40+s//8] & (1 << (s&7))):
            raise ValueError('Diary cover overwrites an existing furniture identity')
        native = profile(r, target_vrom+offset, limit=limit, model_capacity=bank)
        record = struct.pack('>HHI', index, cover, 0)+native+bytes(4)
        metadata = (struct.pack('>HHHBB', index, cover, parent['price'], r['profile']['size_code'], 0)+
            parent['name'].encode('ascii').ljust(16,b' ')+bytes(4)+struct.pack('>HH', 0x2B10+style, 0))
        blob[ROWS+s*80:ROWS+(s+1)*80] = record; blob[ITEMS+s*32:ITEMS+(s+1)*32] = metadata
        profiles.append(dict(source_item_id=item,item_id=item,parent_item_id=parent['item_id'],
            runtime_index=index,profile_ram=ROWS_RAM+s*80+8,profile_hex=native.hex(),
            profile_record_sha256=sha256(record),item_record_sha256=sha256(metadata),
            object_vrom=target_vrom+offset,object_offset=offset,object_bytes=len(raw),
            object_sha256=sha256(raw),selected=False,source=r))
    # All eight high/low reference groups, including the terminator's +2 reader.
    patches = []
    observed = []
    for hi, lows in groups.items():
        if not any(GOODS_RAM+0xFB0 <= v < GOODS_RAM+0xFB0+700 for _,v in lows):
            continue
        if any(v not in (GOODS_RAM+0xFB0,GOODS_RAM+0xFB2) for _,v in lows):
            raise ValueError('Mixed or interior native diary table reference')
        for lo, value in lows:
            replacement = GOODS_RAM+table_at+value-(GOODS_RAM+0xFB0)
            for pos, half in ((hi,(replacement+0x8000)>>16),(lo,replacement&65535)):
                before = u32(data,pos); after = before & 0xFFFF0000 | half
                struct.pack_into('>I',data,pos,after); patches.append(dict(offset=pos,before=before,after=after))
            observed.append((hi,lo))
    if observed != [(0x710,0x744),(0x868,0x86C),(0x9C4,0x9C8),(0x9DC,0x9E0),
                    (0xDB0,0xDBC),(0xDE0,0xDE4),(0xE70,0xE78),(0xEA8,0xEAC)] or any(
            GOODS_RAM+0xFB0 <= v < GOODS_RAM+0xFB0+700 for v in absolute.values()):
        raise ValueError('Incomplete native diary drawing-table consumers')
    data.extend(bytes(-len(data)%16))
    sections = (0xFB0,0x2E0,len(data)-0x1290,0,len(relocations)+len(added_relocations))
    rel = struct.pack('>5I',*sections)+struct.pack('>'+str(sections[4])+'I',*(relocations+added_relocations))
    rel_size = (len(rel)+4+15)&~15; rel = rel.ljust(rel_size-4,b'\0')+struct.pack('>I',rel_size)
    for address in (0x801A0010,0x80310010):
        old_loaded = relocate_verified_data(SimpleNamespace(ram=GOODS_RAM,resident_bytes=len(old)+16,
            sections=struct.unpack_from('>5I',old_rel)),old,old_rel,address)
        loaded = relocate_verified_data(SimpleNamespace(ram=GOODS_RAM,resident_bytes=len(data),sections=sections),data,rel,address)
        changed = {i for p in patches for i in range(p['offset'],p['offset']+4)}
        if any(a!=b and i not in changed for i,(a,b) in enumerate(zip(old_loaded,loaded))):
            raise ValueError('Diary table changes unrelated relocated native data')
    descriptor = 0x80101330-CODE_RAM
    before = (VROM,VROM+len(old),GOODS_RAM,GOODS_RAM+len(old)+16)
    if struct.unpack_from('>4I',core,descriptor) != before:
        raise ValueError('Changed native room graphics allocation descriptor')
    struct.pack_into('>4I',core,descriptor,target_vrom,target_vrom+len(data),GOODS_RAM,GOODS_RAM+len(data))
    config = struct.pack('>8I',0x41464452,1,len(fixes),len(data),table_at,count,first_model,len(data))
    config += b''.join(struct.pack('>3I',*x) for x in fixes)
    p = d['packet']; packet = bytearray(base[p['physical']:p['physical']+p['bytes']])
    if len(config)>0xFF0 or any(packet[0x3000:0x3FF0]) or d['code']['bytes']>0x800:
        raise ValueError('Complete diary room binding exceeds packet reservation')
    code, compiled = compile_part('diary_goods',output/'diary-goods',primary_source='overlays/v3/room_goods.c',
        extra_sources=('overlays/v3/room_goods_bridge.S',),defines=(
            'AF_DIARY_GOODS=1',f'AF_GOODS_TABLE_OFFSET=0x{table_at:X}u',f'AF_GOODS_ROW_COUNT={count}u',
            f'AF_GOODS_VROM=0x{target_vrom:X}u',f'AF_GOODS_ROTATE_LOW=0x{goods["source"]["mask_low"]:X}u',
            'AF_GOODS_ROTATE_HIGH=0x3FFFFu'),
        link_symbols={'af_v3_save_halt':d['code']['symbols']['af_v3_save_halt']})
    if len(code)>0x1800 or any(packet[0x800:0x2000]):
        raise ValueError('Diary room code overwrites existing item readers')
    packet[0x800:0x800+len(code)] = code; packet[0x3000:0x3000+len(config)] = config
    old_packet = goods['packet']; at = old_packet['blob_offset']
    original = bytes(blob[at:at+old_packet['bytes']]); dispatch = []
    if sha256(original)!=old_packet['sha256']:
        raise ValueError('Changed existing room entry packet')
    for name, address in goods['compiled']['symbols'].items():
        if not name.startswith('af_v3_goods_'): continue
        target = compiled['symbols'][name]; pos = at+address-old_packet['ram']
        before_bytes = bytes(blob[pos:pos+8]); after = struct.pack('>2I',jump(target),0)
        blob[pos:pos+8] = after
        dispatch.append(dict(name=name,address=address,target=target,before=before_bytes.hex(),after=after.hex()))
    raw = blob[at:at+old_packet['bytes']]
    old_packet.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    goods['compiled'].update(sha256=sha256(raw[:goods['compiled']['bytes']]),diary_dispatch=dispatch)
    record = dict(p,sha256=sha256(packet),crc32=zlib.crc32(packet)); d['packet']=record
    physical_records = [dict(record) if x['id']==record['id'] else x for x in prior['physical_resources']]
    owners = {VROM:bytes(data),RELOC:rel}
    growth = []
    for move in owner_tail_storage(base,files,list(owners.items()),reservations=physical_records):
        entry=files[move['vrom']]
        growth.append(dict(move,previous_bytes=entry.size,previous_physical=entry.pstart,
            previous_compressed_end=entry.pend,previous_sha256=sha256(entry.extract(base)),
            target_vrom=target_vrom if move['vrom']==VROM else target_rel,
            relocated=True,relocated_blockers=[],retains_old_allocation=True))
    d['profiles']=profiles
    d['room_art']=dict(vrom=target_vrom,reloc=target_rel,ram=GOODS_RAM,bytes=len(data),
        sha256=sha256(data),relocation_sha256=sha256(rel),table_offset=table_at,rows=count,
        art_offset=first_model,art_bytes=sum(r['object_bytes'] for r in profiles),
        fixups=fixes,config_bytes=len(config),compiled=compiled,dispatch=dispatch,table_patches=patches,
        previous_vrom=VROM,previous_reloc=RELOC,previous_bytes=len(old),
        prepared=str(directory.relative_to(ROOT)),prepared_sha256=sha256((directory/'art.json').read_bytes()),
        installed=True,native_execution_tested=False)
    d['pending']=['catalogue/scoring and ordering', 'participation callers', 'selection and connected native verification']
    d['sources'].update({s:sha256((ROOT/s).read_bytes()) for s in (*SOURCES,
        'overlays/v3/room_goods.c','overlays/v3/room_goods.h','overlays/v3/room_goods_bridge.S',
        'overlays/v3/diary_goods.ld')})
    goods['diary_room_art']=dict(vrom=target_vrom,reloc=target_rel,bytes=len(data),compiled=compiled)
    write_new(output/'diary-items.bin',bytes(packet))
    return e,owners,dict(physical_resources=physical_records,resource_growth=growth),[
        (dict(record,previous_sha256=p['sha256']),bytes(packet))]


def catalogue_rows(source):
    """All covers share the donor furniture page and parent-price preview."""
    raw = source.raw('mCL_furniture_list')
    if sha256(raw) != '91bad7d2198f5da32b464547c3a3c15df9cc77e1969ad7eebc7c0fa45f66956f':
        raise ValueError('Changed complete donor furniture ordering')
    _, init = source.function(0x259014)
    if init['sha256'] != '6bfe84fd17e661290e19a263a63a0299614f9ea7b7f091598434328245957e73':
        raise ValueError('Changed donor diary catalogue presentation')
    order = list(struct.iter_unpack('>HH', raw)); rows = []
    for parent in records(source)[0]:
        style = parent['style']; item = parent['display_item_id']; index = 1087+style
        matches = [(p,m) for p,(i,m) in enumerate(order) if i==index]
        if len(matches)!=1 or matches[0][1]!=0:
            raise ValueError('Changed diary furniture-page membership')
        rows.append(dict(item_id=item,runtime_index=index,catalogue_index=index+1024,
            donor_position=matches[0][0],mode=0,representation='diary',
            parent_item_id=parent['item_id'],donor_parent_item_id=parent['donor_item_id'],
            selection_id=parent['id'],catalogue_orderable=True,price=parent['price']))
    return sorted(rows,key=lambda r:r['donor_position'])


def install_catalogue(base, prior, blob, core, output):
    """Connect all prepared covers to the shared catalogue and scoring owners."""
    from v3_furniture_pipeline import Source
    from v3_furniture_install import scoring, STABLE, STABLE_SHA
    from v3_garden_runtime import install_catalogue as shared_catalogue
    from v3_hra_birth import checked_categories
    import v3_hra as hra
    import v3_feng_shui as feng
    e=copy.deepcopy(prior['equipment_resources']);d=e['diary_items']
    if not d.get('room_art') or d.get('catalogue'):
        raise ValueError('Diary catalogue requires installed covers and an uninstalled catalogue')
    e['diaries']['hooks'].setdefault('catalogue_pool_bytes_at_install',prior['catalogue']['category_pool_bytes'])
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rows=catalogue_rows(source);files=by_vrom(base)
    query=d['code']['symbols']['af_diary_item_collection']
    category=dict(imports=rows,query=query,preview_height=36.0,preview_scale=1.0,preview_y=0.0,
        source_initializer=source.function(0x259014)[1],selected=0,installed=True,
        ordinary_order_delivery_tested=False)
    stable=STABLE.read_bytes()
    if sha256(stable)!=STABLE_SHA:raise ValueError('Changed common catalogue source baseline')
    changes,cat=shared_catalogue(base,stable,prior,prior['catalogue']['imports'],output,
        source.rel,source.symbols.encode(),reviewed_rows=prior['catalogue']['imports'],diaries=category)
    changed_core=changes.pop(CODE_VROM,None)
    if changed_core is not None:
        old_core=files[CODE_VROM].extract(base)
        for i,(a,b) in enumerate(zip(old_core,changed_core,strict=True)):
            if a!=b:
                if core[i]!=a:raise ValueError('Conflicting diary catalogue allocation change')
                core[i]=b
    mapping,_=checked_categories(files[hra.NEW_VROM].extract(base),prior['hra'],source)
    if (sha256(source.data[0x4FAFC:0x4FAFC+1266*4])!=hra.DONOR_SHA or
            sha256(source.data[0x4EBF0:0x4EBF0+1266*2])!=feng.DONOR_SHA):
        raise ValueError('Changed complete donor diary scoring tables')
    score_rows=[]
    for row in rows:
        index=row['runtime_index'];value=u32(source.data,0x4FAFC+index*4)
        donor=value>>8&63;birth=mapping[donor];surface=value>>6&3;series=value>>26
        score_rows.append(dict(item_id=row['item_id'],runtime_index=index,
            donor_birth_category=donor,birth_category=birth,surface=surface,series=series,
            donor_hra_hex=f'{value:08x}',native_hra_hex=f'{(value&0xFFFFC000)|(birth<<9)|(surface<<7):08x}',
            donor_series_hex=source.raw('mMkRm_series_info')[series*3:series*3+3].hex(),
            feng_hex=source.data[0x4EBF0+index*2:0x4EBF0+index*2+2].hex()))
    scored,reports=scoring(base,prior,score_rows,source);changes.update(scored)
    # Only the upper-layer clutter test exempts diaries. Calling this through
    # the shared full-register bridge leaves the floor test and every other
    # range/index consumer untouched.
    _,clean=source.function(0x162450)
    if clean['sha256']!='6309d7f4ffb1cbcaab4c16dcbb1aa789cca891261ecae0b2627f113995dc873a':
        raise ValueError('Changed complete donor diary clutter rule')
    p=d['packet'];packet=bytearray(base[p['physical']:p['physical']+p['bytes']])
    if (sha256(packet)!=p['sha256'] or any(packet[0x1000:0x2000]) or
            d['room_art']['compiled']['bytes']>0x800):
        raise ValueError('Diary clutter code overlaps the installed room adapter')
    clutter_code,clutter=compile_part('diary_catalogue',output/'diary-catalogue',
        extra_sources=('overlays/v3/room_entry.S',),defines=('AF_DIARY_CLUTTER=1',),
        link_symbols=dict(af_diary_prior_room_value=prior['furniture_room']['code']['symbols']['af_v3_room_value'],
            af_diary_item_collection=query))
    packet[0x1000:0x1000+len(clutter_code)]=clutter_code
    data=bytearray(changes[hra.NEW_VROM]);h=reports['hra']
    start=h['code']['symbols']['af_v3_hra_range_809261c4']-hra.RAM
    before=bytes.fromhex('2ac11ecd1420000b0000000027bdffe0ffbf0018afb60000241f0000afbf0004')
    call=jump(prior['furniture_room']['code']['symbols']['af_v3_room_query'],link=True)
    if (data[start:start+32]!=before or u32(data,start+32)!=call or u32(data,start+36) or
            any((v&0xFFFFFF)==start+32 for v in struct.unpack_from('>'+str(u32(files[hra.NEW_RELOC].extract(base),16))+'I',
                files[hra.NEW_RELOC].extract(base),20))):
        raise ValueError('Changed complete native upper-layer clutter query')
    target=clutter['symbols']['af_diary_clutter_query'];after=jump(target,link=True)
    struct.pack_into('>I',data,start+32,after)
    h.update(output_sha256=sha256(data),diary_clutter=dict(address=hra.RAM+start+32,
        before=call,after=after,target=target,source=clean,compiled=clutter,
        floor_query_unchanged=True,all_other_queries_unchanged=True))
    changes[hra.NEW_VROM]=bytes(data)
    record=dict(p,sha256=sha256(packet),crc32=zlib.crc32(packet));d['packet']=record
    physical_records=[dict(record) if x['id']==record['id'] else x for x in prior['physical_resources']]
    write_new(output/'diary-items.bin',bytes(packet))
    d['catalogue']=category;d['scoring']=dict(rows=score_rows,metadata_installed=True,
        parent_clutter_exception_installed=True,clutter=h['diary_clutter'])
    d['pending']=['participation callers','selection and connected native verification']
    d['sources'].update({s:sha256((ROOT/s).read_bytes()) for s in (*SOURCES,
        'tools/v3_catalogue.py','tools/v3_garden_runtime.py','overlays/v3/catalogue.c','overlays/v3/catalogue.ld',
        'overlays/v3/diary_catalogue.c','overlays/v3/diary_catalogue.ld','overlays/v3/room_entry.S')})
    return e,changes,dict(catalogue=cat,physical_resources=physical_records,**reports),[
        (dict(record,previous_sha256=p['sha256']),bytes(packet))]
