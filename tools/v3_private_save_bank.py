"""Bind shared save/load work to owned RAM rather than the disposable scene heap."""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_console_disk_install import reservations
from v3_import_storage import jump
import v3_physical_resources as physical

RAM, END, CODE = 0x804E3000, 0x804F4980, 0x804F3100
CONSOLE_RAM, CONSOLE_BYTES = 0x804DE200, 0x4E00
MAGIC, GUARD = 0x41465042, 0xAF53B0DE
RETAINED_STATE_RAM = 0x806A9080
SOURCES = ('tools/v3_private_save_bank.py', 'tools/v3_furniture_install.py',
    'tools/v3_room_goods.py', 'overlays/v3/surface_bootstrap.c',
    'overlays/v3/private_save_bank.c', 'overlays/v3/private_save_bank.h',
    'overlays/v3/private_save_bank.ld', 'overlays/v3/console_storage.c',
    'tools/v3_console_disk_install.py')
# Whole installed functions authenticate all retained branches and delay slots.
FUNCTIONS = (
    ('af_v3_diary_preflight', 0x80670538, 0x80670614,
     '31757af09cf9664df92b826d9616374258f8eebe951c2e4167834a1ff846c569',
     ((0x80670560, 'acquire'), (0x806705EC, 'release'))),
    ('af_v3_save_sync', 0x806706D4, 0x8067088C,
     '79dbeaedfcea2c7c7c1a79e658d91e8558603783a83e5a3d4d08c0a75122f8d7',
     ((0x80670708, 'acquire'), (0x8067079C, 'release'))),
    ('af_cw_save_sync', 0x807C3968, 0x807C3B18,
     '693c9a361677346cfcce48a8ff2131c2c42b61259cdaecf2117a37ef04025d54',
     ((0x807C39A0, 'acquire'), (0x807C3A78, 'release'))),
)


def authenticate_retirement(prior, blob):
    e = prior['equipment_resources']; s = e['console_storage']
    if (s.get('retired_scratch') != dict(ram=RAM, bytes=END-RAM, guard=END)
            or e.get('private_save_bank') or prior['save_codec']['format_version'] != 21
            or prior['save_runtime']['state_bytes'] != 1264
            or sorted(set((a, b) for a, b in reservations(prior)
                          if a < END and RAM < b)) != [(RAM, END)]):
        raise ValueError('Private bank workspace is not exclusively retired scratch')
    p = s['packet']; raw = blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    if (p['ram'] != CONSOLE_RAM or p['bytes'] != CONSOLE_BYTES
            or p['ram']+p['bytes'] != RAM or sha256(raw) != p['sha256']
            or zlib.crc32(raw) != p['crc32']):
        raise ValueError('Changed complete retired-scratch predecessor')
    entries = s['compiled']['dispatch']
    if len(entries) != 23 or len({r['address'] for r in entries}) != 23:
        raise ValueError('Incomplete original scratch-owner export retirement')
    for row in entries:
        at = row['address']-CONSOLE_RAM
        target = row['target']
        if (not 0 <= at <= len(raw)-8 or not 0x80670000 <= target < 0x80676000
                or raw[at:at+8] != bytes.fromhex(row['after'])
                or raw[at:at+8] != struct.pack('>2I', jump(target), 0)):
            raise ValueError('Old scratch export remains live: '+row['name'])
    for code in (prior['save_runtime']['diary_runtime_code'], e['bank']['code']):
        if ('-DAF_V3_DIARY_STORAGE=1' not in code['flags'] or
                '-DAF_DIARY_SCRATCH_RAM=0x80682000u' not in code['flags']):
            raise ValueError('Active save owner still uses obsolete console scratch')
    return bytes(raw), dict(retired_export_count=len(entries),
        retired_exports=copy.deepcopy(entries), active_scratch_ram=0x80682000,
        retired_scratch=copy.deepcopy(s['retired_scratch']))


