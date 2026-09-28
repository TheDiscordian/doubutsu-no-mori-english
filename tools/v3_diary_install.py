"""Install the shared diary menus, resident resources, and native save path.

Consumes checked preparation for the whole category without reconverting art.
Carried-item readers and selection are separate consumers of this same import;
loading a menu does not declare the sixteen styles playable.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from apply_translation import write_new
from v3_asset_loader import ROOT
from v3_console_disk_install import reservations
from v3_diaries import LAYOUT, native_contract
from v3_diary_ui import MEMORY
from v3_import_storage import jump
import v3_physical_resources as physical

SOURCES = ('tools/v3_diary_install.py', 'tools/v3_furniture_install.py',
    'tools/v3_room_goods.py', 'overlays/v3/surface_bootstrap.c')
GUARD = bytes.fromhex('41464447') * 4
WARNING = ('Format-11 V3 saves require this or a newer compatible build. Valid older saves '
    'migrate forward with empty diaries, preserving the town, collections, creature seasons, '
    'and console progress. V2 and earlier V3 builds cannot load new saves. Preserve backups. '
    'Native diary UI and save/reload remain unverified.')
MENU_VROM = {'hboard': (0x4600000, 0x4610000), 'keyboard': (0x4620000, 0x4630000)}


def checked_file(directory, filename, digest, size=None):
    path = (directory / filename).resolve()
    if not path.is_relative_to(directory):
        raise ValueError('Diary preparation escapes its directory')
    data = path.read_bytes()
    if sha256(data) != digest or (size is not None and len(data) != size):
        raise ValueError('Changed prepared diary file: ' + str(path))
    return data


def load(base, prior, directories):
    """Check linked code, source dependencies, resource identity, and all RAM."""
    paths = {k: v.resolve() for k, v in directories.items()}
    if set(paths) != {'core', 'ui', 'screen'} or any(
            not p.is_relative_to(ROOT / 'build') for p in paths.values()):
        raise ValueError('Diaries require three complete ignored preparations')
    core = json.loads((paths['core'] / 'diaries.json').read_bytes())
    ui = json.loads((paths['ui'] / 'ui.json').read_bytes())
    screen = json.loads((paths['screen'] / 'screen.json').read_bytes())
    if (prior['save_codec']['format_version'] != 9 or prior['save_codec']['registry_version'] != 5
            or prior['equipment_resources'].get('diaries')
            or any(r['base_rom_sha256'] != sha256(base) or r['base_runtime_abi'] != prior['runtime_abi']
                   for r in (core, ui))
            or core['planned_memory'] != LAYOUT
            or ui['planned_memory'] != {k: dict(ram=a, bytes=b, guard=a+b-16) for k, (a, b) in MEMORY.items()}
            or ui['core_sha256'] != core['code_sha256'] or ui['art_sha256'] != screen['sha256']
            or (core['disk_format'], core['canonical_format'], core['registry']) != (11, 8, 5)):
        raise ValueError('Changed connected diary preparation or predecessor')
    for receipt in (core, ui, screen):
        for path, digest in receipt['sources'].items():
            # Catalogue additions and build-driver edits cannot alter compiled
            # code. The complete compiled sources and generated art are pinned.
            if path.startswith('overlays/') and sha256((ROOT / path).read_bytes()) != digest:
                raise ValueError('Stale compiled diary dependency: ' + path)
    code = checked_file(paths['core'], core['code_file'], core['code_sha256'], core['compiled']['bytes'])
    native = checked_file(paths['ui'], 'resident/code.bin', ui['compiled']['sha256'], ui['compiled']['bytes'])
    art = checked_file(paths['screen'], screen['file'], screen['sha256'], MEMORY['art'][1]-16)
    checked_file(paths['screen'], 'diary-art.inc', screen['draw_header_sha256'])
    if (len(code) > LAYOUT['code']['bytes']-16 or len(native) > MEMORY['code'][1]-16
            or core['compiled']['sha256'] != sha256(code) or ui['compiled']['ram'] != MEMORY['code'][0]):
        raise ValueError('Diary code exceeds its guarded reservation')
    layout = {k: dict(ram=r['ram'], bytes=r['bytes']+(0 if k == 'code' else 16))
              for k, r in LAYOUT.items()}
    layout.update({'ui_'+k: dict(ram=a, bytes=b) for k, (a, b) in MEMORY.items()})
    used = list(reservations(prior))
    for name, row in layout.items():
        a, b = row['ram'], row['ram']+row['bytes']
        if a & 15 or b & 15 or b > 0x807DA800 or any(x < b and a < y for x, y in used):
            raise ValueError('Diary RAM overlaps an existing owner: ' + name)
        used.append((a, b))
    packets = dict(storage=code.ljust(LAYOUT['code']['bytes']-16, b'\0')+GUARD,
        ui=native.ljust(MEMORY['code'][1]-16, b'\0')+GUARD+bytes(MEMORY['state'][1]-16)+GUARD,
        art=art+GUARD)
    return paths, core, ui, screen, layout, packets


def redirect_storage(prior, equipment, blob, core):
    """Retarget every stable storage export, leaving the canonical codec intact."""
    storage = equipment['console_storage']
    p, old = storage['packet'], storage['compiled']
    data = bytearray(blob[p['blob_offset']:p['blob_offset']+p['bytes']])
    start = 0x804DE200-p['ram']
    if (sha256(data) != p['sha256'] or zlib.crc32(data) != p['crc32']
            or sha256(data[start:start+old['bytes']]) != old['sha256']):
        raise ValueError('Changed stable console/save entry packet')
    compiled = dict(core['compiled'], ram=LAYOUT['code']['ram'])
    first, last = compiled['ram'], compiled['ram']+compiled['bytes']
    rows = []
    for row in old['dispatch']:
        at = row['address']-p['ram']
        before = bytes.fromhex(row['after'])
        target = compiled['symbols'][row['name']]
        if (len(before) != 8 or data[at:at+8] != before or target & 3
                or not first <= target < last):
            raise ValueError('Changed stable diary save export: ' + row['name'])
        after = struct.pack('>2I', jump(target), 0)
        data[at:at+8] = after
        rows.append(dict(row, before=before.hex(), after=after.hex(), target=target))
    blob[p['blob_offset']:p['blob_offset']+len(data)] = data
    p.update(sha256=sha256(data), crc32=zlib.crc32(data))
    storage.update(compiled=dict(old, sha256=sha256(data[start:start+old['bytes']]), dispatch=rows),
        diary_runtime=compiled, save_format=11, canonical_save_format=8,
        retired_scratch=copy.deepcopy(storage['scratch']),
        scratch=dict(LAYOUT['scratch']), diary_state=dict(LAYOUT['state']),
        ordinary_save_reload_tested=False, native_execution_tested=False)
    saved, codec, clothing, surface = (copy.deepcopy(prior[k]) for k in
        ('save_runtime', 'save_codec', 'clothing', 'room_surfaces'))
    saved.update(diary_runtime_code=compiled, diary_state_bytes=core['serialized_bytes'],
        native_save_reload_tested=False)
    # active_codec_code still identifies the canonical format-eight routines;
    # the diary envelope has a different owner and must not disguise that fact.
    codec.update(format_version=11, active_storage_code=compiled,
        active_storage_resource='equipment_resources.diaries')
    clothing['save_extension'].update(format_version=11, active_storage_code=compiled,
        legacy_formats_read=['NAFJ', *[f'AFS3-v{i}' for i in (1, 2, 3, 4, 5, 6, 7, 8, 9)]])
    surface['save'].update(disk_format_version=11, ordinary_persistence_tested=False)
    return dict(save_runtime=saved, save_codec=codec, clothing=clothing, room_surfaces=surface,
        saved_format_changed=True, save_warning=WARNING), rows


def install_menus(base, core, paths, ui):
    files = by_vrom(base)
    owner = bytearray(files[0x7749C0].extract(base))
    changes, menus = {}, {}
    for name, record in ui['hooks']['menus'].items():
        r = copy.deepcopy(record)
        vrom, reloc = r['vrom'], r['reloc']
        if (sha256(files[vrom].extract(base)) != r['previous_sha256']
                or sha256(files[reloc].extract(base)) != r['previous_relocation_sha256']
                or list(struct.unpack_from('>7I', owner, r['owner_at'])) != r['owner_before']):
            raise ValueError('Changed native diary menu predecessor: ' + name)
        data = checked_file(paths['ui'], name+'/prepared.bin', r['overlay_sha256'], r['bytes'])
        rel = checked_file(paths['ui'], name+'/relocation.bin', r['relocation_sha256'])
        target, target_rel = MENU_VROM[name]
        after = list(r['owner_after']); after[:2] = [target, target+len(data)]
        struct.pack_into('>7I', owner, r['owner_at'], *after)
        changes.update({vrom: data, reloc: rel})
        menus[name] = dict(r, target_vrom=target, target_reloc=target_rel, owner_after=after, installed=True)
    changes[0x7749C0] = bytes(owner)
    hooks = ui['hooks']; bound = hooks['pool_bound']
    patches = []
    for address, before, after in (
            (0x800C4AFC, 0x3C0E808A, 0x3C0E0000|((bound+0x8000)>>16)),
            (0x800C4B10, 0x25CEA860, 0x25CE0000|(bound & 0xFFFF))):
        at = address-CODE_RAM
        if struct.unpack_from('>I', core, at)[0] != before:
            raise ValueError('Changed native diary menu arena')
        struct.pack_into('>I', core, at, after)
        patches.append(dict(address=address, before=f'{before:08x}', after=f'{after:08x}'))
    visit = hooks['visit']; at = visit['address']-CODE_RAM
    if core[at:at+8] != bytes.fromhex(visit['before']):
        raise ValueError('Changed native played-day call')
    core[at:at+8] = bytes.fromhex(visit['after'])
    return changes, dict(menus=menus, arena_patches=patches, visit=dict(visit, installed=True),
        previous_pool_bound=hooks['previous_pool_bound'], pool_bound=bound,
        additional_pool_bytes=hooks['additional_pool_bytes'], installed=True)


def redirect_embedded_storage(base, prior, equipment, updates, prepared):
    """Existing insect code calls its own save exports, not just stable stubs.

