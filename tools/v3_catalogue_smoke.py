"""Current native catalogue initialization, selection, names, and model DMA."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from catalogue_names import APPROVED, Image
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_catalogue import RAM, RELOC, SIZE, VROM
from v3_npc_draw_smoke import boot_proofs


def held_previews(debug, rom_path, record):
    """Shared parent category: real list/selection, names, models, and prices."""
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    cat=report['catalogue'];equipment=report['equipment_resources'];category=cat['handheld']
    if sha256(rom)!=report['output_sha256'] or category['category']!='umbrella':
        raise ValueError('Shared parent catalogue requires its checked cartridge/category')
    files,boot=by_vrom(rom),boot_proofs(rom);blob=files[BLOB].extract(rom)
    rows=category['imports'];parents={r['item_id']:r for r in equipment['parent_readers']['rows']}
    pending=equipment.get('optional_selection',{}).get('pending',{})
    if pending:
        rows=[r for r in equipment['catalogue']['imports'] if parents[r['parent_item_id']]['id'] in pending]
        if len(rows)!=len(pending):raise ValueError('Incomplete pending category fixture')
    bridge=None
    def check(label,address,want):
        actual=debug.read_memory(address,len(want));passed=actual==want
        record(dict(held_catalogue_check=label,address=f'{address:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',expected_sha256=sha256(want),actual_sha256=sha256(actual)))
        if not passed:raise ValueError('Shared parent catalogue mismatch: '+label)
    def call(address,args=(),proof=None,expected=None):
        target=address;proof=proof or boot.get(address)
        if address>=0x80400000:
            if bridge is None:raise ValueError('Missing upper-memory call bridge')
            stub=struct.pack('>2I',0x08000000|((address>>2)&0x3FFFFFF),0)
            debug.write_memory(bridge,stub)
            call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            target=bridge;proof=(bridge,stub)
        result=debug.call(f'{target:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof)
        if expected is not None:result['assertion']='passed' if result['return_value']==expected else 'failed'
        record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError('Shared parent catalogue returned an unexpected value')
        return result['return_value']
    def put(address,*values):debug.write_memory(address,struct.pack('>'+'I'*len(values),*values))
    check('complete startup prefix',BLOB_RAM,blob[:0xC000])
    at=equipment['blob_offset'];check('complete equipment readers',0x804A3000,blob[at:at+equipment['bytes']])
    size=0x20000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Shared catalogue fixture allocation failed')
    root,submenu,stub,bridge=(allocation+n for n in (16,0x11000,0x11100,0x11120))
    banks=[allocation+0x13000,allocation+0x17C00]
    programs=[allocation+0x15800,allocation+0x1A400]
    capacity=cat['capacity_expansion'];state=root+capacity['state_offset']
    page=state+0xEC8+4*capacity['page_bytes']
    data,reloc=(files[v].extract(rom) for v in (VROM,RELOC))
    if (sha256(data),sha256(reloc))!=(cat['output_sha256'],cat['relocation_sha256']):
        raise ValueError('Changed complete catalogue image or relocation')
    if root+len(data)+len(reloc)>=allocation+0x10628:
        raise ValueError('Shared catalogue fixture overlaps owner callbacks')
    loaded=relocate_verified_data(Image(RAM,len(data),struct.unpack_from('>5I',reloc)),data,reloc,root)
    debug.write_memory(allocation,bytes(size))
    call(0x800262D0,[VROM,VROM+len(data),RAM,RAM+len(data),root,root+len(data),len(reloc)])
    check('complete actual loaded catalogue',root,loaded);proof=(root,loaded[:14048])
    # Existing catalogue fixture replaces only entry-animation movement.
    debug.write_memory(stub,bytes.fromhex('03E0000800000000'))
    call(0x8002FE00,[stub,8]);call(0x80034CE0,[stub,8])
    put(submenu+0x2C,allocation);put(allocation+0x106B0,stub);put(allocation+0x10720,state)
    player=0x80126EC0
    saved={a:debug.read_memory(a,n) for a,n in ((player,0xBD0),(0x80136FD8,4),
        (0x80460020,192),(0x8046C000,864),(0x801458B8,4),(0x8010FD60,4),
        (TEST_STACK-0x800,16),(TEST_STACK+0x40,16))}
    edge=b'V3HC'*4;guards=[allocation,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40]
    for bank,program in zip(banks,programs):guards += [bank-16,bank+0x2400,program-16,program+0x2000]
    for address in guards:debug.write_memory(address,edge)
    init,name_at=(APPROVED['symbols'][k]+capacity['insert_bytes'] for k in ('af_catalog_init','af_catalog_name'))
    selected=bytearray(saved[0x80460020])
    for row in parents.values():selected[row['profile_byte']]|=row['profile_mask']
    def initialize():
        debug.write_memory(state,bytes(capacity['state_bytes']))
        for n,(program,bank) in enumerate(zip(programs,banks)):
            put(state+8+n*0x760+0x740,program,bank);debug.write_memory(bank,b'\xA5'*0x2400)
        call(root+init,[submenu],(root+init,loaded[init:init+40]))
    try:
        debug.write_memory(0x80460020,selected);call(0x80469200,expected=1)
        put(0x80136FD8,player);put(0x8010FD60,0);debug.write_memory(player,bytes(0xBD0))
        initialize();check('uncollected parents stay absent',page,bytes(2))
        for row in rows:
            parent=int(row['parent_item_id'],16);display=int(row['item_id'],16)
            call(0x800B88EC,[parent])
            call(0x800BEFCC,[parent],expected=display if row.get('room_placement_uses_display') else parent)
            call(0x800BF10C,[display+3],expected=parent)
            if pending:
                selected_kind=next(r for r in equipment['player_actions']['equipment_selection']['rows'] if int(r['item_id'],16)==parent)
                call(equipment['player_actions']['code']['symbols']['af_v3_player_selected_equipment'],
                     [parent],expected=selected_kind['native_kind'])
                call(equipment['player_actions']['code']['symbols']['af_v3_player_passive_equipment'],
                     [selected_kind['native_kind']],expected=0)
        if pending:
            # The shipped catalogue deliberately excludes unfinished choices.
            # Verify that first, then supply only temporary list/count data to
            # exercise installed new models without enabling a release profile.
            from v3_catalogue import UMBRELLA_COUNT
            initialize();check('pending tools absent from real catalogue counts',page,bytes(2))
            table=root+category['table_address']-RAM
            debug.write_memory(table+64,b''.join(struct.pack('>H',r['catalogue_index']) for r in rows))
            put(root+UMBRELLA_COUNT-RAM,32+len(rows))
        initialize()
        check('all collected parent entries',page,struct.pack('>H',len(rows)))
        check('actual donor category ordering',page+8,b''.join(bytes.fromhex(r['item_id']) for r in rows))
        check('partial category indicator',page+6,bytes(1))
        room_rows=[r for r in rows if r.get('room_placement_uses_display')]
        positions={0,len(rows)-1}
        if pending:positions=set(range(len(rows)))
        if room_rows:
            positions.update(rows.index(r) for r in (min(room_rows,key=lambda r:r['object_bytes']),
                max(room_rows,key=lambda r:r['object_bytes'])))
        for position in sorted(positions):
            # Native seven-name page cache: scroll the last record into slot zero.
            debug.write_memory(page+2,struct.pack('>HH',position,0))
            call(root+0x808A6A8C-RAM,[submenu,4],proof)
            buffer=debug.read_memory(state,1)[0]
            if buffer not in (0,1):raise ValueError('Invalid native preview buffer')
            row=rows[position];parent=parents[row['parent_item_id']];preview=state+8+buffer*0x760
            check('selected display identity',preview,struct.pack('>H',row['catalogue_index']))
            check('actual resident profile',preview+0x748,bytes.fromhex(row['profile_ram']))
            check('actual parent price',preview+0x754,struct.pack('>I',parent['price']))
            check('complete donor framing',preview+0x758,struct.pack('>ff',1,36))
            check('centred model height',preview+12,struct.pack('>f',0))
            at=int(row['object_vrom'],16)-BLOB;asset=blob[at:at+row['object_bytes']]
            check('complete prepared model transfer',banks[buffer],asset)
            check('unchanged model buffer tail',banks[buffer]+len(asset),b'\xA5'*(0x2400-len(asset)))
            if row.get('room_placement_uses_display'):
                check('real catalogue constructor initializes room-rig work',preview+0x158,
                      struct.pack('>2I',preview+0x1A4,preview+0x1DA))
                check('room-rig initial state in the real catalogue',preview+0x204,struct.pack('>2f',0,.5))
            name=call(root+name_at,[page+capacity['name_offset']],(root+name_at,loaded[name_at:name_at+92]))
            check('full English parent name',name,parent['name'].encode().ljust(16,b' '))
        # Profile removal hides an owned item without clearing its collection.
        parent=parents[rows[0]['parent_item_id']]
        selected[parent['profile_byte']]&=~parent['profile_mask']
        debug.write_memory(0x80460020,selected);debug.write_memory(0x8046C010,selected)
        initialize();check('disabled owned parent hidden',page,struct.pack('>H',len(rows)-1))
        call(0x80465000,[rows[0]['runtime_index']],expected=0)
        debug.write_memory(player+0xAF0,b'\xFF'*120)
        initialize();check('original umbrella rows retained',page,struct.pack('>H',32+len(rows)-1))
        call(root+0x808A627C-RAM,[state+8,0x1004],proof)
        check('original preview fallback',state+8,bytes.fromhex('0001'))
        for address in guards:check('allocation or stack guard',address,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
        check('equipment guard',0x804A3000+equipment['bytes']-16,bytes.fromhex('AF48C0DE')*4)
        check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    finally:
        for address,value in saved.items():debug.write_memory(address,value)
        call(0x8009C040,[allocation])
    for address,value in saved.items():check('restored fixture state',address,value)
    return dict(native_parent_catalogue=True,category_rows=len(rows),complete_preview_models=len(positions),
        temporary_pending_list=bool(pending),pending_choices_remain_disabled=bool(pending),
        gpu_rendered=False,ordinary_order_delivery_tested=False,saved_data_written=False,
        requires_checkpoint_restore=True)


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    cat = report.get('catalogue')
    if sha256(rom) != report['output_sha256'] or not cat:
        raise ValueError('Catalogue probe needs the exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:0xC000]
    selected = cat['imports']
    item_ids = [int(row['item_id'],16) for row in selected]
    models = {int(row['item_id'],16):row for row in report['furniture']['imports']}
    metadata = {int(row['item_id'],16):row for row in report['furniture_items']['imports']}
    speed_bag = report.get('speed_bag') if 0x3350 in item_ids else None
    expanded = cat.get('capacity_expansion')
    growth = expanded['insert_bytes'] if expanded else 0
    name_offset = expanded['name_offset'] if expanded else 0x380
    page_bytes = expanded['page_bytes'] if expanded else 966
    if speed_bag:
        models[0x3350] = metadata[0x3350] = speed_bag
    calls = 0

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'catalogue_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Catalogue native check failed: ' + label)

    def call(address, args=(), proof=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result); calls += 1
        return result['return_value']

    def put(at, *values):
        debug.write_memory(at, struct.pack('>' + 'I' * len(values), *values))

    check('complete current resident prefix', BLOB_RAM, blob)
    size = 0x20000 if expanded else 0x1C000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Catalogue fixture allocation failed')
    root, submenu, stub, overlay = (allocation + n for n in ((16, 0x11000, 0x11100, 0) if expanded else (16, 0xF000, 0xF100, 0)))
    # These entry points only use overlay + 10628..10723. Its earlier fields
    # are not accessed, so those addresses may share the owned code allocation;
    # do not reserve an otherwise unused second 64-KiB window at title boot.
    banks = [allocation + n for n in ((0x13000, 0x17C00) if expanded else (0x11000, 0x15C00))]
    programs = [allocation + n for n in ((0x15800, 0x1A400) if expanded else (0x13800, 0x18400))]
    state = root + 0x9910
    page = state + 0xEC8
    debug.write_memory(allocation, bytes(size))
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    if sha256(data) != cat['output_sha256'] or sha256(reloc) != cat['relocation_sha256']:
        raise ValueError('Changed catalogue proof')
    if root + len(data) + len(reloc) >= overlay + 0x10628:
        raise ValueError('Catalogue fixture overlaps owner callbacks')
    loaded = relocate_verified_data(Image(RAM, len(data), struct.unpack_from('>5I', reloc)),
                                     data, reloc, root)
    call(0x800262D0, [VROM, VROM + len(data), RAM, RAM + len(data),
                      root, root + len(data), len(reloc)])
    check('complete actual native-relocated catalogue', root, loaded)
    core_proof = (root, loaded[:14048])
    # Only entry-animation movement is substituted. Native list construction,
    # name caching, preview initialization, selection, and DMA run unchanged.
    debug.write_memory(stub, bytes.fromhex('03E0000800000000'))
    call(0x8002FE00, [stub, 8]); call(0x80034CE0, [stub, 8])
    put(submenu + 0x2C, overlay)
    put(overlay + 0x106B0, stub)
    put(overlay + 0x10720, state)
    edge = b'V3CA' * 4
    guards = [allocation, allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40]
    for bank, program in zip(banks, programs):
        guards += [bank - 16, bank + 0x2400, program - 16, program + 0x2000]
    for at in guards:
        debug.write_memory(at, edge)
    player, active_at, runtime_at = 0x80126EC0, 0x80136FD8, 0x8046C000
    old_player, old_active = debug.read_memory(player, 0xBD0), debug.read_memory(active_at, 4)
    profile_bytes = len(bytes.fromhex(report['save_runtime']['profile_hex']))
    runtime_bytes = report['save_runtime']['state_bytes']
    ownership_bytes = 640 if profile_bytes==192 else 512
    old_runtime = debug.read_memory(runtime_at, runtime_bytes)
    old_speed_bag_flag = debug.read_memory(0x80467134,4) if speed_bag else None
    old_segment = debug.read_memory(0x801458B8, 4)
    old_debug = debug.read_memory(0x8010FD60, 4)
    init = APPROVED['symbols']['af_catalog_init'] + growth
    name_at = APPROVED['symbols']['af_catalog_name'] + growth

    def initialize():
        debug.write_memory(state, bytes(expanded['state_bytes'] if expanded else 12576))
        for n, (program, bank) in enumerate(zip(programs, banks)):
            put(state + 8 + n * 0x760 + 0x740, program, bank)
        call(root + init, [submenu], (root + init, loaded[init:init + 40]))

    def preview(n, item):
        at = state + 8 + n * 0x760
        row, meta = models[item], metadata[item]
        profile = int.from_bytes(blob[0x5800 + row['runtime_index'] * 4:0x5804 + row['runtime_index'] * 4], 'big')
        check('actual imported preview profile', at + 0x748, struct.pack('>I', profile))
        check('original catalogue index encoding', at, struct.pack('>H', (item - 0x1000) >> 2))
        check('furniture preview type and native timer', at + 0x750, struct.pack('>HH', 0, 15))
        check('actual catalogue price', at + 0x754, struct.pack('>I', meta['price']))
        check('donor-matched draw scale and native viewing height', at + 0x758,
              struct.pack('>ff', 0.9, 42.0))
        check('donor-matched preview vertical position', at + 12, struct.pack('>f', -3.0))
        start = int(row['object_vrom'], 16) - BLOB
        check('complete actual model bank DMA', banks[n],
              files[BLOB].extract(rom)[start:start + row['object_bytes']])
        if item==0x3350:
            check('catalogue invokes the installed animated constructor',at+0x14C,
                  struct.pack('>II',banks[n]+0xE84,banks[n]+0xE58))
            check('animated catalogue preview has its complete initial pose',at+0x1A4,
                  struct.pack('>9h',800,6508,800,0,0,-16384,0,0,0))

    try:
        if speed_bag: put(0x80467134,1)
        put(active_at, player); put(0x8010FD60, 0)
        debug.write_memory(player + 0xAF0, bytes(0x98))
        debug.write_memory(runtime_at + 16 + profile_bytes, bytes(ownership_bytes))
        initialize()
        check('uncollected imports stay out of catalogue', page, bytes(2))
        for item in item_ids: call(0x800B88EC,[item])
        initialize()
        check('all collected imports appear', page, struct.pack('>H',len(item_ids)))
        order = struct.pack('>'+'H'*len(item_ids),*item_ids)
        check('stable real item IDs in donor catalogue order', page + 8, order)
        check('partial collection is not marked complete', page + 6, bytes(1))
        for n, item in enumerate(item_ids[:7]):
            address = call(root + name_at, [page + name_offset + n * 10],
                           (root + name_at, loaded[name_at:name_at + 92]))
            if not root + 0x9910 <= address <= root + len(data) - 16:
                raise ValueError('Catalogue full name escaped owned storage')
            check('complete displayed English catalogue name', address, metadata[item]['name'].encode().ljust(16, b' '))
        selected_previews = ([(item_ids.index(item), item) for item in (0x31F8, 0x322C)] if expanded
                             else list(enumerate(item_ids[1:], 1)))
        if not expanded: preview(0,item_ids[0])
        for turn, (n,item) in enumerate(selected_previews, 1):
            debug.write_memory(page+4,struct.pack('>H',n))
            call(root + 0x808A6A8C - RAM, [submenu, 0], core_proof)
            check('native selection switches preview buffers', state, bytes([turn & 1]))
            preview(turn & 1,item)
        # Test the true maximum with all native furniture plus selected additions.
        # Native category construction and full-name storage retain their sizes.
        debug.write_memory(player + 0xAF0, b'\xFF' * 120)
        initialize()
        check('complete additive furniture list count', page, struct.pack('>H',436+len(item_ids)))
        check('complete collection indicator', page + 6, bytes([1]))
        check('last imported entries fit the native category', page + 8 + 436 * 2, order)
        if expanded:
            check('unused furniture slots do not spill into names', page + 8 + cat['total_rows'] * 2,
                  bytes((cat['row_capacity'] - cat['total_rows']) * 2))
            check('navigation tail initializes all nine pages', state + expanded['page_order_offset'], bytes(range(9)))
            # A nonzero category exercises the changed stride in selection and
            # name reload, while retaining the complete independent garment list.
            for row in cat['clothing']['imports']: call(0x800B88EC, [int(row['pocket_item_id'], 16)])
            initialize()
            clothes = page + 3 * page_bytes
            clothing_count = cat['clothing']['total_rows']
            check('complete independent garment count', clothes, struct.pack('>H', clothing_count))
            check('garment completion flag', clothes + 6, bytes([1]))
            expected = b''.join(struct.pack('>H', 0x1000 + i * 4) for (i,) in
                struct.iter_unpack('>H', data[cat['clothing']['table_address'] - RAM:cat['clothing']['table_address'] - RAM + clothing_count * 2]))
            check('all native and imported garments retain their order', clothes + 8, expected)
            debug.write_memory(clothes + 2, struct.pack('>HH', clothing_count - 7, 6))
            call(root + 0x808A6A8C - RAM, [submenu, 3], core_proof)
            selected = cat['clothing']['imports'][-1]
            check('last garment is selected from the resized page', state + 8 + 0x760,
                  struct.pack('>H', selected['catalogue_index']))
            address = call(root + name_at, [clothes + name_offset + 60],
                           (root + name_at, loaded[name_at:name_at + 92]))
            garment = next(r for r in report['clothing']['imports'] if r['item_id'] == selected['pocket_item_id'])
            check('scrolled garment full name stays inside its cache', address, garment['name'].encode().ljust(16, b' '))
        # Original complete program and model loaders still run through fallback.
        call(root + 0x808A627C - RAM, [state + 8, 0x1004], core_proof)
        check('original preview keeps original index', state + 8, bytes.fromhex('0001'))
        check('original preview keeps original furniture type', state + 8 + 0x750, bytes(2))
        if speed_bag: debug.write_memory(0x80467134,old_speed_bag_flag)
        check('complete resident prefix retained', BLOB_RAM, blob)
        check('catalogue executable prefix unchanged by menu work', root, loaded[:14048])
        check('catalogue suffix retained', root + SIZE + growth, loaded[SIZE + growth:])
        for at in guards:
            check('fixture guard', at, edge)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        if speed_bag: debug.write_memory(0x80467134,old_speed_bag_flag)
        debug.write_memory(player, old_player); debug.write_memory(active_at, old_active)
        debug.write_memory(runtime_at, old_runtime); debug.write_memory(0x801458B8, old_segment)
        debug.write_memory(0x8010FD60, old_debug)
    call(0x8009C040, [allocation])
    return {'catalogue_native_calls': calls, 'native_list_and_full_name_cases': 3,
            'imported_complete_previews': len(selected_previews) if expanded else len(item_ids), 'native_selection_tested': True,
            'expanded_category_layout_tested': bool(expanded),
            'original_preview_fallback_tested': True, 'gpu_rendered': False,
            'ordinary_order_delivery_tested': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