def refresh_aliases(value, previous, replacement):
    """Update live packet aliases only, leaving historical smaller copies intact."""
    if isinstance(value, dict):
        if all(value.get(k) == previous[k] for k in ('id', 'physical', 'bytes', 'sha256')):
            value.update(copy.deepcopy(replacement))
        for item in value.values():
            refresh_aliases(item, previous, replacement)
    elif isinstance(value, list):
        for item in value:
            refresh_aliases(item, previous, replacement)


def refresh_code(value, before, after, ram):
    if isinstance(value, dict):
        address, n = value.get('ram'), value.get('bytes')
        at = address-ram if type(address) is int else -1
        if (type(n) is int and 0 <= at < at+n <= len(before)
                and value.get('sha256') == sha256(before[at:at+n])):
            value.setdefault('compiled_sha256', value['sha256'])
            value['sha256'] = sha256(after[at:at+n])
            if 'crc32' in value:
                value['crc32'] = zlib.crc32(after[at:at+n])
        for item in value.values():
            refresh_code(item, before, after, ram)
    elif isinstance(value, list):
        for item in value:
            refresh_code(item, before, after, ram)


def bind_function(raw, ram, contract, targets):
    name, first, last, digest, calls = contract
    a, b = first-ram, last-ram
    if not 0 <= a < b <= len(raw) or sha256(raw[a:b]) != digest:
        raise ValueError('Changed complete allocating save consumer: '+name)
    patches = []
    for address, kind in calls:
        at = address-ram
        if u32(raw, at) != 0x0040F809:  # jalr v0; exact native argument delay retained.
            raise ValueError('Changed save allocation call ABI')
        after = jump(targets[kind], link=True)
        patches.append(dict(address=address, before=0x0040F809, after=after, kind=kind,
                            delay_slot=u32(raw, at+4)))
        struct.pack_into('>I', raw, at, after)
    return dict(name=name, first=first, last=last, before_sha256=digest,
                after_sha256=sha256(raw[a:b]), patches=patches)