Keep their addresses so already linked season/console callers cannot enter the
old scratch/guard implementation. Canonical codec bodies and artwork stay intact.
"""
    insects = equipment['creature_insects']
    p, compiled = insects['packet'], insects['compiled']
    data = bytearray(base[p['physical']:p['physical']+p['bytes']])
    if (sha256(data) != p['sha256'] or zlib.crc32(data) != p['crc32']
            or sha256(data[:compiled['bytes']]) != compiled['sha256']):
        raise ValueError('Changed embedded creature save entries')
    addresses = sorted(set(compiled['symbols'].values()))
    patches = []
    for row in prior['equipment_resources']['console_storage']['compiled']['dispatch']:
        address = compiled['symbols'][row['name']]
        end = min((a for a in addresses if a > address), default=p['ram']+compiled['bytes'])
        if address != row['target'] or not p['ram'] <= address < end <= p['ram']+compiled['bytes'] or end-address < 8:
            raise ValueError('Unbounded embedded save entry: '+row['name'])
        target = prepared['compiled']['symbols'][row['name']]
        at = address-p['ram']; before = data[at:at+8]
        after = struct.pack('>2I', jump(target), 0); data[at:at+8] = after
        patches.append(dict(name=row['name'], address=address, target=target,
            before=before.hex(), after=after.hex()))
    replacement = dict(compiled, prepared_sha256=compiled['sha256'],
        sha256=sha256(data[:compiled['bytes']]), diary_storage_dispatch=patches)
    insects['compiled'] = replacement
    p.update(sha256=sha256(data), crc32=zlib.crc32(data))
    insects['physical_resource']['sha256'] = sha256(data)
    equipment['console_storage']['creature_runtime'] = copy.deepcopy(replacement)
    for name in ('codec', 'runtime'):
        equipment['creature_fish']['world']['save'][name] = copy.deepcopy(replacement)
    updates['room_surfaces']['save']['creature_canonical_codec'] = copy.deepcopy(replacement)
    updates['save_codec']['active_codec_code'] = copy.deepcopy(replacement)
    updates['save_runtime']['creature_runtime_code'] = copy.deepcopy(replacement)
    updates['clothing']['save_extension']['active_codec_code'] = copy.deepcopy(replacement)
    write = dict(insects['physical_resource'],
        previous_sha256=prior['equipment_resources']['creature_insects']['packet']['sha256'])
    return write, bytes(data), patches


def install(base, prior, blob, core, output, directories):
    from v3_furniture_install import owner_tail_storage
    paths, prepared, ui, screen, layout, packets = load(base, prior, directories)
    equipment = copy.deepcopy(prior['equipment_resources'])
    updates, dispatch = redirect_storage(prior, equipment, blob, prepared)
    changes, hooks = install_menus(base, core, paths, ui)
    files = by_vrom(base)
    interaction = native_contract(base)
    if interaction != prepared['native_interaction']:
        raise ValueError('Changed complete prepared diary room binding')
    room = bytearray(files[interaction['room_vrom']].extract(base))
    at = interaction['hook_address']-interaction['room_ram']
    target = ui['compiled']['symbols']['af_diary_room_move']
    after = struct.pack('>I', 0x0C000000|(target>>2 & 0x3FFFFFF))+room[at+4:at+8]
    room[at:at+8] = after
    rel = files[0x844400].extract(base)
    header = list(struct.unpack_from('>5I', rel))
    rows = list(struct.unpack_from('>'+str(header[4])+'I', rel, 20))
    rows.remove(interaction['remove_relocation']); header[4] = len(rows)
    relocation = (struct.pack('>5I', *header)+struct.pack('>'+str(len(rows))+'I', *rows)).ljust(len(rel)-4, b'\0')+rel[-4:]
    changes.update({interaction['room_vrom']: bytes(room), 0x844400: relocation})
    interaction.update(installed=True, hook_after=after.hex(), target=target,
        installed_owner_sha256=sha256(room), installed_relocation_sha256=sha256(relocation))

    records = copy.deepcopy(prior.get('physical_resources', []))
    replacement, data, embedded_dispatch = redirect_embedded_storage(base, prior, equipment, updates, prepared)
    records = [dict(equipment['creature_insects']['physical_resource']) if r['id'] == replacement['id'] else r
               for r in records]
    staging = bytearray(base); staging[replacement['physical']:replacement['physical']+len(data)] = data
    writes = [(replacement, data)]; installed_packets = {}
    for name, data in packets.items():
        record = physical.allocate(staging, records, data, 'diary-'+name+'-GAFE01-r0')
        records.append(record); writes.append((record, data))
        staging[record['physical']:record['physical']+len(data)] = data
        ram = LAYOUT['code']['ram'] if name == 'storage' else MEMORY['code' if name == 'ui' else 'art'][0]
        installed_packets[name] = dict(record, ram=ram, crc32=zlib.crc32(data), storage='physical-ROM', guard=GUARD.hex())
        write_new(output/('diary-'+name+'.bin'), data)
    # The complete prepared overlays contain deliberate checked prefix edits,
    # not append-only resources. Preserve their old allocations and compressed
    # relocation predecessor while assigning new logical identities together.
    menu_changes = [(r[key], changes[r[key]]) for r in hooks['menus'].values() for key in ('vrom', 'reloc')]
    placements = owner_tail_storage(base, files, menu_changes, reservations=records)
    growth = []
    for row in placements:
        vrom = row['vrom']; entry = files[vrom]
        target = next(r['target_vrom' if vrom == r['vrom'] else 'target_reloc']
                      for r in hooks['menus'].values() if vrom in (r['vrom'], r['reloc']))
        growth.append(dict(row, previous_bytes=entry.size, previous_physical=entry.pstart,
            previous_compressed_end=entry.pend, previous_sha256=sha256(entry.extract(base)),
            target_vrom=target, relocated=True, relocated_blockers=[], retains_old_allocation=True))
    equipment['diaries'] = dict(format='AFV3-DIARY-INSTALLED-1', packets=installed_packets,
        compiled=dict(prepared['compiled'], ram=LAYOUT['code']['ram']), ui_compiled=ui['compiled'],
        memory=layout, hooks=hooks, room=interaction, stable_storage_entries=dispatch,
        embedded_storage_entries=embedded_dispatch,
        prepared={k: str(v.relative_to(ROOT)) for k, v in paths.items()},
        prepared_sha256={k: sha256((paths[k]/f).read_bytes()) for k, f in
            (('core', 'diaries.json'), ('ui', 'ui.json'), ('screen', 'screen.json'))},
        screen_sha256=screen['sha256'], additional_resident_bytes=sum(r['bytes'] for r in layout.values()),
        installed=True, selectable=False, choices_added=0, web_patcher_enabled=False,
        native_execution_tested=False, ordinary_save_reload_tested=False,
        pending=['Carried identity/readers and complete profile/selector integration',
                 'Actual event participation callers', 'Connected native UI/save verification'],
        sources={p: sha256((ROOT/p).read_bytes()) for p in (*prepared['sources'], *ui['sources'], *SOURCES)})
    updates.update(physical_resources=records, resource_growth=growth)
    return equipment, changes, updates, writes