def relocate_retained_state(base, prior, output):
    """Rebind one existing save record, retaining every feature and entry address.

    Authenticate the whole original linked program and every instruction pair
    constructing the record/guard pointer. Rebind only the high address words;
    keep all lower words, registers, branches, delay slots, and symbols intact.
    """
    bank = prior['equipment_resources']['bank']
    old = bank['memory']['account']
    font = prior['equipment_resources']['passwords']['nook']['font']
    title = font['title_buffer']
    from aflib import by_vrom
    native_title = by_vrom(base)[title['resource_vrom']].extract(base)
    if (old != dict(ram=0x807E9080, bytes=64, record_bytes=48, guard_bytes=16)
            or not title['ram'] <= old['ram'] < old['ram']+64 <= title['end']
            or len(native_title) != title['resource_bytes']
            or sha256(native_title) != title['resource_sha256']
            or any(a<RETAINED_STATE_RAM+64 and RETAINED_STATE_RAM<b for a,b in reservations(prior))):
        raise ValueError('Changed retained-state/title-buffer collision or new owned extent')
    directory = ROOT/bank['linked']
    linked_bytes = (directory/'linked.json').read_bytes()
    if sha256(linked_bytes) != bank['linked_sha256']:
        raise ValueError('Changed original saved-owner link receipt')
    linked = json.loads(linked_bytes)
    before = (directory/'bank-code.bin').read_bytes()
    if (sha256(before) != '7f07aa7c9fa5b2b1df2e83ba35036105b6be426d04313b39c2562df0ef330cf9'
            or len(before) != 38336 or sha256(before) != bank['code']['sha256']
            or linked['code']['sha256'] != bank['code']['sha256']):
        raise ValueError('Changed complete saved-state pointer consumer')
    # Every original 9080/90B0 ORI in this authenticated complete program.
    pairs = ((0x807DD8D0,(0x807DD8D8,)), (0x807DDA38,(0x807DDA3C,)),
             (0x807DDD30,(0x807DDD34,0x807DDD78)), (0x807DE120,(0x807DE154,)),
             (0x807DE234,(0x807DE238,)), (0x807DE4D8,(0x807DE4DC,)),
             (0x807DE600,(0x807DE604,)), (0x807DE624,(0x807DE628,)),
             (0x807DE78C,(0x807DE794,)), (0x807DE8E8,(0x807DE8F8,)))
    origin = bank['ram']
    ori_addresses = {origin+at for at in range(0,len(before),4)
                     if u32(before,at)>>26==13 and u32(before,at)&65535 in (0x9080,0x90B0)}
    if ori_addresses != {a for _,lower in pairs for a in lower}:
        raise ValueError('Incomplete retained-state pointer binding set')
    after = bytearray(before)
    changes = []
    for address, lower in pairs:
        at = address-origin; old_word = u32(before,at)
        register = old_word>>16&31
        if old_word>>26 != 15 or old_word&65535 != 0x807E:
            raise ValueError('Changed retained-state high-address instruction')
        for low_address in lower:
            word = u32(before,low_address-origin)
            if word>>26 != 13 or word>>21&31 != register or word&65535 not in (0x9080,0x90B0):
                raise ValueError('Changed retained-state lower-address instruction')
        new_word = old_word&0xFFFF0000 | RETAINED_STATE_RAM>>16
        struct.pack_into('>I',after,at,new_word)
        changes.append(dict(address=address,before=old_word,after=new_word,
                            lower_addresses=list(lower)))
    out = output/'retained_state'; out.mkdir()
    write_new(out/'relocated-code.bin',after)
    return before, after, dict(previous_ram=old['ram'], ram=RETAINED_STATE_RAM, bytes=64,
        record_bytes=48, guard_bytes=16, title_buffer=copy.deepcopy(title), patches=changes,
        before_sha256=sha256(before), after_sha256=sha256(after),
        original_symbols_retained=True, pointer_only_changes=True,
        original_code_reused=True, artwork_recompiled=False,
        initialized_by_existing_save_reset=True)


def install(base, prior, blob, core, module, output):
    del module
    old_console, retirement = authenticate_retirement(prior, blob)
    e = copy.deepcopy(prior['equipment_resources'])
    updates = {k: copy.deepcopy(prior[k]) for k in ('save_runtime', 'save_codec', 'clothing', 'room_surfaces')}
    code, compiled = compile_part('private_save_bank', output/'private_save_bank',
        defines=('AF_PRIVATE_SAVE_BANK_RAM=0x804E3000u',),
        link_symbols={'af_v3_save_halt': prior['save_runtime']['code']['symbols']['af_v3_save_halt']})
    targets = {k: compiled['symbols']['af_v3_private_bank_'+k] for k in ('acquire', 'release')}
    original_saved_code, relocated_saved_code, retained_state = relocate_retained_state(base, prior, output/'private_save_bank')
    payload = bytearray(END-CONSOLE_RAM); payload[:len(old_console)] = old_console
    at = RAM-CONSOLE_RAM
    struct.pack_into('>4I', payload, at, MAGIC, 0, GUARD, GUARD)
    struct.pack_into('>4I', payload, at+16+65536, *([GUARD]*4))
    payload[CODE-CONSOLE_RAM:CODE-CONSOLE_RAM+len(code)] = code
    if RAM+65568 > CODE or CODE+len(code) > END:
        raise ValueError('Complete private bank overlaps its compiled code')
    records = copy.deepcopy(prior['physical_resources'])
    bank = physical.allocate(base, records, payload, 'private-save-bank', best_fit=True)
    packet = dict(bank, ram=CONSOLE_RAM, crc32=zlib.crc32(payload), storage='physical-ROM')
    records.append(bank)
    # Extend one existing preload; do not grow the bounded startup descriptor table.
    old_packet = copy.deepcopy(e['console_storage']['packet'])
    e['console_storage']['retained_packet'] = old_packet
    e['console_storage']['packet'] = copy.deepcopy(packet)
    del e['console_storage']['retired_scratch']
    report = dict(format='AFV3-PRIVATE-SAVE-BANK-INSTALLED-1', installed=True,
        packet=copy.deepcopy(packet), reservation=dict(ram=RAM, bytes=END-RAM),
        workspace=dict(ram=RAM, bytes=65568, bank_ram=RAM+16, bank_bytes=65536),
        code=dict(compiled, ram=CODE), retirement=retirement,
        initialized_by_checked_preload=True, startup_descriptor_growth=0,
        scene_heap_bytes=0, saved_format_changed=False, native_execution_verified=False,
        ordinary_save_reload_verified=False, consumers=[], native_patches=[],
        retained_state=retained_state,
        sources={p: sha256((ROOT/p).read_bytes()) for p in SOURCES})
    writes = [(bank, bytes(payload))]
    owners = [(e['diaries']['packets']['storage'], FUNCTIONS[:2]),
              (e['carried_items']['quest']['packet'], FUNCTIONS[2:])]
    for old, functions in owners:
        previous = copy.deepcopy(old)
        before = base[old['physical']:old['physical']+old['bytes']]
        if sha256(before) != old['sha256']:
            raise ValueError('Changed complete saved-owner physical packet')
        raw = bytearray(before)
        if functions == FUNCTIONS[2:]:
            at = e['bank']['ram']-old['ram']
            if raw[at:at+len(original_saved_code)] != original_saved_code:
                raise ValueError('Actual loaded saved-owner code differs from authenticated original link')
            raw[at:at+len(relocated_saved_code)] = relocated_saved_code
        report['consumers'].extend(bind_function(raw, old['ram'], f, targets) for f in functions)
        replacement = dict(old, sha256=sha256(raw), crc32=zlib.crc32(raw))
        refresh_aliases(e, previous, replacement)
        refresh_aliases(updates, previous, replacement)
        # Loaded code aliases get hashes from actual bytes, never from stale preparations.
        refresh_code(e, before, raw, old['ram'])
        refresh_code(updates, before, raw, old['ram'])
        record = next(r for r in records if r['id'] == old['id'])
        record['sha256'] = replacement['sha256']
        writes.append((dict(record, previous_sha256=previous['sha256']), bytes(raw)))
    e['bank']['memory']['account']['ram'] = RETAINED_STATE_RAM
    def update_flags(value):
        if isinstance(value, dict):
            if value.get('sha256') == sha256(relocated_saved_code) and 'flags' in value:
                value['flags'] = [f.replace('AF_BANK_STATE_RAM=0x807E9080u',
                    f'AF_BANK_STATE_RAM=0x{RETAINED_STATE_RAM:X}u') for f in value['flags']]
            for item in value.values(): update_flags(item)
        elif isinstance(value, list):
            for item in value: update_flags(item)
    update_flags(e); update_flags(updates)
    a, b = 0x8008F968-CODE_RAM, 0x8008FA28-CODE_RAM
    if sha256(core[a:b]) != 'a8279a87758989bed9f29ef7019a0e8cf2912dc2e72fe59853c12ee20825bdf5':
        raise ValueError('Changed complete native allocated loader')
    for address, before, kind in ((0x8008F994, 0x0C026FF0, 'acquire'),
                                  (0x8008FA04, 0x0C027010, 'release')):
        at = address-CODE_RAM
        if u32(core, at) != before:
            raise ValueError('Changed native loader allocation call')
        after = jump(targets[kind], link=True)
        struct.pack_into('>I', core, at, after)
        report['native_patches'].append(dict(address=address, before=before, after=after,
                                             kind=kind, delay_slot=u32(core, at+4)))
    e['private_save_bank'] = report
    updates['physical_resources'] = records
    write_new(output/'private_save_bank/packet.bin', payload)
    write_new(output/'private_save_bank/installed.json',
              (json.dumps(report, indent=2)+'\n').encode())
    return e, {}, updates, writes
