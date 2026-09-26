"""Reusable representative furniture reader/DMA/acquisition check from a build manifest."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM
from v3_npc_draw_smoke import boot_proofs
import v3_furniture_install as runtime
import v3_furniture_runtime as furniture
import v3_catalogue as catalogue


def representatives(rows):
    """Cover each footprint, stock, and layer category, not each item identity."""
    result, covered = [], set()
    for row in sorted(rows,key=lambda r:(-r['object_bytes'],r['item_id'])):
        features={('size',row['size_code']),('stock',row['stock_group']),('sound',row.get('action_sound',0)),
                  ('placement',row.get('layer_type',0)),('interaction',row.get('interaction_flags',0)),
                  ('preview',row.get('preview_mode',0)),
                  ('lighting',bytes.fromhex(row['native_profile_scalar_hex'])[11]),
                  ('contact',bytes.fromhex(row['native_profile_scalar_hex'])[12]),
                  ('layers',tuple(sorted(row.get('model_offsets',{}))))}
        if features-covered: result.append(row); covered.update(features)
    if len(result)>12: raise ValueError('Split new behaviour categories into bounded smoke passes')
    return result


def pocket_icons(debug, rom_path, record):
    """Actual loaded submenu drawing for one shared imported icon category."""
    from v3_furniture_icon import VROM, RELOC, RAM, RESIDENT
    from runtime_layout import TEST_STACK
    from v3_furniture_room_smoke import extend
    path=Path(rom_path);image=path.read_bytes()
    report=json.loads((path.parent/'build.json').read_bytes())
    equipment=report['equipment_resources'];icons=equipment['pocket_icons']
    if sha256(image)!=report['output_sha256']:
        raise ValueError('Pocket-icon probe requires its exact current cartridge')
    files,boot=by_vrom(image),boot_proofs(image)
    blob=files[runtime.BLOB].extract(image);start=equipment['blob_offset']
    module=blob[start:start+equipment['bytes']]
    def check(label,at,expected):
        actual=debug.read_memory(at,len(expected))
        record(dict(pocket_icon_check=label,address=f'{at:08X}',bytes=len(expected),
                    assertion='passed' if actual==expected else 'failed'))
        if actual!=expected:raise ValueError('Pocket-icon mismatch: '+label)
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    check('complete equipment module and resources',0x804A3000,module)
    check('original selected profile',0x80460020,blob[0x20:0xE0])
    saved={at:debug.read_memory(at,n) for at,n in ((0x8010DCEC,4),(0x80460020,192))}
    size=0x18000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Pocket-icon fixture allocation outside native heap')
    root,graph,gfx,stack=(allocation+n for n in (16,0x14000,0x14600,0x16800))
    debug.write_memory(allocation,bytes(size))
    guards=(allocation,graph-16,gfx-16,gfx+0x1000,stack-0x800,stack+0x200,
            allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    edge=b'V3PI'*4
    for at in guards:debug.write_memory(at,edge)
    data,rel=(files[v].extract(image) for v in (VROM,RELOC))
    if sha256(data)!=icons['owner_sha256'] or sha256(rel)!=icons['relocation_sha256']:
        raise ValueError('Changed pocket-icon parent binding')
    sections=struct.unpack_from('>5I',rel)
    loaded=relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=RESIDENT,sections=sections),
                                 data,rel,root,address_constants=(RAM+RESIDENT,))
    call(0x800262D0,[VROM,VROM+len(data),RAM,RAM+RESIDENT,root,root+RESIDENT,len(rel)])
    check('complete actual loaded parent and BSS',root,loaded)
    proof=(root,loaded[:sections[0]])
    selection={r['item_id']:r for r in equipment['parent_readers']['rows']}
    rows=icons['rows'];first,second=rows[0],rows[-1]
    pending=equipment.get('optional_selection',{}).get('pending',{})
    pending_rows=[r for r in rows if r['id'] in pending]
    if pending_rows:first,second=pending_rows[0],pending_rows[-1]
    def selected(row):
        profile=bytearray(saved[0x80460020])
        for p in selection.values():profile[p['profile_byte']]&=~p['profile_mask']
        if row:
            p=selection[row['item_id']];profile[p['profile_byte']]|=p['profile_mask']
        debug.write_memory(0x80460020,profile)
    try:
        put(0x8010DCEC,root);selected(first)
        # Exercise the installed hook with live upper GPR halves and HI/LO.
        before=debug.command('g')
        regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
        if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:
            raise ValueError('Pocket-icon hook requires paused native game frame')
        for i in range(1,32):
            if i not in (26,27):regs[i]=(0x13579000+i)<<32|(0x2468A000+i)
        item=int(first['item_id'],16)
        regs[16],regs[14]=item,(item&255)*8
        regs[29],regs[37]=extend(stack),extend(root+icons['hook']['address']-RAM)
        regs[33],regs[34]=0x123456789ABCDEF0,0xFEDCBA9876543210
        target=root+0x8085C95C-RAM;bp=f'0,{target:x},4'
        if debug.command('Z'+bp)!='OK':raise ValueError('Pocket-icon breakpoint refused')
        try:
            if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':
                raise ValueError('Pocket-icon register write refused')
            stopped=debug.command('c');raw=debug.command('g')
            actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
            wanted=regs.copy();wanted[15]=extend(first['descriptor_ram']-regs[14])
            changed={str(i):[f'{wanted[i]:016X}',f'{actual[i]:016X}']
                     for i in (*range(26),28,29,30,31,33,34,*range(38,70)) if wanted[i]!=actual[i]}
            passed=not changed and stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==target
            record(dict(pocket_icon_register_window=first['item_id'],differences=changed,
                        assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Pocket-icon hook changed unrelated registers or continuation')
        finally:
            debug.command('z'+bp);debug.command('G'+before)
        cases=((first,first,0),(second,first,0),(second,second,0),(first,None,0),
               (first,None,1),(0x2200,None,0),(0x2223,None,0))
        if pending_rows:
            cases+=tuple((r,r,0) for r in pending_rows[1:-1])
            retained=next(r for r in rows if r['id'] not in pending)
            cases+=((retained,retained,0),)
        segments=debug.read_memory(0x801458A0,64)
        segment_bases=struct.unpack('>16I',segments)
        for row,enabled,wrapped in cases:
            selected(enabled);item=int(row['item_id'],16) if isinstance(row,dict) else row
            debug.write_memory(gfx,bytes(0x1000));put(graph+0x298,gfx,gfx+0x1000)
            call(root+0x8085C7B8-RAM,[graph,0,0,0x3F800000,item,wrapped,1,wrapped,0],proof)
            end=int.from_bytes(debug.read_memory(graph+0x298,4),'big')
            if not gfx<=end<=gfx+0x1000 or (end-gfx)%8:
                raise ValueError('Pocket icon escaped its private graphics arena')
            commands=debug.read_memory(gfx,end-gfx) if end!=gfx else b''
            pointers=[b&0x1FFFFFFF for a,b in struct.iter_unpack('>2I',commands) if a>>24==0xFD]
            if isinstance(row,dict) and not wrapped:
                expected=([row['palette']&0x1FFFFFFF,row['texture']&0x1FFFFFFF]
                          if enabled==row else [])
            else:
                # Native gifts take priority; original tools/umbrellas retain their table.
                descriptor=0x8085DD18 if wrapped else 0x8085DD68 if item==0x2200 else 0x8085DD88
                # Lib_SegmentedToVirtual resolves original artwork through its
                # segment; a segmented 0Cxxxxxx pointer is not a physical one.
                expected=[((v&0xFFFFFF)+segment_bases[(v>>24)&15])&0x1FFFFFFF
                          for v in struct.unpack_from('>2I',loaded,descriptor-RAM)]
            passed=pointers==expected and (bool(commands)==bool(expected))
            record(dict(pocket_icon_draw=f'{item:04X}',selected=enabled['item_id'] if enabled else None,
                        wrapped=wrapped,commands=len(commands)//8,texture_pointers=pointers,
                        expected_pointers=expected,assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Pocket icon drew an incorrect resource or disabled item')
        check('complete parent retained',root,loaded)
        check('equipment resources retained',0x804A3000,module)
        check('native segment bases retained',0x801458A0,segments)
        for at in guards:check('private memory guard',at,edge)
        check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    for at,value in saved.items():check('restored current parent/profile',at,value)
    return dict(native_pocket_icon_cases=len(cases),register_windows=1,gpu_rendered=False,
                ordinary_inventory_tested=False,save_reload_tested=False,requires_checkpoint_restore=True)


def inventory_preview(debug, rom_path, record):
    """Loaded inventory selection, complete resource DMA, and actual draw dispatch."""
    from v3_inventory_equipment import VROM,RELOC,OWNER_RAM,SECTIONS
    from v3_furniture_room_smoke import extend
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes()
    report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:
        raise ValueError('Inventory preview requires the exact current cartridge')
    equipment=report['equipment_resources'];preview=equipment['inventory_preview']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image)
    start=equipment['blob_offset'];module=blob[start:start+equipment['bytes']]
    def check(label,at,want):
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(inventory_preview_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Inventory-preview mismatch: '+label)
    def call(at,args=(),want=None,proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:
            raise ValueError('Inventory-preview return mismatch')
        return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    check('complete startup equipment module',0x804A3000,module)
    check('original profile',0x80460020,blob[0x20:0xE0])
    saved={at:debug.read_memory(at,n) for at,n in ((0x80136FD8,4),(0x80460020,192))}
    size=0x1A000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Inventory-preview allocation outside native heap')
    root,overlay,player,submenu,graph,game,gfx,buffer,stack=(allocation+n for n in
        (16,0x5000,0x15800,0x16000,0x16100,0x16500,0x16600,0x17000,0x19800))
    debug.write_memory(allocation,bytes(size));edge=b'V3IV'*4
    guards=(allocation,overlay-16,player-16,submenu-16,graph-16,game-16,gfx-16,
            gfx+0x100,buffer-16,buffer+0x1200,stack-0x800,stack+0x200,
            allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    data,rel=(files[v].extract(image) for v in (VROM,RELOC));resident=sum(struct.unpack_from('>4I',rel))
    spec=SimpleNamespace(ram=OWNER_RAM,resident_bytes=resident,sections=struct.unpack_from('>5I',rel))
    loaded=relocate_verified_data(spec,data,rel,root);proof=(root,loaded[:SECTIONS[0]])
    parents={r['item_id']:r for r in equipment['parent_readers']['rows']}
    models={r['index']:r for r in equipment['records']}
    motions={r['index']:r for r in equipment['player_motion']['records']}
    first,second=preview['rows'][0],preview['rows'][-1]
    def select(row):
        profile=bytearray(saved[0x80460020])
        for p in parents.values():profile[p['profile_byte']]&=~p['profile_mask']
        if row:
            p=parents[row['item_id']];profile[p['profile_byte']]|=p['profile_mask']
        debug.write_memory(0x80460020,profile)
    try:
        call(0x800262D0,[VROM,VROM+len(data),OWNER_RAM,OWNER_RAM+resident,root,root+resident,len(rel)])
        check('complete relocated inventory owner and BSS',root,loaded)
        put(0x80136FD8,player);put(submenu+0x2C,overlay)
        put(overlay+0x106DC,root+preview['native_bss_address']-OWNER_RAM)
        put(game,graph)
        cases=[(0x2200,1,None),(0x2201,0,None),(0x2202,4,None),(0x2203,3,None),
               (0x2223,2,None),(0,5,None),(0xFFFF,5,None),
               (int(first['item_id'],16),5,None),
               (int(first['item_id'],16),first['preview_kind'],first),
               (int(second['item_id'],16),5,first),
               (int(second['item_id'],16),second['preview_kind'],second)]
        for item,want,enabled in cases:
            select(enabled);debug.write_memory(player+0x3EC,struct.pack('>H',item))
            call(root+0x8087D51C-OWNER_RAM,want=want,proof=proof)
        for row in (first,second):
            model=models[row['fields']['shape']]
            fill=bytes([0xA5])*0x1200;debug.write_memory(buffer,fill)
            call(0x800B167C,[buffer,model['index']])
            raw=blob[model['blob_offset']:model['blob_offset']+model['bytes']]
            check('complete selected inventory model and untouched tail',buffer,raw+fill[len(raw):])
        motion=motions[first['fields']['player_animation']]
        debug.write_memory(buffer,fill);call(0x800B1D94,[buffer,motion['index']])
        raw=blob[motion['blob_offset']:motion['blob_offset']+motion['bytes']]
        check('complete inventory holding pose and untouched tail',buffer,raw+fill[len(raw):])
        # Run the native table lookup and callback call, after the outer matrix/
        # segment setup. This checks dispatch, not full scene or GPU rendering.
        draws=[(r['preview_kind'],models[r['fields']['shape']]['pointer']) for r in (first,second)]
        draws.extend(((0,0x06000228),(4,0x06003420)))
        for kind,pointer in draws:
            debug.write_memory(overlay+0x10016,struct.pack('>H',kind))
            debug.write_memory(gfx,bytes(0x100));put(graph+0x298,gfx,gfx+0x100)
            put(stack+0x30,submenu,game)
            before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
            if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:
                raise ValueError('Inventory drawing requires paused native game frame')
            regs[6]=extend(overlay+0x10000);regs[29]=extend(stack)
            regs[37]=extend(root+0x8087E5F4-OWNER_RAM)
            target=root+0x8087E618-OWNER_RAM;bp=f'0,{target:x},4'
            if debug.command('Z'+bp)!='OK':raise ValueError('Inventory draw breakpoint refused')
            try:
                if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':
                    raise ValueError('Inventory draw registers refused')
                stopped=debug.command('c');raw=debug.command('g')
                actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
                passed=(stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==target
                        and actual[29]==regs[29] and actual[16:24]==regs[16:24] and actual[30]==regs[30])
                record(dict(inventory_preview_draw_kind=kind,assertion='passed' if passed else 'failed'))
                if not passed:raise ValueError('Inventory draw continuation or preserved register mismatch')
            finally:
                debug.command('z'+bp);debug.command('G'+before)
            check('complete draw command and unchanged tail',gfx,struct.pack('>2I',0xDE000000,pointer)+bytes(0xF8))
            check('native graphics pointer advance',graph+0x298,struct.pack('>I',gfx+8))
        check('inventory code and BSS retained',root,loaded)
        check('equipment module retained',0x804A3000,module)
        for at in guards:check('private memory guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    for at,value in saved.items():check('restored player/profile',at,value)
    return dict(native_inventory_preview_cases=len(cases),draw_windows=len(draws),
                gpu_rendered=False,ordinary_inventory_tested=False,save_reload_tested=False,
                requires_checkpoint_restore=True)


def inventory_rigs(debug,rom_path,record):
    """Actual inventory load/init/draw path for complete animated preview records."""
    from v3_inventory_equipment import VROM,RELOC,OWNER_RAM,SECTIONS
    from v3_furniture_room_smoke import extend
    from runtime_layout import TEST_STACK
    from v3_import_storage import jump
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed animated inventory cartridge')
    e=report['equipment_resources'];preview=e['inventory_preview'];files=by_vrom(image)
    tools=preview.get('tool_previews')
    blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(inventory_rig_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',actual=actual.hex() if len(actual)<=32 else sha256(actual)))
        if not passed:raise ValueError('Animated inventory mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    def word(at):return int.from_bytes(debug.read_memory(at,4),'big')
    module=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
    check('complete cartridge-loaded inventory tables/code',0x804A3000,module)
    saved={at:debug.read_memory(at,n) for at,n in ((0x801458B8,4),(0x801458D0,4),(0x8046C000,864))}
    size=0x1D000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Animated inventory fixture outside native heap')
    root,overlay,submenu,graph,game,gfx,xlu,bank,stack=(allocation+n for n in
        (16,0x5000,0x15800,0x15A00,0x15E00,0x16000,0x17020,0x18000,0x1C800))
    bridge=allocation+0x4C00
    debug.write_memory(allocation,bytes(size));edge=b'V3IR'*4
    guards=(allocation,bridge-16,bridge+16,overlay-16,submenu-16,graph-16,game-16,gfx-16,gfx+0x1000,
            xlu-16,xlu+0x600,bank-16,bank+0x4000,stack+0x100,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    data,rel=(files[v].extract(image) for v in (VROM,RELOC));resident=sum(struct.unpack_from('>4I',rel))
    loaded=relocate_verified_data(SimpleNamespace(ram=OWNER_RAM,resident_bytes=resident,
        sections=struct.unpack_from('>5I',rel)),data,rel,root)
    proof=(root,loaded[:SECTIONS[0]]);bss=root+preview['native_bss_address']-OWNER_RAM
    work=preview.get('joint_work',dict(joint_offset=0x294,morph_offset=0x2BE,array_bytes=42,vectors=7))
    guards=(*guards,root+resident,root+resident+len(rel))
    debug.write_memory(root+resident+len(rel),edge)
    resources={r['index']:r for r in e['records']};rows=[r for r in preview['rows'] if r.get('draw_callback')]
    groups={callback:[r for r in rows if r['draw_callback']==callback] for callback in {r['draw_callback'] for r in rows}}
    representatives=[row for _,group in sorted(groups.items()) for row in
                     (min(group,key=lambda r:r['model_bytes']),max(group,key=lambda r:r['model_bytes']))]
    if tools:
        representatives=[r for r in rows if r['preview_kind'] in tools['preview_indices']]
        if sorted(r['preview_kind'] for r in representatives)!=[6,7,8,9]:
            raise ValueError('Missing complete shared tool preview category')
    matrix=call(0x800E02AC);matrix_before=debug.read_memory(matrix,64)
    identity=game+0x40;debug.write_memory(identity,struct.pack('>16f',*(1 if i%5==0 else 0 for i in range(16))))
    def initialize(kind):
        debug.write_memory(overlay+0x10016,struct.pack('>h',kind));put(stack+0x60,bss)
        before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
        if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:raise ValueError('Inventory init requires paused native frame')
        for register,value in ((3,kind),(8,0),(16,overlay+0x10000),(17,bank),(29,stack),
                               (37,root+0x8087D930-OWNER_RAM)):regs[register]=extend(value)
        target=root+0x8087DA8C-OWNER_RAM;bp=f'0,{target:x},4'
        if debug.command('Z'+bp)!='OK':raise ValueError('Inventory init breakpoint refused')
        try:
            if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':raise ValueError('Inventory init register write refused')
            stopped=debug.command('c');raw=debug.command('g')
            actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
            passed=stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==target and actual[29]==regs[29]
            record(dict(inventory_rig_native_initialize=kind,assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Inventory init continuation/stack mismatch')
        finally:debug.command('z'+bp);debug.command('G'+before)
    def draw():
        # Execute the actual cartridge table lookup and relocated/resident
        # dispatcher, without uploading a substitute callback bridge.
        put(stack+0x30,submenu,game)
        before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
        if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:
            raise ValueError('Inventory drawing requires the paused native frame')
        for register,value in ((6,overlay+0x10000),(29,stack),(37,root+0x8087E5F4-OWNER_RAM)):
            regs[register]=extend(value)
        target=root+0x8087E618-OWNER_RAM;bp=f'0,{target:x},4'
        if debug.command('Z'+bp)!='OK':raise ValueError('Inventory draw breakpoint refused')
        try:
            if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':raise ValueError('Inventory draw register write refused')
            stopped=debug.command('c');raw=debug.command('g')
            actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
            passed=(stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==target
                    and actual[29]==regs[29] and actual[16:24]==regs[16:24] and actual[30]==regs[30])
            record(dict(inventory_native_draw_kind=int.from_bytes(debug.read_memory(overlay+0x10016,2),'big'),
                        assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Inventory native draw continuation or register mismatch')
        finally:debug.command('z'+bp);debug.command('G'+before)
    try:
        call(0x800262D0,[VROM,VROM+len(data),OWNER_RAM,OWNER_RAM+resident,root,root+resident,len(rel)])
        check('complete cartridge-loaded relocated inventory owner',root,loaded)
        # The loader uses the following bytes for relocation scratch. Protect
        # the BSS boundary only once relocation has finished using that space.
        check('native overlay loader scratch guard',root+resident+len(rel),edge)
        debug.write_memory(root+resident,edge)
        put(submenu+0x2C,overlay);put(overlay+0x106DC,bss);put(game,graph)
        if not tools:
            initialize(1);check('original tool animation timing retained',bss+0x224+12,struct.pack('>2f',1,2))
        for row in representatives:
            model=resources[row['fields']['shape']]
            motion=resources[row['fields']['item_animation']] if row['fields']['skeleton'] else None
            fill=b'\xA5'*0x4000;debug.write_memory(bank,fill);initialize(row['preview_kind'])
            wanted=blob[model['blob_offset']:model['blob_offset']+model['bytes']]
            if motion:wanted+=blob[motion['blob_offset']:motion['blob_offset']+motion['bytes']]
            check('complete native model/animation transfers and untouched tail',bank,wanted+fill[len(wanted):])
            if motion:
                speed=row['native_frame_speed']
                check('source-correct preview speed and first frame',bss+0x224+12,struct.pack('>2f',speed,1+speed))
                check('native inventory work and morph pointers',bss+0x224+0x24,
                      struct.pack('>2I',bss+work['joint_offset'],bss+work['morph_offset']))
            put(0x801458B8,word(overlay+0x10030)&0x1FFFFFFF);call(0x800E0284,[identity])
            put(graph+0x298,gfx,gfx+0x1000);put(graph+0x2A8,xlu,xlu+0x600)
            rod=row['draw_callback']==0x8087E2AC
            if rod:
                debug.write_memory(bss+0x2E8,debug.read_memory(identity,64))
                put(overlay+0x100F8,bank&0x1FFFFFFF)
            if tools:draw()
            elif OWNER_RAM<=row['draw_callback']<OWNER_RAM+SECTIONS[0]:
                call(root+row['draw_callback']-OWNER_RAM,[submenu,game],proof)
            else:
                stub=struct.pack('>2I',jump(row['draw_callback']),0);debug.write_memory(bridge,stub)
                call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
                call(bridge,[submenu,game],(bridge,stub))
            front,back=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
            if not gfx<front<=back<=gfx+0x1000:raise ValueError('Animated inventory escaped graphics arena')
            commands=debug.read_memory(gfx,front-gfx)
            drawn=[p for w,p in struct.iter_unpack('>2I',commands) if w>>24==0xDE]
            expected=([0x06000000+p for p in model['source']['model_offsets'].values()] if motion else [model['pointer']])
            if rod:expected.append(tools['bobber']['display_pointer'])
            reflection=row['draw_callback']==preview.get('balloon_drawer',{}).get('address')
            allocation_bytes=(model['source']['skeleton']['shown_joints']*64 if motion else 0)+(48 if reflection else 0)+(64 if rod else 0)
            passed=drawn==expected and back==gfx+0x1000-allocation_bytes
            record(dict(inventory_rig_joint_draws=drawn,expected=expected,
                        assertion='passed' if passed else 'failed',model=model['index']))
            if not passed:raise ValueError('Animated inventory omitted a joint or allocated wrong matrices')
            check('native translucent matrix binding retained',graph+0x2A8,struct.pack('>2I',xlu+(8 if motion else 0),xlu+0x600))
            check('balanced native matrix stack',0x801462B4,struct.pack('>I',matrix))
            if not rod:check('unchanged parent transform',matrix,debug.read_memory(identity,64))
            if rod:
                check('native common-resource segment retained',0x801458D0,struct.pack('>I',bank))
            for at in guards:check('inventory rig guard',at,edge)
        if tools:
            # The changed pointer consumer must also retain the ordinary rod.
            debug.write_memory(overlay+0x10016,struct.pack('>h',3));put(stack+88,submenu)
            before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
            regs[29]=extend(stack);regs[37]=extend(root+tools['hook']['address']-OWNER_RAM)
            target=root+tools['hook']['address']-OWNER_RAM+8;bp=f'0,{target:x},4'
            if debug.command('Z'+bp)!='OK':raise ValueError('Ordinary bobber breakpoint refused')
            try:
                if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':raise ValueError('Ordinary bobber registers refused')
                stopped=debug.command('c');raw=debug.command('g');actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
                passed=(stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==target
                        and actual[13]==tools['native_bobber_pointer']
                        and all(actual[i]==regs[i] for i in range(34) if i not in (1,13,31)))
                record(dict(inventory_native_ordinary_bobber=True,assertion='passed' if passed else 'failed'))
                if not passed:raise ValueError('Ordinary bobber pointer or live registers changed')
            finally:debug.command('z'+bp);debug.command('G'+before)
        if work['vectors']>7 and not preview.get('balloon_drawer'):
            # Supply the largest installed skeleton through temporary table
            # data, not uploaded code or a claimed enabled inventory option.
            model=max((r for r in resources.values() if r['type']==1),
                      key=lambda r:r['source']['skeleton']['joints'])
            source_motion=model['source']['motion_bindings'][0]['default_animation']
            motion=next(r for r in resources.values() if r['source_index']==source_motion)
            fields=dict(shape=model['index'],skeleton=model['pointer'],
                        item_animation=motion['index'],item_pointer=motion['pointer'])
            changed={};slot=40
            try:
                for table in preview['tables']:
                    if table['role'] in fields:
                        at=table['ram']+slot*4;changed[at]=debug.read_memory(at,4)
                        put(at,fields[table['role']])
                poison=b'\xA5\x5A'*(work['array_bytes']//2)
                debug.write_memory(bss+work['joint_offset'],poison)
                debug.write_memory(bss+work['morph_offset'],poison)
                old_work=debug.read_memory(bss+0x294,84)
                initialize(slot)
                check('maximum rig retains actual enlarged work pointers',bss+0x248,
                      struct.pack('>2I',bss+work['joint_offset'],bss+work['morph_offset']))
                used=(model['source']['skeleton']['joints']+1)*6
                pose=debug.read_memory(bss+work['joint_offset'],used)
                written=all(pose[i:i+2]!=b'\xA5\x5A' for i in range(0,used,2))
                record(dict(inventory_capacity_vectors=used//6,temporary_table_slot=slot,
                            assertion='passed' if written else 'failed'))
                if not written:raise ValueError('Native inventory did not write every maximum-rig component')
                assertions+=1
                check('maximum-rig initialization retains morph buffer',bss+work['morph_offset'],poison)
                check('maximum rig retains original short arrays',bss+0x294,old_work)
                wanted=b''.join(blob[r['blob_offset']:r['blob_offset']+r['bytes']] for r in (model,motion))
                check('maximum-rig complete native DMA',bank,wanted)
                for at in guards:check('maximum inventory rig guard',at,edge)
            finally:
                for at,value in changed.items():debug.write_memory(at,value)
        check('save/profile remains unchanged',0x8046C000,saved[0x8046C000])
        check('complete equipment module remains unchanged',0x804A3000,module)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(matrix,matrix_before)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    return dict(native_inventory_rigs=True,representatives=len(representatives),assertions=assertions,
        complete_model_animation_dma=True,original_tool_speed_retained=not bool(tools),
        native_tool_draw_dispatch=bool(tools),golden_and_ordinary_bobber_checked=bool(tools),gpu_rendered=False,
        ordinary_inventory_tested=False,parent_selection_tested=False,flash_written=False,requires_checkpoint_restore=True)


def room_rigs(debug,rom_path,record,*,mode=2):
    """Manifest-selected complete room lifecycles, without enabling parent choices."""
    from runtime_layout import TEST_STACK
    from v3_import_storage import jump
    from v3_equipment_runtime import RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed room-rig cartridge')
    equipment=report['equipment_resources'];rigs=equipment['room_rigs'];files=by_vrom(image)
    blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(room_rig_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=actual.hex() if len(actual)<=32 else sha256(actual)))
        if not passed:raise ValueError('Room-rig mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    def floating(at):return struct.unpack('>f',debug.read_memory(at,4))[0]
    module=blob[equipment['blob_offset']:equipment['blob_offset']+equipment['bytes']]
    # The equipment package also contains live cache/cursor state owned by
    # unrelated categories. Check this runtime's whole immutable reservation.
    packet=rigs.get('packet')
    first,last=(0x804B1800-RAM,0x804B1FB4-RAM) if packet else (0,len(module))
    if packet:
        actual=debug.read_memory(RAM,len(module))
        differences=[dict(address=f'{RAM+at:08X}',rom=module[at:at+4].hex(),live=actual[at:at+4].hex())
                     for at in range(0,len(module),4) if module[at:at+4]!=actual[at:at+4]]
        record(dict(room_rig_module_live_differences=differences))
    check('complete startup-loaded room lifecycle reservation',RAM+first,module[first:last])
    state=report['save_runtime']
    saved={at:debug.read_memory(at,n) for at,n in ((0x801458B8,4),(state['state_ram'],state['state_bytes']))}
    if mode==1:saved[0x80136FC4]=debug.read_memory(0x80136FC4,4)
    if mode==5:saved[0x80136F2C]=debug.read_memory(0x80136F2C,4)
    size=0x8300 if mode==4 else 0x6200;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Room-rig fixture outside native heap')
    actor,other,graph,game,identity,bridge,bank,gfx,xlu=(allocation+n for n in
        (16,0x800,0x1500,0x1900,0x1A00,0x1B00,0x2000,0x4600,0x5800))
    game_bytes=0x1EB0 if mode==4 else 0xB0
    if mode==4:game=allocation+0x6300
    debug.write_memory(allocation,bytes(size));edge=b'V3RR'*4
    guards=(allocation,actor+0x740,other-16,other+0x740,graph-16,graph+0x300,
            game-16,game+game_bytes,identity-16,identity+64,bridge-16,bridge+32,
            bank-16,bank+9216,gfx-16,gfx+0x1000,xlu-16,xlu+0x800,
            allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    names=('ct','mv','dw');symbols=rigs['bootstrap' if packet else 'code']['symbols']
    prefix='af_v3_room_boot_' if packet else 'af_v3_room_rig_'
    jumps=b''.join(struct.pack('>2I',jump(symbols[prefix+name]),0) for name in names)
    if mode==1:
        jumps+=struct.pack('>2I',jump(rigs['code']['symbols']['clock_before']),0)
    debug.write_memory(bridge,jumps)
    call(0x8002FE00,[bridge,len(jumps)]);call(0x80034CE0,[bridge,len(jumps)])
    def callback(name,target):
        args=[target,bank] if name=='ct' else [target,0,game,bank]
        return call(bridge+names.index(name)*8,args,(bridge,jumps))
    matrix=call(0x800E02AC);matrix_before=debug.read_memory(matrix,64)
    debug.write_memory(identity,struct.pack('>16f',*(1 if i%5==0 else 0 for i in range(16))))
    if mode==4:debug.write_memory(game+0x1E5C,debug.read_memory(identity,64))
    rows=[r for r in rigs['rows'] if r.get('mode')==mode] if packet else rigs['rows']
    selected=[min(rows,key=lambda r:r['bytes']),max(rows,key=lambda r:r['bytes'])]
    if mode==3:
        # One complete representative of each source hit policy, independent
        # of item identities and object size ordering.
        policies=sorted({(r['first'],r['last']) for r in rows})
        selected=[max((r for r in rows if (r['first'],r['last'])==policy),key=lambda r:r['bytes']) for policy in policies]
    if mode==1:
        unique={}
        for row in rows:unique.setdefault(row['source']['profile']['skeleton']['header']['donor_offset'],row)
        selected=list(unique.values())
    put(game,graph)
    if mode==5:
        put(0x80136F2C,bridge+0x100);put(bridge+0x100,bridge+0x200)
    try:
        for iteration,row in enumerate(selected):
            parity=iteration&1
            fill=b'\xA5'*9216;debug.write_memory(bank,fill)
            call(0x80026B44,[bank,row['vrom'],row['bytes']])
            data=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            check('complete cartridge DMA and untouched bank tail',bank,data+fill[len(data):])
            put(0x801458B8,bank&0x1FFFFFFF)
            for target in (actor,other):
                debug.write_memory(target,b'\xA5'*0x740)
                debug.write_memory(target,struct.pack('>H',row['runtime_index']))
                if mode==4:debug.write_memory(target+0x714,struct.pack('>3f',1,1,1))
                if mode==5:debug.write_memory(target+8,struct.pack('>3f',10,0,20))
                debug.write_memory(target+0x12D,bytes(1));callback('ct',target)
                check('initial per-instance state',target+0x204,struct.pack('>2f',*((10,20) if mode==5 else (0,.5))))
                check('native work vectors belong to this instance',target+0x158,
                      struct.pack('>2I',target+0x1A4,target+0x1DA))
                initial=(.5,1.5) if mode in (1,4) else (0,1.5) if mode in (3,5) else (0,1)
                check('source initial speed and frame',target+0x140,struct.pack('>2f',*initial))
                if packet:
                    check('native category animation mode',target+0x148,struct.pack('>I',1 if mode in (1,4,5) else 0))
                    check('complete lazily loaded room packet',packet['ram'],
                          blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']])
                    check('startup cache remembers the verified packet',0x804B1E00,struct.pack('>I',packet['crc32']))
            independent=debug.read_memory(other,0x740)
            if mode==1:
                callback('mv',actor)
                check('clock preserves source two-step timing',actor+0x140,struct.pack('>2f',.5,2.5))
                # Call the actual installed joint callback using its immutable
                # descriptor; preserve wraparound and all other rotation axes.
                debug.write_memory(0x80136FC4,struct.pack('>2H',32770,65500))
                descriptor=rigs['table_ram']+16+rigs['rows'].index(row)*24
                rotation=bridge+64
                for joint,angle in ((3,65500),(4,32770),(2,0)):
                    debug.write_memory(rotation,struct.pack('>3H',123,65215,32760)+b'G'*10)
                    call(bridge+24,[0,actor+0x134,joint,0,0,descriptor,rotation,0],(bridge,jumps))
                    check('live clock angles and rotation guards',rotation,
                          struct.pack('>3H',123,65215,(32760-angle)&0xFFFF)+b'G'*10)
            elif mode==3:
                # Exercise the real keyframe evaluator and the shared callback.
                # Suppress synthesis through a native transition state; sound
                # identity/program integrity and dispatch have separate checks.
                debug.write_memory(actor+0x3C,struct.pack('>h',5))
                if row['first']:
                    end=floating(actor+0x138)
                    cases=((1,0,0,0,1),(1,0,1,.25,1),(20,.25,0,.25,20.5),
                        (20,.25,1,.25,20.5),(end,.25,1,0,end),(end,0,1,.25,1))
                else:cases=((1,0,1,.5,1),(20,.5,0,.5,21),(20,.5,1,.5,1.5))
                for frame,speed,changed,want_speed,want in cases:
                    debug.write_memory(actor+0x140,struct.pack('>2f',speed,frame))
                    debug.write_memory(actor+0x12D,bytes((changed,)));callback('mv',actor)
                    check('hit policy retains native source evaluation order',actor+0x140,struct.pack('>2f',want_speed,want))
                    check('room owner retains hit pulse',actor+0x12D,bytes((changed,)))
            elif mode==5:
                # The real owner copies position to last_position before mv.
                # Keep that ordering in the fixture instead of supplying a
                # conveniently older value that the game never exposes.
                for motion_state,direction,delta,forward in ((11,3,6,True),(12,3,8,False),(3,3,4,None),(1,0,4,None)):
                    x=floating(actor+8)+delta
                    debug.write_memory(actor+8,struct.pack('>3f',x,0,20))
                    debug.write_memory(actor+0x14,struct.pack('>3f',x,0,20))
                    debug.write_memory(actor+0x3C,struct.pack('>h',motion_state))
                    put(bridge+0x200+0x1A0,direction);callback('mv',actor)
                    expected=(.1+(delta*.5)/1.55)*.5 if forward is not None else 0
                    actual=floating(actor+0x140)
                    passed=abs(actual-expected)<.00001
                    record(dict(rolling_motion_state=motion_state,direction=direction,speed=actual,
                        expected_speed=expected,assertion='passed' if passed else 'failed'))
                    if not passed:raise ValueError('Native rolling motion speed differs from source timing')
                    assertions+=1
                    if forward is not None:
                        duration=struct.unpack('>f',struct.pack('>I',row['first']))[0]
                        check('rolling forward/reverse endpoints',actor+0x134,
                              struct.pack('>2f',*((1,duration) if forward else (duration,1))))
                    check('per-instance previous position survives native overwrite',actor+0x204,struct.pack('>2f',x,20))
            elif mode==4:
                # Its positional sound is unconditional. Do not call movement
                # in this isolated fixture without the actual audio owner.
                # Source bindings and sanitized argument checks cover that path.
                pass
            elif packet:
                stopped=debug.read_memory(actor,0x740);callback('mv',actor)
                check('storage without a room owner remains stopped',actor,stopped)
            else:
                debug.write_memory(actor+0x12D,b'\x01');callback('mv',actor)
                actual=[floating(actor+p) for p in (0x204,0x208,0x144)]
                passed=all(abs(a-b)<.00001 for a,b in zip(actual,(.02,1.25,1.03)))
                record(dict(room_rig_switch_response=actual,assertion='passed' if passed else 'failed'))
                if not passed:raise ValueError('Room rig lost source two-step switch response')
                assertions+=1
                check('native owner retains switch pulse',actor+0x12D,b'\x01')
                debug.write_memory(actor+0x12D,bytes(1))
                debug.write_memory(actor+0x204,struct.pack('>2f',1.24,1.25));callback('mv',actor)
                check('source speed peak switches back to idle',actor+0x204,struct.pack('>2f',1.24,.5))
            check('second room instance remains independent',other,independent)
            put(game+0xA0,parity);call(0x800E0284,[identity])
            put(graph+0x298,gfx,gfx+0x1000);put(graph+0x2A8,xlu,xlu+0x800)
            callback('dw',actor)
            front,back=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
            if not gfx<front<=back<=gfx+0x1000:raise ValueError('Room rig escaped graphics arena')
            commands=debug.read_memory(gfx,front-gfx)
            drawn=[b for a,b in struct.iter_unpack('>2I',commands) if a>>24==0xDE]
            offsets=row['source']['model_offsets']
            expected=[0x06000000+p for p in offsets.values()]
            if mode==4:
                adapter=row['source']['profile']['callback_adapter'];flame=adapter['billboard']['joint']
                opaque=[j for j in adapter['skeleton']['rows']
                        if 'model' in j and j['index']!=flame and not j['draw_stream']]
                expected=[0x06000000+offsets['joint'+str(j['index'])] for j in opaque]
                # A hidden shape still emits its joint matrix to the opaque
                # stream before the camera-facing after-callback draws it.
                passed=drawn==expected and back==((gfx+0x1000-176)&~15) and len(commands)==(3+2*len(opaque))*8
                xfront,xback=struct.unpack('>2I',debug.read_memory(graph+0x2A8,8))
                if not xlu<xfront<=xback==xlu+0x800:raise ValueError('Billboard escaped translucent arena')
                xcommands=debug.read_memory(xlu,xfront-xlu)
                xdrawn=[b for a,b in struct.iter_unpack('>2I',xcommands) if a>>24==0xDE]
                xexpected=[0x06000000+offsets['joint'+str(j['index'])] for j in adapter['skeleton']['rows']
                           if 'model' in j and (j['index']==flame or j['draw_stream'])]
                passed=passed and xdrawn==xexpected and len(xcommands)==(3+2*len(xexpected))*8
                check('frame-owned scroll segment',xlu+8,struct.pack('>2I',0xDB060024,back+128))
                scroll=[]
                for tile in adapter['scrolling']['tiles']:
                    x,y=(((parity*rate*2)&0x3FFF)>>2 for rate in tile['rate'])
                    scroll.extend((0xE8000000,0,0xF2000000|(x<<12)|y,
                        (tile['index']<<24)|(((x+(tile['width']-1)*4)&0xFFF)<<12)|((y+(tile['height']-1)*4)&0xFFF)))
                scroll.extend((0xDF000000,0))
                check('complete source-derived scroll commands',back+128,struct.pack('>10I',*scroll))
                record(dict(room_rig_billboard_lists=xdrawn,expected=xexpected))
            else:
                passed=drawn==expected and back==gfx+0x1000-64 and len(commands)==(2+2*row['shown'])*8
            record(dict(room_rig_draw=row['source_item_id'],lists=drawn,expected=expected,
                        assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Room rig omitted complete models or misused graphics allocation')
            assertions+=1
            if mode!=4:check('translucent stream only binds skeleton matrices',graph+0x2A8,struct.pack('>2I',xlu+8,xlu+0x800))
            check('untouched opposite matrix bank',actor+0x210+(1-parity)*0x280,b'\xA5'*0x280)
            check('unused matrix slots retain their bytes',actor+0x210+parity*0x280+row['shown']*64,b'\xA5'*((10-row['shown'])*64))
            tail=bytearray(b'\xA5'*0x30)
            if mode==4:struct.pack_into('>3f',tail,4,1,1,1)
            check('native tail fields retain their bytes',actor+0x710,tail)
            check('unused morph-vector bytes retain their bytes',actor+0x20C,b'\xA5'*4)
            check('balanced matrix stack',0x801462B4,struct.pack('>I',matrix))
            check('unchanged parent transform',matrix,debug.read_memory(identity,64))
            for at in guards:check('room-rig work/graphics/stack guard',at,edge)
        check('complete save/profile state unchanged',state['state_ram'],saved[state['state_ram']])
        expected_module=bytearray(module)
        if packet:struct.pack_into('>I',expected_module,0x804B1E00-RAM,packet['crc32'])
        check('room lifecycle retains code and only updates its cache',RAM+first,expected_module[first:last])
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(matrix,matrix_before)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    return dict(native_room_rigs=True,representatives=len(selected),assertions=assertions,
        complete_model_animation_dma=True,independent_instances=True,gpu_rendered=False,
        native_move_tested=mode!=4,native_billboard_helpers_tested=mode==4,
        storage_open_close_gameplay_tested=False,lazy_packet_tested=bool(packet),
        ordinary_room_tested=False,parent_selection_tested=False,flash_written=False,requires_checkpoint_restore=True)


def item_categories(debug,rom_path,record):
    """Loaded police capacity/drawing and handover category/table windows."""
    import v3_category_runtime as category
    from v3_furniture_room_smoke import extend
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Category probe requires the current cartridge')
    equipment=report['equipment_resources'];receipt=equipment['item_categories']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image)
    at=equipment['blob_offset'];module=blob[at:at+equipment['bytes']]
    def check(label,at,want):
        observed=debug.read_memory(at,len(want));passed=observed==want
        record(dict(item_category_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Category mismatch: '+label)
    def call(at,args=(),want=None,proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Category return mismatch')
        return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    check('complete startup module including all artwork',category.RAM,module)
    saved_profile=debug.read_memory(0x80460020,192)
    size=0x10000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Category fixture allocation outside native heap')
    root,actor,block,items,game,graph,gfx,bridge,stack=(allocation+n for n in
        (16,0x3000,0x7800,0x7900,0x7C00,0x8000,0x8500,0xA000,0xF000))
    debug.write_memory(allocation,bytes(size));edge=b'V3CT'*4
    guards=(allocation,actor-16,actor+receipt['owners'][0]['capacity']['actor_bytes'],
            block-16,items-16,game-16,graph-16,gfx-16,gfx+0x1000,bridge-16,
            bridge+16,stack-0x800,stack+0x200,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    parents=equipment['parent_readers']['rows'];parent=parents[-1];item=int(parent['item_id'],16)
    art=next(r for r in receipt['objects'] if item in [int(p,16) for p in r['parent_item_ids']])
    def select(enabled):
        profile=bytearray(saved_profile)
        for p in parents:profile[p['profile_byte']]&=~p['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    def load(spec):
        data,rel=(files[spec[k]].extract(image) for k in ('vrom','reloc'))
        sections=struct.unpack_from('>5I',rel);resident=sum(sections[:4])
        loaded=relocate_verified_data(SimpleNamespace(ram=spec['ram'],resident_bytes=resident,sections=sections),data,rel,root)
        call(0x800262D0,[spec['vrom'],spec['vrom']+len(data),spec['ram'],spec['ram']+resident,
                        root,root+resident,len(rel)])
        check(spec['role']+' actual loaded owner and BSS',root,loaded)
        return loaded,(root,loaded[:sections[0]])
    def window(start,end,updates):
        before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
        if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:
            raise ValueError('Category native window requires paused game frame')
        regs[29]=extend(stack);regs[37]=extend(start)
        for r,v in updates.items():regs[r]=extend(v)
        bp=f'0,{end:x},4'
        if debug.command('Z'+bp)!='OK':raise ValueError('Category breakpoint refused')
        try:
            if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':raise ValueError('Category registers refused')
            stopped=debug.command('c');raw=debug.command('g')
            actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
            passed=(stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==end and actual[29]==regs[29]
                    and actual[16:24]==regs[16:24] and actual[30]==regs[30])
            record(dict(item_category_window=f'{start:08X}',assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Category window continuation/register mismatch')
            return actual
        finally:debug.command('z'+bp);debug.command('G'+before)
    try:
        stub=struct.pack('>II',category.jump(receipt['code']['symbols']['af_v3_equipment_category']),0)
        debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        native_type=call(0x800A5630,[0x2200])
        for value,enabled,want in ((item,False,0),(item,True,art['native_category']),
                                   (0x2224,True,0),(0x2200,False,native_type)):
            select(enabled);call(bridge,[value],want,(bridge,stub))
        police=receipt['owners'][0];loaded,proof=load(police);capacity=police['capacity']
        tbl=actor+0x174;put(block+12,items)
        debug.write_memory(tbl+4,b'\xA5'*(capacity['start_indices']*2))
        # The real native setter clears/copies every extended slot and initialises
        # all 257 matrix nodes; an empty field avoids unrelated terrain queries.
        call(root+0x808EB954-police['ram'],[actor,tbl,block],proof=proof)
        check('all extended police start indices',tbl+4,bytes(capacity['start_indices']*2))
        positions=tbl+capacity['draw_positions_offset']
        check('all 257 native matrix-list sentinels',positions,(struct.pack('>I',256)+bytes(64))*257)
        check('police draw flag',tbl,struct.pack('>I',1))
        for invalid in (capacity['start_indices'],0xFFFFFFFF):
            call(root,[tbl+4,block+0x20,block+0x28,invalid,block,0],proof=proof)
        check('invalid categories do not index the start array',tbl+4,bytes(capacity['start_indices']*2))
        # Draw the last extended category and an original category through the
        # actual expanded native loop, material setup, matrix, and geometry.
        native=1;imported=art['native_category']
        for category_id,index in ((imported,1),(native,2)):
            debug.write_memory(tbl+4+2*(category_id-1),struct.pack('>H',index))
            matrix=struct.pack('>16f',*[1.0 if i%5==0 else 0.0 for i in range(16)])
            debug.write_memory(positions+index*68,struct.pack('>i',-index)+matrix)
        put(game,graph);put(graph+0x298,gfx,gfx+0x1000)
        put(root+0x7C0,game,graph,tbl,0,0,0,0)
        call(root+0x808EBC7C-police['ram'],proof=proof)
        head,tail=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
        if not gfx<=head<tail<=gfx+0x1000:raise ValueError('Police graphics exceeded its private arena')
        commands=debug.read_memory(gfx,head-gfx)
        lists=[b for a,b in struct.iter_unpack('>2I',commands) if a==0xDE000000]
        values=[struct.unpack_from('>'+str(receipt['count'])+'I',module,t['offset']) for t in receipt['tables']]
        expected=[values[0][native],values[1][native],values[0][imported],values[1][imported]]
        # Graphics setup can also call shared lists; retained item lists must occur once, in order.
        observed=[p for p in lists if p in expected]
        passed=observed==expected
        record(dict(police_category_draw_lists=observed,expected=expected,assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Police material/matrix/geometry dispatch mismatch')
        handover=receipt['owners'][1];loaded,proof=load(handover)
        put(block,0,0,0);debug.write_memory(block+14,struct.pack('>H',item))
        for enabled,want in ((False,0),(True,imported)):
            select(enabled)
            window(root+handover['call'],root+handover['call']+12,{16:actor,24:block})
            check('native handover category assignment',actor+0x1E2,bytes([want]))
        for value in (0,native,imported):
            debug.write_memory(actor+0x1E2,bytes([value]))
            registers=window(root+0x809647FC-handover['ram'],root+0x80964828-handover['ram'],{16:actor})
            check('handover material lookup',stack+0x64,struct.pack('>I',values[0][value]))
            if registers[8]&0xFFFFFFFF!=values[1][value]:raise ValueError('Handover geometry lookup mismatch')
        check('complete equipment module retained',category.RAM,module)
        for at in guards:check('category fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(0x80460020,saved_profile);call(0x8009C040,[allocation])
    check('restored selected profile',0x80460020,saved_profile)
    return dict(native_category_cases=4,police_start_indices=capacity['start_indices'],
        police_matrix_nodes=257,police_draw_categories=2,handover_windows=5,
        ground_tested=False,gpu_rendered=False,ordinary_gameplay_tested=False,
        save_reload_tested=False,requires_checkpoint_restore=True)


def event_stock(debug,rom_path,record):
    """Execute the shared stock routines and real relocated initializer once."""
    import v3_event_acquisition as event
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Event stock probe requires its exact cartridge')
    equipment=report['equipment_resources'];receipt=equipment['event_acquisition']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image)
    at=equipment['blob_offset'];module=blob[at:at+equipment['bytes']]
    def check(label,at,want):
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(event_stock_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Event stock mismatch: '+label)
    def call(at,args=(),want=None,proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Event stock return mismatch')
        return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    check('complete startup equipment module',event.RAM,module)
    saved={at:debug.read_memory(at,n) for at,n in ((event.SLOT,4),(0x80460020,192),(0x80135CF4,244))}
    size=0x3000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Event probe allocation outside native heap')
    root,bridge,offer=allocation+16,allocation+0x2000,allocation+0x2100
    debug.write_memory(allocation,bytes(size));edge=b'V3ES'*4
    guards=(allocation,bridge-16,bridge+16,offer-16,offer+16,allocation+size-16,
            TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    parents=equipment['parent_readers']['rows']
    def select(rows):
        profile=bytearray(saved[0x80460020])
        for row in parents:profile[row['profile_byte']]&=~row['profile_mask']
        for row in rows:profile[row['profile_byte']]|=row['profile_mask']
        debug.write_memory(0x80460020,profile)
    def routine(name,args=(),want=None):
        stub=struct.pack('>2I',event.jump(receipt['code']['symbols']['af_v3_event_stock_'+name]),0)
        debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        return call(bridge,args,want,(bridge,stub))
    try:
        data,rel=(files[v].extract(image) for v in (event.OWNER,event.RELOC))
        sections=struct.unpack_from('>5I',rel)
        loaded=relocate_verified_data(SimpleNamespace(ram=event.OWNER_RAM,resident_bytes=len(data),sections=sections),data,rel,root)
        call(0x800262D0,[event.OWNER,event.OWNER+len(data),event.OWNER_RAM,
                        event.OWNER_RAM+len(data),root,root+len(data),len(rel)])
        check('complete loaded night-stall owner',root,loaded);put(event.SLOT,root)
        # Existing event record avoids synthesising the full calendar/NPC scene.
        # Both the original save initializer and the real getter execute.
        native=struct.pack('>10H',*range(0x2600,0x2608),8,0)
        put(0x80135CF4,1);debug.write_memory(0x80135CF8,b'\x0B\0'+bytes(6)+native+bytes(20))
        area,stock=0x80135D00,0x80135D14
        select([]);routine('construct');check('disabled imports preserve all forty event bytes',area,native+bytes(20))
        chosen=(parents[0],parents[-1]);select(chosen);routine('construct')
        expected=bytearray(20)
        for row in chosen:struct.pack_into('>H',expected,(int(row['item_id'],16)-0x2254)*2,int(row['item_id'],16))
        struct.pack_into('>2H',expected,16,8,0)
        check('source-selected sparse stock and original wares',area,native+expected)
        routine('count',[stock,0],2);routine('index',[stock,0,1],7)
        routine('quote',[stock,7,offer],1);check('official item, price, message, and slot',offer,struct.pack('>4H',0x225B,780,0x1758,7))
        routine('commit',[stock,offer],1);routine('commit',[stock,offer],0)
        struct.pack_into('>H',expected,14,0)
        routine('construct');check('constructor retains purchases instead of refilling',area,native+expected)
        routine('quote',[stock,0,offer],1);routine('commit',[stock,offer],1)
        struct.pack_into('>H',expected,0,0)
        routine('construct');routine('count',[stock,0],0)
        check('sold-out marker persists across owner initialisation',area,native+expected)
        for at in guards:check('memory guard',at,edge)
    finally:
        for at,raw in saved.items():debug.write_memory(at,raw)
        call(0x8009C0F0,[allocation])
    for at,raw in saved.items():check('restored event/profile/owner',at,raw)
    return dict(event_stock_native=True,ordinary_purchase_tested=False,save_reload_tested=False,
                requires_checkpoint_restore=True)


def event_menu(debug,rom_path,record):
    """Installed menu/payment/handover against isolated native event and pockets."""
    import v3_event_acquisition as event
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Event menu probe requires its exact cartridge')
    equipment=report['equipment_resources'];receipt=equipment['event_acquisition']['menu']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image)
    at=equipment['blob_offset'];module=blob[at:at+equipment['bytes']]
    def check(label,at,want):
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(event_menu_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',
                    **({} if passed else dict(expected=want.hex(),actual=actual.hex()))))
        if not passed:raise ValueError('Event menu mismatch: '+label)
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    check('complete menu startup module',event.RAM,module)
    private=0x80126EC0
    saved={at:debug.read_memory(at,n) for at,n in ((event.SLOT,4),(0x80460020,192),
        (0x8046C000,864),(private,0xBD0),(0x80135CF4,244),(0x80136FD8,4))}
    size=0x5000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Event menu allocation outside native heap')
    root,vendor,bridge=(allocation+n for n in (16,0x1800,0x4800))
    debug.write_memory(allocation,bytes(size));edge=b'V3EM'*4
    guards=(allocation,vendor-16,vendor+0x958,
            bridge-16,bridge+16,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    parents=equipment['parent_readers']['rows']
    added=set(equipment.get('category_refresh',{}).get('added_parent_ids',[]))
    stock_categories=equipment['event_acquisition']['source']['rows']
    eligible=[category for category in stock_categories
        if any(p['item_id']==row['item_id'] for p in parents for row in category['items'])]
    category=next((c for c in eligible if any(row['item_id'] in added for row in c['items'])),eligible[0])
    category_ids={r['item_id'] for r in category['items']}
    candidates=[p for p in parents if p['item_id'] in category_ids]
    selected=(candidates[0],candidates[-1]);price=category['price']
    if len(candidates)<2:raise ValueError('Menu probe requires two implemented variants in one stock category')
    record(dict(event_menu_category=category['kind'],representative_parents=[p['item_id'] for p in selected],price=price))
    def profile(rows):
        data=bytearray(saved[0x80460020])
        for row in parents:data[row['profile_byte']]&=~row['profile_mask']
        for row in rows:data[row['profile_byte']]|=row['profile_mask']
        debug.write_memory(0x80460020,data)
        # Collection validates both an actual player slot and the live format-2
        # profile. Initialise isolated working state instead of faking either.
        resident(0x80469200)
    def resident(target,args=()):
        stub=struct.pack('>2I',event.jump(target),0);debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8]);return call(bridge,args,(bridge,stub))
    def routine(name,args=()):
        return resident(receipt['code']['symbols']['af_v3_event_menu_'+name],args)
    def response(choice):
        put(window+0x1B0+0x80,choice);call(0x8007B44C,[4,9,1])
    def state(action):check('vendor action '+str(action),vendor+0x93C,struct.pack('>I',action))
    def message(value):check('continued message '+hex(value),window+0x2C4,struct.pack('>I',value))
    def enter_imports():
        routine('start',[vendor]);response(1);routine('route',[vendor,0]);state(1)
        message(category['message']);response(0);routine('select',[vendor,0]);state(3);message(0x1761)
    try:
        data,rel=(files[v].extract(image) for v in (event.OWNER,event.RELOC))
        sections=struct.unpack_from('>5I',rel)
        loaded=relocate_verified_data(SimpleNamespace(ram=event.OWNER_RAM,resident_bytes=len(data),sections=sections),data,rel,root)
        call(0x800262D0,[event.OWNER,event.OWNER+len(data),event.OWNER_RAM,
                        event.OWNER_RAM+len(data),root,root+len(data),len(rel)])
        check('complete relocated menu owner',root,loaded);put(event.SLOT,root);put(0x80136FD8,private)
        debug.write_memory(private,bytes(0xBD0))
        native=struct.pack('>10H',*range(0x2600,0x2608),8,0)
        put(0x80135CF4,1);debug.write_memory(0x80135CF8,b'\x0B\0'+bytes(6)+native+bytes(20))
        area,stock=0x80135D00,0x80135D14;window=call(0x8009D1F0)
        if window!=0x80142410:raise ValueError('Changed native message-window binding')
        profile([]);routine('start',[vendor]);check('disabled imports use original route',vendor+0x954,bytes(4))
        check('original route price',vendor+0x94C,struct.pack('>I',980))
        profile(selected);routine('start',[vendor]);check('route-selector mode',vendor+0x954,struct.pack('>I',2))
        check('original route label',0x8019A840,b'Original wares  ')
        check('imported route label',0x8019A860,b'Festival items  ')
        routine('setup',[vendor,6]);state(6)
        response(0);routine('route',[vendor,0]);state(1);message(receipt['text']['first_id'])
        enter_imports()
        for i,row in enumerate(selected):
            at=0x57F0+16+(int(row['item_id'],16)-0x2224)*24+8
            # Native mMsg_Get_Length_String trims spaces, and Add_choice_data
            # copies only that visible length. Unused row tails are not cleared.
            visible=module[at:at+16].rstrip(b' ')
            check('complete source item choice',0x8019A840+32*i,visible)
            check('visible choice length',window+0x1B0+0x5C+4*i,struct.pack('>I',len(visible)))
        check('import price',vendor+0x94C,struct.pack('>I',price))
        stock_before=debug.read_memory(stock,20)
        debug.write_memory(private+0x14,struct.pack('>15H',*([0x2600]*15)));put(private+0x38,1000)
        response(0);routine('purchase',[vendor,0]);state(4);message(0x175D)
        check('full pockets preserve stock',stock,stock_before);check('full pockets preserve money',private+0x38,struct.pack('>I',1000))
        debug.write_memory(private+0x14,bytes(30));put(private+0x38,price-1)
        enter_imports();response(0);routine('purchase',[vendor,0]);state(4);message(0x175E)
        check('insufficient funds preserve stock',stock,stock_before);check('short funds unchanged',private+0x38,struct.pack('>I',price-1))
        # Use actual pocket/payment/collection with the isolated first player;
        # the shared collection probe covers all four resident contexts.
        put(private+0x38,2000);enter_imports();response(1);routine('purchase',[vendor,0]);state(5);message(0x1764)
        last=int(selected[-1]['item_id'],16)
        check('native pocket insertion',private+0x14,struct.pack('>H',last)+bytes(28))
        owned=bytearray(640);parent=selected[-1]
        owned[parent['profile_byte']-32]|=parent['profile_mask']
        check('purchase records only the active player collection',0x8046C0D0,owned)
        check('native single payment',private+0x38,struct.pack('>I',2000-price))
        expected=bytearray(stock_before);struct.pack_into('>H',expected,2*(last-category['first']),0)
        check('one consumed slot',stock,expected)
        routine('purchase',[vendor,0]);check('same order cannot charge twice',private+0x38,struct.pack('>I',2000-price))
        call(0x8007B44C,[4,1,2]);routine('give',[vendor,0]);state(0);message(0x1766)
        values=[call(0x8007B49C,[5,i]) for i in range(3)]
        record(dict(event_menu_handover=values,assertion='passed' if values==[last,7,0] else 'failed'))
        if values!=[last,7,0]:raise ValueError('Changed native handover request')
        enter_imports();response(0);routine('purchase',[vendor,0]);state(5)
        check('second native payment',private+0x38,struct.pack('>I',2000-2*price))
        parent=selected[0];owned[parent['profile_byte']-32]|=parent['profile_mask']
        check('both purchased parents are collected',0x8046C0D0,owned)
        routine('give',[vendor,0]);state(4);message(0x1760)
        routine('start',[vendor]);response(1);routine('route',[vendor,0]);state(4);message(0x1757)
        check('sold-out marker retained',stock,bytes(16)+struct.pack('>2H',8,category['kind']))
        check('all original merchandise retained',area,native)
        for at in guards:check('menu memory guard',at,edge)
    finally:
        for at,raw in saved.items():debug.write_memory(at,raw)
        call(0x8009C0F0,[allocation])
    for at,raw in saved.items():check('restored menu globals',at,raw)
    return dict(event_menu_native=True,ordinary_conversation_tested=False,
                catalogue_ownership_tested=True,save_reload_tested=False,requires_checkpoint_restore=True)


def wrapped_menu_cases(debug,image,receipt,call,check,record):
    """Actual relocated hand/exchange hook windows; no menu or reward simulation."""
    from v3_furniture_room_smoke import extend
    files=by_vrom(image);size=0x18000
    allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Wrapped menu allocation outside native heap')
    root,fixture,stack=(allocation+n for n in (16,0x12000,0x16000))
    edge=b'V3WP'*4
    debug.write_memory(allocation,bytes(size))
    guards=(allocation,fixture-16,fixture+0x400,stack-0x800,stack+0x200,allocation+size-16)
    for address in guards:debug.write_memory(address,edge)
    profiles={a:debug.read_memory(a,192) for a in (0x80460020,0x8046C010)}
    cases=0
    try:
        for row in receipt['consumers']:
            if not row['relocation_vrom']:continue
            data,rel=(files[v].extract(image) for v in (row['vrom'],row['relocation_vrom']))
            if sha256(data)!=row['output_sha256'] or sha256(rel)!=row['relocation_sha256']:
                raise ValueError('Wrapped menu owner differs from its full receipt')
            sections=struct.unpack_from('>5I',rel);ram=row['ram'];resident=len(data)+sections[3]
            if resident+len(rel)>=fixture-root-16:raise ValueError('Wrapped menu fixture overlaps owner')
            hand=row['vrom']==0x7829E0
            constants=(0x808742A8,) if hand else () # Native biased Bell table.
            loaded=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=resident,sections=sections),
                                         data,rel,root,address_constants=constants)
            call(0x800262D0,[row['vrom'],row['vrom']+len(data),ram,ram+resident,root,root+resident,len(rel)])
            check('complete cartridge hand/exchange owner and BSS',root,loaded)
            hook=next(h for h in receipt['hooks'] if h['vrom']==row['vrom'])
            start=root+hook['address']-ram;target=start+8
            # One case for each mapping, plus unavailable and ordinary states.
            tests=[(r,True,1) for r in receipt['rows']]
            tests += [(receipt['rows'][0],False,1),(None,True,0)]
            if not hand:tests += [(receipt['rows'][0],True,0),(receipt['rows'][0],True,2)]
            for parent,enabled,condition in tests:
                for address,original in profiles.items():
                    profile=bytearray(original)
                    for r in receipt['rows']:profile[r['profile_byte']]|=r['profile_mask']
                    if parent and not enabled:profile[parent['profile_byte']]&=~parent['profile_mask']
                    debug.write_memory(address,profile)
                item=int(parent['wrapped_item_id' if hand else 'item_id'],16) if parent else 0x2200
                result=(int(parent['item_id'],16) if enabled else 0) if hand and parent else item
                if not hand and parent and enabled and condition==1:result=int(parent['wrapped_item_id'],16)
                debug.write_memory(fixture,bytes(0x400))
                if hand:
                    debug.write_memory(fixture+0x3C,struct.pack('>I',item))
                    debug.write_memory(root+0x26E4,bytes(4))
                else:
                    debug.write_memory(fixture+0x23C,struct.pack('>H',item))
                    debug.write_memory(fixture+0x2E4,struct.pack('>I',condition))
                before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
                if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:
                    raise ValueError('Wrapped hook requires a paused native game frame')
                for i in range(1,32):
                    if i not in (26,27):regs[i]=(0x13579000+i)<<32|(0x2468A000+i)
                regs[3 if hand else 25]=extend(fixture)
                regs[29],regs[37]=extend(stack),extend(start)
                regs[33],regs[34]=0x123456789ABCDEF0,0xFEDCBA9876543210
                wanted=regs.copy();wanted[31]=extend(target)
                if hand:wanted[1],wanted[2]=0x251C,result
                else:wanted[3],wanted[7]=result&0xF000,result
                bp=f'0,{target:x},4'
                if debug.command('Z'+bp)!='OK':raise ValueError('Wrapped hook breakpoint refused')
                try:
                    if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':
                        raise ValueError('Wrapped hook register write refused')
                    stopped=debug.command('c');raw=debug.command('g')
                    actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
                    changes={str(i):[f'{wanted[i]:016X}',f'{actual[i]:016X}']
                        for i in (*range(26),28,29,30,31,33,34,*range(38,70)) if wanted[i]!=actual[i]}
                    passed=not changes and stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==target
                    record(dict(wrapped_menu_hook=hook['symbol'],item=f'{item:04X}',selected=enabled,
                        condition=condition,differences=changes,assertion='passed' if passed else 'failed'))
                    if not passed:raise ValueError('Wrapped hook changed live registers or continuation')
                finally:debug.command('z'+bp);debug.command('G'+before)
                if hand:
                    check('actual relocated hand condition',root+0x26E4,struct.pack('>I',int(parent is not None and enabled)))
                    debug.write_memory(root+0x26E4,bytes(4))
                check('complete hand/exchange owner retained',root,loaded)
                for address in guards:check('wrapped menu memory guard',address,edge)
                cases+=1
    finally:
        for address,original in profiles.items():debug.write_memory(address,original)
        call(0x8009C040,[allocation])
    for address,original in profiles.items():check('restored wrapped menu profile',address,original)
    return cases


def held_names(debug,rom_path,record):
    """Both real name entry points, with isolated selections and bounded outputs."""
    from runtime_layout import TEST_STACK
    from aflib import CODE_VROM,CODE_RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed held-name cartridge')
    equipment=report['equipment_resources'];wrapped=equipment['wrapped_presents'];names=wrapped['name_readers']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image)
    module=blob[equipment['blob_offset']:equipment['blob_offset']+equipment['bytes']]
    def check(label,address,want):
        actual=debug.read_memory(address,len(want));passed=actual==want
        record(dict(held_name_check=label,address=f'{address:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Held-name mismatch: '+label)
    def call(address,args=(),expected=None):
        result=debug.call(f'{address:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=boot.get(address))
        record(result)
        if expected is not None:
            passed=result['return_value']==expected
            record(dict(held_name_return=f'{address:08X}',actual=result['return_value'],
                expected=expected,assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Held-name return mismatch')
    check('complete startup equipment module',0x804A3000,module)
    check('complete current display readers',0x80466C00,blob[0x6C00:0x6F00])
    core=files[CODE_VROM].extract(image)
    check('complete hooked legacy getter',0x80096740,core[0x80096740-CODE_RAM:0x80096860-CODE_RAM])
    saved={a:debug.read_memory(a,n) for a,n in ((0x80460020,192),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16))}
    live=debug.read_memory(0x80126EA0,0xF980);state=debug.read_memory(0x8046C000,864)
    # Reuse the resident test scratch, below the independent call stack.
    output=MODULE_RAM+0x7000;before_output=debug.read_memory(output,64);edge=b'V3HN'*4;cases=0
    try:
        for address in (TEST_STACK-0x800,TEST_STACK+0x40):debug.write_memory(address,edge)
        for enabled in (True,False):
            selected=bytearray(saved[0x80460020])
            for row in wrapped['rows']:
                if enabled:selected[row['profile_byte']]|=row['profile_mask']
                else:selected[row['profile_byte']]&=~row['profile_mask']
            debug.write_memory(0x80460020,selected)
            for row in wrapped['rows']:
                item=int(row['wrapped_item_id'],16)
                for entry,width in ((0x801969C8,16),(0x80096740,10)):
                    debug.write_memory(output,b'\xA5'*64)
                    args=[output+17,width,item] if width==16 else [output+17,item]
                    call(entry,args,int(enabled) if width==16 else None)
                    want=bytearray(b'\xA5'*64)
                    if enabled:want[17:17+width]=b'present'.ljust(width,b' ')
                    check('exact name and both destination guards',output,want);cases+=1
                call(0x800C0194,[item],0) # Miscellaneous gifts have no sale price in either game.
        selected=bytearray(saved[0x80460020])
        for row in wrapped['rows']:selected[row['profile_byte']]|=row['profile_mask']
        debug.write_memory(0x80460020,selected)
        for item,capacity in ((0x251F,15),(0xFFFF251F,16),(0xFFFF,16)):
            debug.write_memory(output,b'\xA5'*64);call(0x801969C8,[output+17,capacity,item],0)
            check('invalid full-name arguments retain destination',output,b'\xA5'*64)
        call(0x801969C8,[0,16,0x251F],0);call(0x80096740,[0,0x251F])
        for item,label in ((0x251C,b'present'),(0x2200,b'net')):
            for entry,width in ((0x801969C8,16),(0x80096740,10)):
                debug.write_memory(output,b'\xA5'*64)
                call(entry,[output+17,width,item] if width==16 else [output+17,item],1 if width==16 else None)
                want=bytearray(b'\xA5'*64);want[17:17+width]=label.ljust(width,b' ')
                check('ordinary item reader retained',output,want);cases+=1
        check('equipment resources retained',0x804A3000,module)
        check('complete live save retained',0x80126EA0,live);check('extended save state retained',0x8046C000,state)
        for address in (TEST_STACK-0x800,TEST_STACK+0x40):check('name test stack guard',address,edge)
        check('no native fault',0x8003CE34,bytes(4))
    finally:
        for address,value in saved.items():debug.write_memory(address,value)
        debug.write_memory(output,before_output)
    for address,value in saved.items():check('restored name fixture',address,value)
    return dict(native_held_name_cases=cases,ten_and_sixteen_byte_entries=True,
        ordinary_gameplay_tested=False,flash_written=False,requires_checkpoint_restore=True)


def held_collection(debug,rom_path,record):
    """Actual acquisition/collection with four isolated resident records; no Flash writes."""
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed collection cartridge')
    equipment=report['equipment_resources'];receipt=equipment['collection']
    wrapped=equipment.get('wrapped_presents');menu_cases=0
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image)
    at=equipment['blob_offset'];module=blob[at:at+equipment['bytes']]
    boot=boot_proofs(image)
    bridge=None
    def check(label,address,want):
        actual=debug.read_memory(address,len(want));passed=actual==want
        record(dict(held_collection_check=label,address=f'{address:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',expected_sha256=sha256(want),actual_sha256=sha256(actual)))
        if not passed:raise ValueError('Held collection mismatch: '+label)
    def call(address,args=(),expected=None):
        target=address;proof=boot.get(address)
        if address>=0x80400000:
            if bridge is None:raise ValueError('Missing upper-memory call bridge')
            # Reuse the checked lower-memory jump bridge used by the menu
            # fixture; debugger code proofs intentionally exclude Expansion RAM.
            stub=struct.pack('>2I',0x08000000|((address>>2)&0x3FFFFFF),0)
            debug.write_memory(bridge,stub)
            call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            target=bridge;proof=(bridge,stub)
        result=debug.call(f'{target:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof)
        record(result)
        if expected is not None:
            passed=result['return_value']==expected
            record(dict(held_collection_return=f'{address:08X}',expected=expected,
                actual=result['return_value'],assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Held collection return mismatch')
        return result['return_value']
    check('complete startup equipment module',0x804A3000,module)
    saved={a:debug.read_memory(a,n) for a,n in ((0x80460020,192),(0x8046C000,864),
        (0x80136FD8,4),(0x80126EC0,4*0xBD0),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16))}
    edge=b'V3HC'*4
    allocation=call(0x8009BFC0,[64])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FFFC0:
        raise ValueError('Collection call bridge outside native heap')
    bridge=allocation+16
    debug.write_memory(allocation,edge+bytes(32)+edge)
    selected=bytearray(saved[0x80460020])
    for row in receipt['rows']:selected[row['profile_byte']]|=row['profile_mask']
    try:
        debug.write_memory(0x80460020,selected);call(0x80469200,expected=1)
        debug.write_memory(0x80126EC0,bytes(4*0xBD0))
        for address in (TEST_STACK-0x800,TEST_STACK+0x40):debug.write_memory(address,edge)
        wanted=bytearray(640)
        first,last=receipt['rows'][0],receipt['rows'][-1]
        if wrapped:
            parents={r['item_id']:r for r in receipt['rows']}
            first,last=(parents[r['item_id']] for r in (wrapped['rows'][0],wrapped['rows'][-1]))
        for p in range(4):
            private=0x80126EC0+p*0xBD0
            debug.write_memory(0x80136FD8,struct.pack('>I',private))
            row=(first,last)[p%2];item=int(row['item_id'],16);display=int(row['display_item_id'],16)
            call(0x80469AD4,[private,item],0)
            call(0x800B8B8C,[private,item,0])
            check('actual native pocket insertion',private+0x14,struct.pack('>H',item)+bytes(28))
            wanted[p*128+row['profile_byte']-32]|=row['profile_mask']
            check('only correct resident ownership changes',0x8046C0D0,wanted)
            call(0x80469AD4,[private,item],1);call(0x80469AD4,[private,display+3],1)
            call(0x800B88EC,[display+1]);check('rotation shares one bit',0x8046C0D0,wanted)
            other=(last,first)[p%2];other_item=int(other['item_id'],16)
            if wrapped:
                # Rotate through all four aliases without crediting ownership.
                alias=wrapped['rows'][(p+1)%4];other_item=int(alias['item_id'],16)
                if other_item==item:alias=wrapped['rows'][(p+2)%4];other_item=int(alias['item_id'],16)
                wrapped_id=int(alias['wrapped_item_id'],16)
                call(0x800B8B8C,[private,wrapped_id,0],1)
                call(0x800B8B08,[private,2,wrapped_id,0])
                check('wrapped aliases become actual pocket parents',private+0x14,struct.pack('>3H',item,other_item,other_item)+bytes(24))
                check('wrapped aliases set both pocket conditions',private+0x34,struct.pack('>I',0x14))
                call(0x804AA000,[wrapped_id],14)
            else:call(0x800B8B8C,[private,other_item,1])
            check('wrapped condition does not collect',0x8046C0D0,wanted)
            call(0x80469AD4,[private,other_item],0)
            check('original native furniture collection untouched',private+0xAF0,bytes(120))
        call(0x80469AD4,[0x80126EC1,int(first['item_id'],16)],0)
        # Disable a selected parent in both live profile copies without clearing
        # its owned bits. Queries and recording must not credit or mutate it.
        selected[first['profile_byte']]&=~first['profile_mask']
        debug.write_memory(0x80460020,selected);debug.write_memory(0x8046C010,selected)
        call(0x80469AD4,[0x80126EC0,int(first['item_id'],16)],0)
        call(0x800B88EC,[int(first['item_id'],16)])
        check('disabled parent leaves ownership intact',0x8046C0D0,wanted)
        if wrapped:
            private=0x80126EC0;alias=int(wrapped['rows'][0]['wrapped_item_id'],16)
            pockets=debug.read_memory(private+0x14,36)
            call(0x800B8B8C,[private,alias,0],0);call(0x800B8B08,[private,0,alias,0])
            check('unselected aliases never mutate pockets',private+0x14,pockets)
            call(0x804AA000,[alias],0)
            selected[first['profile_byte']]|=first['profile_mask']
            debug.write_memory(0x80460020,selected);debug.write_memory(0x8046C010,selected)
            full=struct.pack('>15H',*([0x2200]*15))+pockets[30:]
            debug.write_memory(private+0x14,full);call(0x800B8B8C,[private,alias,0],0)
            check('full pockets reject without mutation',private+0x14,full)
            menu_cases=wrapped_menu_cases(debug,image,wrapped,call,check,record)
            check('wrapped handling does not grant ownership',0x8046C0D0,wanted)
        for address in (TEST_STACK-0x800,TEST_STACK+0x40):check('test stack guard',address,edge)
        check('save-state guard',0x8046C350,bytes.fromhex('AF53C0DE')*4)
        check('equipment guard',0x804A3000+equipment['bytes']-16,bytes.fromhex('AF48C0DE')*4)
        check('no CPU fault',0x8003CE34,bytes(4))
        check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
        check('call bridge leading guard',allocation,edge);check('call bridge trailing guard',allocation+48,edge)
    finally:
        for address,value in saved.items():debug.write_memory(address,value)
        call(0x8009C040,[allocation])
    for address,value in saved.items():check('restored isolated state',address,value)
    return dict(native_held_collection=True,players=4,flash_written=False,wrapped_menu_windows=menu_cases,
        ordinary_gameplay_tested=False,catalogue_screen_tested=False,requires_checkpoint_restore=True)


def rod_effects_cases(debug,record,image,effects,actor,field,table,profile,call,check):
    """Load both cartridge fish owners; execute real angle windows and bite setup."""
    from v3_furniture_room_smoke import extend
    files=by_vrom(image);boot=boot_proofs(image);size=0x4000
    allocation=call(0x8009BFC0,[size]);root=allocation+16;stack=root+0x3C00
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Fish fixture allocation outside native heap')
    edge=b'V3RF'*4
    debug.write_memory(allocation,edge+bytes(size-32)+edge)
    debug.write_memory(stack-0x400,edge);debug.write_memory(stack+0x40,edge)
    f32=lambda value:struct.unpack('>f',struct.pack('>f',value))[0]
    try:
        for row in effects['owners']:
            data=files[row['vrom']].extract(image);rel=files[row['relocation_vrom']].extract(image)
            sections=struct.unpack_from('>5I',rel);ram=row['ram']
            expected=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=len(data),sections=sections),data,rel,root)
            call(0x800262D0,[row['vrom'],row['vrom']+len(data),ram,ram+len(data),root,root+len(data),len(rel)],
                 proof=boot[0x800262D0])
            check('complete cartridge fish owner and relocation',root,expected)
            factor=struct.unpack_from('>f',expected,row['angle_scale']-ram)[0]
            start=root+row['angle_window']-ram-4;end=root+row['angle_end']-ram
            imm=struct.unpack_from('>h',expected,row['angle_window']-ram-2)[0]
            scale_base=root+row['angle_scale']-ram-imm
            def angle(kind,index,value,want):
                before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
                if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:
                    raise ValueError('Rod window requires the paused native game frame')
                regs[1]=extend(scale_base);regs[2]=index*4;regs[4]=extend(value&0xFFFFFFFF)
                regs[29]=extend(stack);regs[37]=extend(start)
                bp=f'0,{end:x},4'
                if debug.command('Z'+bp)!='OK':raise ValueError('Rod angle breakpoint rejected')
                try:
                    if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':
                        raise ValueError('Rod angle registers rejected')
                    stopped=debug.command('c');raw=debug.command('g')
                    actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
                    passed=(stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==end
                            and actual[2]&0xFFFFFFFF==want and actual[29]&0xFFFFFFFF==stack
                            and actual[4]&0xFFFFFFFF==value&0xFFFFFFFF
                            and all(actual[i]&0xFFFFFFFF==regs[i]&0xFFFFFFFF for i in (*range(16,24),30)))
                    record(dict(rod_angle_window=f'{row["angle_window"]:08X}',kind=kind,search_class=index,
                        target_angle=value,expected=want,actual=actual[2]&0xFFFFFFFF,
                        stack_restored=actual[29]&0xFFFFFFFF==stack,assertion='passed' if passed else 'failed'))
                    if not passed:raise ValueError('Rod angle window changed result or live state')
                finally:debug.command('z'+bp);debug.command('G'+before)
            def bite(kind,index,want):
                debug.write_memory(actor+0x1D4,struct.pack('>I',index))
                debug.write_memory(actor+0x74,struct.pack('>3f',3.5,7.5,-2.25))
                before=bytearray(debug.read_memory(actor,0x13A0))
                call(root+row['bite_first']-ram,[actor],proof=(root,expected[:sections[0]]))
                before[0x214:0x218]=struct.pack('>I',want);before[0x228:0x22A]=struct.pack('>H',3)
                before[0x74:0x78]=before[0x7C:0x80]=bytes(4)
                check(f'rod kind {kind} fish {index}: exact bite setup and unrelated state',actor,bytes(before))
            for item,kind in ((0x2203,34),(0x2239,87),(0x2239,88)):
                if item==0x2239:debug.write_memory(table,struct.pack('>HbBHBB',item,kind,0,159,0x80,1))
                debug.write_memory(field,struct.pack('>H',item))
                values=(7.5,15.0,40.0,60.0,180.0) if kind==88 else (3.0,7.0,30.0,50.0,180.0)
                for i in (range(5) if kind!=87 else (0,)):
                    limit=int(f32(values[i]*factor))
                    # Include the gap where only the golden rod sees the bobber.
                    middle=int(f32(((3,7,30,50,180)[i]+(7.5,15,40,60,180)[i])*0.5*factor))
                    for value in dict.fromkeys((limit-1,limit,-limit,middle)):
                        if -32768<=value<=32767:angle(kind,i,value,int(-limit<value<limit))
                for index,cls in ((31,0),(7,1),(1,2),(2,3),(0,4)):
                    bite(kind,index,effects['golden_bite_frames' if kind==88 else 'normal_bite_frames'][cls])
            profile[159]&=0x7F;debug.write_memory(0x80460020,profile)
            angle('unselected golden',0,int(4*factor),0);bite('unselected golden',31,10)
            profile[159]|=0x80;debug.write_memory(0x80460020,profile)
            check('loaded fish code retained',root,expected)
        for at in (allocation,allocation+size-16,stack-0x400,stack+0x40):check('fish fixture guard',at,edge)
    finally:call(0x8009C040,[allocation])


def net_capture_cases(debug,record,actor,result,field,table,profile,owner_call,check):
    """Analytical collision cases through the actual native candidate loop."""
    def capture(name,span,points,winner=None,*,count=None,forced=0,diagonal=False):
        top=(10.0,20.0,30.0)
        end=(10.0+span*0.6,20.0,30.0+span*0.8) if diagonal else (10.0,20.0,30.0+span)
        debug.write_memory(actor+0xE3C,struct.pack('>6f',*top,*end))
        labels=[0x90000001+i for i in range(8)];types=bytes((254,127,3,4,5,6,7,8))
        padded=points+[(1000.0,1000.0,1000.0,0.0)]*(8-len(points))
        debug.write_memory(actor+0xE70,struct.pack('>8I',*labels)+types+
            b''.join(struct.pack('>3f',*(p[i]+top[i] for i in range(3))) for p in padded)+
            struct.pack('>8f',*(p[3] for p in padded))+
            struct.pack('>iIB',len(points) if count is None else count,forced,128))
        before=debug.read_memory(actor,0x13A0)
        output=b'NETG'+bytes.fromhex('1234567855ABCDEF')+b'NETG'
        debug.write_memory(result,output)
        want=int(bool(forced) or winner is not None)
        owner_call(0x808CC7E0,0x808CC988,[actor,result+4,result+8],want)
        expected=output if not want else b'NETG'+struct.pack('>IB',forced or labels[winner],
            128 if forced else types[winner])+bytes.fromhex('ABCDEF')+b'NETG'
        check(name+' output and bounded stores',result,expected)
        check(name+' immutable actor',actor,before)
        record(dict(net_capture_case=name,span=span,candidates=len(points) if count is None else count,
                    expected_winner=winner,forced_label=forced))
    for item,kind in ((0x2200,1),(0x2239,45),(0x2239,46)):
        if item==0x2239:debug.write_memory(table,struct.pack('>HbBHBB',item,kind,0,159,0x80,1))
        debug.write_memory(field,struct.pack('>H',item))
        golden=kind==46;span=60.0 if golden else 50.0;radius=21.0 if golden else 15.0
        for name,x,z,rad,winner in (
            ('inside',0.0,25.0,0.0,0),('radial boundary',radius,25.0,0.0,0),
            ('outside radius',radius+0.25,25.0,0.0,None),
            ('requested radius',radius+2.0,25.0,2.0,0),
            ('outside requested radius',radius+2.25,25.0,2.0,None),
            ('front cap',0.0,-1.0,2.0,0),('outside front cap',0.0,-3.0,2.0,None),
            ('end cap',0.0,span+1.0,2.0,0),('outside end cap',0.0,span+3.0,2.0,None),
            ('golden-only radius',18.0,25.0,0.0,0 if golden else None),
            ('golden-only span',0.0,55.0,0.0,0 if golden else None)):
            capture(f'kind {kind}: {name}',span,[(x,0.0,z,rad)],winner)
        capture(f'kind {kind}: first qualifying candidate',span,[(radius+1,0,25,0),(0,0,25,0),(1,0,25,0)],1)
        capture(f'kind {kind}: overlapping candidates',span,[(0,0,25,0),(0,0,30,0)],0)
        capture(f'kind {kind}: eighth candidate',span,[(radius+1,0,25,0)]*7+[(0,0,25,0)],7)
        capture(f'kind {kind}: diagonal span',span,[(span*0.3,0,span*0.4,0)],0,diagonal=True)
    for count in (-1,0,9):capture('rejected count '+str(count),60.0,[(0,0,25,0)],count=count)
    for count in (-1,0,8,9):
        capture('forced before count '+str(count),60.0,[(1000,0,25,0)],count=count,forced=0x87654321)
    profile[159]&=0x7F;debug.write_memory(0x80460020,profile)
    capture('unselected golden kind cannot enlarge net',50.0,[(18,0,25,0)])
    profile[159]|=0x80;debug.write_memory(0x80460020,profile)


def shovel_effects_cases(debug,record,image,effects,actor,game,check):
    """Actual hook/ABI/RNG; injected digging outcomes isolate the new suffix.

    One negative-world-position case also executes the complete unchanged native
    status routine. Other cases do not claim terrain or ordinary digging tests.
    """
    from aflib import CODE_RAM,CODE_VROM
    from v3_furniture_room_smoke import extend
    core=by_vrom(image)[CODE_VROM].extract(image)
    start=effects['hook']['address'];end=start+8;native=0x8008CAD8
    check('cartridge shovel hook and delay',start,core[start-CODE_RAM:end-CODE_RAM])
    check('complete native digging function',native,core[native-CODE_RAM:0x8008CC1C-CODE_RAM])
    rng=effects['random_function'];offset=rng-0x80025C60+0x1060
    check('complete native random function',rng,image[offset:offset+0x54])
    state=effects['previous_position_ram'];stack=game+0xC00;item=game+0x500
    spans=((state,12),(0x8003C590,4),(0x800419F0,4))
    saved={at:debug.read_memory(at,n) for at,n in spans}
    edge=b'V3DG'*4
    debug.write_memory(stack-0x200,edge);debug.write_memory(stack+0x2C0,edge)
    debug.write_memory(stack+676,struct.pack('>I',actor))
    origin=(100.0,9.0,-100.0);cases=[]
    for kind in (35,89,90):
        for status in range(6):cases.append((f'kind {kind}, status {status}',kind,status,(140.0,9.0,-100.0),True))
    for p in ((100,9999,-100),(120,9,-100),(80,9,-100),(100,9,-80),(100,9,-120),
              (120.001,9,-100),(79.999,9,-100),(100,9,-79.999),(100,9,-120.001)):
        cases.append(('strict position bounds',90,3,p,True))
    cases+= [('golden losing roll',90,3,(140,9,-100),False),
             ('native outside-world cancel',90,None,(-100,0,0),True)]
    try:
        for name,kind,status,position,win in cases:
            rawpos=struct.pack('>3f',*position);position=struct.unpack('>3f',rawpos)
            different=abs(position[0]-origin[0])>20 or abs(position[2]-origin[2])>20
            eligible=kind==90 and status==3 and different
            random_value=0x26666666 if win else 0x80000000
            seed=((random_value-0x3C6EF35F)*pow(0x19660D,-1,1<<32))&0xFFFFFFFF
            debug.write_memory(state,struct.pack('>3f',*origin))
            debug.write_memory(0x8003C590,struct.pack('>I',seed))
            debug.write_memory(0x800419F0,bytes(4))
            debug.write_memory(actor+0x1117,bytes((kind,)))
            actor_before=debug.read_memory(actor,0x13A0)
            debug.write_memory(item,b'\xA5\x5A\xFF\xFF\x5A\xA5')
            before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
            if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:
                raise ValueError('Shovel fixture requires the paused native frame')
            regs[4]=extend(item+2)
            for i,value in enumerate(struct.unpack('>3I',rawpos),5):regs[i]=extend(value)
            regs[29]=extend(stack);regs[37]=extend(start)
            bps=[f'0,{address:x},4' for address in (native,end)]
            for bp in bps:
                if debug.command('Z'+bp)!='OK':raise ValueError('Shovel breakpoint rejected')
            try:
                if debug.command('G'+''.join(f'{v:016x}' for v in regs))!='OK':raise ValueError('Shovel registers rejected')
                stopped=debug.command('c');raw=debug.command('g')
                current=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
                if (stopped[:3] not in ('T05','S05') or current[37]&0xFFFFFFFF!=native
                        or any(current[i]&0xFFFFFFFF!=regs[i]&0xFFFFFFFF for i in range(4,8))):
                    raise ValueError('Actual shovel bridge changed native item/position arguments')
                if status is not None:
                    # Data/register fixture only: no mock code enters cartridge RAM.
                    debug.write_memory(item+2,struct.pack('>H',0x4321))
                    current[2]=status;current[37]=current[31]
                    if debug.command('G'+''.join(f'{v:016x}' for v in current))!='OK':raise ValueError('Dig outcome injection rejected')
                debug.command('z'+bps[0]);stopped=debug.command('c');raw=debug.command('g')
                current=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
                expected_status=5 if eligible and win else 1 if status is None else status
                okay=(stopped[:3] in ('T05','S05') and current[37]&0xFFFFFFFF==end
                      and current[2]&0xFFFFFFFF==expected_status and current[29]&0xFFFFFFFF==stack
                      and all(current[i]&0xFFFFFFFF==regs[i]&0xFFFFFFFF for i in (*range(16,24),30)))
                record(dict(shovel_effects_case=name,kind=kind,injected_native_result=status,
                    actual_status=current[2]&0xFFFFFFFF,expected_status=expected_status,
                    actual_random_roll=eligible,stack_restored=current[29]&0xFFFFFFFF==stack,
                    assertion='passed' if okay else 'failed'))
                if not okay:raise ValueError('Native shovel effect result or ABI mismatch')
                expected_item=0x2103 if eligible and win else 0 if status is None else 0x4321
                check('shovel item and neighbouring guards',item,struct.pack('>3H',0xA55A,expected_item,0x5AA5))
                check('source previous-position update',state,rawpos if status==3 else struct.pack('>3f',*origin))
                check('exact RNG advancement',0x8003C590,struct.pack('>I',random_value if eligible else seed))
                check('actual player unchanged',actor,actor_before)
            finally:
                for bp in bps:debug.command('z'+bp)
                debug.command('G'+before)
        for at in (stack-0x200,stack+0x2C0):check('shovel stack guard',at,edge)
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
    for at,data in saved.items():check('restored digging and random state',at,data)


def tool_controls(debug,rom_path,record,*,transitions=False,capture=False,rod=False,shovel=False):
    """Execute current cartridge input consumers with isolated equipment data."""
    from aflib import CODE_RAM,CODE_VROM
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed tool-control cartridge')
    e=report['equipment_resources'];actions=e['player_actions'];controls=actions['tool_controls']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);core=files[CODE_VROM].extract(image)
    module=blob[e['blob_offset']:e['blob_offset']+e['bytes']];assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));ok=actual==want
        record(dict(tool_controls_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if ok else 'failed'))
        if not ok:raise ValueError('Tool-control mismatch: '+label)
        assertions+=1
    def call(address,args=(),want=None,proof=None):
        nonlocal assertions
        result=debug.call(f'{address:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof)
        if want is not None:
            result['assertion']='passed' if result['return_value']==want else 'failed';assertions+=1
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Native tool control returned wrong class/input')
        return result['return_value']
    def core_call(entry,end,args=()):
        return call(entry,args,proof=(entry,core[entry-CODE_RAM:end-CODE_RAM]))
    check('complete cartridge-loaded equipment code',equipment.RAM,module)
    constructor=struct.unpack('>I',debug.read_memory(0x80143900,4))[0]
    owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data=files[equipment.PLAYER_VROM].extract(image);rel=files[equipment.PLAYER_RELOC].extract(image)
    sections=struct.unpack_from('>5I',rel)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):raise ValueError('Missing loaded player')
    loaded=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete game-loaded player text',owner,loaded[:sections[0]])
    def owner_call(entry,end,args=(),want=None):
        at=owner+entry-equipment.PLAYER_RAM
        return call(at,args,want,(at,loaded[entry-equipment.PLAYER_RAM:end-equipment.PLAYER_RAM]))
    title=core_call(0x8007D90C,0x8007D91C)
    actual_game=struct.unpack('>I',debug.read_memory(0x8010EF90,4))[0]
    if title:
        controller=core_call(0x800B593C,0x800B594C);field=controller+0x3C
        button_spans=((controller+0x38,4),)
    else:
        private=struct.unpack('>I',debug.read_memory(0x80136FD8,4))[0];field=private+0x3EC
        button_spans=((actual_game+0x14,2),(actual_game+0x20,2))
    table=actions['equipment_selection']['table_ram']+16+(0x2239-0x2200)*8
    spans=((field,2),(0x80460020,192),(0x80126EB4,4),(table,8),*button_spans)
    if transitions:spans+=((0x8013767D,1),(0x80137908,1))
    if any(not 0x80000400<=a<=0x80800000-n for a,n in spans):raise ValueError('Invalid tool fixture data')
    saved={a:debug.read_memory(a,n) for a,n in spans};save_state=debug.read_memory(0x8046C000,864)
    allocation=call(0x8009BFC0,[0x3200]);actor=allocation+16;game=allocation+0x1400
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FCE00:raise ValueError('Tool fixture allocation failed')
    edge=b'V3TC'*4;debug.write_memory(allocation,edge+bytes(0x31E0)+edge)
    debug.write_memory(game+0x1C90,struct.pack('>I',actor));debug.write_memory(actor+0xCF0,struct.pack('>I',7))
    debug.write_memory(actor+0xE65,b'\1')
    def buttons(trigger,held,b=0):
        if title:debug.write_memory(controller+0x38,bytes((trigger,held,b,b)))
        else:
            debug.write_memory(actual_game+0x14,struct.pack('>H',(0x8000 if held else 0)|(0x4000 if b else 0)))
            debug.write_memory(actual_game+0x20,struct.pack('>H',(0x8000 if trigger else 0)|(0x4000 if b else 0)))
    predicates=[r for r in controls['consumers'] if r['symbol'].rsplit('for',1)[-1] in ('Axe','Net','Rod','Scoop')]
    try:
        profile=bytearray(saved[0x80460020]);profile[159]|=0x80
        debug.write_memory(0x80460020,profile);debug.write_memory(0x80126EB4,bytes(4))
        cases=((0x2201,0,0),(0x2200,1,1),(0x2203,34,34),(0x2202,35,35),
               (0x2239,44,0),(0x2239,46,1),(0x2239,88,34),(0x2239,90,35),
               (0x2239,91,2),(0x2239,107,2))
        if capture:
            if not actions.get('net_capture'):raise ValueError('Cartridge lacks golden net geometry')
            cases=()
            net_capture_cases(debug,record,actor,game+0x500,field,table,profile,owner_call,check)
        if rod:
            cases=()
            rod_effects_cases(debug,record,image,actions['rod_effects'],actor,field,table,profile,call,check)
        if shovel:
            cases=()
            shovel_effects_cases(debug,record,image,actions['shovel_effects'],actor,game,check)
            debug.write_memory(table,struct.pack('>HbBHBB',0x2239,90,0,159,0x80,1))
            debug.write_memory(field,struct.pack('>H',0x2239))
        if transitions:
            cases=();debug.write_memory(0x8013767D,b'\0');debug.write_memory(0x80137908,b'\0')
            requests=((0x808CB32C,0x808CB39C,40),(0x808CC108,0x808CC178,43),
                      (0x808CCCF4,0x808CCD64,44))
            def clear_request():debug.write_memory(actor+0xD00,struct.pack('>3I',7,0,0))
            for item,kind in ((0x2200,1),(0x2201,0),(0x2239,45),(0x2239,46)):
                if item==0x2239:debug.write_memory(table,struct.pack('>HbBHBB',item,kind,0,159,0x80,1))
                debug.write_memory(field,struct.pack('>H',item));net=kind in (1,45,46)
                for first,last,action in requests:
                    clear_request();owner_call(first,last,[game,5],int(net))
                    check('actual net request and priority',actor+0xD00,
                        struct.pack('>3I',action,5,1) if net else struct.pack('>3I',7,0,0))
                    clear_request();owner_call(first,last,[game,0],0)
                    check('equal priority cannot replace action',actor+0xD00,struct.pack('>3I',7,0,0))
                for held,done in ((1,0),(1,1),(0,0)):
                    clear_request();buttons(held,held)
                    owner_call(0x808CB6BC,0x808CB74C,[actor,game,done])
                    wanted=(7,34,1) if not net else ((43,22,1) if not held else ((41,13,1) if done else (7,0,0)))
                    check('slip exit chooses actual next action',actor+0xD00,struct.pack('>3I',*wanted))
            for first,last,_ in requests:
                clear_request();debug.write_memory(actor+0xE64,b'\1')
                owner_call(first,last,[game,5],0)
                debug.write_memory(actor+0xE64,b'\0');profile[159]&=0x7F;debug.write_memory(0x80460020,profile)
                owner_call(first,last,[game,5],0)
                profile[159]|=0x80;debug.write_memory(0x80460020,profile)
        for item,kind,family in cases:
            if item==0x2239:debug.write_memory(table,struct.pack('>HbBHBB',item,kind,int(family==2),159,0x80,1))
            debug.write_memory(field,struct.pack('>H',item));buttons(1,1)
            owner_call(0x808BD5C4,0x808BD668,[actor,7],kind)
            # Enter through the real relocated N64 callers. Their installed
            # calls exercise the Expansion Pak adapter without uploaded code.
            for row,wanted in zip(predicates,(0,1,34,35)):
                owner_call(row['entry'],row['end'],[game],int(family==wanted))
            if family in (0,1,34,35):
                index=(0,1,34,35).index(family);row=predicates[index];buttons(0,1)
                owner_call(row['entry'],row['end'],[game],int(family==1))
                buttons(0,0);owner_call(row['entry'],row['end'],[game],0)
            buttons(1,1)
            for name,want in (('Pickup',0),('Shake_tree',int(family==2))):
                row=next(r for r in controls['consumers'] if r['symbol']=='Player_actor_CheckController_for'+name)
                owner_call(row['entry'],row['end'],[game],want)
            record(dict(tool_family=family,actual_kind=kind,synthetic_extended_selector=item==0x2239))
        # Original selector guards still precede classification.
        debug.write_memory(actor+0xE64,b'\1');owner_call(0x808BD5C4,0x808BD668,[actor,7],0xFFFFFFFF)
        debug.write_memory(actor+0xE64,b'\0');debug.write_memory(0x80126EB4,struct.pack('>I',35))
        owner_call(0x808BD5C4,0x808BD668,[actor,7],0xFFFFFFFF)
        debug.write_memory(0x80126EB4,bytes(4));profile[159]&=0x7F;debug.write_memory(0x80460020,profile)
        owner_call(0x808BD5C4,0x808BD668,[actor,7],0xFFFFFFFF)
        check('saved state unchanged',0x8046C000,save_state)
        for a in (allocation,allocation+0x31F0):check('scratch guard',a,edge)
    finally:
        for a,data in saved.items():debug.write_memory(a,data)
        call(0x8009C040,[allocation])
    for a,data in saved.items():check('restored selector/profile/input state',a,data)
    check('complete equipment module restored',equipment.RAM,module)
    check('no fault',0x8003CE34,bytes(4));check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    return dict(native_shared_tool_controls=not transitions and not capture and not rod and not shovel,native_tool_transitions=transitions,
        native_net_capture=capture,native_rod_effects=rod,native_shovel_effects=shovel,
        digging_outcomes_injected=shovel,
        assertions=assertions,title_demo_input=bool(title),
        code_uploaded=False,synthetic_equipment_data=True,ordinary_gameplay_tested=False,
        golden_net_geometry_tested=capture,golden_rod_effects_tested=rod,
        golden_effects_tested=False,flash_written=False,requires_checkpoint_restore=True)


def exercise(debug, rom_path, record, *, section='automatic_furniture'):
    if section=='password_runtime':
        from v3_password_smoke import exercise as passwords
        return passwords(debug,rom_path,record)
    if section=='staged_profiles':return staged_profiles(debug,rom_path,record)
    if section=='scroll_lifecycles':return scroll_lifecycles(debug,rom_path,record)
    if section=='contact_lifecycles':return scroll_lifecycles(debug,rom_path,record,contact_only=True)
    if section=='movement_sounds':return movement_sounds(debug,rom_path,record)
    if section=='initial_switch':return initial_switch(debug,rom_path,record)
    if section=='room_surfaces':return room_surfaces(debug,rom_path,record)
    if section=='surface_consumers':return surface_consumers(debug,rom_path,record)
    if section=='surface_items':return surface_items(debug,rom_path,record)
    if section=='surface_application':return surface_application(debug,rom_path,record)
    if section=='surface_save':return surface_save(debug,rom_path,record)
    if section=='surface_menu':return surface_menu(debug,rom_path,record)
    if section=='surface_scoring':return surface_scoring(debug,rom_path,record)
    if section=='furniture_scoring':return furniture_scoring(debug,rom_path,record)
    if section=='birth_scoring':
        from v3_hra_birth_smoke import exercise as birth_scoring
        return birth_scoring(debug,rom_path,record)
    if section=='surface_audio':return surface_audio(debug,rom_path,record)
    if section=='surface_stock':return surface_stock(debug,rom_path,record)
    if section=='surface_selection':return surface_selection(debug,rom_path,record)
    if section=='furniture_audio':return furniture_audio(debug,rom_path,record)
    if section in ('scenery_planting_sparkle','scenery_planting_sparkle_remaining'):
        from v3_scenery_smoke import planting_sparkle
        return planting_sparkle(debug,rom_path,record,remaining_only=section.endswith('_remaining'))
    if section=='scenery_field_insects':
        from v3_scenery_smoke import field_insects
        return field_insects(debug,rom_path,record)
    if section=='scenery_felling_camera':
        from v3_scenery_smoke import felling_camera
        return felling_camera(debug,rom_path,record)
    if section in ('scenery_player_queries','scenery_player_guarded_consumers'):
        from v3_scenery_smoke import player_queries
        return player_queries(debug,rom_path,record,consumers_only=section=='scenery_player_guarded_consumers')
    if section=='scenery_interactions':
        from v3_scenery_smoke import interactions
        return interactions(debug,rom_path,record)
    if section=='scenery_world_queries':
        from v3_scenery_smoke import world_queries
        return world_queries(debug,rom_path,record)
    if section=='scenery_hidden_contents':
        from v3_scenery_smoke import daily_growth
        return daily_growth(debug,rom_path,record,contents=True)
    if section=='scenery_daily_growth':
        from v3_scenery_smoke import daily_growth
        return daily_growth(debug,rom_path,record)
    if section=='scenery_tree_states':
        from v3_scenery_smoke import tree_states
        return tree_states(debug,rom_path,record)
    if section=='seasonal_scenery':
        from v3_scenery_smoke import exercise as scenery
        return scenery(debug,rom_path,record)
    if section=='balloon_menu':return balloon_menu(debug,rom_path,record)
    if section=='balloon_release':return balloon_release(debug,rom_path,record)
    if section=='balloon_exchange':return reward_exchange(debug,rom_path,record,balloons=True)
    if section=='balloon_actor':return balloon_actor(debug,rom_path,record)
    if section=='balloon_selection':return balloon_actor(debug,rom_path,record,selection_only=True)
    if section=='reward_actions':return reward_actions(debug,rom_path,record)
    if section=='reward_pickup':return reward_pickup(debug,rom_path,record)
    if section=='reward_exchange':return reward_exchange(debug,rom_path,record)
    if section=='reward_controls':return reward_controls(debug,rom_path,record)
    if section=='reward_messages':return reward_messages(debug,rom_path,record)
    if section=='reward_motion':return reward_motion(debug,rom_path,record)
    if section=='held_names':return held_names(debug,rom_path,record)
    if section=='shovel_effects':return tool_controls(debug,rom_path,record,shovel=True)
    if section=='rod_effects':return tool_controls(debug,rom_path,record,rod=True)
    if section=='net_capture':return tool_controls(debug,rom_path,record,capture=True)
    if section=='tool_transitions':return tool_controls(debug,rom_path,record,transitions=True)
    if section=='tool_recovery':return held_rig_actions(debug,rom_path,record,tools=True,recovery=True)
    if section=='tool_motion':return held_rig_actions(debug,rom_path,record,tools=True)
    if section=='tool_controls':return tool_controls(debug,rom_path,record)
    if section=='held_catalogue':
        from v3_catalogue_smoke import held_previews
        return held_previews(debug,rom_path,record)
    if section=='held_collection':return held_collection(debug,rom_path,record)
    if section=='event_menu':return event_menu(debug,rom_path,record)
    if section=='event_acquisition':return event_stock(debug,rom_path,record)
    if section in ('ground_categories','ground_copy'):
        from v3_ground_categories_smoke import exercise as ground_categories
        return ground_categories(debug,rom_path,record,copy_only=section=='ground_copy')
    if section=='equipment_resources':return equipment_resources(debug,rom_path,record)
    if section=='equipment_bank_switch':return equipment_bank_switch(debug,rom_path,record)
    if section=='held_rig_actions':return held_rig_actions(debug,rom_path,record)
    if section=='held_level_sound':return held_level_sound(debug,rom_path,record)
    if section=='player_motion':return player_motion(debug,rom_path,record)
    if section=='pocket_icons':return pocket_icons(debug,rom_path,record)
    if section=='inventory_preview':return inventory_preview(debug,rom_path,record)
    if section=='inventory_rigs':return inventory_rigs(debug,rom_path,record)
    if section=='room_rigs':return room_rigs(debug,rom_path,record)
    if section=='clock_rigs':return room_rigs(debug,rom_path,record,mode=1)
    if section=='hit_rigs':return room_rigs(debug,rom_path,record,mode=3)
    if section=='billboard_rigs':return room_rigs(debug,rom_path,record,mode=4)
    if section=='rolling_rigs':return room_rigs(debug,rom_path,record,mode=5)
    if section=='item_categories':return item_categories(debug,rom_path,record)
    path = Path(rom_path)
    image = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_bytes())
    if sha256(image) != report['output_sha256'] or report['runtime_abi'] < 84:
        raise ValueError('Furniture probe requires its current checked cartridge')
    rows = representatives(report[section]['imports'])
    record(dict(representative_furniture=[r['item_id'] for r in rows],
                categories=['stock','footprint','display-list layers','action sounds','placement layers',
                            'interaction flags','preview framing','lighting','contact behaviour']))
    files, boot = by_vrom(image), boot_proofs(image)
    blob = files[runtime.BLOB].extract(image)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record(dict(furniture_batch_check=label, address=f'{address:08X}', bytes=len(expected),
                    assertion='passed' if actual == expected else 'failed',
                    expected_sha256=sha256(expected), observed_sha256=sha256(actual)))
        if actual != expected: raise ValueError('Native furniture mismatch: ' + label)

    def call(address, args=(), expected=None, proof=None):
        result = debug.call(f'{address:08X}', list(args), return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value'] == expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Native furniture call {address:08X}: unexpected result')
        return result['return_value']

    check('current startup and profile', 0x80460000, blob[:0x100])
    if 'furniture_placement' in report:
        placement=report['furniture_placement'];start=placement['reservation_start'];end=placement['reservation_end']
        at=runtime.PACKAGE+start-runtime.PACKAGE_RAM
        check('complete placement table and guards',start,blob[at:at+end-start])
    if 'catalogue_preview_records' in report:
        preview=report['catalogue_preview_records'];start=preview['reservation_start'];end=preview['reservation_end']
        at=runtime.PACKAGE+start-runtime.PACKAGE_RAM
        check('complete catalogue framing table and guards',start,blob[at:at+end-start])
    saved = {at: debug.read_memory(at, n) for at, n in (
        (0x80100DF0, 32), (0x8046C000, 864), (0x80126EC0, 0xBD0),
        (0x80136FD8, 4), (0x80135B1C, 1), (0x80135C00, 2), (0x801458B8, 4),
        (0x8003C590,4),(0x80126EB4,4),(0x80137000,15*56))}
    pool = report['furniture']['bank_pool']
    bank, bank_size = pool['data'], pool['bank_bytes']
    bank_before = debug.read_memory(bank, bank_size)
    index_ram = int(report['furniture']['expanded_tables']['bank_index_ram'], 16)
    for row in rows:
        at = index_ram + row['runtime_index']; saved[at] = debug.read_memory(at, 1)
    # The category owners share this temporary buffer, never coexist in it.
    # Use their actual resident/relocation lengths rather than reserving an
    # unrelated fixed 128-KiB owner arena in the crowded title-screen heap.
    owners=[(furniture.RESIDENT,len(files[furniture.RELOC].extract(image))),
            (files[catalogue.VROM].size,len(files[catalogue.RELOC].extract(image)))]
    changed_routes={r.get('reward_route') for r in rows}
    owners.extend((r['resident'],len(files[r['reloc']].extract(image)))
        for r in report.get('furniture_rewards',{}).get('routes',[]) if r['route'] in changed_routes)
    scratch_offset=(max(n+rel for n,rel in owners)+63)&~15
    size = scratch_offset+0x1000
    allocation = call(0x8009BFC0, [size])
    record(dict(furniture_fixture_bytes=size,owner_bytes=scratch_offset-32,allocation=allocation))
    if allocation & 15 or not MODULE_RAM + 0x8000 <= allocation <= 0x80400000 - size:
        raise ValueError('Furniture fixture allocation outside native heap')
    owner, scratch, bridge = allocation + 16, allocation + scratch_offset, allocation + scratch_offset+0xF00
    edge = b'V3SD' * 4
    guards = (allocation, scratch - 16, scratch + 0x100, bridge - 16, bridge + 8, allocation + size - 16)
    for at in guards: debug.write_memory(at, edge)

    def load(vrom, reloc_vrom, ram, resident):
        source, reloc = files[vrom].extract(image), files[reloc_vrom].extract(image)
        sections = struct.unpack_from('>5I', reloc)
        if resident + len(reloc) >= scratch - owner - 16:
            raise ValueError('Native furniture owner exceeds its fixture reservation')
        spec = SimpleNamespace(ram=ram, resident_bytes=resident, sections=sections)
        expected = relocate_verified_data(spec, source, reloc, owner)
        call(0x800262D0, [vrom, vrom+len(source), ram, ram+resident, owner, owner+resident, len(reloc)])
        check('complete actual owner load and relocations', owner, expected)
        return expected, (owner, expected[:sections[0]])

    loaded, furniture_proof = load(furniture.VROM, furniture.RELOC, furniture.RAM, furniture.RESIDENT)
    check('native directional chair table after relocation', owner+0x8094CFF8-furniture.RAM,
          loaded[0x8094CFF8-furniture.RAM:0x8094D028-furniture.RAM])
    debug.write_memory(0x80100E00, struct.pack('>I', owner))
    debug.write_memory(owner+0x18D68, struct.pack('>I', bank))
    public = next(r for r in report['furniture']['expanded_tables']['public_entries']
                  if r['name'] == 'af_v3_furniture_import_dma')
    check('installed furniture DMA public entry', public['entry'], bytes.fromhex(public['after']))
    stub = struct.pack('>II', 0x08000000 | ((public['entry'] >> 2) & 0x3FFFFFF), 0)
    debug.write_memory(bridge, stub)
    call(0x8002FE00, [bridge, 8]); call(0x80034CE0, [bridge, 8])
    tested_beds=set()
    tested_palettes=[]
    def palette_callbacks(row, asset, *, legacy=False):
        """One actual callback-category check, plus its unchanged-asset compatibility path."""
        receipt=report['furniture_palette_fade'];symbols=receipt['code']['symbols']
        at=runtime.PACKAGE+receipt['ram']-runtime.PACKAGE_RAM
        check('complete shared palette code, tables, and layout',receipt['ram'],blob[at:at+receipt['bytes']])
        layout=bytes.fromhex(receipt['legacy_layout_hex']) if legacy else asset[:32]
        _,n,count,on,off,*models=struct.unpack('>IHH6I',layout)
        if n!=len(asset):raise ValueError('Palette test layout differs from complete object')
        actor,gfx,game,arena=(scratch+x for x in (0x120,0x900,0xC00,0xC80))
        actor_data=bytearray(b'\xA5'*0x740);actor_data[0x12C]=0
        debug.write_memory(actor,actor_data);debug.write_memory(game,struct.pack('>I',gfx))
        debug.write_memory(gfx+0x298,struct.pack('>II',arena,arena+0x200))
        debug.write_memory(arena-16,edge);debug.write_memory(arena+0x200,edge)
        def callback(role):
            name='af_v3_palette_fade_dw' if role=='dw' and not legacy else 'af_v3_tent_model_'+role
            entry=symbols[name];jump=struct.pack('>II',0x08000000|(entry>>2&0x3FFFFFF),0)
            debug.write_memory(bridge,jump)
            call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            call(bridge,[actor,bank] if role in ('ct','dt') else [actor,0,game,bank],proof=(bridge,jump))
        callback('ct');actor_data[0x1A4:0x1A8]=bytes(4)
        check('palette constructor preserves complete actor',actor,actor_data)
        palettes=[]
        for step in (0,1):
            if step:
                debug.write_memory(actor+0x12C,b'\x01');actor_data[0x12C]=1
                callback('mv');actor_data[0x1A4:0x1A8]=struct.pack('>f',.1)
            check('palette movement preserves complete actor',actor,actor_data)
            head,tail=struct.unpack('>II',debug.read_memory(gfx+0x298,8));allocation=(tail-96)&~31
            callback('dw')
            expected=[0xDA380003,allocation,0xDB060020,allocation+64]
            for model in models[:count]:expected.extend((0xDE000000,model))
            check('every palette model in actual draw order',head,struct.pack('>'+str(len(expected))+'I',*expected))
            check('bounded palette arena endpoints',gfx+0x298,struct.pack('>II',head+(count+2)*8,allocation))
            fade=struct.unpack('>f',actor_data[0x1A4:0x1A8])[0]
            ons,offs=struct.unpack_from('>16H',asset,on),struct.unpack_from('>16H',asset,off)
            values=[(a&1)|sum(int((a>>s&31)+fade*((b>>s&31)-(a>>s&31)))<<s for s in (1,6,11))
                    for a,b in zip(offs,ons)]
            palette=struct.pack('>16H',*values);check('all interpolated native colours',allocation+64,palette)
            palettes.append((allocation+64,palette))
        callback('dt');actor_data[0x1A4:0x1A8]=bytes(4)
        check('palette destructor preserves complete actor',actor,actor_data)
        for address,palette in palettes:check('submitted palette survives movement and destruction',address,palette)
        check('palette draw retains complete source asset',bank,asset)
        check('palette arena leading guard',arena-16,edge);check('palette arena trailing guard',arena+0x200,edge)
        tested_palettes.append(row['item_id'])
        debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
    try:
        if 'furniture_behaviours' in report:
            from v3_furniture_behaviours import RAM as SOUND_RAM,ENTRY as SOUND_ENTRY,NATIVE_CATEGORIES
            from aflib import CODE_RAM,CODE_VROM
            behaviour=report['furniture_behaviours']
            at=runtime.PACKAGE+SOUND_RAM-runtime.PACKAGE_RAM
            check('complete shared behaviour code',SOUND_RAM,blob[at:at+behaviour['code']['bytes']])
            original_types=files[CODE_VROM].extract(image)[NATIVE_CATEGORIES-CODE_RAM:NATIVE_CATEGORIES-CODE_RAM+947]
            for category in (0,1,2):
                index=original_types.index(category)
                call(SOUND_ENTRY,[index,0],(0xFFFFFFFF,0x41F,0x420)[category])
            # Changed records, not every previously installed chair. Their
            # unchanged code/audio evidence is retained by the build contract.
            audible=[r for r in rows if r.get('action_sound',0)]
            for row in audible:
                for mode in (0,1):
                    call(SOUND_ENTRY,[row['runtime_index'],mode],((0x41F,0x422),(0x420,0x423))[row['action_sound']-1][mode])
            if audible:
                row=audible[0]
                profile=next(r for r in report['furniture']['imports'] if r['item_id']==row['item_id'])
                enable=int(profile['profile_ram'],16)-4;saved[enable]=debug.read_memory(enable,4)
                debug.write_memory(enable,bytes(4));call(SOUND_ENTRY,[row['runtime_index'],0],0xFFFFFFFF)
                debug.write_memory(enable,saved[enable])
                for mode in (0xFFFFFFFF,2):call(SOUND_ENTRY,[row['runtime_index'],mode],0xFFFFFFFF)
            for index in (947,1023,2048,0xFFFFFFFF):call(SOUND_ENTRY,[index,0],0xFFFFFFFF)
        for row in rows:
            item, index = int(row['item_id'], 16), row['runtime_index']
            contact=bytes.fromhex(row['native_profile_scalar_hex'])[12]
            if contact in (8,16) and contact not in tested_beds:
                from v3_furniture_behaviours import BED_HEAD,BED_FOOT_SIDES,BED_PILLOW_SIDES
                actor=scratch+0x200;actor_data=bytearray(0x740)
                struct.pack_into('>H',actor_data,0,index)
                struct.pack_into('>fff',actor_data,8,100,7,200)
                # One representative per contact category: actual native
                # geometry consumes its imported profile and all rotations.
                for rotation,(cosine,sine) in enumerate(((1,0),(0,1),(-1,0),(0,-1))):
                    struct.pack_into('>H',actor_data,0x124,rotation*0x4000)
                    debug.write_memory(actor,actor_data)
                    call(owner+BED_HEAD-furniture.RAM,[actor],(1,2,3,0)[rotation],furniture_proof)
                    # Both native branches are profile-driven: a double bed
                    # has a wider side span and a half-cell pillow offset.
                    foot,pillow,side=(40,0,40) if contact==8 else (20,-20,60)
                    for entry,x in ((BED_FOOT_SIDES,foot),(BED_PILLOW_SIDES,pillow)):
                        debug.write_memory(scratch,b'\xA5'*24)
                        call(owner+entry-furniture.RAM,[scratch,scratch+12,actor,1],1,furniture_proof)
                        expected=[v for z in (-side,side) for v in
                                  (100+x*cosine+z*sine,7,200-x*sine+z*cosine)]
                        actual=struct.unpack('>6f',debug.read_memory(scratch,24))
                        passed=all(abs(a-b)<.02 for a,b in zip(actual,expected))
                        record(dict(furniture_batch_check='native bed sides',item=row['item_id'],
                            rotation=rotation,entry=f'{entry:08X}',expected=expected,observed=actual,
                            assertion='passed' if passed else 'failed'))
                        if not passed: raise ValueError('Native imported bed positioning differs')
                for entry in (BED_FOOT_SIDES,BED_PILLOW_SIDES):
                    call(owner+entry-furniture.RAM,[scratch,scratch+12,actor,0],0,furniture_proof)
                    check('inactive bed has no entry/exit positions',scratch,bytes(24))
                check('native bed helpers preserve complete actor',actor,actor_data)
                tested_beds.add(contact)
            if row.get('interaction_flags',0)&0x10:
                from v3_furniture_placement import REGISTER
                # The actual native registration routine must skip collision in
                # an ordinary field, retaining its shop exceptions unchanged.
                call(0x80087E14,[],0)
                if call(0x80087C88)==0x3002: raise ValueError('Furniture fixture is in the broker shop')
                actor=scratch+0x200;expected=bytearray(0x740)
                struct.pack_into('>H',expected,0,index);debug.write_memory(actor,expected)
                call(owner+REGISTER-furniture.RAM,[actor,int(row['profile_ram'],16)],1,furniture_proof)
                struct.pack_into('>i',expected,0xD0,-1)
                check(row['name']+' complete native no-collision registration',actor,expected)
            debug.write_memory(scratch, bytes(0x100))
            call(0x801969C8, [scratch, 16, item], 1)
            check(row['name'] + ' full English name', scratch, row['name'].encode().ljust(16, b' '))
            call(0x800A5630, [item | 3], 10)
            call(0x800C0194, [item | 3], row['price'])
            call(0x800BE69C, [item | 3], row['size_code'])
            for rotation in (range(4) if row['size_code'] else (0,)):
                call(0x800BE72C, [item | rotation, 5, 6, scratch+32], row['size_code'])
                if row['size_code']==2:
                    cells=[(1,5,6),(1,6,6),(1,6,7),(1,5,7)]
                else:
                    cells = [(1, 5, 6)]
                    dx, dz = ((1, 0), (0, -1), (-1, 0), (0, 1))[rotation]
                    cells.append((1, 5+dx, 6+dz) if row['size_code'] else (0, 5, 6))
                    cells += [(0, 5, 6)] * 2
                check(row['name'] + f' complete footprint rotation {rotation}', scratch+32,
                      b''.join(struct.pack('>iii', *c) for c in cells))
            at = int(row['object_vrom'], 16)-runtime.BLOB
            asset = blob[at:at+row['object_bytes']]
            debug.write_memory(bank, b'\xA5' * bank_size)
            debug.write_memory(index_ram+index, b'\xFF')
            call(bridge, [index, item, bank, 0], 1, (bridge, stub))
            check(row['name'] + ' complete DMA and untouched bank tail', bank,
                  asset+b'\xA5'*(bank_size-len(asset)))
            check(row['name'] + ' bank assignment', index_ram+index, b'\x00')
            if (not tested_palettes and
                    row.get('profile',{}).get('callback_adapter',{}).get('category')=='switch-palette-fade'):
                palette_callbacks(row,asset)
                previous=next(r for r in report['tent_model']['imports'] if r['item_id']=='336C')
                old_index=previous['runtime_index'];address=index_ram+old_index
                saved.setdefault(address,debug.read_memory(address,1));debug.write_memory(address,b'\xFF')
                call(bridge,[old_index,int(previous['item_id'],16),bank,0],1,(bridge,stub))
                at=int(previous['object_vrom'],16)-runtime.BLOB
                old_asset=blob[at:at+previous['object_bytes']]
                check('legacy palette model complete DMA',bank,old_asset)
                palette_callbacks(previous,old_asset,legacy=True)
        loaded, proof = load(catalogue.VROM, catalogue.RELOC, catalogue.RAM, files[catalogue.VROM].size)
        available = owner + report['catalogue']['code']['symbols']['af_v3_catalogue_available'] - catalogue.RAM
        if 'catalogue_preview_records' in report:
            frame=owner+report['catalogue']['code']['symbols']['af_v3_catalogue_frame']-catalogue.RAM
            preview=scratch+0x200; before=b'\xA5'*0x760
            for row in rows:
                expected=bytearray(before);scalar=bytes.fromhex(row['donor_preview_scalar_hex'])
                expected[0xC:0x10]=scalar[4:];expected[0x758:0x75C]=scalar[:4]
                debug.write_memory(preview,before)
                call(frame,[preview,int(row['item_id'],16)|3],proof=proof)
                check(row['name']+' source framing and untouched preview fields',preview,expected)
            row=rows[0];item=int(row['item_id'],16)
            enable=int(row['profile_ram'],16)-4;saved[enable]=debug.read_memory(enable,4)
            debug.write_memory(enable,bytes(4));debug.write_memory(preview,before)
            call(frame,[preview,item],proof=proof);check('disabled preview untouched',preview,before)
            debug.write_memory(enable,saved[enable])
            selector=0x80498000+runtime.slot(item)*32+26;saved[selector]=debug.read_memory(selector,1)
            debug.write_memory(selector,b'\xFF')
            call(frame,[preview,item],proof=proof);check('invalid preview selector untouched',preview,before)
            debug.write_memory(selector,saved[selector])
            call(frame,[preview,0x1000],proof=proof);check('native preview untouched',preview,before)
        # Existing native list membership, acquisition, and ownership functions
        # use temporary state restored below; no FlashRAM write is requested.
        debug.write_memory(0x80135B1C, b'\x18')
        debug.write_memory(0x80135C00, bytes(2))
        debug.write_memory(0x80136FD8, struct.pack('>I', 0x80126EC0))
        debug.write_memory(0x80126ED4, bytes(0x24))
        debug.write_memory(0x8046C000+208, bytes(640))
        ownership = bytearray(128)
        for n, row in enumerate(rows):
            item = int(row['item_id'], 16)
            groups={0} if row.get('reward_route') else {0,row['stock_group']}
            for group in sorted(groups):
                call(0x800C0490, [item, 0, group, 0], int(not row.get('reward_route') and group == row['stock_group']))
            call(available, [item, 0, row['stock_group'], 0], int(row['catalogue_orderable']), proof)
            call(available, [item, 1, row['stock_group'], 0], 0, proof)
            call(available, [item, 0, 6, 0], 0, proof)
            if row['stock_group']>=3: call(available,[item,0,0,0],0,proof)
            call(0x800B8B8C, [0x80126EC0, item, 0], 1)
            check(row['name'] + ' acquired full pocket identity', 0x80126ED4+n*2, struct.pack('>H', item))
            bit = runtime.slot(item); ownership[bit//8] |= 1 << (bit & 7)
            check(row['name'] + ' saved catalogue ownership', 0x8046C000+208, ownership)
        if 'furniture_rewards' in report and any(r.get('reward_route') for r in rows):
            reward=report['furniture_rewards'];entry=reward['entry']
            first,last=reward['reservation_start'],reward['reservation_end']
            offset=runtime.PACKAGE+first-runtime.PACKAGE_RAM
            check('complete shared reward helper and guards',first,blob[offset:offset+last-first])
            # The debugger's direct-call proof is deliberately limited to
            # native low RAM. Reuse the checked low-RAM bridge, as model DMA
            # already does, to execute the actual upper-memory helper.
            reward_stub=struct.pack('>II',0x08000000|((entry>>2)&0x3FFFFFF),0)
            debug.write_memory(bridge,reward_stub)
            call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            reward_proof=(bridge,reward_stub)
            changed_routes={r.get('reward_route') for r in rows}
            for route in [r for r in reward['routes']+reward.get('trade_routes',[]) if r['route'] in changed_routes]:
                if 'vrom' in route:
                    loaded,_=load(route['vrom'],route['reloc'],route['ram'],route['resident'])
                    for patch in route['patches']:
                        check('native reward call after actual relocation',owner+patch['address']-route['ram'],
                              struct.pack('>I',patch['after']))
                members=[r for r in reward['imports'] if r['route']==route['route']]
                enables=[]
                for member in members:
                    address=runtime.ROWS_RAM+runtime.slot(int(member['item_id'],16))*80+4
                    saved[address]=debug.read_memory(address,4);enables.append(address)
                    debug.write_memory(address,bytes(4))
                # One isolated candidate, then a different sparse candidate:
                # neither can be selected by prefix count or list position.
                for selected in sorted({0,len(members)-1}):
                    debug.write_memory(enables[selected],struct.pack('>I',1))
                    call(bridge,[0,scratch,1,0,0,0,route['encoded']],proof=reward_proof)
                    check('selected-only native reward',scratch,bytes.fromhex(members[selected]['item_id']))
                    debug.write_memory(enables[selected],bytes(4))
                call(bridge,[0,scratch,1,0,0,0,route['encoded']],proof=reward_proof)
                fallback=struct.unpack('>H',debug.read_memory(scratch,2))[0]
                if fallback in {int(r['item_id'],16) for r in members}:
                    raise ValueError('Empty reward profile returned a disabled import')
                groups=(0,1,2) if route['fallback']==8 else (route['fallback'],)
                membership=[call(0x800C0490,[fallback,0,g,0]) for g in groups]
                passed=any(membership)
                record(dict(furniture_batch_check='native fallback stock membership',
                            route=route['route'],item=f'{fallback:04X}',assertion='passed' if passed else 'failed'))
                if not passed:raise ValueError('Optional reward fallback is outside native stock')
                for address in enables:debug.write_memory(address,saved[address])
            check('reward reservation unchanged',first,blob[offset:offset+last-first])
            if report['camper_trade'].get('shared_reward_categories') and any(r.get('reward_route') in (19,23) for r in rows):
                from v3_villager_rewards_smoke import ordinal
                trade=report['camper_trade'];loaded,proof=load(trade['vrom'],trade['relocation_vrom'],trade['ram'],trade['bytes'])
                picker=owner+0x8091ED64-trade['ram'];common=owner+0x8091EFDC-trade['ram']
                state=owner+0x80921DE8-trade['ram']
                private,animal,categories=owner+0x7000,owner+0x7B00,scratch+0x40
                debug.write_memory(animal,bytes.fromhex('E0EA')+bytes(0x526))
                debug.write_memory(categories,struct.pack('>3I',0,3,4))
                debug.write_memory(0x80136FD8,struct.pack('>I',private))
                def wanted(seed,threshold):
                    _,seed=ordinal(seed,1);r,seed=ordinal(seed,100);house,_=ordinal(seed,10)
                    return r>=threshold and house>0
                for route,scene,threshold in ((19,31,90),(23,35,80)):
                    members=[r for r in reward['imports'] if r['route']==route]
                    if not members:continue
                    chosen=members[-1];item=int(chosen['item_id'],16);enables=[]
                    for member in members:
                        address=runtime.ROWS_RAM+runtime.slot(int(member['item_id'],16))*80+4
                        saved.setdefault(address,debug.read_memory(address,4));enables.append(address)
                        debug.write_memory(address,struct.pack('>I',member==chosen))
                    seed=next(s for s in range(10000) if wanted(s,threshold))
                    for disabled in ((False,True) if route==19 else (False,)):
                        if disabled:
                            for address in enables:debug.write_memory(address,bytes(4))
                        data=bytearray(0xA80);struct.pack_into('>H',data,0x14,0x3224)
                        struct.pack_into('>H',data,0xA78,0x34BF);debug.write_memory(private,data)
                        debug.write_memory(state,bytes(0x30));debug.write_memory(0x8003C590,struct.pack('>I',seed))
                        debug.write_memory(0x80126EB4,struct.pack('>I',scene))
                        call(common,[picker,animal,categories,3,1],proof=proof)
                        check('complete camping trade retains input slot',state+12,bytes(4))
                        check('complete camping trade retains full input',state+0x14,bytes.fromhex('3224'))
                        check('complete camping trade retains pitfall mode',state+0x1C,bytes.fromhex('2512'))
                        if not disabled:check('source-category reward through full native trade',state+0x16,struct.pack('>H',item))
                        else:
                            actual=struct.unpack('>H',debug.read_memory(state+0x16,2))[0]
                            if actual in {int(r['item_id'],16) for r in members}:
                                raise ValueError('Unselected winter reward escaped native fallback')
                        other=struct.unpack('>2H',debug.read_memory(state+0x18,4))
                        passed=other[0]>>8==0x26 and other[1]>>8==0x27
                        record(dict(furniture_batch_check='complete seasonal trade categories',route=route,
                                    disabled=disabled,seed=seed,assertion='passed' if passed else 'failed'))
                        if not passed:raise ValueError('Camping trade lost native carpet/wall categories')
                    for address in enables:debug.write_memory(address,saved[address])
        check('no faulted CPU thread', 0x8003CE34, bytes(4))
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
        check('resident package guard', 0x804A2FF0, bytes.fromhex('AFACC0DE')*4)
        for at in guards: check('private allocation guard', at, edge)
    finally:
        debug.write_memory(bank, bank_before)
        for at, value in saved.items(): debug.write_memory(at, value)
    check('complete save state restored', 0x8046C000, saved[0x8046C000])
    check('native owner descriptor restored', 0x80100DF0, saved[0x80100DF0])
    call(0x8009C040, [allocation])
    return dict(native_furniture_batch_readers=True, complete_native_model_dma=True,
                native_preview_framing='catalogue_preview_records' in report,
                full_catalogue_initialization_tested=False,
                native_footprint_sizes=sorted({r['size_code'] for r in rows}), native_stock_membership=True,
                native_acquisition_and_ownership=True, ordinary_seating_tested=False,
                native_optional_rewards_tested='furniture_rewards' in report and any(r.get('reward_route') for r in rows),
                ordinary_npc_gift_handover_tested=False,
                native_shared_camping_trade_tested=bool(report['camper_trade'].get('shared_reward_categories')) and any(r.get('reward_route') in (19,23) for r in rows),
                native_bed_geometry_tested=bool(tested_beds),native_bed_contact_actions=sorted(tested_beds),
                native_palette_callbacks=tested_palettes,
                ordinary_bed_gameplay_tested=False,
                gpu_or_hardware_tested=False, flash_written=False, requires_checkpoint_restore=True)


def equipment_resources(debug,rom_path,record):
    """Exercise source-derived resource categories through the real item DMA."""
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed equipment cartridge')
    resources=report['equipment_resources'];files=by_vrom(image);blob=files[runtime.BLOB].extract(image)
    assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(equipment_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Equipment mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480)
        if want is not None:
            result['assertion']='passed' if result['return_value']==want else 'failed';assertions+=1
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError(f'Equipment call {at:08X} mismatch')
        return result['return_value']
    at=resources['blob_offset']
    check('complete startup-loaded code and resource table',equipment.RAM,blob[at:at+resources['bytes']])
    saved=debug.read_memory(0x8046C000,864)
    # Largest transfer in each distinct category, plus original native categories.
    selected={}
    for row in resources['records']:
        key=(row['kind'],row['type'])
        if key not in selected or row['bytes']>selected[key]['bytes']:selected[key]=row
    rows=list(selected.values());contract=resources['native_contract']
    original=files[0x00B8B000].extract(image)
    for i in (0,1,2,16):
        origin=contract['bounds'][i]-0x06000000+8;n=contract['sizes'][i]
        rows.append(dict(index=i,pointer=contract['pointers'][i],type=contract['types'][i],bytes=n,
            vrom=0x00B8B000+origin,origin=origin,expected=original[origin:origin+n]))
    rigs=resources.get('animated_rigs')
    capacity=rigs['allocation']['bank_bytes'] if rigs else equipment.CAPACITY
    size=0x2000+capacity*2+32;allocation=call(0x8009BFC0,[size]);target=allocation+0x2000
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Equipment scratch allocation outside native heap')
    edge=b'V3HR'*4;end=target+capacity
    debug.write_memory(allocation,edge);debug.write_memory(end,edge)
    debug.write_memory(target-16,edge);debug.write_memory(target+capacity*2,edge)
    try:
        for row in rows:
            index=row['index'];origin=row.get('origin',0)
            for address,want in ((0x800B12C8,row['pointer']),(0x800B12F4,row['type']),
                    (0x800B131C,row['bytes']),(0x800B1614,origin),(0x800B1650,row['vrom'])):
                call(address,[index],want)
            fill=bytes([0xA5])*capacity;debug.write_memory(target,fill)
            call(0x800B167C,[target,index])
            expected=row.get('expected')
            if expected is None:expected=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            check('complete held resource DMA',target,expected+fill[len(expected):])
            call(0x800B16D0,[index,target],target-origin)
            check('resource DMA left guard',allocation,edge);check('resource DMA right guard',end,edge)
        if rigs:
            # Actual native bank registration, not a guessed buffer-size limit.
            # The scratch Game_Play is isolated from the current scene/save.
            game=allocation+16;debug.write_memory(game,bytes(0x1FE0))
            put=lambda at,*v:debug.write_memory(at,struct.pack('>'+str(len(v))+'I',*v))
            put(game+0x1910,target,target+capacity*2+16)
            call(0x800B1590,[],capacity)
            call(0x800B1A28,[game]);call(0x800B1A28,[game])
            check('both real native bank records registered',game+0x1904,struct.pack('>I',2))
            check('both complete banks reserved',game+0x1910,struct.pack('>I',target+capacity*2))
            for i in range(2):
                status=game+0x110+i*0x54;bank=target+i*capacity
                check('native equipment bank identity',status,struct.pack('>H',35))
                check('native equipment bank pointers',status+4,struct.pack('>2I',bank,bank))
                check('native equipment bank capacity',status+16,struct.pack('>I',capacity))
            model=selected[('animated-model',1)]
            binding=model['source']['motion_bindings'][0]
            animation=next(r for r in resources['records'] if r['source_index']==binding['default_animation'])
            expected=b''.join(blob[r['blob_offset']:r['blob_offset']+r['bytes']] for r in (model,animation))
            for i in range(2):
                bank=target+i*capacity;debug.write_memory(bank,b'\xA5'*capacity)
                call(0x800B167C,[bank,model['index']])
                call(0x800B167C,[bank+model['bytes'],animation['index']])
                check('complete largest rig and motion in native bank',bank,expected+b'\xA5'*(capacity-len(expected)))
            check('double-bank left guard',allocation,edge)
            check('double-bank data left guard',target-16,edge)
            check('double-bank data right guard',target+capacity*2,edge)
            # This boundary is distinct from the old single-bank guard.
            check('double-bank end remains owned',game+0x1914,struct.pack('>I',target+capacity*2+16))
        missing=next(i for i in range(equipment.COUNT) if equipment.FIRST+i not in {r['index'] for r in resources['records']})
        for index in (0xFFFFFFFF,equipment.FIRST+equipment.COUNT,equipment.FIRST+missing):
            call(0x800B131C,[index],0);call(0x800B12C8,[index],0)
        check('save/profile unchanged',0x8046C000,saved)
        check('no faulted CPU thread',0x8003CE34,bytes(4))
        check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
        check('resident package guard',0x804A2FF0,bytes.fromhex('AFACC0DE')*4)
        check('equipment module guard',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
    finally:call(0x8009C040,[allocation])
    return dict(native_equipment_resources=True,representative_transfers=len(rows),assertions=assertions,
        imported_categories=len(selected),ordinary_menu_reload_tested=False,player_actions_tested=False,
        hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)


def equipment_bank_switch(debug,rom_path,record):
    """Switch complete rigs of different sizes through the loaded native owner."""
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed equipment-switch cartridge')
    resources=report['equipment_resources'];rigs=resources['animated_rigs'];files=by_vrom(image)
    if not rigs.get('animation_cache_invalidated_on_model_change'):
        raise ValueError('Equipment-switch probe requires model-change invalidation')
    blob=files[runtime.BLOB].extract(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(equipment_switch_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Equipment switch mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof)
        record(result);return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    constructor=struct.unpack('>I',debug.read_memory(0x80143900,4))[0]
    owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data=files[equipment.PLAYER_VROM].extract(image);rel=files[equipment.PLAYER_RELOC].extract(image)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):
        raise ValueError('Equipment switch requires the actual loaded player owner')
    sections=struct.unpack_from('>5I',rel)
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),
                                                  sections=sections),data,rel,owner)
    check('complete current player owner',owner,expected[:sections[0]])
    at=resources['blob_offset'];check('complete current shared equipment code',equipment.RAM,blob[at:at+resources['bytes']])
    saved=debug.read_memory(0x8046C000,864)
    capacity=rigs['allocation']['bank_bytes']
    player_bytes=resources.get('held_rig_actions',{}).get('player_allocation',{}).get('bytes',0x12D8)
    bank_offset=(player_bytes+63)&~15;size=bank_offset+capacity*2+32
    allocation=call(0x8009BFC0,[size]);actor=allocation+16;bank0=allocation+bank_offset
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Equipment switch scratch escapes native heap')
    edge=b'V3RS'*4;guards=(allocation,actor+player_bytes,bank0-16,bank0+capacity*2)
    debug.write_memory(actor,bytes(player_bytes))
    for at in guards:debug.write_memory(at,edge)
    put(actor+0xDBC,bank0,bank0+capacity)
    put(actor+0xDDC,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF)
    models=[r for r in resources['records'] if r['type']==1]
    small,large=min(models,key=lambda r:r['bytes']),max(models,key=lambda r:r['bytes'])
    animations={r['source_index']:r for r in resources['records'] if r['kind']=='animation'}
    entry=owner+0x808B5A10-equipment.PLAYER_RAM
    proof=(entry,expected[0x808B5A10-equipment.PLAYER_RAM:0x808B5B38-equipment.PLAYER_RAM])
    try:
        if call(0x800B1590)!=capacity:raise ValueError('Native bank allocation size differs from installed capacity')
        for step,model in enumerate((small,small,large,large,small,small)):
            animation=animations[model['source']['motion_bindings'][0]['default_animation']]
            index=(step+1)%2;bank=bank0+index*capacity
            call(entry,[actor,model['index'],animation['index']],proof)
            check('native alternating bank index',actor+0xDEC,struct.pack('>I',index))
            check('native model index',actor+0xDDC+index*4,struct.pack('>I',model['index']))
            check('native animation index',actor+0xDE4+index*4,struct.pack('>I',animation['index']))
            check('native animation address follows current model',actor+0xDC4+index*4,struct.pack('>I',bank+model['bytes']))
            check('native animation segment bias follows current model',actor+0xDD4+index*4,struct.pack('>I',bank+model['bytes']))
            wanted=b''.join(blob[r['blob_offset']:r['blob_offset']+r['bytes']] for r in (model,animation))
            check('complete actual model and animation after switch',bank,wanted)
            for at in guards:check('native bank-switch memory guard',at,edge)
        joint=resources.get('player_joint_work')
        if joint:
            check('actual player allocation includes complete animation work',0x8010BCEC,struct.pack('>I',player_bytes))
            segment=debug.read_memory(0x801458B8,4)
            original_work=b'\xA5\x5A'*42
            debug.write_memory(actor+0xA88,original_work)
            def owner_call(first,last,args):
                start=owner+first-equipment.PLAYER_RAM
                return call(start,args,(start,expected[first-equipment.PLAYER_RAM:last-equipment.PLAYER_RAM]))
            for model in (small,large):
                animation=animations[model['source']['motion_bindings'][0]['default_animation']]
                used=(model['source']['skeleton']['joints']+1)*6
                joint_at,morph_at=(actor+joint[k] for k in ('joint_offset','morph_offset'))
                poison=b'\xA5\x5A'*(joint['array_bytes']//2)
                debug.write_memory(joint_at,poison);debug.write_memory(morph_at,poison)
                owner_call(0x808BD934,0x808BDACC,[actor,model['index'],animation['index'],0,0,0x3F800000,1])
                check('native initializer binds both enlarged arrays',actor+0xA3C,struct.pack('>2I',joint_at,morph_at))
                owner_call(0x808BD81C,0x808BD880,[actor])
                pose=debug.read_memory(joint_at,used)
                written=all(pose[i:i+2]!=b'\xA5\x5A' for i in range(0,used,2))
                record(dict(equipment_joint_vectors=used//6,model=model['index'],
                            assertion='passed' if written else 'failed'))
                if not written:raise ValueError('Native animation did not write every joint component')
                assertions+=1
                check('no-morph playback retains other array',morph_at,poison)
                if used<joint['array_bytes']:
                    check('small rig retains unused joint vectors',joint_at+used,poison[used:])
                # Frame one, stationary, with a one-frame morph: the real
                # evaluator must write the complete morph table and joint pose.
                put(actor+0xA38,0x3F800000)
                owner_call(0x808BD81C,0x808BD880,[actor])
                check('native morph writes every expected vector',morph_at,pose+poison[used:])
                check('native morph retains stationary pose',joint_at,pose+poison[used:])
                check('original short work arrays are not overwritten',actor+0xA88,original_work)
                check('native animation restores segment six',0x801458B8,segment)
                for at in guards:check('native expanded-joint memory guard',at,edge)
        check('saved state retained',0x8046C000,saved)
        check('no CPU fault',0x8003CE34,bytes(4))
        check('equipment module guard',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
    finally:call(0x8009C040,[allocation])
    return dict(native_equipment_bank_switch=True,assertions=assertions,transitions=6,
        unchanged_animation_index=True,joint_work_vectors=resources.get('player_joint_work',{}).get('vectors',7),
        ordinary_gameplay_tested=False,hardware_tested=False,
        flash_written=False,requires_checkpoint_restore=True)


def held_rig_actions(debug,rom_path,record,*,tools=False,recovery=False):
    """Complete native rig initialization and draw callbacks on isolated actors."""
    import v3_equipment_runtime as equipment
    from v3_import_storage import jump
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed held-rig cartridge')
    resources=report['equipment_resources'];receipt=resources['held_rig_actions'];symbols=receipt['code']['symbols']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(held_rig_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',actual=actual.hex() if len(actual)<=32 else sha256(actual)))
        if not passed:raise ValueError('Held rig mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    def scalar(at):return struct.unpack('>I',debug.read_memory(at,4))[0]
    def floating(at):return struct.unpack('>f',debug.read_memory(at,4))[0]
    constructor=scalar(0x80143900);owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data=files[equipment.PLAYER_VROM].extract(image);rel=files[equipment.PLAYER_RELOC].extract(image)
    sections=struct.unpack_from('>5I',rel)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):
        raise ValueError('Held rigs require the actual loaded player owner')
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete game-loaded player code',owner,expected[:sections[0]])
    at=resources['blob_offset'];module=blob[at:at+resources['bytes']]
    check('complete startup-loaded rig module',equipment.RAM,module)
    check('native player allocation includes transient rig state',0x8010BCEC,struct.pack('>I',receipt['player_allocation']['bytes']))
    saved={at:debug.read_memory(at,n) for at,n in ((0x8046C000,864),(0x801458B8,4),(0x80107ADC,4),(0x80107AE8,4))}
    real_game=scalar(0x8010EF90)
    if not MODULE_RAM+0x8000<=real_game<=0x80400000-0x1000:raise ValueError('Missing current game')
    capacity=resources['animated_rigs']['allocation']['bank_bytes'];size=0x5000+capacity*2+32
    allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Held-rig fixture allocation outside native heap')
    actor,bridge,identity,game,graph,gfx,bank0=(allocation+x for x in (16,0x1400,0x1480,0x1500,0x1800,0x2000,0x5000))
    translucent=allocation+0x4100
    debug.write_memory(allocation,bytes(size));edge=b'V3RA'*4
    guards=(allocation,actor+receipt['player_allocation']['bytes'],bridge-16,bridge+16,graph-16,
            gfx-16,gfx+0x2000,translucent-16,translucent+0x700,
            bank0-16,bank0+capacity*2,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    def resident(name,args):
        stub=struct.pack('>II',jump(symbols[name]),0);debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        return call(bridge,args,(bridge,stub))
    def owner_call(first,last,args):
        entry=owner+first-equipment.PLAYER_RAM
        return call(entry,args,(entry,expected[first-equipment.PLAYER_RAM:last-equipment.PLAYER_RAM]))
    matrix_now=call(0x800E02AC);matrix_before=debug.read_memory(matrix_now,64)
    debug.write_memory(identity,struct.pack('>16f',*(1.0 if i%5==0 else 0.0 for i in range(16))))
    put(game,graph);put(actor+0xDBC,bank0,bank0+capacity)
    put(actor+0xDDC,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF)
    model_indices={r['fields'][2] for r in resources['kind_readers']['rows'] if r['item_main']==22}
    models=[r for r in resources['records'] if r['index'] in model_indices]
    models=[min(models,key=lambda r:r['bytes']),max(models,key=lambda r:r['bytes'])]
    if tools:models=[]
    animations={r['source_index']:r for r in resources['records'] if r['kind']=='animation'}
    try:
        # An ordinary original setup exercises the resident wrapper and its
        # owner-relative prologue bridge before native pinwheel initialization.
        put(actor+0xD00,0);debug.write_memory(actor+0x1117,b'\xFF')
        owner_call(0x808B83B4,0x808B846C,[actor,7,0xFFFFFFFF,0x3F800000,0,0xBF800000,identity+64,identity+68])
        check('ordinary setup retains no equipped item',actor+0x1117,b'\xFF')
        check('ordinary setup retains requested player animation',identity+64,struct.pack('>I',7))
        if tools:
            from aflib import CODE_RAM,CODE_VROM
            core=files[CODE_VROM].extract(image)
            def core_call(first,last):
                return call(first,proof=(first,core[first-CODE_RAM:last-CODE_RAM]))
            title=core_call(0x8007D90C,0x8007D91C)
            field=(core_call(0x800B593C,0x800B594C)+0x3C if title else scalar(0x80136FD8)+0x3EC)
            table=resources['player_actions']['equipment_selection']['table_ram']+16+(0x2239-0x2200)*8
            for at,n in ((field,2),(table,8),(0x80460020,192),(0x80126EB4,4)):
                saved[at]=debug.read_memory(at,n)
            profile=bytearray(saved[0x80460020]);profile[159]|=0x80
            debug.write_memory(0x80460020,profile);put(0x80126EB4,0)
            put(actor+0xD00,44);put(actor+0xCF0,7);debug.write_memory(actor+0xE65,b'\1')
            bobber=allocation+0x4800;put(actor+0xF28,bobber)
            by_index={r['index']:r for r in resources['records']}
            cases=((0x2200,1,1,3,3,4),(0x2239,46,22,3,24,4),
                   (0x2203,34,9,13,13,13),(0x2239,88,31,13,35,13))
            if recovery:
                cases=()
                for kind,shape,fall,rise,main in ((1,1,6,5,2),(46,22,27,26,2),(88,31,36,36,11)):
                    for getup,entry,end in ((False,0x808C2C8C,0x808C2D4C),(True,0x808C320C,0x808C32CC)):
                        put(bobber+0x234,7)
                        owner_call(entry,end,[actor,game,kind,0xC0A00000])
                        index=scalar(actor+0xDEC)
                        check('recovery preserves actual tool kind',actor+0x1117,bytes((kind,)))
                        check('recovery loads actual complete model',actor+0xDDC+index*4,struct.pack('>I',shape))
                        check('recovery uses proper fall/get-up motion',actor+0xDE4+index*4,struct.pack('>I',rise if getup else fall))
                        net=main==2
                        check('recovery selects native callback category',actor+0xCFC,struct.pack('>I',(6 if getup else 5) if net else main))
                        check('net recovery stops, other tools repeat',actor+0xA2C,struct.pack('>I',int(not net)))
                        check('recovery preserves native animation speed',actor+0xA24,struct.pack('>f',1))
                        check('non-net recovery retains bobber',bobber+0x234,struct.pack('>I',0 if net else 7))
                        for at in guards:check('recovery memory guard',at,edge)
            for iteration,(item,kind,shape,native_motion,motion,item_main) in enumerate(cases):
                family=1 if kind in (1,46) else 34
                if item==0x2239:debug.write_memory(table,struct.pack('>HbBHBB',item,kind,0,159,0x80,1))
                debug.write_memory(field,struct.pack('>H',item));put(bobber+0x234,7)
                owner_call(0x808B84DC,0x808B856C,[actor,family,native_motion,item_main,0,0x3F800000,1])
                index=scalar(actor+0xDEC);bank=bank0+index*capacity
                check('tool action keeps actual kind',actor+0x1117,bytes((kind,)))
                check('tool action keeps requested callback',actor+0xCFC,struct.pack('>I',item_main))
                check('tool action selects complete model',actor+0xDDC+index*4,struct.pack('>I',shape))
                check('tool action selects correct animation',actor+0xDE4+index*4,struct.pack('>I',motion))
                check('rod survives model/animation setup',bobber+0x234,struct.pack('>I',7 if family==34 else 0))
                check('tool action uses native timing',actor+0xA24,struct.pack('>2f',1,1))
                if kind>35:
                    model,animation=by_index[shape],by_index[motion]
                    wanted=b''.join(blob[r['blob_offset']:r['blob_offset']+r['bytes']] for r in (model,animation))
                    check('complete tool model and animation loaded',bank,wanted)
                    owner_call(0x808BD81C,0x808BD880,[actor])
                    put(0x801458B8,bank&0x1FFFFFFF);call(0x800E0284,[identity])
                    put(game+0xA0,iteration);put(graph+0x298,gfx,gfx+0x2000)
                    put(graph+0x2A8,translucent,translucent+0x700)
                    first,last=(0x808BE788,0x808BE85C) if family==1 else (0x808BF288,0x808BF360)
                    owner_call(first,last,[actor,game])
                    front,back=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
                    if not gfx<front<=back<=gfx+0x2000:raise ValueError('Tool drawer escaped its graphics arena')
                    draws=[p for w,p in struct.iter_unpack('>2I',debug.read_memory(gfx,front-gfx)) if w>>24==0xDE]
                    expected_lists=[0x06000000+m['native_offset'] for m in model['source']['models']]
                    passed=draws==expected_lists
                    record(dict(tool_draw_kind=kind,lists=draws,expected=expected_lists,assertion='passed' if passed else 'failed'))
                    if not passed:raise ValueError('Tool drawer omitted complete source model joints')
                    assertions+=1
                    check('tool drawer retains matrix stack',0x801462B4,struct.pack('>I',matrix_now))
                    check('rod-tip callback validity',actor+0xF44,struct.pack('>I',int(family==34)))
                if family==34:
                    owner_call(0x808B856C,0x808B8628,[actor,7,0x3FE00000,0,identity+64,identity+68])
                    index=scalar(actor+0xDEC)
                    check('rod walking selects moving animation',actor+0xDE4+index*4,struct.pack('>I',11 if kind==34 else 33))
                    check('rod walking preserves requested native speed',actor+0xA24,struct.pack('>f',1.75))
                for at in guards:check('tool setup/draw memory guard',at,edge)
            for at in (field,table,0x80460020,0x80126EB4):debug.write_memory(at,saved[at])
            check('complete tool module restored',equipment.RAM,module)
        for iteration,model in enumerate(models):
            animation=animations[model['source']['motion_bindings'][0]['default_animation']]
            owner_call(0x808BD934,0x808BDACC,[actor,model['index'],animation['index'],0,0,0x3F800000,1])
            check('native rig starts with stationary frame one',actor+0xA24,struct.pack('>2f',0,1))
            put(0x80107ADC,0);put(0x80107AE8,0x3F800000)
            debug.write_memory(actor+0x12D8,bytes(44))
            resident('af_v3_held_pinwheel_main',[actor,real_game])
            speed=floating(actor+0xA24);frame=floating(actor+0xA28)
            passed=abs(speed-1.2)<0.0001 and abs(frame-2.2)<0.0001
            record(dict(held_rig_native_animation=model['index'],speed=speed,frame=frame,
                        assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Native rig wind speed/frame mismatch')
            assertions+=1
            bank=bank0+scalar(actor+0xDEC)*capacity
            put(0x801458B8,bank&0x1FFFFFFF);call(0x800E0284,[identity])
            put(game+0xA0,iteration);put(graph+0x298,gfx,gfx+0x2000)
            # The native skeleton renderer binds its matrix segment in both
            # streams, even when every joint is opaque.
            put(graph+0x2A8,translucent,translucent+0x700)
            resident('af_v3_held_pinwheel_draw',[actor,game])
            front,back=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
            if not gfx<front<=back<gfx+0x2000:raise ValueError('Held rig drawing escaped its graphics arena')
            check('translucent stream contains only its matrix-segment binding',graph+0x2A8,
                  struct.pack('>2I',translucent+8,translucent+0x700))
            command=scalar(gfx);commands=debug.read_memory(gfx,front-gfx)
            draws=[p for w,p in struct.iter_unpack('>2I',commands) if w>>24==0xDE]
            passed=command==0xDA380003 and len(draws)==2 and scalar(actor+0x1300)==1
            record(dict(held_rig_native_draw=model['index'],commands=(front-gfx)//8,lists=draws,
                        assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Native rig drawing omitted complete joints or state')
            assertions+=1
            check('first draw has no spurious movement delta',actor+0x12D8,debug.read_memory(actor+0x12E4,12))
            check('balanced matrix-stack pointer',0x801462B4,struct.pack('>I',matrix_now))
            check('unchanged parent matrix',matrix_now,debug.read_memory(identity,64))
            check('native rod-tip validity cleared',actor+0xF44,bytes(4))
            for at in guards:check('native rig memory guard',at,edge)
        if receipt.get('balloon') and not tools:
            # The real view/light fields are required by reflection drawing.
            # Redirect only its graphics context to the isolated command arenas.
            saved[real_game]=debug.read_memory(real_game,4)
            saved[real_game+0xA0]=debug.read_memory(real_game+0xA0,4)
            model_indices={r['fields'][2] for r in resources['kind_readers']['rows'] if r['item_main']==21}
            balloons=[r for r in resources['records'] if r['index'] in model_indices]
            balloons=[min(balloons,key=lambda r:r['bytes']),max(balloons,key=lambda r:r['bytes'])]
            for iteration,model in enumerate(balloons):
                animation=animations[model['source']['motion_bindings'][0]['default_animation']]
                owner_call(0x808BD934,0x808BDACC,[actor,model['index'],animation['index'],0,0,0x3F800000,0])
                maximum=floating(actor+0xA20)
                put(actor+0xCFC,21);put(actor+0xDF0,0x3F800000)
                debug.write_memory(actor+0x5C,struct.pack('>3f',.01,.01,.01))
                resident('af_v3_held_balloon_setup',[actor,0])
                check('balloon setup uses actual duration and stop mode',actor+0xA24,struct.pack('>2fI',0,maximum,0))
                call(0x800E0284,[identity])
                owner_call(0x808BFA84,0x808BFAC4,[actor])
                check('native hand callback retains the hand matrix',actor+0x1054,debug.read_memory(identity,64))
                put(real_game,graph);put(real_game+0xA0,iteration)
                put(graph+0x298,gfx,gfx+0x2000);put(graph+0x2A8,translucent,translucent+0x700)
                bank=bank0+scalar(actor+0xDEC)*capacity;put(0x801458B8,bank&0x1FFFFFFF)
                resident('af_v3_held_balloon_main',[actor,real_game])
                resident('af_v3_held_balloon_draw',[actor,real_game])
                front,back=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
                if not gfx<front<=back<gfx+0x2000:raise ValueError('Balloon draw escaped its command arena')
                commands=debug.read_memory(gfx,front-gfx)
                draws=[p for w,p in struct.iter_unpack('>2I',commands) if w>>24==0xDE]
                expected_lists=[0x06000000+m['native_offset'] for m in model['source']['models']]
                passed=(draws==expected_lists and abs(floating(actor+0xA28)-(maximum-.085))<.0001
                        and abs(floating(actor+0xA24)+.0810415)<.0001)
                record(dict(held_balloon_native_draw=model['index'],lists=draws,frame=floating(actor+0xA28),
                    speed=floating(actor+0xA24),assertion='passed' if passed else 'failed'))
                if not passed:raise ValueError('Balloon omitted source joints or timed spring advance')
                assertions+=1
                check('balloon duration survives playback',actor+0xA20,struct.pack('>f',maximum))
                check('balloon consumes second substep',actor+receipt['balloon']['state_offset']+44,bytes(4))
                check('balloon retains the parent matrix',matrix_now,debug.read_memory(identity,64))
                check('balloon balances matrix stack',0x801462B4,struct.pack('>I',matrix_now))
                for at in guards:check('balloon work/graphics/stack guard',at,edge)
        check('save/profile unchanged',0x8046C000,saved[0x8046C000])
        check('no CPU fault',0x8003CE34,bytes(4))
        if receipt.get('loop_sound_installed'):
            # The new pinwheel callback legitimately updates only this float.
            level=receipt['loop_sound']['level_ram']-equipment.RAM
            check('module before runtime volume remains intact',equipment.RAM,module[:level])
            check('module after runtime volume remains intact',equipment.RAM+level+4,module[level+4:])
        else:check('complete module remains intact',equipment.RAM,module)
    finally:
        debug.write_memory(matrix_now,matrix_before)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    if tools:
        return dict(native_tool_motion=not recovery,native_tool_recovery=recovery,assertions=assertions,
            original_tools=1 if recovery else 2,imported_rigs=2,
            synthetic_equipment_data=True,code_uploaded=False,gpu_rendered=False,
            golden_effects_tested=False,ordinary_gameplay_tested=False,flash_written=False,
            requires_checkpoint_restore=True)
    return dict(native_held_rig_actions=True,assertions=assertions,
        representative_rigs=len(models)+(len(balloons) if receipt.get('balloon') else 0),
        representative_pinwheels=len(models),representative_balloons=len(balloons) if receipt.get('balloon') else 0,
        gpu_rendered=False,ordinary_gameplay_tested=False,pinwheel_selection_tested=False,
        sound_tested=False,flash_written=False,requires_checkpoint_restore=True)


def held_level_sound(debug,rom_path,record):
    """Shared sustained-equipment sound: native gain, registration, DMA, and expiry."""
    from aflib import CODE_VROM,u32
    from v3_import_storage import jump
    from v3_sound_programs import installed_resource
    from runtime_layout import TEST_STACK
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed level-sound cartridge')
    resources=report['equipment_resources'];rig=resources['held_rig_actions'];loop=rig['loop_sound']
    sound=resources['sound_programs'];rows=[r for r in sound['imports'] if r.get('kind')=='level']
    if len(rows)!=1 or not rig['loop_sound_installed']:raise ValueError('Expected one representative shared level program')
    row=rows[0];sid=row['native_sound_id'];symbols=rig['code']['symbols'];boot=boot_proofs(image);assertions=0
    files=by_vrom(image);core=files[CODE_VROM].extract(image);blob=files[runtime.BLOB].extract(image)
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(level_sound_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',actual=actual.hex() if len(actual)<=32 else sha256(actual)))
        if not passed:raise ValueError('Shared level sound mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def word(at):return u32(debug.read_memory(at,4),0)
    def bounded(at,n):
        if at&3 or not 0x80000400<=at<=0x80400000-n:raise ValueError('Level-sound pointer escapes native RAM')
        return at
    at=resources['blob_offset'];module=blob[at:at+resources['bytes']]
    check('complete startup-loaded sound module',equipment.RAM,module)
    hook=loop['hook'];check('installed native volume call',hook['address'],bytes.fromhex(hook['after']))
    seq=sound['sequence'];data=image[seq['physical']:seq['physical']+seq['bytes']]
    header=bytearray.fromhex(seq['header_after']);struct.pack_into('>I',header,0,seq['physical'])
    check('loaded sequence header',seq['header_address'],header)
    sequence=bounded(word(0x8014CBA8),len(data))
    check('complete sustained program',sequence+row['offset'],data[row['offset']:row['offset']+row['bytes']])
    check('level dispatch registration',sequence+row['native_table']+sid*2,struct.pack('>H',row['offset']))
    start,current,capacity,count=struct.unpack('>4I',debug.read_memory(0x8014C260,16))
    bounded(start,capacity)
    if capacity!=sound['after_budget']['capacity'] or not start<=current<=start+capacity or not count:
        raise ValueError('Shared level sound exceeds actual permanent heap')
    record(dict(level_sound_heap_used=current-start,capacity=capacity,remaining=start+capacity-current,assertion='passed'))
    allocation=bounded(call(0x8009BFC0,[0x1500]),0x1500);actor=allocation+16;bridge=allocation+0x1400
    debug.write_memory(allocation,bytes(0x1500));edge=b'V3LS'*4
    guards=(allocation,actor+0x1310,bridge-16,bridge+16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    def resident(name,args):
        stub=struct.pack('>II',jump(symbols[name]),0);debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8]);return call(bridge,args,(bridge,stub))
    saved={at:debug.read_memory(at,n) for at,n in ((0x80113D3C,120),(0x801138A8,1),(0x80113954,1),
          (0x80114324,72),(0x8010EF80,4),(0x80113844,1),(0x80113934,2),(0x8046C000,864))}
    observations=0
    try:
        debug.write_memory(0x8010EF80,bytes(4));debug.write_memory(0x80113844,b'\x01')
        debug.write_memory(0x80113934,bytes(2));debug.write_memory(0x801138A8,b'\0')
        mic=bounded(call(0x80060D6C,[word(0x8010EF90)]),12)
        debug.write_memory(actor+0x28,debug.read_memory(mic,12))
        for speed,gain in ((22,.25),(-44,.5),(176,1),(0,1)):
            debug.write_memory(actor+0xA24,struct.pack('>f',speed))
            resident('af_v3_held_pinwheel_sound',[actor])
            check('speed-dependent gain with zero retaining expiry',loop['level_ram'],struct.pack('>f',gain))
        entries=debug.read_memory(0x80113E04,50*16)
        matches=[i for i in range(50) if u32(entries,i*16)==actor]
        if len(matches)!=1:raise ValueError('Native actor sound identity was not registered uniquely')
        entry=0x80113E04+matches[0]*16
        check('native actor registration retains sound ID',entry+6,struct.pack('>H',sid))
        # Exercise the actual native volume consumer, including its unchanged
        # pause branch, fade factor, pan, and reverb command paths.
        for channel,kind,paused,fade,gain in ((0,sid,0,1,.25),(5,sid,0,.5,.25),
                                            (0,sid,1,1,.25),(2,sid-1,0,1,.25)):
            row_at=0x80113D3C+channel*20;temporary=bytearray(20);temporary[0]=kind
            struct.pack_into('>f',temporary,8,.8);temporary[16]=31;temporary[18]=temporary[19]=1
            debug.write_memory(row_at,temporary);debug.write_memory(loop['level_ram'],struct.pack('>f',gain))
            debug.write_memory(0x801138A8,bytes((paused,)));debug.write_memory(0x80113954,b'\x01')
            debug.write_memory(0x80114324+channel*12,struct.pack('>f',fade))
            cursor=debug.read_memory(0x80151BD8,1)[0];call(0x800F76CC,[channel])
            expected=.8*(.5 if paused else fade*(gain if kind==sid else 1))
            check('native queued volume',0x80151C54+cursor*8,struct.pack('>If',0x01000000|((channel+8)<<8),expected))
            if not paused:
                check('native queued pan',0x80151C54+((cursor+1)&255)*8,struct.pack('>2I',0x03000000|((channel+8)<<8),31<<24))
                check('native queued reverb',0x80151C54+((cursor+2)&255)*8,struct.pack('>2I',0x05000000|((channel+8)<<8),40<<24))
        for at in (0x80113D3C,0x801138A8,0x80113954,0x80114324):debug.write_memory(at,saved[at])
        debug.write_memory(0x801138A8,b'\0');debug.write_memory(actor+0xA24,struct.pack('>f',44))
        bank,header,_=installed_resource(image,core,'bank',row['native_bank'])
        _,_,wave=installed_resource(image,core,'wave',header[10])
        instrument=u32(bank,8+row['native_instrument']*4);sample=u32(bank,instrument+16)
        sample_bytes=u32(bank,sample)&0xFFFFFF;sample_start=wave+u32(bank,sample+4)
        for frame in range(10):
            resident('af_v3_held_pinwheel_sound',[actor]);record(debug.advance_game_frame())
            n=word(0x8014BB20)
            if not 0<n<=256:raise ValueError('Unbounded level-sound sample-DMA list')
            entries=debug.read_memory(bounded(word(0x8014BB1C),n*16),n*16)
            for i in range(n):
                raw=entries[i*16:(i+1)*16];ram,device=struct.unpack_from('>2I',raw)
                size=struct.unpack_from('>H',raw,10)[0];first,last=max(device,sample_start),min(device+size,sample_start+sample_bytes)
                if first>=last or not raw[14]:continue
                got=debug.read_memory(bounded(ram,size)+first-device,last-first)
                if got!=image[first:last]:raise ValueError('Level sound sample transfer differs from cartridge')
                observations+=1;record(dict(level_sound_sample_dma=True,frame=frame+1,bytes=len(got),assertion='passed'))
        if not observations:raise ValueError('No native sample transfers observed for sustained sound')
        check('sound remains registered while refreshed',entry,struct.pack('>I',actor))
        debug.write_memory(actor+0xA24,bytes(4))
        for _ in range(12):
            resident('af_v3_held_pinwheel_sound',[actor]);record(debug.advance_game_frame())
        check('native sound expires when speed reaches zero',entry,bytes(4))
        for at in guards:check('sound fixture guard',at,edge)
        check('save/profile remains unchanged',0x8046C000,saved[0x8046C000])
        check('no CPU fault',0x8003CE34,bytes(4))
        before=bytearray(module);at=loop['level_ram']-equipment.RAM
        before[at:at+4]=debug.read_memory(loop['level_ram'],4)
        check('only reserved loop gain changes in module',equipment.RAM,before)
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    return dict(native_held_level_sound=True,assertions=assertions,sample_dma_observations=observations,
        native_volume_pause_fade_pan_reverb=True,native_actor_registration_and_expiry=True,
        physical_audio_played=False,pcm_or_listening_verified=False,ordinary_gameplay_tested=False,
        flash_written=False,requires_checkpoint_restore=True)


def surface_selection(debug,rom_path,record):
    """Cold startup of a composed profile, including both checked packets."""
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed composed surface cartridge')
    blob=by_vrom(image)[runtime.BLOB].extract(image);surface=report['room_surfaces']
    selected=surface['optional_selection'];assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(surface_selection_check=label,address=f'{at:08X}',bytes=len(want),
            expected_sha256=sha256(want),actual_sha256=sha256(actual),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Composed surface startup mismatch: '+label)
        assertions+=1
    for name,resource in (('equipment',report['equipment_resources']),('surfaces',surface['items'])):
        start=resource['blob_offset'];data=blob[start:start+resource['bytes']]
        if sha256(data)!=resource['sha256']:raise ValueError('Changed complete '+name+' receipt')
        if name=='equipment':
            scenery=resource['scenery'];cache=scenery['tree_states']['cache_word']
            at=cache-resource['ram'];value=debug.read_memory(cache,4)
            if data[at:at+4]!=bytes(4) or value not in (bytes(4),struct.pack('>I',scenery['crc32'])):
                raise ValueError('Unexpected native scenery bootstrap cache')
            data=bytearray(data);data[at:at+4]=value
            record(dict(retained_scenery_cache=f'{cache:08X}',value=value.hex(),bound_crc32=scenery['crc32']))
        check('complete startup-loaded '+name+' packet',resource['ram'],data)
    bits=bytes.fromhex(selected['profile_hex']);base=bytes.fromhex(report['save_runtime']['profile_hex'])
    if len(bits)!=64 or len(base)!=192:raise ValueError('Invalid composed saved profile width')
    expected=struct.pack('>4I',0xAF535633,0,0,0)+base+bytes(880-192)+bits+bytes(256)+bytes.fromhex('AF53C0DE')*4
    check('complete format-4 state initialized from selected metadata',0x8046C000,expected)
    check('ordinary startup installed flag',0x8019ACD0,struct.pack('>I',1))
    check('no CPU fault',0x8003CE34,bytes(4))
    return dict(native_surface_selection=True,assertions=assertions,real_cold_startup=True,
        selected_surfaces=surface['items']['enabled_items'],ordinary_gameplay_tested=False,
        explicit_flash_write=False,requires_checkpoint_restore=True)


def surface_stock(debug,rom_path,record):
    """Real size-derived goods DMA, selected-only membership, and native RNG."""
    from aflib import CODE_RAM,CODE_VROM
    from flash_mail import SAVE_RAM,SAVE_BYTES
    from runtime_layout import TEST_STACK
    from v3_surface_items import RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface-stock cartridge')
    files=by_vrom(image);core=files[CODE_VROM].extract(image);boot=boot_proofs(image)
    surface=report['room_surfaces'];stock=surface['stock'];items=surface['items']
    blob=files[runtime.BLOB].extract(image)
    packet=blob[items['blob_offset']:items['blob_offset']+items['bytes']];assertions=0
    proofs={at:(at,core[at-CODE_RAM:at-CODE_RAM+n]) for at,n in
        ((0x800C0490,336),(0x800C05E0,164),(0x800BFCF0,668),(0x800C1BF0,72))}
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_stock_check=label,address=f'{at:08X}',bytes=len(want),
            expected=want.hex() if len(want)<32 else sha256(want),
            actual=got.hex() if len(got)<32 else sha256(got),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Surface-stock mismatch: '+label)
        assertions+=1
    def call(at,args=(),expected=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proofs.get(at) or boot.get(at))
        record(result);value=result['return_value']
        if expected is not None:
            if value!=expected&0xFFFFFFFF:raise ValueError(f'Surface-stock call {at:08X}: {value}, expected {expected}')
            assertions+=1
        return value
    def put(at,value):debug.write_memory(at,struct.pack('>I',value))
    check('complete current surface packet',RAM,packet)
    for row in stock['resources']:
        check('actual complete native goods descriptor',row['descriptor'],bytes.fromhex(row['descriptor_after']))
    for at,data in proofs.values():check('complete current native stock consumer',at,data)
    allocation=call(0x8009BFC0,[0x1000])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FF000:
        raise ValueError('Surface-stock fixture allocation escapes native heap')
    result_at,priority_at=allocation+32,allocation+64
    edge=b'V3SS'*4;guards=(allocation,result_at+16,priority_at+16,allocation+0xFF0,
        TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    saved={at:debug.read_memory(at,n) for at,n in
        ((SAVE_RAM,SAVE_BYTES),(0x8046C000,1232),(0x8003C590,4),(0x800419F0,4),(0x801458B8,4))}
    enabled={r['item_id']:RAM+r['offset']+4 for r in items['rows']}
    def select(values):
        for item,at in enabled.items():put(at,int(item in values))
    next_random=0xFF800000
    seed=((next_random-0x3C6EF35F)*pow(0x19660D,-1,1<<32))&0xFFFFFFFF
    try:
        # The title-screen fixture has no initialized town. Supply two valid
        # native rarity permutations in its disposable RAM payload only.
        for resource in stock['resources']:
            category=resource['category']
            wanted=(0,1,2) if category==3 else (2,1,0)
            debug.write_memory(0x80135B1C+category,bytes((wanted[0]<<6|wanted[1]<<4|wanted[2]<<2,)))
            call(0x800C1BF0,[priority_at,category])
            priorities=tuple(debug.read_memory(priority_at,3))
            if priorities!=wanted:raise ValueError('Invalid native surface stock priorities')
            record(dict(surface_stock_category=category,town_priorities=priorities))
            for group in resource['lists']:
                list_type=priorities[group['group']] if group['group']<3 else group['group']
                original=group['original_items'][-1];additions=group['added_items']
                # Each category is checked all-off/all-on. The event category
                # also tests a partial set, proving compaction before the RNG.
                selections=[[],additions]+([additions[:1]] if len(additions)>1 else [])
                for selected in selections:
                    select(selected)
                    for item in additions:
                        call(0x800C0490,[int(item,16),category,list_type,0],int(item in selected))
                        call(0x800C05E0,[int(item,16)],category if item in selected else -1)
                    call(0x800C0490,[original,category,list_type,0],1)
                    call(0x800C05E0,[original],category)
                    put(0x8003C590,seed);debug.write_memory(result_at,bytes(2))
                    call(0x800BFCF0,[0,result_at,1,0,0,category,list_type])
                    expected=int(selected[-1],16) if selected else original
                    check('complete native selector chooses the last eligible row',result_at,struct.pack('>H',expected))
                    check('native RNG advances once',0x8003C590,struct.pack('>I',next_random))
        select([])
        for item in (0x2640,0x2740,0x264B,0x274D):call(0x800C05E0,[item],-1)
        for category in (3,4):
            at=0x80135B1C+category;off=at-SAVE_RAM
            debug.write_memory(at,saved[SAVE_RAM][off:off+1])
        check('game saved payload unchanged',SAVE_RAM,saved[SAVE_RAM])
        check('import runtime saved state unchanged',0x8046C000,saved[0x8046C000])
        check('complete restored surface packet',RAM,packet)
        for at in guards:check('private arena/stack guard',at,edge)
        check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
        check('save guard',0x8046C4C0,bytes.fromhex('AF53C0DE')*4)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for row in items['rows']:
            at=row['offset']+4;debug.write_memory(RAM+at,packet[at:at+4])
        for at,data in saved.items():debug.write_memory(at,data)
        call(0x8009C040,[allocation])
    return dict(native_surface_stock=True,assertions=assertions,full_native_selector=True,
        native_stock_membership=True,native_size_derived_goods_dma=True,
        ordinary_purchase_or_event_delivery=False,saved_data_written=False,requires_checkpoint_restore=True)


def surface_audio(debug,rom_path,record):
    """Current complete native floor callers, sound dispatch, and audio heap."""
    from aflib import CODE_RAM,CODE_VROM,u32
    from v3_surface_items import RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface-audio cartridge')
    files=by_vrom(image);core=files[CODE_VROM].extract(image);audio=report['room_surfaces']['sound']
    items=report['room_surfaces']['items'];blob=files[runtime.BLOB].extract(image)
    packet=blob[items['blob_offset']:items['blob_offset']+items['bytes']];assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_audio_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=got.hex() if len(got)<32 else sha256(got)))
        if not passed:raise ValueError('Surface-audio mismatch: '+label)
        assertions+=1
    def word(at):return u32(debug.read_memory(at,4),0)
    def bounded(at,n):
        if at&3 or not 0x80000400<=at<=0x80400000-n:raise ValueError('Surface audio allocation escapes native RAM')
        return at
    def call(at,args):
        owner=next(r for r in audio['native_consumers'] if r['address']==at)
        proof=(at,core[at-CODE_RAM:at-CODE_RAM+owner['bytes']])
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof)
        record(result)
    check('complete resident selector packet',RAM,packet)
    seq=audio['sequence'];header=bytearray.fromhex(seq['header_after']);struct.pack_into('>I',header,0,seq['physical'])
    check('actual loaded SFX header',seq['header_address'],header)
    sequence=bounded(word(0x8014CBA8),seq['bytes'])
    expected=bytearray(image[seq['physical']:seq['physical']+seq['bytes']])
    # Six original channels use C7 stores to patch their own index/group
    # operands from live ports. These are dispatch state, not ROM corruption.
    scratch=[]
    for channel in range(6):
        for at,limit in ((0x5C+41*channel,128),(0x64+41*channel,6)):
            command=bytes((0xC7,0))+struct.pack('>H',at)
            if expected[at-5:at-1]!=command or expected[at]!=0:
                raise ValueError('Changed self-modifying native SFX channel')
            value=debug.read_memory(sequence+at,1)[0]
            if value>=limit:raise ValueError('Native SFX dispatch scratch exceeds its table bounds')
            expected[at]=value;scratch.append(dict(offset=at,value=value))
    record(dict(native_sequence_dispatch_scratch=scratch))
    check('complete loaded sequence retaining checked live dispatch operands',sequence,expected)
    total,fixed,permanent=struct.unpack_from('>3I',core,0x80119A44-CODE_RAM)
    heap=bounded(word(0x8014CB84),total);check('actual audio malloc size',0x8014CB88,struct.pack('>I',total))
    for label,at,size,expected_start in (('fixed',0x8014BEC0,fixed,heap),
            ('session',0x8014BEA0,total-fixed,heap+fixed),('permanent',0x8014C260,permanent,None)):
        start,current,capacity,count=struct.unpack('>4I',debug.read_memory(at,16))
        if (size!=capacity or not heap<=start<=current<=start+size<=heap+total or
                expected_start is not None and start!=expected_start):raise ValueError('Incorrect native '+label+' audio pool')
        record(dict(surface_audio_pool=label,capacity=capacity,used=current-start,allocations=count,assertion='passed'));assertions+=1
    saved={at:debug.read_memory(at,n) for at,n in ((0x80113844,0x28),(0x80113C34,192),(0x8046C000,1232))}
    try:
        debug.write_memory(0x80113844,b'\x01')
        # The real common walk dispatcher chooses one of four variants for each
        # walking/running mode. Verify its actual result against the bound set.
        rows=[dict(index=0,native_walk_selector=27,native_movement_sound=27)]+audio['imports']
        for row in rows:
            for entry,dash in ((0x800F9064,1),(0x800F9064,3),(0x800F9170,1),(0x800FA520,1)):
                debug.write_memory(0x80113C34,bytes(192));debug.write_memory(0x80113868,bytes((dash,)))
                debug.write_memory(0x8011385C,bytes(12));call(entry,[row['index'],0,0])
                slots=debug.read_memory(0x80113C34,192)
                live=[(i,struct.unpack_from('>H',slots,i*32)[0]) for i in range(6) if slots[i*32:i*32+2]!=bytes(2)]
                expected=({row['native_movement_sound']} if entry==0x800FA520 else
                    {0x2E6+row['native_walk_selector']+9*v+(36 if dash==3 else 0) for v in range(4)})
                if len(live)!=1 or live[0][1] not in expected:
                    raise ValueError('Native floor caller selected an unbound sound: '+str((row['index'],entry,dash,live,expected)))
                record(dict(native_floor_index=row['index'],caller=f'{entry:08X}',dash=dash,
                    actual_sound=f'{live[0][1]:04X}',assertion='passed'));assertions+=1
                check('actual sound priority',0x80113C34+live[0][0]*32+28,b'\x32')
        check('surface saved state unchanged',0x8046C000,saved[0x8046C000])
        check('surface packet unchanged',RAM,packet);check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
    return dict(native_surface_audio=True,assertions=assertions,complete_native_floor_consumers=True,
        native_synthesis_tested=False,physical_audio_played=False,ordinary_room_interaction=False,
        saved_data_written=False,requires_checkpoint_restore=True)


def furniture_scoring(debug,rom_path,record):
    """Changed theme bounds, all group rows, and native category score loops."""
    import v3_hra as hra
    from catalogue_names import Image
    from aflib import u32
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed theme-scoring cartridge')
    files=by_vrom(image);hr=report['hra'];series=hr['series'];boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(theme_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Native theme mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proof or boot.get(at));record(result);return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    size=0xA000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Theme-scoring arena allocation failed')
    owner,layers,points,theme,recommendation,name=(allocation+n for n in (16,0x8800,0x8840,0x8870,0x8880,0x88A0))
    data,reloc=(files[v].extract(image) for v in (hra.NEW_VROM,hra.NEW_RELOC))
    if (sha256(data),sha256(reloc))!=(hr['output_sha256'],hr['relocation_sha256']):
        raise ValueError('Changed complete scoring owner')
    if owner+len(data)+len(reloc)>layers-16:raise ValueError('Scoring owner exceeds isolated arena')
    loaded=relocate_verified_data(Image(hra.RAM,len(data),struct.unpack_from('>5I',reloc)),data,reloc,owner)
    debug.write_memory(allocation,bytes(size))
    call(0x800262D0,[hra.NEW_VROM,hra.NEW_VROM+len(data),hra.RAM,hra.RAM+len(data),owner,owner+len(data),len(reloc)])
    check('complete actual scoring load and relocation',owner,loaded)
    linked=lambda at:owner+at-hra.RAM
    proof=(owner,loaded[:hra.SECTIONS[0]])
    old_pointer=debug.read_memory(0x80107B50,4);old_state=debug.read_memory(0x8046C000,1232)
    edge=b'V3TH'*4;guards=(allocation,layers-16,points-16,name+16,allocation+size-16)
    for at in guards:debug.write_memory(at,edge)
    try:
        put(0x80107B50,owner)
        info_at=series['info_address']-hra.RAM;table_at=hr['metadata_address']-hra.RAM
        info=bytearray(data[info_at:info_at+63*3]);table=bytearray(data[table_at:table_at+hr['metadata_rows']*4])
        for idx in range(63):
            kind=info[idx*3];group=5 if kind==1 else 0;count=0
            for i in range(hr['metadata_rows']):
                value=u32(table,i*4)
                if value>>26==idx:
                    if kind==255:raise ValueError('A real item uses an inert padding theme')
                    if kind!=1 or (value>>16&1023)>=5:
                        struct.pack_into('>I',table,i*4,value&0xFC00FFFF|group<<16);group+=1
                    count+=1
            info[idx*3+1]=count&255
        call(linked(0x8092817C),[layers,5],proof)
        check('all installed furniture group assignments',linked(hr['metadata_address']),table)
        check('all 63 category counts and inert padding',linked(series['info_address']),info)
        check('all 63 empty search masks',linked(series['search_address']),bytes(63*4))
        for index in (57,59):
            call(linked(hra.RAM),[name,index],proof)
            key=data[series['names_address']-hra.RAM+index*10:series['names_address']-hra.RAM+(index+1)*10]
            check('actual full English theme key '+str(index),name,key)
        # Isolate each actual type without claiming the missing item delivery
        # is installed. These are disposable scoring tables, not saved rooms.
        for index,kind,pair in ((57,1,77),(59,2,75)):
            local=bytearray(info)
            for i in range(63):local[i*3+1]=0
            count=10 if kind==1 else 4
            local[index*3+1]=count
            debug.write_memory(linked(series['info_address']),local)
            debug.write_memory(linked(series['search_address']),bytes(63*4))
            put(linked(series['search_address'])+index*4,(1<<count)-1)
            for wall,floor,bonus in ((0,0,48000 if kind==1 else 0),(pair,pair,58000 if kind==1 else 43000)):
                put(points,17);put(theme,0xFFFFFFFF);put(recommendation,0)
                if kind==1:call(linked(0x80926FA0),[points,recommendation,wall,floor],proof)
                else:call(linked(0x80926B34),[points,theme,recommendation,name,wall,floor],proof)
                check('native category/matching-pair score '+str((index,wall,floor)),points,struct.pack('>I',17+bonus))
            debug.write_memory(linked(series['search_address']),bytes(63*4))
            for address,args in ((0x8092726C,[points]),(0x80926A08,[points]),
                    (0x80926FA0,[points,recommendation,0,0]),(0x80926B34,[points,theme,recommendation,name,0,0])):
                put(points,17);call(linked(address),args,proof)
                check('expanded scoring loop terminates without false bonus '+hex(address),points,struct.pack('>I',17))
        for index in (59,60,61,62,63,0xFFFFFFFF):
            result=call(linked(0x80925A5C),[0,index],proof)
            record(dict(theme_remaining_index=index,return_value=result,assertion='passed' if result==0 else 'failed'))
            if result:raise ValueError('Uninstalled or sentinel theme recommends a fabricated item')
            assertions+=1
        for at in guards:check('bounded theme arena guard',at,edge)
        check('complete scoring instructions remain unchanged',owner,loaded[:hra.SECTIONS[0]])
        check('no CPU fault',0x8003CE34,bytes(4))
        check('saved state unchanged',0x8046C000,old_state)
    finally:
        debug.write_memory(0x80107B50,old_pointer);call(0x8009C040,[allocation])
    check('prior scoring pointer restored',0x80107B50,old_pointer)
    return dict(native_furniture_theme_categories=True,assertions=assertions,complete_native_loops=True,
        synthetic_theme_membership=True,ordinary_score_letters_tested=False,acquisition_tested=False,
        saved_data_written=False,requires_checkpoint_restore=True)


def surface_scoring(debug,rom_path,record):
    """Current complete HRA evaluator with additive weights and matching themes."""
    import v3_hra as hra
    from catalogue_names import Image
    from v3_surface_items import RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface-scoring cartridge')
    files=by_vrom(image);hr=report['hra'];score=hr['surface_scoring'];items=report['room_surfaces']['items']
    blob=files[runtime.BLOB].extract(image);packet=blob[items['blob_offset']:items['blob_offset']+items['bytes']]
    boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_score_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Surface-score mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proof or boot.get(at));record(result);return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    check('complete current surface packet',RAM,packet)
    size=0x9000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Surface-scoring arena allocation failed')
    owner,layers,points,grid,theme,recommendation,name=(allocation+n for n in (16,0x8000,0x8020,0x8100,0x8050,0x8060,0x8070))
    data,reloc=(files[v].extract(image) for v in (hra.NEW_VROM,hra.NEW_RELOC))
    if (sha256(data),sha256(reloc))!=(hr['output_sha256'],hr['relocation_sha256']):
        raise ValueError('Changed complete HRA owner')
    if owner+len(data)+len(reloc)>=layers-16:raise ValueError('HRA image exceeds bounded scoring arena')
    loaded=relocate_verified_data(Image(hra.RAM,len(data),struct.unpack_from('>5I',reloc)),data,reloc,owner)
    debug.write_memory(allocation,bytes(size))
    call(0x800262D0,[hra.NEW_VROM,hra.NEW_VROM+len(data),hra.RAM,hra.RAM+len(data),owner,owner+len(data),len(reloc)])
    check('complete actual HRA loading and relocation',owner,loaded)
    linked=lambda at:owner+at-hra.RAM
    proof=(owner,loaded[:hra.SECTIONS[0]])
    old_pointer=debug.read_memory(0x80107B50,4);old_state=debug.read_memory(0x8046C000,1232)
    edge=b'V3SC'*4;guards=(allocation,layers-16,points-16,points+16,grid-16,grid+512,allocation+size-16)
    for at in guards:debug.write_memory(at,edge)
    try:
        put(0x80107B50,owner)
        for index,weight in [(0,51),(73,412),(74,51),(75,1000),(76,412),(77,1177),(72,0),(255,0)]:
            put(points,17)
            call(linked(0x809274F8),[points,layers,5,index,index],proof)
            check('full-index native surface contribution '+str(index),points,struct.pack('>I',17+2*weight))
        put(points,17);call(linked(0x809274F8),[points,layers,5,256,0xFFFFFFFF],proof)
        check('out-of-range arguments cannot read outside weight tables',points,struct.pack('>I',17))
        # A real original furnishing proves the new tail keeps prior accumulation.
        put(layers,grid);debug.write_memory(grid+34,bytes.fromhex('1000'))
        birth=struct.unpack_from('>I',data,hr['metadata_address']-hra.RAM)[0]>>9&31
        weight=struct.unpack_from('>I',data,hr['birth_extension']['points_address']-hra.RAM+birth*4)[0]
        put(points,17);call(linked(0x809274F8),[points,layers,5,75,77],proof)
        check('native furnishing score and caller total retained',points,struct.pack('>I',17+1000+1177+weight))
        put(layers,0)
        call(linked(0x8092817C),[layers,5],proof)
        series=linked(hr['series']['info_address']);search=linked(hr['series']['search_address'])
        for row in score['themes']:
            count=debug.read_memory(series+row['series']*3+1,1)[0]
            if not 1<=count<=32:raise ValueError('Theme member count exceeds native mask')
            debug.write_memory(search,bytes(hr['series']['count']*4))
            put(points,17);put(theme,0xFFFFFFFF);put(recommendation,0)
            call(linked(0x80926B34),[points,theme,recommendation,name,row['index'],row['index']],proof)
            check('matching surfaces retain native partial-theme bonus '+row['name'],points,struct.pack('>I',10017))
            put(search+row['series']*4,(1<<count)-1)
            put(points,17);put(theme,0xFFFFFFFF);put(recommendation,0)
            call(linked(0x80926B34),[points,theme,recommendation,name,row['index'],row['index']],proof)
            check('complete matching theme uses native bonus '+row['name'],points,struct.pack('>I',17+7000*count+15000))
            check('native complete theme identity '+row['name'],theme,struct.pack('>I',row['series']))
            check('existing English theme name '+row['name'],name,row['name'].encode().ljust(10,b' '))
        for at in guards:check('scoring arena guard',at,edge)
        check('complete installed evaluator stays intact',linked(0x809274F8),loaded[0x809274F8-hra.RAM:0x809277F8-hra.RAM])
        check('no CPU fault',0x8003CE34,bytes(4))
        check('saved profile and ownership remain unchanged',0x8046C000,old_state)
        check('surface packet remains unchanged',RAM,packet)
    finally:
        debug.write_memory(0x80107B50,old_pointer);call(0x8009C040,[allocation])
    check('prior HRA owner pointer restored',0x80107B50,old_pointer)
    return dict(native_surface_scoring=True,assertions=assertions,full_native_evaluator=True,
        existing_matching_theme_categories=3,complete_original_furniture_accumulator=True,
        ordinary_score_letters_tested=False,saved_data_written=False,requires_checkpoint_restore=True)


def surface_menu(debug,rom_path,record):
    """Actual surface catalogue initialization and native pocket exchange bodies."""
    from v3_catalogue import VROM,RELOC,RAM as CAT_RAM
    from catalogue_names import APPROVED,Image
    from v3_surface_items import RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface-menu cartridge')
    files=by_vrom(image);surface=report['room_surfaces'];items=surface['items'];cat=report['catalogue']
    blob=files[runtime.BLOB].extract(image);packet=blob[items['blob_offset']:items['blob_offset']+items['bytes']]
    boot=boot_proofs(image);assertions=0;bridge=None
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_menu_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Surface-menu mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None,proof=None):
        nonlocal assertions
        if at>=0x80400000:
            if bridge is None:raise ValueError('Missing upper-memory bridge')
            stub=struct.pack('>2I',0x08000000|(at>>2&0x3FFFFFF),0)
            debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            at,proof=bridge,(bridge,stub)
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want&0xFFFFFFFF else 'failed'
        record(result)
        if want is not None:
            if result['return_value']!=want&0xFFFFFFFF:raise ValueError('Surface-menu return mismatch')
            assertions+=1
        return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    check('complete current packet loaded by ordinary startup',RAM,packet)
    size=0x11000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Surface-menu fixture allocation failed')
    root,submenu,stub,bridge,tag_copy,actor=(allocation+n for n in (16,0x10A00,0x10B00,0x10B20,0x10C00,0x10E00))
    data,reloc=(files[v].extract(image) for v in (VROM,RELOC))
    if (sha256(data),sha256(reloc))!=(cat['output_sha256'],cat['relocation_sha256']):
        raise ValueError('Changed complete current catalogue')
    if root+len(data)+len(reloc)>=allocation+0x10628:raise ValueError('Catalogue overlaps private callbacks')
    loaded=relocate_verified_data(Image(CAT_RAM,len(data),struct.unpack_from('>5I',reloc)),data,reloc,root)
    debug.write_memory(allocation,bytes(size))
    call(0x800262D0,[VROM,VROM+len(data),CAT_RAM,CAT_RAM+len(data),root,root+len(data),len(reloc)])
    check('complete real loader relocation including resident table pointers',root,loaded)
    proof=(root,loaded[:14048]);cap=cat['capacity_expansion'];state=root+cap['state_offset']
    player=0x80126EC0
    saved={a:debug.read_memory(a,n) for a,n in ((player,0xBD0),(0x80136FD8,4),(0x8046C000,1232),
        (0x80136F48,4),(0x801458B8,4),(0x8010FD60,4))}
    edge=b'V3SM'*4;guards=(allocation,allocation+0x109F0,allocation+size-16)
    for at in guards:debug.write_memory(at,edge)
    debug.write_memory(stub,bytes.fromhex('03E0000800001025'))
    call(0x8002FE00,[stub,8]);call(0x80034CE0,[stub,8])
    put(submenu+0x2C,allocation);put(allocation+0x106B0,stub);put(allocation+0x10720,state)
    put(allocation+0x106D0,allocation+0x10400)
    init,name_at=(APPROVED['symbols'][k]+cap['insert_bytes'] for k in ('af_catalog_init','af_catalog_name'))
    def initialize():
        debug.write_memory(state,bytes(cap['state_bytes']))
        call(root+init,[submenu],proof=(root+init,loaded[init:init+40]))
    def page(kind):return state+0xEC8+(1 if kind=='wall' else 2)*cap['page_bytes']
    try:
        put(0x80136FD8,player);put(0x8010FD60,0);debug.write_memory(player,bytes(0xBD0))
        initialize()
        for row in surface['menu']['tables']:
            check('disabled surface imports do not change category count',root+row['descriptor']-CAT_RAM+4,struct.pack('>I',64))
            check('empty original category stays empty',page(row['kind']),bytes(2))
            put(root+row['descriptor']-CAT_RAM+4,69)
        for row in items['rows']:put(RAM+row['offset']+4,1)
        call(0x80469200,want=1)
        initialize()
        for row in surface['menu']['tables']:check('uncollected enabled surfaces remain absent',page(row['kind']),bytes(2))
        for row in items['rows']:call(0x800B88EC,[int(row['item_id'],16)])
        initialize()
        for row in surface['menu']['tables']:
            p=page(row['kind']);expected=b''.join(bytes.fromhex(r['item_id']) for r in row['imports'])
            check('all five collected category identities',p,struct.pack('>H',5))
            check('stable additive IDs in source order',p+8,expected)
            check('partial category completion flag',p+6,bytes(1))
            address=call(root+name_at,[p+cap['name_offset']],proof=(root+name_at,loaded[name_at:name_at+92]))
            item=next(i for i in items['rows'] if i['item_id']==row['imports'][0]['item_id'])
            check('full official name through actual catalogue cache',address,item['name'].encode().ljust(16,b' '))
        debug.write_memory(player+0xB68,b'\xFF'*16);initialize()
        for row in surface['menu']['tables']:
            p=page(row['kind']);base=0x2700 if row['kind']=='wall' else 0x2600
            check('original and imported complete category count',p,struct.pack('>H',69))
            check('complete category flag',p+6,b'\x01')
            check('all original identities retained before additions',p+8,struct.pack('>64H',*(base+i for i in range(64))))
        # Clear one selected tail row and its required-profile bit together.
        # Catalogue count must describe the selected list, not all reservations.
        row=surface['menu']['tables'][0];item=next(i for i in items['rows'] if i['item_id']==row['imports'][-1]['item_id'])
        put(RAM+item['offset']+4,0);selected=bytearray(debug.read_memory(0x8046C010+880,64));selected[41]&=~32
        debug.write_memory(0x8046C010+880,selected);put(root+row['descriptor']-CAT_RAM+4,68)
        initialize();check('removed surface excluded without breaking completion',page('wall'),struct.pack('>H',68))
        check('selected catalogue completion remains correct',page('wall')+6,b'\x01')
        put(RAM+item['offset']+4,1);selected[41]|=32;debug.write_memory(0x8046C010+880,selected)
        bit=root+cat['code']['symbols']['af_v3_catalogue_bit']-CAT_RAM
        call(bit,[player+0xB68,255],want=0,proof=(bit,loaded[bit-root:bit-root+84]))
        # Copy each complete installed native action. Only UI index/close calls
        # use inert fixture callbacks; the full-ID pocket/clip exchange is native.
        tag=files[0x3950000].extract(image)
        actions=((0x808726B0,'9cee59526cfdbc061ec72c5aa5595588574a8dad1be0a5530f4a3d12de7fe707','wall',0x274D,76,0x1A8,4),
                 (0x80872748,'547dc344834b78be59ce6ec9621d22843e01129c8c22b2a6658785a62fca36bf','floor',0x264A,73,0x1B0,8))
        put(0x80136F48,actor+0x190);put(actor+0x190,actor)
        for number,(entry,digest,kind,new,old,pending,clip) in enumerate(actions):
            code=bytearray(tag[entry-0x8086F310:entry-0x8086F310+152])
            if sha256(code)!=digest:raise ValueError('Changed complete native surface inventory action')
            seen=[]
            for at in range(0,len(code),4):
                word=struct.unpack_from('>I',code,at)[0]
                if word>>26==3:
                    target=(word&0x3FFFFFF)<<2|0x80000000;seen.append(target)
                    struct.pack_into('>I',code,at,0x0C000000|(stub>>2&0x3FFFFFF))
            if seen!=[0x8086F910,0x8086F4AC,0x80871760]:raise ValueError('Changed inventory UI-only calls')
            dest=tag_copy+number*152;debug.write_memory(dest,code)
            call(0x8002FE00,[dest,len(code)]);call(0x80034CE0,[dest,len(code)])
            put(actor+0x190+clip,items['code']['symbols']['af_v3_surface_reserve_'+kind])
            debug.write_memory(actor+(0x176 if kind=='wall' else 0x174),struct.pack('>H',old))
            debug.write_memory(player+0x14,struct.pack('>H',new))
            call(dest,[submenu,allocation+0x10628],proof=(dest,bytes(code)))
            check('native inventory returns complete previous surface item',player+0x14,struct.pack('>H',(new&0xFF00)+old))
            check('native action queues complete selected item',actor+pending,struct.pack('>IH',1,new))
        for at in guards:check('private arena guard',at,edge)
        check('complete live catalogue executable retained',root,loaded[:14048])
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        debug.write_memory(RAM,packet)
        call(0x8009C040,[allocation])
    check('complete resident packet restored',RAM,packet)
    for at,value in saved.items():check('fixture state restored',at,value)
    return dict(native_surface_menu=True,assertions=assertions,native_catalogue_initializer=True,
        native_inventory_exchange_bodies=True,inventory_ui_callbacks_stubbed=True,
        imports_enabled_only_in_fixture=True,ordinary_inventory_gameplay_tested=False,
        gpu_rendered=False,saved_data_written=False,requires_checkpoint_restore=True)


def surface_save(debug,rom_path,record):
    """Current format-4 codec, stable runtime entries, and native collection."""
    import sys
    if str(runtime.ROOT) not in sys.path:sys.path.insert(0,str(runtime.ROOT))
    from tests.test_v3_surface_save import fixture,reference_pack
    from tests import test_v3_save_rewards as reward_reference
    from tests import test_v3_save_codec as legacy_reference
    from v3_surface_items import RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface-save cartridge')
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);items=report['room_surfaces']['items']
    receipt=report['room_surfaces']['save'];saved_runtime=report['save_runtime'];boot=boot_proofs(image);assertions=0
    packet=blob[items['blob_offset']:items['blob_offset']+items['bytes']]
    base_profile=bytes.fromhex(saved_runtime['profile_hex'])
    source,working=fixture(base_profile);packed=reference_pack(source,working)
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_save_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Surface-save mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None,proof=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want&0xFFFFFFFF else 'failed'
        record(result)
        if want is not None:
            if result['return_value']!=want&0xFFFFFFFF:raise ValueError('Surface-save return mismatch')
            assertions+=1
        return result['return_value']
    check('complete expanded packet loaded by startup',RAM,packet)
    check('startup initializes full state without surface selections',0x8046C000,
        struct.pack('>4I',0xAF535633,0,0,0)+base_profile+bytes(1008)+bytes.fromhex('AF53C0DE')*4)
    allocation=call(0x8009BFC0,[0x11000])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-0x11000:
        raise ValueError('Surface-save fixture allocation failed')
    bank,profile,state,out,bridge=(allocation+x for x in (16,0x10040,0x10120,0x10600,0x10B00))
    edge=b'V3SS'*4;guards=(allocation,bank+0x10000,profile+192,state+1200,out+1200,allocation+0x10FF0)
    for at in guards:debug.write_memory(at,edge)
    targets={k:report['save_codec']['code']['symbols']['af_v3_save_'+k] for k in ('check','pack','collect')}
    targets.update({k:saved_runtime['code']['symbols']['af_v3_save_'+k] for k in ('reset','commit')})
    targets['owned']=report['collection']['code']['symbols']['af_v3_catalogue_owned']
    wrappers=bytearray();entries={}
    for name,target in targets.items():
        entries[name]=bridge+len(wrappers);wrappers.extend(struct.pack('>4I',0x08000000|(target>>2&0x3FFFFFF),0,0,0))
    debug.write_memory(bridge,wrappers);call(0x8002FE00,[bridge,len(wrappers)]);call(0x80034CE0,[bridge,len(wrappers)])
    proof=(bridge,bytes(wrappers))
    def entry(name,args=(),want=None):return call(entries[name],args,want,proof)
    saved={at:debug.read_memory(at,n) for at,n in ((0x8046C000,1232),(0x80126EA0,0xF980),(0x80136FD8,4))}
    try:
        for row in items['rows']:debug.write_memory(RAM+row['offset']+4,struct.pack('>I',1))
        debug.write_memory(profile,base_profile);debug.write_memory(state,working)
        debug.write_memory(bank,reward_reference.reference_pack(source,working[:880]))
        entry('check',[bank,0x10000,profile,out],1)
        check('format-3 migration retains all old state and clears surface ownership',out,working[:944]+bytes(256))
        debug.write_memory(bank,source);entry('pack',[bank,0x10000,state],1)
        check('complete format-4 bank matches independent encoder',bank,packed)
        entry('check',[bank,0x10000,profile,out],1);check('complete extended working state decodes',out,working)
        first=RAM+items['rows'][0]['offset']+4;debug.write_memory(first,bytes(4));debug.write_memory(out,b'\xA5'*1200)
        entry('check',[bank,0x10000,profile,out],-7);check('missing surface refuses without output writes',out,b'\xA5'*1200)
        debug.write_memory(first,struct.pack('>I',1))
        bad=bytearray(packed);bad[0xF980+0x3D0]=1;legacy_reference.seal_extension(bad)
        debug.write_memory(bank,bad);entry('check',[bank,0x10000,profile,out],-8)
        check('invalid ownership refuses without output writes',out,b'\xA5'*1200)
        debug.write_memory(bank,packed);entry('reset',[],1);entry('commit',[bank,0x80126EA0,0xF980])
        check('stable native commit restores full extended state',0x8046C010,working)
        check('stable native commit preserves native payload',0x80126EA0,packed[:0xF980])
        expected=bytearray(working);player=3;private=0x80126EC0+player*0xBD0
        debug.write_memory(0x80136FD8,struct.pack('>I',private))
        entry('owned',[private,0x274D],0);call(0x800B88EC,[0x274D]);entry('owned',[private,0x274D],1)
        expected[944+player*64+41]|=32
        check('native pocket collection records only the selected surface/player',0x8046C010,expected)
        call(0x800B7ADC,[private])
        expected[192+player*128:192+(player+1)*128]=bytes(128)
        expected[704+player*32:704+(player+1)*32]=bytes(32)
        expected[832+player*12:832+(player+1)*12]=bytes(12)
        expected[944+player*64:944+(player+1)*64]=bytes(64)
        check('native player deletion clears its surfaces and preserves the existing clear chain',0x8046C010,expected)
        check('expanded state guard retained',saved_runtime['guard_ram'],bytes.fromhex('AF53C0DE')*4)
        for at in guards:check('surface-save arena guard',at,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for row in items['rows']:debug.write_memory(RAM+row['offset']+4,bytes(4))
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    check('complete packet restored',RAM,packet)
    return dict(native_surface_save=True,assertions=assertions,actual_format4_codec_and_stable_runtime=True,
        native_collection_and_player_clear=True,physical_audio_played=False,flash_written=False,
        ordinary_save_restart_tested=False,requires_checkpoint_restore=True)


def surface_application(debug,rom_path,record):
    """Actual room reservation/commit and saved-byte reload in a private actor."""
    from v3_surface_application import OWNER,RELOC,OWNER_RAM
    from v3_surface_items import RAM,SIZE
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface application cartridge')
    surface=report['room_surfaces'];items=surface['items'];files=by_vrom(image)
    blob=files[runtime.BLOB].extract(image);packet=blob[items['blob_offset']:items['blob_offset']+SIZE]
    boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_application_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=got.hex() if len(got)<=16 else sha256(got)))
        if not passed:raise ValueError('Surface application mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None,proof=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proof or boot.get(at));record(result)
        if want is not None:
            passed=result['return_value']==want
            record(dict(surface_application_return=f'{at:08X}',expected=want,actual=result['return_value'],
                assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Surface application return mismatch')
            assertions+=1
        return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    check('complete packet loaded by startup',RAM,packet)
    size=0x7000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Surface application fixture allocation failed')
    root,actor,field,game,floor,wall=(allocation+n for n in (16,0x1000,0x1240,0x1300,0x3000,0x5100))
    data,rel=(files[v].extract(image) for v in (OWNER,RELOC));sections=struct.unpack_from('>5I',rel)
    if (sha256(data)!=surface['owners'][0]['sha256'] or sha256(rel)!=surface['owners'][0]['relocation_sha256']):
        raise ValueError('Changed complete room application owner')
    loaded=relocate_verified_data(SimpleNamespace(ram=OWNER_RAM,resident_bytes=len(data)+sections[3],
        sections=sections),data,rel,root)
    if len(loaded)>0xFE0:raise ValueError('Surface fixture owner exceeds small arena')
    debug.write_memory(allocation,bytes(size));debug.write_memory(root,loaded)
    call(0x8002FE00,[root,len(loaded)]);call(0x80034CE0,[root,len(loaded)])
    proof=(root,loaded[:sections[0]]);edge=b'V3SA'*4
    guards=(allocation,allocation+0xFF0,allocation+0x1220,floor-16,floor+0x2020,wall-16,wall+0x1020,allocation+size-16)
    for at in guards:debug.write_memory(at,edge)
    state=report['save_runtime'];saved={at:debug.read_memory(at,n) for at,n in
        ((0x80126EA0,0xF980),(0x80136EA0,4),(0x80136F48,4),(0x8013A248,4),
         (0x80137655,1),(state['state_ram'],state['state_bytes']))}
    def room(at,args=(),want=None):return call(root+at-OWNER_RAM,args,want,proof)
    home=0x80126EA0+0x3588+3*0xB48
    try:
        put(0x8013A248,field);debug.write_memory(field,bytes.fromhex('60030000'))
        put(0x80126EB4,20);debug.write_memory(0x80136EA1,b'\x01')
        debug.write_memory(0x80136EA3,b'\xFF') # No live player notification in this private actor.
        put(0x80136F48,actor+0x190);put(actor+0x190,actor)
        debug.write_memory(home+0x14,bytes([26,48]))
        room(0x80951F14,[actor,game])
        check('native initializer reads full saved home bytes',actor+0x174,bytes.fromhex('001A003000000000'))
        put(actor+0x180,floor,floor,wall,wall)
        original=debug.read_memory(actor,0x1B8)
        room(0x8095267C,[0x264A],0);check('disabled floor cannot exchange inventory',actor,original)
        selected=[items['rows'][1],items['rows'][-1]]
        for row in selected:put(RAM+row['offset']+4,1)
        # Different identities cover both shared paths without replaying every texture.
        for kind,item,old,reserve,commit,pending,identity,target,stride in (
                ('floor',0x264A,0x261A,0x8095267C,0x8095253C,0x1B0,0x174,floor,0x2020),
                ('wall',0x274D,0x2730,0x809526D4,0x80952444,0x1A8,0x176,wall,0x1020)):
            debug.write_memory(target,b'\xA5'*stride)
            room(reserve,[0x12340000|item],old);room(reserve,[item],0)
            queued=debug.read_memory(actor,0x1B8);put(game+0x1CC8,1)
            room(commit,[actor,game]);check('open menu defers complete room change',actor,queued)
            put(game+0x1CC8,0);room(commit,[actor,game])
            check('queued change consumed once',actor+pending,bytes(4))
            check('actor keeps full surface identity',actor+identity,struct.pack('>H',item&255))
            check('native writer keeps full saved byte',home+0x14+(kind=='wall'),bytes([item&255]))
            row=next(r for r in surface['rows'] if int(r['destination_item_id'],16)==item)
            check('native commit loads full surface resource',target,blob[row['blob_offset']:row['blob_offset']+stride])
        call(0x800BEEC4,[],74)
        # Reload uses the untouched complete native home initializer.
        room(0x80951F14,[actor,game]);check('native initializer reloads added pair',actor+0x174,bytes.fromhex('004A004D00000000'))
        for row in selected:put(RAM+row['offset']+4,0)
        call(0x800BEEC4,[],74&63)
        put(0x80126EB4,35);call(0x800BEEC4,[],68)
        put(0x80126EB4,9);call(0x800BEEC4,[],64)
        check('packet restored after fixture selections',RAM,packet)
        check('save profile and ownership remain unchanged',state['state_ram'],saved[state['state_ram']])
        for at in guards:check('room fixture guard',at,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for row in items['rows']:put(RAM+row['offset']+4,0)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    return dict(native_surface_application=True,assertions=assertions,complete_relocated_owner_copy=True,
        actual_reservation_commit_texture_dma_and_saved_byte_reload=True,
        live_player_notification_tested=False,ordinary_inventory_exchange_tested=False,
        ordinary_save_restart_tested=False,physical_audio_played=False,flash_written=False,
        requires_checkpoint_restore=True)


def surface_items(debug,rom_path,record):
    """Live installed startup/name/type/price paths, without enabling gameplay."""
    from v3_surface_items import RAM,SIZE,BOOT_END
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface-item cartridge')
    items=report['room_surfaces']['items'];files=by_vrom(image);blob=files[runtime.BLOB].extract(image)
    packet=blob[items['blob_offset']:items['blob_offset']+SIZE];boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_item_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=got.hex() if len(got)<=16 else sha256(got)))
        if not passed:raise ValueError('Surface-item native mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=boot.get(at))
        record(result)
        if want is not None:
            passed=result['return_value']==want
            record(dict(surface_item_return=f'{at:08X}',expected=want,actual=result['return_value'],
                assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Surface-item native return mismatch')
            assertions+=1
        return result['return_value']
    check('complete new packet loaded by real startup',RAM,packet)
    check('existing equipment guard retained',BOOT_END,bytes.fromhex('AF48C0DE')*4)
    allocation=call(0x8009BFC0,[128])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-128:
        raise ValueError('Surface-item fixture allocation failed')
    fill=b'\xA5'*128;state=report['save_runtime'];saved=debug.read_memory(state['state_ram'],state['state_bytes'])
    try:
        for row in (items['rows'][0],items['rows'][-1]):
            item=int(row['item_id'],16);debug.write_memory(allocation,fill)
            call(0x801969C8,[allocation+16,16,item],0)
            call(0x800A5630,[item],0);call(0x800C0194,[item],0)
            check('disabled identity writes no name',allocation,fill)
        for row in items['rows']:
            item=int(row['item_id'],16);flag=RAM+row['offset']+4
            debug.write_memory(flag,struct.pack('>I',1));debug.write_memory(allocation,fill)
            call(0x801969C8,[allocation+16,16,item],1)
            call(0x800A5630,[0x12340000|item],12)
            call(0x800C0194,[0x12340000|item],row['price_word'])
            check('complete official name and untouched guards',allocation,
                fill[:16]+row['name'].encode().ljust(16,b' ')+fill[32:])
            debug.write_memory(flag,bytes(4))
        debug.write_memory(allocation,fill)
        native_names=files[0x2A00000].extract(image);index=sum((64,4,36,32,255,30))
        name=native_names[32+index*16:48+index*16]
        call(0x801969C8,[allocation+16,16,0x2600],1);call(0x800A5630,[0x2600],12)
        check('original floor keeps its complete English name',allocation,fill[:16]+name+fill[32:])
        for item in (0x2640,0x2648,0x264E,0x27FF):
            call(0x800A5630,[item],0);call(0x800C0194,[item],0)
        check('complete surface packet restored',RAM,packet)
        check('saved profile and ownership retained',state['state_ram'],saved)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for row in items['rows']:debug.write_memory(RAM+row['offset']+4,bytes(4))
        call(0x8009C040,[allocation])
    return dict(native_surface_items=True,assertions=assertions,actual_startup_and_public_entries=True,
        fixture_only_enabled_records=True,ordinary_acquisition_tested=False,surface_application_tested=False,
        saved_format_changed=False,flash_written=False,physical_audio_played=False,requires_checkpoint_restore=True)


def surface_consumers(debug,rom_path,record):
    """Changed single-buffer/preview paths and the actual constructor bounds."""
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface-consumer cartridge')
    surface=report['room_surfaces'];files=by_vrom(image);blob=files[runtime.BLOB].extract(image)
    boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_consumer_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=got.hex() if len(got)<=16 else sha256(got)))
        if not passed:raise ValueError('Surface-consumer native mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    allocation=call(0x8009BFC0,[0x4000])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-0x4000:
        raise ValueError('Surface-consumer fixture allocation failed')
    actor,single,preview,bounds,target=(allocation+n for n in (16,0x800,0x900,0xB20,0x1000))
    debug.write_memory(allocation,bytes(0x4000));edge=b'V3SC'*4
    guards=(allocation,actor+0x760,single-16,single+0xB0,preview-16,preview+0x200,bounds-16,bounds+0x80,
        target-16,target+0x2020,allocation+0x3FF0)
    for at in guards:debug.write_memory(at,edge)
    bodies=[]
    for owner,destination in zip(surface['secondary_owners'],(single,preview)):
        data=files[owner['vrom']].extract(image);start=owner['windows'][0]['offset']
        body=data[start:start+owner['compiled']['bytes']]
        if sha256(data)!=owner['sha256'] or sha256(body)!=owner['compiled']['sha256']:
            raise ValueError('Changed installed complete surface consumer')
        bodies.append(body);debug.write_memory(destination,body)
        call(0x8002FE00,[destination,len(body)]);call(0x80034CE0,[destination,len(body)])
    bound=surface['secondary_owners'][0]['bounds'];data=files[0x845C40].extract(image)
    body=data[bound['offset']:bound['offset']+bound['bytes']]
    if body.hex()!=bound['after']:raise ValueError('Changed installed constructor bounds')
    bridge=struct.pack('>4I',0x0200C825,0x00808025,0x00A02025,0x00C03825)+body+struct.pack('>5I',0xAE07017C,0xAE080184,0x03208025,0x03E00008,0)
    debug.write_memory(bounds,bridge);call(0x8002FE00,[bounds,len(bridge)]);call(0x80034CE0,[bounds,len(bridge)])
    state=report['save_runtime'];saved_state=debug.read_memory(state['state_ram'],state['state_bytes'])
    fill=b'\xA5'*0x2020
    try:
        for kind,index in (('wall',73),('floor',77),('floor',68)):
            debug.write_memory(target,fill)
            row=next((r for r in surface['rows'] if r['kind']==kind and r['destination_index']==index),None)
            want=blob[row['blob_offset']:row['blob_offset']+row['bytes']]+fill[row['bytes']:] if row else fill
            entry=single+(0 if kind=='wall' else 0x54)
            call(entry,[target,index],(single,bodies[0]));check('single-buffer complete resource and untouched tail',target,want)
        for kind,index in (('wall',0),('floor',74)):
            stride=0x1020 if kind=='wall' else 0x2020;item=(0x2700 if kind=='wall' else 0x2600)+index
            stock_kind=4 if kind=='wall' else 3
            eligible=any(call(0x800C0490,[item,stock_kind,stock,0]) for stock in range(3))
            price=call(0x800C0194,[item]) if eligible else 0
            expected=bytearray(b'\xA7'*0x760);struct.pack_into('>I',expected,0x744,target)
            debug.write_memory(actor,expected);debug.write_memory(target,fill)
            call(preview+(0 if kind=='wall' else 0xF8),[actor,0x12340000|item],(preview,bodies[1]))
            struct.pack_into('>H',expected,0,index);struct.pack_into('>2I',expected,0x748,0,index*stride)
            struct.pack_into('>H',expected,0x750,2 if kind=='wall' else 3)
            struct.pack_into('>3I',expected,0x754,price,0x3F000000,0xC2B40000)
            check('complete preview fields and native catalogue pricing',actor,expected)
            if index<68:
                raw=files[0x182A000 if kind=='wall' else 0x17A1000].extract(image);texture=raw[index*stride:(index+1)*stride]
            else:
                row=next(r for r in surface['rows'] if r['kind']==kind and r['destination_index']==index)
                texture=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            check('preview complete resource and untouched tail',target,texture+fill[stride:])
        for floor,wall in ((26,48),(73,77),(68,72),(78,255)):
            expected=bytearray(b'\xA7'*0x200);debug.write_memory(actor,expected)
            call(bounds,[actor,floor,wall],(bounds,bridge))
            selected=lambda i:i if i<64 or 73<=i<78 else 63
            struct.pack_into('>I',expected,0x174,0);struct.pack_into('>I',expected,0x17C,selected(wall))
            struct.pack_into('>I',expected,0x184,selected(floor))
            check('actual arranged-room bound block retains identities and fallback',actor,expected)
        for at in guards:check('consumer code/actor/resource guard',at,edge)
        check('saved extension retained',state['state_ram'],saved_state);check('no CPU fault',0x8003CE34,bytes(4))
    finally:call(0x8009C040,[allocation])
    return dict(native_surface_consumers=True,assertions=assertions,complete_installed_reader_copy=True,
        actual_constructor_bound_block=True,actual_native_stock_and_price=True,
        ordinary_room_entry_tested=False,gpu_appearance_tested=False,surface_application_tested=False,
        physical_audio_played=False,flash_written=False,requires_checkpoint_restore=True)


def room_surfaces(debug,rom_path,record):
    """Execute installed shared room copies with actual original/additive DMA."""
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed surface cartridge')
    surface=report['room_surfaces'];files=by_vrom(image);blob=files[runtime.BLOB].extract(image)
    bodies=[]
    for owner in surface['owners']:
        data=files[owner['vrom']].extract(image);start=owner['windows'][0]['offset']
        code=data[start:start+owner['compiled']['bytes']]
        if sha256(data)!=owner['sha256'] or sha256(code)!=owner['compiled']['sha256']:
            raise ValueError('Changed installed complete surface reader')
        bodies.append(code)
    if len(bodies)!=2 or bodies[0]!=bodies[1]:raise ValueError('Room/shop readers no longer share identical instructions')
    body=bodies[0];boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(surface_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=got.hex() if len(got)<=16 else sha256(got)))
        if not passed:raise ValueError('Surface native mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    size=0x5000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Surface fixture allocation failed')
    actor,function,first,second=(allocation+n for n in (16,0x300,0x800,0x2840))
    debug.write_memory(allocation,bytes(size));edge=b'V3SF'*4
    guards=(allocation,actor+0x200,function-16,function+0x240,first-16,first+0x2020,second-16,second+0x2020,allocation+size-16)
    for at in guards:debug.write_memory(at,edge)
    debug.write_memory(function,body);call(0x8002FE00,[function,len(body)]);call(0x80034CE0,[function,len(body)])
    state=report['save_runtime'];saved_state=debug.read_memory(state['state_ram'],state['state_bytes'])
    actor_data=bytearray(b'\xA7'*0x200);struct.pack_into('>4I',actor_data,0x180,first,second,first,second)
    debug.write_memory(actor,actor_data);fill=b'\xA5'*0x2020
    try:
        # One per routing/size/buffer class, not every individual surface.
        for kind,index,bank in (('floor',26,2),('floor',74,0),('wall',77,2),('wall',64,1),('floor',68,2)):
            debug.write_memory(first,fill);debug.write_memory(second,fill)
            stride=0x2020 if kind=='floor' else 0x1020
            expected=None
            if index<68:
                raw=files[0x17A1000 if kind=='floor' else 0x182A000].extract(image)
                expected=raw[index*stride:(index+1)*stride]
            elif index>=73:
                row=next(r for r in surface['rows'] if r['kind']==kind and r['destination_index']==index)
                expected=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            entry=function+(0 if kind=='floor' else 0x118)
            call(entry,[actor,0x12340000|index,0x56780000|bank],(function,body))
            for i,at in enumerate((first,second)):
                want=expected+fill[stride:] if expected is not None and (bank==2 or i==bank) else fill
                check('complete '+kind+' DMA and untouched other buffer/tail',at,want)
            check('surface transfer preserves complete actor',actor,actor_data)
        for at in guards:check('surface code/actor/buffer guard',at,edge)
        check('saved extension retained',state['state_ram'],saved_state)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:call(0x8009C040,[allocation])
    return dict(native_surface_readers=True,assertions=assertions,complete_installed_function_copy=True,
        actual_original_and_added_resource_dma=True,room_and_shop_instructions_identical=True,
        ordinary_room_entry_tested=False,gpu_appearance_tested=False,surface_application_tested=False,
        physical_audio_played=False,flash_written=False,requires_checkpoint_restore=True)


def initial_switch(debug,rom_path,record):
    """Execute the complete installed initializer's changed fresh-placement path.

    Copy its checked function into a small isolated arena; do not allocate or
    replay an entire room owner. Unchanged reload/gyroid callees are not invoked.
    """
    import v3_furniture_behaviours as behaviours
    from v3_furniture_runtime import VROM,RAM as OWNER_RAM
    from v3_import_storage import jump,ROWS,slot,PACKAGE,PACKAGE_RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed placement cartridge')
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image)
    binding=behaviours.checked_initial_switch(image,report,blob)
    if binding is None:raise ValueError('Missing complete initial-switch adapter')
    owner=files[VROM].extract(image);body=owner[behaviours.SWITCH_FIRST-OWNER_RAM:behaviours.SWITCH_END-OWNER_RAM]
    boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(initial_switch_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=got.hex() if len(got)<=16 else sha256(got)))
        if not passed:raise ValueError('Initial-switch native mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    allocation=call(0x8009BFC0,[0xC00])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-0xC00:
        raise ValueError('Fresh-placement fixture allocation failed')
    actor,function,bridge,profile=allocation+16,allocation+0x780,allocation+0x900,allocation+0x940
    debug.write_memory(allocation,bytes(0xC00));edge=b'V3IS'*4
    guards=(allocation,actor+0x740,function-16,function+0x140,bridge-16,bridge+16,profile-16,profile+80,allocation+0xBF0)
    for at in guards:debug.write_memory(at,edge)
    debug.write_memory(function,body);call(0x8002FE00,[function,len(body)]);call(0x80034CE0,[function,len(body)])
    table=int(report['furniture']['expanded_tables']['profile_table_ram'],16)
    row=report['automatic_furniture']['imports'][0];index=row['runtime_index']
    at=ROWS+slot(int(row['item_id'],16))*80+8;native_profile=blob[at:at+68]
    if len(native_profile)!=68 or struct.unpack_from('>H',native_profile,62)[0]!=0x1000:
        raise ValueError('Fixture needs a real installed start-disabled profile')
    code=report['furniture_behaviours']['code'];at=PACKAGE+behaviours.RAM-PACKAGE_RAM
    check('complete installed shared behaviour helper',0x80483D00,blob[at:at+code['bytes']])
    state=report['save_runtime'];saved_state=debug.read_memory(state['state_ram'],state['state_bytes'])
    saved={}
    try:
        for selected,flags,expected in ((index,0x1000,0),(index,0,1),(1,0x1000,1)):
            pointer=table+selected*4
            if pointer not in saved:saved[pointer]=debug.read_memory(pointer,4)
            data=bytearray(native_profile);struct.pack_into('>H',data,62,flags)
            debug.write_memory(profile,data);debug.write_memory(pointer,struct.pack('>I',profile))
            actor_data=bytearray(b'\xA7'*0x740);struct.pack_into('>H',actor_data,0,selected)
            debug.write_memory(actor,actor_data)
            call(function,[actor,1,0],(function,body))
            actor_data[0x12C]=expected;actor_data[0x12E]=255
            check('complete fresh actor; native defaults preserved',actor,actor_data)
            debug.write_memory(pointer,saved[pointer])
        # The real installed scrolling constructor must consume the initial
        # off bit. Its unchanged movement/rendering checks are not replayed.
        data=bytearray(0x740);struct.pack_into('>H',data,0,index);debug.write_memory(actor,data)
        entry=report['equipment_resources']['room_rigs']['bootstrap']['symbols']['af_v3_room_boot_scroll_ct']
        stub=struct.pack('>2I',jump(entry),0);debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8]);call(bridge,[actor,0],(bridge,stub))
        check('installed fade constructor keeps fresh off state',actor+0x1A4,bytes(6))
        for at in guards:check('fresh-placement actor/code guard',at,edge)
        check('saved state retained',state['state_ram'],saved_state);check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for pointer,data in saved.items():debug.write_memory(pointer,data)
        call(0x8009C040,[allocation])
    return dict(native_initial_switch=True,assertions=assertions,complete_installed_function_copy=True,
        fresh_placement_path=True,reload_or_gyroid_execution=False,ordinary_room_interaction=False,
        physical_audio_played=False,requires_checkpoint_restore=True)


def movement_sounds(debug,rom_path,record):
    """Complete room movement owner plus actual new shared sound dispatch."""
    from aflib import CODE_RAM,CODE_VROM,u32
    import v3_room_movement as movement
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed movement cartridge')
    e=report['equipment_resources'];scroll=e['room_rigs']['scrolling'];rules=scroll['movement']
    files=by_vrom(image);core=files[CODE_VROM].extract(image);blob=files[runtime.BLOB].extract(image)
    body=movement.checked_owner(image,movement.BRIDGE)[movement.FIRST-movement.RAM:movement.LAST-movement.RAM]
    boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(movement_sound_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=actual.hex() if len(actual)<=16 else sha256(actual)))
        if not passed:raise ValueError('Native movement sound mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def publish(at,data):
        debug.write_memory(at,data);call(0x8002FE00,[at,len(data)]);call(0x80034CE0,[at,len(data)])
    sequence=u32(debug.read_memory(0x8014CBA8,4),0);seq=e['sound_programs']['sequence']
    if not 0x80000400<=sequence<=0x80400000-seq['bytes']:raise ValueError('Unbounded loaded movement sequence')
    raw=image[seq['physical']:seq['physical']+seq['bytes']]
    for row in rules['programs']:
        check('complete loaded movement program',sequence+row['offset'],raw[row['offset']:row['offset']+row['bytes']])
        word=row['native_sound_word'];table=struct.unpack_from('>H',raw,0x188+2*(word>>8))[0]
        check('real trigger-table entry',sequence+table+2*(word&255),struct.pack('>H',row['offset']))
    allocation=call(0x8009BFC0,[0xC00])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-0xC00:
        raise ValueError('Movement fixture allocation failed')
    actor,capture,function,owner,clip=(allocation+n for n in (16,0x780,0x800,0x900,0xB00))
    debug.write_memory(allocation,bytes(0xC00));edge=b'V3MS'*4
    guards=(allocation,actor+0x740,capture-16,capture+32,function-16,function+0x80,
        owner-16,owner+0x1B0,clip-16,clip+16,allocation+0xBF0)
    for at in guards:debug.write_memory(at,edge)
    publish(function,body)
    saved_code={}
    for entry,target in ((0x800D1D58,capture),(0x800D1DE4,capture+16)):
        original=core[entry-CODE_RAM:entry-CODE_RAM+40];check('native sound wrapper before recorder',entry,original)
        saved_code[entry]=original
        publish(entry,struct.pack('>10I',0x3C080000|(target>>16),0x35080000|(target&65535),
            0xAD040000,0xAD050004,0xAD060008,0x8D09000C,0x25290001,0xAD09000C,0x03E00008,0))
    entry=0x80087C88;original=core[entry-CODE_RAM:entry-CODE_RAM+12]
    check('native room query before isolated fixture',entry,original);saved_code[entry]=original
    publish(entry,struct.pack('>3I',0x24026000,0x03E00008,0))
    field=0x6000
    native_floor=(0x7BD80000+(((((field*4-field)*4-field)*4+field)*8+field)*8)-23492)&0xFFFFFFFF
    if not 0x80100000<=native_floor<0x80150000:raise ValueError('Unbounded original floor reader')
    saved={at:debug.read_memory(at,n) for at,n in ((0x80136F2C,4),(0x80137655,1),(native_floor,1))}
    state=report['save_runtime'];saved_state=debug.read_memory(state['state_ram'],state['state_bytes'])
    directional,grass=rules['rows'];a,b=grass['floors']
    cases=[(directional['runtime_index'],a,4,1,True,1,directional['sounds'][0]),
        (directional['runtime_index'],a,7,0,True,1,directional['sounds'][1]),
        (directional['runtime_index'],a,8,1,True,0,0),
        (directional['runtime_index'],a,1,1,False,0,0),
        (grass['runtime_index'],a,1,0,True,1,grass['sounds'][0]),
        (grass['runtime_index'],b,4,0,True,1,grass['sounds'][0]),
        (grass['runtime_index'],26,1,0,True,2,26),
        (grass['runtime_index'],a,5,0,True,0,0),
        (grass['runtime_index'],a,1,1,True,0,0),
        (grass['runtime_index'],a,1,0,False,0,0),(37,27,1,0,True,2,27)]
    try:
        for index,floor,step,direction,connected,kind,sound in cases:
            data=bytearray(b'\xA7'*0x740);struct.pack_into('>H',data,0,index);struct.pack_into('>h',data,0x3C,step)
            debug.write_memory(actor,data);debug.write_memory(capture,bytes(32))
            debug.write_memory(clip,struct.pack('>I',owner));debug.write_memory(owner+0x1A0,struct.pack('>i',direction))
            debug.write_memory(0x80136F2C,struct.pack('>I',clip if connected else 0))
            for at in (native_floor,0x80137655):debug.write_memory(at,bytes((floor,)))
            call(function,[actor],(function,body))
            for output in (1,2):
                at=capture+(output-1)*16
                check('source movement condition and call count',at+12,struct.pack('>I',int(output==kind)))
                if kind==output:check('native sound identity and actor position',at,struct.pack('>2I',sound,actor+8))
            check('complete actor untouched by movement sound',actor,data)
        p=scroll['packet'];check('complete lazy-loaded movement packet',p['ram'],blob[p['blob_offset']:p['blob_offset']+p['bytes']])
        for at in guards:check('movement work guard',at,edge)
        check('saved state preserved',state['state_ram'],saved_state);check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
        for at,data in saved_code.items():publish(at,data)
        call(0x8009C040,[allocation])
    return dict(native_movement_sounds=True,assertions=assertions,complete_native_owner_copy=True,
        real_lazy_loader=True,loaded_programs=True,sound_arguments_recorded=True,
        synthesis_tested=False,physical_audio_played=False,ordinary_room_interaction=False,requires_checkpoint_restore=True)


def scroll_lifecycles(debug,rom_path,record,*,contact_only=False):
    """One bounded shared-category callback/loader check; no ordinary play claim."""
    from aflib import CODE_RAM,CODE_VROM,u32
    from v3_import_storage import jump
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed scrolling lifecycle cartridge')
    e=report['equipment_resources'];rig=e['room_rigs'];scroll=rig['scrolling'];audio=e['furniture_level_audio']
    files=by_vrom(image);core=files[CODE_VROM].extract(image);blob=files[runtime.BLOB].extract(image)
    boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(scroll_lifecycle_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',actual=got.hex() if len(got)<=16 else sha256(got)))
        if not passed:raise ValueError('Scrolling lifecycle mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    if not contact_only:
        sequence=u32(debug.read_memory(0x8014CBA8,4),0);seq=audio['sequence']
        if not 0x80000400<=sequence<=0x80400000-seq['bytes']:raise ValueError('Unbounded native sound sequence')
        raw=image[seq['physical']:seq['physical']+seq['bytes']]
        for row in audio['programs']:
            check('loaded complete positioned-loop program',sequence+row['offset'],raw[row['offset']:row['offset']+row['bytes']])
            check('actual level dispatch binding',sequence+row['native_table']+row['native_sound_id']*2,
                  struct.pack('>H',row['offset']))
    size=0xC00 if contact_only else 0x900
    allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Scrolling callback fixture allocation failed')
    actor,capture,bridge=allocation+16,allocation+0x780,allocation+0x800
    debug.write_memory(allocation,bytes(size));edge=b'V3SL'*4
    guards=(allocation,actor+0x740,capture-16,capture+32,bridge-16,bridge+32,allocation+size-16)
    if contact_only:guards+=(allocation+0x8F0,allocation+0xAB0,allocation+0xAF0,allocation+0xB10)
    for at in guards:debug.write_memory(at,edge)
    names=('ct','mv','dt');stubs=b''.join(struct.pack('>2I',jump(rig['bootstrap']['symbols']['af_v3_room_boot_scroll_'+n]),0) for n in names)
    debug.write_memory(bridge,stubs);call(0x8002FE00,[bridge,len(stubs)]);call(0x80034CE0,[bridge,len(stubs)])
    def invoke(name):return call(bridge+names.index(name)*8,[actor,0,0,0],(bridge,stubs))
    # Observe the real MIPS callback's sound arguments without audible output.
    # Native synthesis and ordinary interactions are deliberately separate.
    saved={}
    for entry,target in (() if contact_only else ((0x800D1D08,capture),(0x800D1D58,capture+16))):
        original=core[entry-CODE_RAM:entry-CODE_RAM+40];check('native sound entry before recorder',entry,original)
        saved[entry]=original
        recorder=struct.pack('>10I',0x3C080000|(target>>16),0x35080000|(target&65535),
            0xAD040000,0xAD050004,0xAD060008,0x8D09000C,0x25290001,0xAD09000C,0x03E00008,0)
        debug.write_memory(entry,recorder);call(0x8002FE00,[entry,40]);call(0x80034CE0,[entry,40])
    saved_state=debug.read_memory(report['save_runtime']['state_ram'],report['save_runtime']['state_bytes'])
    globals_saved={at:debug.read_memory(at,n) for at,n in ((0x80136F2C,4),(0x80137655,1))} if contact_only else {}
    rows=[r for r in scroll['lifecycle_rows'] if (r['mode']==3)==contact_only]
    if not rows:raise ValueError('No installed lifecycle rows for this focused category')
    try:
        for row in rows:
            if contact_only:
                owner,clip=allocation+0x900,allocation+0xB00
                debug.write_memory(clip,struct.pack('>I',owner))
                # Real complete MIPS easing; expected values use single-precision
                # rounding at each operation, not an invented linear fade.
                def f32(value):return struct.unpack('>f',struct.pack('>f',value))[0]
                value=f32(.04);value=f32(value+f32(f32(.04)*f32(1.0-value)))
                for floor,state,direction,connected,expected in (
                        (row['on'],1,0,True,value),(row['off'],4,0,True,value),
                        (26,1,0,True,0.),(row['on'],5,0,True,0.),
                        (row['on'],1,1,True,0.),(row['on'],1,0,False,0.)):
                    data=bytearray(b'\xA7'*0x740)
                    struct.pack_into('>H',data,0,row['runtime_index']);struct.pack_into('>h',data,0x3C,state)
                    debug.write_memory(actor,data);invoke('ct');data[0x1A4:0x1A8]=bytes(4)
                    check('contact constructor changes only private alpha',actor,data)
                    debug.write_memory(0x80137655,bytes((floor,)))
                    debug.write_memory(0x80136F2C,struct.pack('>I',clip if connected else 0))
                    debug.write_memory(owner+0x1A0,struct.pack('>i',direction))
                    invoke('mv');data[0x1A4:0x1A8]=struct.pack('>f',expected)
                    check('source contact, state, and complete floor identity',actor,data)
                    invoke('dt');check('contact teardown does not invent saved state',actor,data)
                continue
            debug.write_memory(actor,bytes(0x740));debug.write_memory(actor,struct.pack('>H',row['runtime_index']))
            invoke('ct');check('constructor starts from saved off state',actor+0x1A4,bytes(6))
            debug.write_memory(actor+0x12D,b'\x01');debug.write_memory(capture,bytes(32));invoke('mv')
            check('actual positioned sound identity, position, and count',capture,
                  struct.pack('>4I',actor,row['sound'],actor+8,1))
            if row['mode']==2:
                check('one edge and one source-half fade',actor+0x1A4,struct.pack('>fh',row['step'],1))
                check('switch edge is owned by native parent',actor+0x12D,b'\x01')
                if row['on']:check('actual switch-on click and count',capture+16,struct.pack('>2I',row['on'],actor+8))
                else:check('no invented switch click',capture+16,bytes(16))
                debug.write_memory(actor+0x12D,b'\0');debug.write_memory(capture,bytes(32));invoke('mv')
                check('two source updates per native frame',actor+0x1A4,struct.pack('>fh',row['step']*3,1))
                check('sustained refresh uses the same actor',capture,struct.pack('>4I',actor,row['sound'],actor+8,2))
                invoke('dt');check('source-specific teardown persistence',actor+0x12C,bytes((row['flags'],)))
            debug.write_memory(actor+0x3C,struct.pack('>h',12));debug.write_memory(actor+0x12D,b'\0')
            debug.write_memory(capture,bytes(32));invoke('mv');check('excluded native state suppresses sound',capture,bytes(32))
        p=scroll['packet'];check('complete lazy-loaded scroll code and both tables',p['ram'],blob[p['blob_offset']:p['blob_offset']+p['bytes']])
        for at in guards:check('native callback work guard',at,edge)
        check('saved data retained',report['save_runtime']['state_ram'],saved_state)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for at,data in globals_saved.items():debug.write_memory(at,data)
        for entry,original in saved.items():
            debug.write_memory(entry,original);call(0x8002FE00,[entry,len(original)]);call(0x80034CE0,[entry,len(original)])
        call(0x8009C040,[allocation])
    return dict(native_scroll_lifecycles=True,contact_only=contact_only,assertions=assertions,source_shapes=len(rows),
        callback_dispatch_recorder=not contact_only,ordinary_room_interaction=False,physical_audio_played=False,
        synthesis_tested=False,requires_checkpoint_restore=True)


def staged_profiles(debug,rom_path,record):
    """Check inactive batch registration and one reader/model per shared category.

    Temporary activation is confined to this paused fixture; it is not an
    acquisition or gameplay claim. Previously verified callbacks are not replayed.
    """
    from v3_import_storage import ROWS,ROWS_RAM,ITEMS,ITEMS_RAM,slot
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed staged-profile cartridge')
    blob=by_vrom(image)[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    rows=report['staged_furniture']['rows'];table=int(report['furniture']['expanded_tables']['profile_table_ram'],16)
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(staged_profile_check=label,address=f'{at:08X}',bytes=len(want),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Staged-profile mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None,proof=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None:
            if result['return_value']!=want:raise ValueError('Staged-profile native return differs')
            assertions+=1
        return result['return_value']
    selected={}
    for row in rows:
        i=slot(int(row['item_id'],16))
        check('inactive complete profile '+row['item_id'],ROWS_RAM+i*80,blob[ROWS+i*80:ROWS+(i+1)*80])
        check('inactive complete item '+row['item_id'],ITEMS_RAM+i*32,blob[ITEMS+i*32:ITEMS+(i+1)*32])
        check('excluded from startup profile lookup '+row['item_id'],table+row['runtime_index']*4,bytes(4))
        selected.setdefault(row['category'],row)
    size=0x2500;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Staged-profile fixture outside native heap')
    bank,text,bridge=allocation+16,allocation+0x2420,allocation+0x2440;edge=b'V3SP'*4
    saved={};guards=(allocation,bank+9216,text-16,text+16,bridge+16,allocation+size-16)
    for at in guards:debug.write_memory(at,edge)
    entry=next(r for r in report['furniture']['expanded_tables']['public_entries'] if r['name']=='af_v3_furniture_import_profile')
    check('installed native profile lookup entry',entry['entry'],bytes.fromhex(entry['after']))
    jump=struct.pack('>2I',0x08000000|((entry['entry']>>2)&0x3FFFFFF),0)
    debug.write_memory(bridge,jump);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
    try:
        for row in selected.values():
            item=int(row['item_id'],16);index=row['runtime_index'];i=slot(item)
            locations=((ROWS_RAM+i*80+4,4),(ITEMS_RAM+i*32+7,1),(table+index*4,4))
            for at,n in locations:saved[at]=debug.read_memory(at,n)
            debug.write_memory(text,b'\xA5'*16)
            call(bridge,[index],0,(bridge,jump));call(0x801969C8,[text,16,item],0)
            check('disabled item writes no name',text,b'\xA5'*16)
            for (at,n),value in zip(locations,(struct.pack('>I',1),b'\x01',struct.pack('>I',row['profile_ram'])),strict=True):
                debug.write_memory(at,value)
            call(bridge,[index],1,(bridge,jump));call(0x801969C8,[text,16,item],1)
            check('complete official name',text,row['name'].encode().ljust(16,b' '))
            call(0x800A5630,[item],10);call(0x800C0194,[item],row['price'])
            call(0x800BE69C,[item],row['size_code'])
            call(0x80026B44,[bank,row['object_vrom'],row['object_bytes']])
            at=row['object_vrom']-runtime.BLOB
            check('complete profile-directed model DMA',bank,blob[at:at+row['object_bytes']])
            for at,_ in locations:debug.write_memory(at,saved[at])
            call(bridge,[index],0,(bridge,jump))
        for at in guards:check('temporary reader/model guard',at,edge)
        check('saved profile unchanged',0x80460020,blob[0x20:0xE0])
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    return dict(native_staged_profiles=True,assertions=assertions,records=len(rows),
        category_representatives=len(selected),acquisition_tested=False,ordinary_gameplay_tested=False)


def furniture_audio(debug,rom_path,record):
    """One current-build check for the complete shared trigger category."""
    from aflib import CODE_RAM,CODE_VROM,u32
    from runtime_layout import TEST_STACK
    from v3_import_storage import jump
    from v3_equipment_runtime import RAM
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed furniture-audio cartridge')
    e=report['equipment_resources'];audio=e['furniture_audio'];rig=e['room_rigs'];files=by_vrom(image)
    newest=audio.get('batches',[dict(programs=audio['programs'])])[-1]['programs']
    incremental=len(newest)<len(audio['programs'])
    core=files[CODE_VROM].extract(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(furniture_audio_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=actual.hex() if len(actual)<=32 else sha256(actual)))
        if not passed:raise ValueError('Furniture audio mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def word(at):return u32(debug.read_memory(at,4),0)
    def bounded(at,n):
        if at&3 or not 0x80000400<=at<=0x80400000-n:raise ValueError('Furniture-audio pointer escapes native RAM')
        return at
    for row in (audio['sequence'],audio['font'],audio['wave']):
        header=bytearray.fromhex(row['header_after']);struct.pack_into('>I',header,0,row['physical'])
        check('actual relocated resource header',row['header_address'],header)
    total,fixed,permanent=struct.unpack_from('>3I',core,0x80119A44-CODE_RAM)
    heap=bounded(word(0x8014CB84),total);check('actual audio malloc size',0x8014CB88,struct.pack('>I',total))
    for label,at,size,expected_start in (('fixed',0x8014BEC0,fixed,heap),
            ('session',0x8014BEA0,total-fixed,heap+fixed),('permanent',0x8014C260,permanent,None)):
        start,current,capacity,count=struct.unpack('>4I',debug.read_memory(at,16))
        if (size!=capacity or not heap<=start<=current<=start+size<=heap+total or
                expected_start is not None and start!=expected_start):raise ValueError('Incorrect native '+label+' pool')
        record(dict(furniture_audio_pool=label,capacity=capacity,used=current-start,allocations=count,assertion='passed'))
        assertions+=1
    seq=audio['sequence'];sequence=bounded(word(0x8014CBA8),seq['bytes'])
    data=image[seq['physical']:seq['physical']+seq['bytes']]
    for table in audio['tables']:
        check('registered complete trigger table',sequence+table['offset'],data[table['offset']:table['offset']+256])
        at=0x188+table['group']*2;check('native group pointer',sequence+at,data[at:at+2])
    for row in audio['programs']:
        check('complete trigger program',sequence+row['offset'],data[row['offset']:row['offset']+row['bytes']])
    font_row=audio['font'];font=image[font_row['physical']:font_row['physical']+font_row['bytes']]
    count=audio['layout']['instrument_count'];info=bounded(word(0x8014BD48),145*20)+font_row['index']*20
    check('expanded font count and wave binding',info,bytes((count,0,audio['wave']['index'],255,0,0)))
    bank=bounded(word(info+8)-8,len(font));expected=bytearray(font);samples=set()
    for index in range(count):
        inst=u32(font,8+4*index)
        if not inst:continue
        struct.pack_into('>I',expected,8+4*index,bank+inst);expected[inst]=1
        struct.pack_into('>I',expected,inst+4,bank+u32(font,inst+4))
        for field in (8,16,24):
            sample=u32(font,inst+field)
            if sample:struct.pack_into('>I',expected,inst+field,bank+sample);samples.add(sample)
    for at in samples:
        flags,start,loop,book=struct.unpack_from('>4I',font,at)
        struct.pack_into('>4I',expected,at,flags|0x09000000,audio['wave']['physical']+start,bank+loop,bank+book)
    check('complete native font and every instrument/sample relocation',bank,expected)
    allocation=bounded(call(0x8009BFC0,[0x800]),0x800);actor=allocation+16;capture=allocation+0x760;bridge=allocation+0x780
    debug.write_memory(allocation,bytes(0x800));edge=b'V3FA'*4
    guards=(allocation,actor+0x740,capture-16,bridge+16,allocation+0x7F0,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    stub=struct.pack('>2I',jump(rig['bootstrap']['symbols']['af_v3_room_boot_sound_mv']),0)
    debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
    native_entry=0x800D1D58;native_bytes=core[native_entry-CODE_RAM:native_entry-CODE_RAM+24]
    recorder=struct.pack('>6I',0x3C080000|(capture>>16),0x35080000|(capture&65535),0xAD040000,0xAD050004,0x03E00008,0)
    state=report['save_runtime'];saved=debug.read_memory(state['state_ram'],state['state_bytes'])
    saved_scene=debug.read_memory(0x80113844,1)
    observed=set()
    try:
        check('original position dispatcher before isolated recorder',native_entry,native_bytes)
        debug.write_memory(native_entry,recorder);call(0x8002FE00,[native_entry,24]);call(0x80034CE0,[native_entry,24])
        row=(next(r for r in rig['sound_rows'] if r['native_sound_word']==newest[0]['native_sound_word']) if incremental else
             next(r for r in rig['sound_rows'] if r['native_sound_word']&0x8000))
        cases=((0,1,False),) if incremental else ((0,1,False),(12,1,False),(13,1,False),(14,1,False),(15,1,False),
                                                (0,0,False),(0,2,False),(-1,1,True))
        for action,changed,alias in cases:
            debug.write_memory(actor,struct.pack('>H',row['runtime_index']+(1024 if alias else 0)))
            debug.write_memory(actor+0x3C,struct.pack('>h',action));debug.write_memory(actor+0x12D,bytes((changed,)))
            debug.write_memory(capture,bytes(8));before=debug.read_memory(actor,0x740)
            call(bridge,[actor,0,0,0],(bridge,stub))
            expected=struct.pack('>2I',row['native_sound_word'],actor+8) if changed==1 and not 12<=action<=15 else bytes(8)
            check('source state/switch rule and full sound word',capture,expected)
            check('callback retains complete native actor',actor,before)
        debug.write_memory(native_entry,native_bytes);call(0x8002FE00,[native_entry,24]);call(0x80034CE0,[native_entry,24])
        check('complete lazy-loaded room packet',rig['packet']['ram'],
              blob[rig['packet']['blob_offset']:rig['packet']['blob_offset']+rig['packet']['bytes']])
        selected=[max(newest,key=lambda r:len(r['source_program']['events'])),
                  next(r for r in audio['programs'] if r['singleton'])]
        debug.write_memory(0x80113844,b'\x01')
        mic=bounded(call(0x80060D6C,[word(0x8010EF90)]),12)
        debug.write_memory(actor+8,debug.read_memory(mic,12))
        debug.write_memory(actor+0x3C,bytes(2));debug.write_memory(actor+0x12D,b'\x01')
        sample_ranges={}
        for row in selected:
            sid=row['native_sound_word']
            selected_row=next(r for r in rig['sound_rows'] if r['native_sound_word']==sid)
            debug.write_memory(actor,struct.pack('>H',selected_row['runtime_index']))
            call(bridge,[actor,0,0,0],(bridge,stub))
            slots=debug.read_memory(0x80113C34,192)
            matches=[i for i in range(6) if struct.unpack_from('>H',slots,i*32)[0]==sid]
            if len(matches)!=1:raise ValueError('Native furniture trigger was not registered uniquely')
            check('actual native trigger priority',0x80113C34+matches[0]*32+28,bytes((row['trigger_priority'],)))
            if row['singleton']:
                call(bridge,[actor,0,0,0],(bridge,stub))
                for i in range(6):check('single-instance retrigger retains native identity',0x80113C34+i*32,slots[i*32:i*32+2])
            inst=u32(font,8+row['native_instrument']*4);sample=u32(font,inst+16)
            sample_ranges[sid]=(audio['wave']['physical']+u32(font,sample+4),u32(font,sample)&0xFFFFFF)
        for frame in range(12):
            record(debug.advance_game_frame());n=word(0x8014BB20)
            if not 0<n<=256:raise ValueError('Unbounded audio sample-DMA list')
            entries=debug.read_memory(bounded(word(0x8014BB1C),n*16),n*16)
            for i in range(n):
                r=entries[i*16:(i+1)*16];ram,device=struct.unpack_from('>2I',r);size=struct.unpack_from('>H',r,10)[0]
                if not r[14]:continue
                for sid,(first,length) in sample_ranges.items():
                    a,b=max(device,first),min(device+size,first+length)
                    if a>=b or sid in observed:continue
                    check('actual imported sample transfer',bounded(ram,size)+a-device,image[a:b]);observed.add(sid)
            if len(observed)==len(selected):break
        if len(observed)!=len(selected):raise ValueError('Missing representative complete sample transfer')
        for at in guards:check('callback work/stack guard',at,edge)
        check('complete saved profile retained',state['state_ram'],saved)
        check('native dispatcher restored',native_entry,native_bytes)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(native_entry,native_bytes);call(0x8002FE00,[native_entry,24]);call(0x80034CE0,[native_entry,24])
        debug.write_memory(0x80113844,saved_scene)
        call(0x8009C040,[allocation])
    return dict(native_furniture_audio=True,assertions=assertions,sample_representatives=len(observed),
        incremental_batch=incremental,source_sound_words=[r['source_sound_word'] for r in selected],
        callback_dispatch_recorder=True,ordinary_room_interaction=False,physical_audio_played=False,
        pcm_or_listening_verified=False,requires_checkpoint_restore=True)


def sound_programs_probe(debug,image,resources,check,call,record):
    """Exercise one representative of the shared single-layer sound format."""
    from aflib import CODE_VROM,u32
    from v3_sound_programs import installed_resource
    sound=resources['sound_programs'];row=sound['imports'][0]
    code=by_vrom(image)[CODE_VROM].extract(image)
    def word(at):return u32(debug.read_memory(at,4),0)
    def bounded(at,n):
        if at&3 or not 0x80000400<=at<=0x80400000-n:
            raise ValueError('Shared sound pointer escapes native RAM')
        return at
    seq=sound['sequence'];data=image[seq['physical']:seq['physical']+seq['bytes']]
    header=bytearray.fromhex(seq['header_after']);struct.pack_into('>I',header,0,seq['physical'])
    check('shared sound loaded header',seq['header_address'],header)
    sequence=bounded(word(0x8014CBA8),seq['bytes'])
    check('shared sound complete program and envelope',sequence+row['offset'],
          data[row['offset']:row['offset']+row['bytes']])
    table=struct.unpack_from('>H',data,0x18A)[0];sid=row['native_sound_id']
    check('shared sound registered dispatch',sequence+table+(sid&255)*2,struct.pack('>H',row['offset']))
    start,current,size,count=struct.unpack('>4I',debug.read_memory(0x8014C260,16))
    bounded(start,size)
    if size!=sound['after_budget']['capacity'] or not start<=current<=start+size or not count:
        raise ValueError('Shared sound permanent allocation exceeds its checked heap')
    record(dict(shared_sound_heap_capacity=size,used=current-start,remaining=start+size-current,
        conservative_spare=sound['after_budget']['conservative_spare'],assertion='passed'))
    bank,entry,_=installed_resource(image,code,'bank',row['native_bank'])
    _,_,wave=installed_resource(image,code,'wave',entry[10])
    instrument=u32(bank,8+row['native_instrument']*4)
    sample=u32(bank,instrument+16);sample_bytes=u32(bank,sample)&0xFFFFFF
    sample_start=wave+u32(bank,sample+4)
    if sample_bytes!=row['instrument_identity']['samples'][1]['sample_bytes']:
        raise ValueError('Shared sound representative needs its checked middle sample')
    call(0x800F8D5C,[sid])
    slots=debug.read_memory(0x80113C34,6*32)
    matches=[i for i in range(6) if struct.unpack_from('>H',slots,i*32)[0]==sid]
    if len(matches)!=1:raise ValueError('Shared sound did not allocate its native trigger slot')
    check('shared sound original priority',0x80113C34+matches[0]*32+28,bytes((row['trigger_priority'],)))
    observations=0
    for frame in range(8):
        record(debug.advance_game_frame())
        count=word(0x8014BB20)
        if not 0<count<=256:raise ValueError('Unbounded sound sample-DMA list')
        entries=debug.read_memory(bounded(word(0x8014BB1C),count*16),count*16)
        for i in range(count):
            r=entries[i*16:(i+1)*16];ram,device=struct.unpack_from('>2I',r)
            n=struct.unpack_from('>H',r,10)[0]
            first,last=max(device,sample_start),min(device+n,sample_start+sample_bytes)
            if first>=last or not r[14]:continue
            got=debug.read_memory(bounded(ram,n)+first-device,last-first)
            if got==image[first:last]:
                observations+=1
                record(dict(shared_sound_sample_dma=True,frame=frame+1,slot=i,
                    first=first-sample_start,last=last-sample_start,sha256=sha256(got),assertion='passed'))
    if not observations:raise ValueError('No complete sample transfer observed for shared sound')
    check('shared sound retains program after playback',sequence+row['offset'],
          data[row['offset']:row['offset']+row['bytes']])
    return dict(sound_id=sid,native_loader_trigger_and_sample_dma=True,observations=observations,
                physical_audio_played=False,pcm_or_listening_verified=False)


def original_equipment_kinds(original):
    """Read original switch returns for the shared probe, not guessed item order."""
    from aflib import verified_rom
    from v3_equipment_runtime import PLAYER_VROM,PLAYER_RAM
    data=by_vrom(verified_rom(original))[PLAYER_VROM].extract(original)
    table=data[0x808E0274-PLAYER_RAM:0x808E0274-PLAYER_RAM+144]
    if sha256(table)!='b46dbe4b89cb5647022dddcf27baa8e2ca8ea5ffc73c02a249f32b3c695c6af1':
        raise ValueError('Changed original equipment switch for native probe')
    result=[]
    for pointer in struct.unpack('>36I',table):
        branch,value=struct.unpack_from('>II',data,pointer-PLAYER_RAM)
        distance=struct.unpack('>h',struct.pack('>H',branch&65535))[0]*4
        if branch>>16!=0x1000 or pointer+4+distance!=0x808BD574:
            raise ValueError('Original equipment case is not a constant return')
        if value==0x00001025:kind=0
        elif value>>16==0x2402:kind=value&65535
        else:raise ValueError('Original equipment case has an unknown delay slot')
        result.append(kind)
    if sorted(result)!=list(range(36)):raise ValueError('Original equipment switch is incomplete')
    return result


def balloon_actor(debug,rom_path,record,*,selection_only=False):
    """Real ctor-created actor, all complete banks, native flight, and two drawers."""
    from runtime_layout import TEST_STACK
    import v3_balloon_actor as runtime_actor
    from v3_import_storage import jump
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Balloon probe requires current cartridge')
    resources=report['equipment_resources'];r=resources['player_actions']['balloon_actor'];symbols=r['code']['symbols']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(balloon_actor_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Balloon actor mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        value=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(value);return value['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    def scalar(at):return int.from_bytes(debug.read_memory(at,4),'big')
    def floating(at):return struct.unpack('>f',debug.read_memory(at,4))[0]
    def pointer(at,n):
        p=scalar(at)
        if p&3 or not MODULE_RAM+0x8000<=p<=0x80400000-n:raise ValueError('Missing balloon lifecycle pointer')
        return p
    start=resources['blob_offset'];module=blob[start:start+resources['bytes']]
    check('complete installed flight code',runtime_actor.RAM+r['offset'],module[r['offset']:r['offset']+r['code']['bytes']])
    game=pointer(0x8010EF90,0x1E00);player=pointer(game+0x1C90,r['player_bytes'])
    actor=pointer(player+r['player_pointer_offset'],r['actor_bytes'])
    packet=runtime_actor.RAM+r['packet_offset'];before=debug.read_memory(actor,r['actor_bytes'])
    check('ordinary player ctor created distinct CB actor',actor,b'\x00\xCB\x04')
    check('actor owns resident descriptor',actor+0x170,struct.pack('>I',packet))
    check('native descriptor instance count',packet+0x1E,b'\x01')
    check('complete descriptor/profile except mutable count',packet,module[r['packet_offset']:r['packet_offset']+0x1E])
    check('complete descriptor/profile suffix',packet+0x1F,module[r['packet_offset']+0x1F:r['packet_offset']+0x60])
    check('hidden source mode',actor+0x448,bytes(4))
    check('player extension padding',player+0x13A4,bytes(12))
    saved={at:debug.read_memory(at,n) for at,n in ((game,4),(game+0xA0,4),(0x801458A0,64),
        (0x80460020,192),(0x8046C000,report['save_runtime']['state_bytes']),(0x80126EA0,0xF980),
        (TEST_STACK-0x800,16),(TEST_STACK+0x40,16))}
    matrix=call(0x800E02AC);matrix_before=debug.read_memory(matrix,128)
    size=0x3A00;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:raise ValueError('Balloon fixture allocation failed')
    graph,bridge,args,gfx,xlu=(allocation+x for x in (0x10,0x400,0x500,0x800,0x2A00))
    debug.write_memory(allocation,bytes(size));edge=b'V3BA'*4
    guards=(allocation,graph+0x300,bridge-16,bridge+0x80,args-16,args+0x80,gfx-16,gfx+0x2000,
            xlu-16,xlu+0x800,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    names=('fly','main','draw','hide','descriptor')
    stubs=b''.join(struct.pack('>2I',jump(symbols['af_v3_balloon_'+name]),0) for name in names)
    debug.write_memory(bridge,stubs);call(0x8002FE00,[bridge,len(stubs)]);call(0x80034CE0,[bridge,len(stubs)])
    def resident(name,args=()):return call(bridge+names.index(name)*8,args,(bridge,stubs))
    position=debug.read_memory(player+0x28,12);models={x['index']:x for x in r['resources']}
    try:
        for iteration,shape in enumerate(() if selection_only else (0,7)):
            debug.write_memory(actor,before)
            debug.write_memory(args,struct.pack('>3h',400,1234,-200));debug.write_memory(args+16,position)
            value=resident('fly',[actor,game,shape,args,100,args+16,0xBF800000 if not iteration else 0x41400000,0x40E00000])
            check('request accepted with source shape',actor+0x450,struct.pack('>2I',1,shape))
            if value!=1:raise ValueError('Selected balloon release rejected')
            resident('main',[actor,game])
            check('source fly mode and pending sentinel',actor+0x448,struct.pack('>3I',1,shape,0xFFFFFFFF))
            check('complete independent model',actor+0x480,blob[models[40+shape]['blob_offset']:
                  models[40+shape]['blob_offset']+models[40+shape]['bytes']])
            idle=models[48];check('complete independent idle motion',actor+0x1AE0,blob[idle['blob_offset']:idle['blob_offset']+idle['bytes']])
            check('native setup readiness',actor+0x474,struct.pack('>I',1))
            delta=floating(actor+0x2C)-struct.unpack_from('>f',position,4)[0]
            passed=abs(delta-.15)<.001
            record(dict(balloon_rise_delta=delta,assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Incorrect donor half-step movement')
            assertions+=1
            check('native keyframe speed/frame/repeat',actor+0x180,struct.pack('>2fI',.5,2,1))
            check('main restores CPU segment six',0x801458B8,saved[0x801458A0][24:28])
            put(game,graph);put(game+0xA0,iteration)
            put(graph+0x298,gfx,gfx+0x2000);put(graph+0x2A8,xlu,xlu+0x800)
            resident('draw',[actor,game])
            front,back=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
            if not gfx<front<back<=gfx+0x2000:raise ValueError('Balloon drawing escaped private graphics arena')
            commands=list(struct.iter_unpack('>2I',debug.read_memory(gfx,front-gfx)))
            lists=[p for w,p in commands if w==0xDE000000 and p>>24==6]
            passed=len(lists)==4 and all(p==0x6000000 or p-0x6000000<models[40+shape]['bytes'] for p in lists)
            record(dict(balloon_shape=shape,source_joint_lists=lists,assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Balloon drawer omits complete model joints')
            assertions+=1
            check('drawer restores opaque segment',front-8,struct.pack('>II',0xDB060018,int.from_bytes(saved[0x801458A0][24:28],'big')))
            check('drawer restores CPU segment',0x801458B8,saved[0x801458A0][24:28])
            check('balanced matrix stack',0x801462B4,struct.pack('>I',matrix))
            check('parent matrix unchanged',matrix,matrix_before[:64])
            # Sample disappearance at the real source threshold, not a replacement timer.
            debug.write_memory(actor+0x2C,struct.pack('>f',struct.unpack_from('>f',position,4)[0]+199.99))
            put(actor+0x6C,0);resident('main',[actor,game])
            check('height threshold requests then enters hide',actor+0x448,struct.pack('>3I',0,shape,0xFFFFFFFF))
            check('hidden actor follows actual player position',actor+0x28,position)
            for at in guards:check('bounded work graphics and stack',at,edge)
        # Every other shape uses the same implementation; verify actual transfer,
        # animation construction, and bank isolation without repeating its draw.
        for shape in (() if selection_only else range(1,7)):
            resident('fly',[actor,game,shape,args,0,args+16,0xBF800000,0x40E00000]);resident('main',[actor,game])
            row=models[40+shape];check('complete shared shape bank',actor+0x480,blob[row['blob_offset']:row['blob_offset']+row['bytes']])
        profile=bytearray(saved[0x80460020])
        for row in resources['parent_readers']['rows']:
            if 0x2244<=int(row['item_id'],16)<0x224C:profile[row['profile_byte']]&=~row['profile_mask']
        debug.write_memory(0x80460020,profile)
        state=debug.read_memory(actor+0x448,0x30)
        if resident('fly',[actor,game,0,args,0,args+16,0xBF800000,0x40E00000])!=0:raise ValueError('Unselected balloon accepted')
        check('rejected release leaves actor untouched',actor+0x448,state)
        row=next(x for x in resources['parent_readers']['rows'] if int(x['item_id'],16)==0x224B)
        profile[row['profile_byte']]|=row['profile_mask'];debug.write_memory(0x80460020,profile)
        if resident('fly',[actor,game,7,args,0,args+16,0xBF800000,0x40E00000])!=1:raise ValueError('Selected shape rejected')
        check('selected shape accepted after rejection',actor+0x450,struct.pack('>2I',1,7))
        check('saved payload retained',0x80126EA0,saved[0x80126EA0])
        check('save/profile state retained',0x8046C000,saved[0x8046C000])
    finally:
        debug.write_memory(actor,before);debug.write_memory(matrix,matrix_before)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    check('complete actor restored',actor,before)
    for at,value in saved.items():check('restored live state',at,value)
    check('no fault',0x8003CE34,bytes(4))
    return dict(native_balloon_actor=not selection_only,native_balloon_selection=selection_only,
        assertions=assertions,actual_player_ctor=True,models=0 if selection_only else 8,
        representative_drawers=0 if selection_only else 2,source_timing_sampled=not selection_only,
        game_code_uploaded=False,test_jump_bridges=True,
        ordinary_release_tested=False,hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)


def balloon_menu(debug,rom_path,record):
    """Actual relocated menu cursor/dispatch, pocket transfer and flight queue."""
    from runtime_layout import TEST_STACK
    from v3_import_storage import jump
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed balloon menu cartridge')
    resources=report['equipment_resources'];r=resources['player_actions']['balloon_menu']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(balloon_menu_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Balloon menu mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    def scalar(at):return int.from_bytes(debug.read_memory(at,4),'big')
    def pointer(at,size):
        value=scalar(at)
        if value&3 or not MODULE_RAM+0x8000<=value<=0x80400000-size:raise ValueError('Invalid menu fixture pointer')
        return value
    start=resources['blob_offset'];module=bytearray(blob[start:start+resources['bytes']])
    packet=resources['player_actions']['balloon_actor']['packet_offset']
    check('one actual flying actor instance',equipment.RAM+packet+0x1E,b'\1');module[packet+0x1E]=1
    check('complete installed equipment module',equipment.RAM,module)
    game=pointer(0x8010EF90,0x1E00);actor=pointer(game+0x1C90,0x13B0)
    balloon=pointer(actor+0x13A0,0x2080);actor_before=debug.read_memory(actor,0x13B0)
    saved={at:debug.read_memory(at,n) for at,n in ((0x8010DCEC,4),(0x80136EA1,1),(0x80460020,192),
        (0x8046C000,report['save_runtime']['state_bytes']),(0x80126EA0,0xF980),(0x80136FD8,4),
        (0x80143910,0x50),(balloon,0x2080),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16))}
    size=0x1D000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:raise ValueError('Menu fixture allocation failed')
    tag,overlay,state,submenu,menu,bridge,counts=(allocation+n for n in
        (0x10,0xC000,0x1C720,0x1CA00,0x1CB20,0x1CC00,0x1CD00))
    # These two isolated owners use disjoint offsets in one fixture buffer.
    parent=overlay
    debug.write_memory(overlay,bytes(size-(overlay-allocation)))
    data,rel=(files[v].extract(image) for v in (0x3950000,0x3960000));ram=0x8086F310
    if len(data)+len(rel)+0x20>=0xC000:raise ValueError('Expanded menu exceeds fixture staging')
    loaded=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=len(data),sections=struct.unpack_from('>5I',rel)),data,rel,tag)
    call(0x800262D0,[0x3950000,0x3950000+len(data),ram,ram+len(data),tag,tag+len(data),len(rel)])
    check('complete cartridge-loaded expanded menu',tag,loaded)
    raw=struct.pack('>2I',jump(r['code']['symbols']['af_v3_balloon_menu_type']),0)
    close=bridge+len(raw)
    raw+=struct.pack('>9I',0x3C080000|((counts+0x8000)>>16),0x25080000|(counts&65535),
        0x8D090000,0x25290001,0xAD090000,0xAD040004,0xAD050008,0x03E00008,0)
    debug.write_memory(bridge,raw);call(0x8002FE00,[bridge,len(raw)]);call(0x80034CE0,[bridge,len(raw)])
    edge=b'V3BM'*4;guards=(allocation,overlay-16,state-16,submenu-16,menu-16,bridge-16,
        allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    put(submenu+0x2C,overlay);put(overlay+0x106D0,state);put(overlay+0x106B0,close)
    put(parent+0x2CC0,tag+0x808787A0-ram)
    selected_tag=state+8+0x54;private=0x80126EC0
    def dispatch(button):
        put(overlay+0x1068C,button);a,b=0x80876C50-ram,0x80876D90-ram
        return call(tag+a,[submenu,menu,selected_tag],(tag+a,loaded[a:b]))
    def type_check(item,slot,want):
        nonlocal assertions
        actual=call(bridge,[submenu,item,slot],(bridge,raw));passed=actual==want
        record(dict(balloon_menu_type=item,slot=slot,expected=want,observed=actual,assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Native balloon menu classification mismatch')
        assertions+=1
    try:
        put(0x8010DCEC,parent);put(0x80136FD8,private);put(private+0x34,0)
        for shape in (0,7):
            for field,want in ((0,44),(1,12),(2,8),(3,8)):
                debug.write_memory(0x80136EA1,bytes([field]));type_check(0x2244+shape,14,want)
        debug.write_memory(0x80136EA1,b'\0')
        for condition,want in ((1,11),(2,8),(3,11)):
            put(private+0x34,condition<<28);type_check(0x224B,14,want)
        put(private+0x34,0)
        row=next(x for x in resources['parent_readers']['rows'] if x['item_id']=='224B')
        profile=bytearray(saved[0x80460020]);profile[row['profile_byte']]&=~row['profile_mask']
        debug.write_memory(0x80460020,profile);type_check(0x224B,14,1)
        debug.write_memory(0x80460020,saved[0x80460020])
        put(state,1,0);debug.write_memory(selected_tag,b'\x2C');put(selected_tag+0x3C,0)
        for button,want in ((4,1),(4,2),(4,2),(8,1),(8,0),(8,0)):
            dispatch(button);check('actual native three-option cursor bounds',selected_tag+0x3C,struct.pack('>I',want))
        for shape,slot,replacement in ((0,0,0),(7,14,0x1234)):
            debug.write_memory(state,bytes(0x200));put(state,1,0);debug.write_memory(selected_tag,b'\x2C')
            put(selected_tag+0x3C,1);put(state+8+0x34,0,slot%5,slot//5)
            put(menu+0x38,13 if replacement else 0,replacement);put(counts,0,0,0)
            debug.write_memory(submenu+0xDF,b'\xA5'*3);put(private+0x34,0)
            pockets=bytearray(b'\x12\x00'*15);struct.pack_into('>H',pockets,slot*2,0x2244+shape)
            debug.write_memory(private+0x14,pockets);debug.write_memory(0x80143910,b'\xA5'*0x50)
            dispatch(0x8000)
            check('A dispatch queues selected balloon before close',0x80143910,struct.pack('>9I',81,1,2,shape,0,0,0,0,0))
            check('native handler records selected pocket and full item',submenu+0xDF,struct.pack('>BH',slot,0x2244+shape))
            struct.pack_into('>H',pockets,slot*2,replacement);check('actual pocket setter replaces only the selected item',private+0x14,pockets)
            check('native return-tag initializer completes',state+4,b'\xFF'*4)
            check('native close invokes isolated close callback',counts,struct.pack('>3I',1,menu,0))
        check('native menu retains complete expanded owner',tag,loaded)
        check('equipment module unchanged',equipment.RAM,module)
        check('release queue does not prematurely mutate player',actor,actor_before)
        check('saved import state unchanged',0x8046C000,saved[0x8046C000])
        for at in guards:check('menu memory guard',at,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    for at,value in saved.items():check('live state restored',at,value)
    return dict(native_balloon_menu=True,assertions=assertions,actual_cursor_and_A_dispatch=True,
        actual_pocket_setter=True,actual_return_tag_initializer=True,test_only_close_callback=True,
        test_only_classification_bridge=True,ordinary_gameplay_tested=False,hardware_tested=False,
        flash_written=False,requires_checkpoint_restore=True)


def balloon_release(debug,rom_path,record):
    """Current cartridge callbacks, source pose, head tracking and fall handoff."""
    from runtime_layout import TEST_STACK
    from v3_import_storage import jump
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed balloon release cartridge')
    resources=report['equipment_resources'];r=resources['player_actions']['balloon_release']
    flying=resources['player_actions']['balloon_actor'];files=by_vrom(image)
    blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(balloon_release_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Balloon release mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    def scalar(at):return int.from_bytes(debug.read_memory(at,4),'big')
    def pointer(at,n):
        p=scalar(at)
        if p&3 or not MODULE_RAM+0x8000<=p<=0x80400000-n:raise ValueError('Missing live release pointer')
        return p
    module=blob[resources['blob_offset']:resources['blob_offset']+resources['bytes']];symbols={}
    for row in r['codes'].values():
        a,n=row['offset'],row['code']['bytes'];check('complete installed consumer code',equipment.RAM+a,module[a:a+n])
        symbols.update(row['code']['symbols'])
    constructor=scalar(0x80143900);owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data,rel=(files[v].extract(image) for v in (equipment.PLAYER_VROM,equipment.PLAYER_RELOC))
    sections=struct.unpack_from('>5I',rel)
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete relocated player code',owner,expected[:sections[0]])
    def native(entry,args):
        at=entry-equipment.PLAYER_RAM
        return call(owner+at,args,(owner+at,expected[at:at+8]))
    game=pointer(0x8010EF90,0x1E00);actor=pointer(game+0x1C90,0x13B0)
    balloon=pointer(actor+0x13A0,flying['actor_bytes'])
    actor_before=debug.read_memory(actor,0x13B0);balloon_before=debug.read_memory(balloon,flying['actor_bytes'])
    saved={at:debug.read_memory(at,n) for at,n in ((0x80460020,192),(0x8046C000,report['save_runtime']['state_bytes']),
        (0x80126EA0,0xF980),(0x80136FD8,4),(0x8013767D,2),(0x80143910,0x50),(0x80123E10,0x154),
        (0x801458A0,64),(0x80104F94,4),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16))}
    banks={}
    for index in struct.unpack_from('>2h',actor_before,0xDA0):
        if not 0<=index<8:raise ValueError('Invalid player animation bank')
        p=pointer(game+0x114+84*index,equipment.PLAYER_CAPACITY);banks[p]=debug.read_memory(p,equipment.PLAYER_CAPACITY)
    size=0x200;allocation=call(0x8009BFC0,[size]);bridge=allocation+16;args=allocation+0x120
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:raise ValueError('Balloon release fixture allocation failed')
    names=('request','submenu','release_setup','look','release_transition','getup','getup_transition')
    raw=b''.join(struct.pack('>2I',jump(symbols['af_v3_balloon_'+name]),0) for name in names)
    debug.write_memory(bridge,raw);call(0x8002FE00,[bridge,len(raw)]);call(0x80034CE0,[bridge,len(raw)])
    def resident(name,values):return call(bridge+names.index(name)*8,values,(bridge,raw))
    edge=b'V3BR'*4;guards=(allocation,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    for row in r['callbacks']:check('actual registered creature callback',equipment.RAM+row['offset'],struct.pack('>I',row['after']))
    def prepare():
        put(actor+0xCF0,7);put(actor+0xD00,7,0,0,0);put(actor+0xD70,77)
        debug.write_memory(actor+0xE64,b'\1')
    try:
        put(0x80136FD8,0x80126EC0);put(0x80104F94,0);debug.write_memory(0x8013767D,bytes(2))
        debug.write_memory(0x80127908,b'\0');debug.write_memory(0x80126EC0+0x3EC,bytes(2))
        for shape in (0,7):
            prepare();put(0x80143910,81,1,2,shape,0,0,0,0,0)
            resident('submenu',[actor,game])
            check('submenu accepts selected balloon and native priority',actor+0xD00,struct.pack('>3I',81,31,1))
            check('request carries complete shape union',actor+0xD58,struct.pack('>6I',2,shape,0,0,0,0))
            check('ordinary release clears reward flag',actor+0xD70,bytes(4))
            debug.write_memory(actor+0xDE,bytes(2));position=struct.unpack('>3f',debug.read_memory(actor+0x28,12))
            resident('release_setup',[actor,game])
            check('native base installs release action',actor+0xCF0,struct.pack('>I',81))
            check('setup owns flying actor and clears timer',actor+0xD10,struct.pack('>5I',2,balloon,0,1,0))
            check('flight request retains source angle and shape',balloon+0x450,struct.pack('>2I4h',1,shape,0,0,0,0))
            check('ordinary flight frame and speed',balloon+0x460,struct.pack('>2f',-1,7))
            check('source world offset',balloon+0x468,struct.pack('>3f',position[0]+10,position[1]+17.5,position[2]+10))
            # Pending flight prevents completion, including after the minimum timer.
            put(actor+0xD00,7,0,0,0);debug.write_memory(actor+0xD18,struct.pack('>f',41))
            resident('look',[actor]);native(0x808D7814,[actor,game])
            check('live balloon keeps release action at timing boundary',actor+0xD08,bytes(4))
            check('pending flight continuation is false',actor+0x13A4,bytes(4))
            put(balloon+0x448,0,shape,0xFFFFFFFF);resident('look',[actor]);native(0x808D7814,[actor,game])
            check('hidden balloon permits ordinary wait',actor+0xD00,struct.pack('>3I',7,1,1))
            check('finished release clamps native timer',actor+0xD18,struct.pack('>f',42))
            check('finished release clears tracked actor',actor+0xD14,bytes(4))
        # Native smoothing must use the source balloon limits, not native insect ones.
        put(actor+0xD10,2,balloon,0,0,0);put(balloon+0x448,1,0,0xFFFFFFFF)
        debug.write_memory(actor+0xDC,bytes(6));debug.write_memory(actor+0x48,struct.pack('>3f',0,0,0))
        debug.write_memory(balloon+0x28,struct.pack('>3f',100,50,0));debug.write_memory(actor+0x1136,bytes(6))
        resident('look',[actor]);check('two donor head substeps with 500 limits',actor+0x1136,struct.pack('>2h',1000,1000))
        debug.write_memory(actor+0xD18,struct.pack('>f',30));resident('look',[actor])
        check('post-tracking recovery uses smaller pitch limit',actor+0x1136,struct.pack('>2h',501,600))
        for shape in (0,7):
            prepare();debug.write_memory(0x80126EC0+0x3EC,struct.pack('>H',0x2244+shape))
            debug.write_memory(actor+0x1370,struct.pack('>4h',100,-10,80,-70));debug.write_memory(actor+0x1388,struct.pack('>h',20))
            debug.write_memory(actor+0xDE,struct.pack('>h',80));debug.write_memory(actor+0x103C,struct.pack('>3f',14,25,36))
            debug.write_memory(actor+0xA28,struct.pack('>f',12.5))
            native(0x808C320C,[actor,game,91+shape,0xC0A00000])
            check('fall records correct shape',actor+0x13A8,struct.pack('>I',shape))
            check('fall clears equipped item',0x80126EC0+0x3EC,bytes(2))
            check('fall carries complete current hand pose',balloon+0x450,
                struct.pack('>2I4h5f',1,shape,110,80,0,-70,12.5,7,14,25,36))
            check('native get-up now has empty hand',actor+0x1117,b'\xFF')
            native(0x808C33A0,[actor,game,0]);check('get-up waits for animation end',actor+0xD08,bytes(4))
            native(0x808C33A0,[actor,game,1])
            check('get-up requests source release priority',actor+0xD00,struct.pack('>3I',81,30,1))
            check('get-up reuses flying actor',actor+0xD6C,struct.pack('>I',balloon))
            resident('release_setup',[actor,game]);check('existing flight retains frame',balloon+0x460,struct.pack('>f',12.5))
            check('existing flight not treated as new birth',actor+0xD1C,bytes(4))
        prepare();put(actor+0x13A0,0);debug.write_memory(0x80126EC0+0x3EC,struct.pack('>H',0x2244))
        native(0x808C320C,[actor,game,91,0xC0A00000])
        check('missing actor retains equipped balloon',0x80126EC0+0x3EC,struct.pack('>H',0x2244))
        check('missing actor records ordinary recovery',actor+0x13A8,b'\xFF'*4)
        put(actor+0x13A0,balloon);prepare();put(actor+0xD00,7,40,1);put(args,0,0,0,0)
        if resident('request',[game,2,1,args,0,31])!=0:raise ValueError('Priority rejection bypassed')
        check('rejected request retains pending flag',actor+0xD70,struct.pack('>I',77))
        check('save extension untouched',0x8046C000,saved[0x8046C000])
        for at in guards:check('bounded actor handoff and stack',at,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(actor,actor_before);debug.write_memory(balloon,balloon_before)
        for at,value in banks.items():debug.write_memory(at,value)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    check('complete player restored',actor,actor_before);check('complete flying actor restored',balloon,balloon_before)
    for at,value in saved.items():check('restored live state',at,value)
    return dict(native_balloon_release=True,assertions=assertions,actual_registered_callbacks=2,
        actual_release_getup_hooks=True,source_timing_sampled=True,test_jump_bridges=True,
        ordinary_menu_release_tested=False,ordinary_gameplay_tested=False,hardware_tested=False,
        flash_written=False,requires_checkpoint_restore=True)


def reward_exchange(debug,rom_path,record,*,balloons=False):
    """Loaded tag routing and actual native deferred request/setup/completion paths."""
    import v3_equipment_runtime as equipment
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed deferred reward cartridge')
    resources=report['equipment_resources'];receipt=resources['player_actions']['reward_exchange']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(reward_exchange_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(actual),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Deferred reward mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    def pointer(at,size):
        value=int.from_bytes(debug.read_memory(at,4),'big')
        if value&3 or not MODULE_RAM+0x8000<=value<=0x80400000-size:raise ValueError('Invalid deferred fixture pointer')
        return value
    start=resources['blob_offset'];module=bytearray(blob[start:start+resources['bytes']])
    if balloons:
        packet=resources['player_actions']['balloon_actor']['packet_offset']
        check('one live flying actor instance',equipment.RAM+packet+0x1E,b'\1')
        module[packet+0x1E]=1
    check('complete installed module',equipment.RAM,module)
    constructor=int.from_bytes(debug.read_memory(0x80143900,4),'big');owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data,rel=(files[v].extract(image) for v in (equipment.PLAYER_VROM,equipment.PLAYER_RELOC))
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):raise ValueError('Missing live player owner')
    sections=struct.unpack_from('>5I',rel)
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete relocated player code',owner,expected[:sections[0]])
    native_rows={r['entry']:r for r in receipt['bindings']['native_functions']}
    def player(entry,args):
        row=native_rows[entry];a,b=entry-equipment.PLAYER_RAM,row['end']-equipment.PLAYER_RAM
        return call(owner+a,args,(owner+a,expected[a:b]))
    game=pointer(0x8010EF90,0x1E00);actor_bytes=resources['held_rig_actions']['player_allocation']['bytes']
    actor=pointer(game+0x1C90,actor_bytes);actor_before=debug.read_memory(actor,actor_bytes)
    saved={at:debug.read_memory(at,size) for at,size in ((0x80460020,192),(0x8046C000,report['save_runtime']['state_bytes']),
        (0x80126EA0,0xF980),(0x80136FD8,4),(0x8013767D,2),(0x80143910,0x50),(0x80123E10,0x154),(0x801458A0,64))}
    if balloons:
        balloon=pointer(actor+0x13A0,0x2080);saved[balloon]=debug.read_memory(balloon,0x2080)
        saved[0x80104F94]=debug.read_memory(0x80104F94,4)
    banks={}
    for index in struct.unpack_from('>2h',actor_before,0xDA0):
        if not 0<=index<8:raise ValueError('Invalid native animation bank')
        address=pointer(game+0x114+84*index,equipment.PLAYER_CAPACITY)
        banks[address]=debug.read_memory(address,equipment.PLAYER_CAPACITY)
    size=0x1D000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:raise ValueError('Deferred fixture allocation failed')
    tag,overlay,hand,submenu,menu,bridge,counts,pos=(allocation+n for n in (0x10,0xC000,0x1C720,0x1CA40,0x1CAA0,0x1CB00,0x1CC00,0x1CC20))
    debug.write_memory(overlay,bytes(size-(overlay-allocation)))
    tag_data,tag_rel=(files[v].extract(image) for v in (0x3950000,0x3960000))
    tag_sections=struct.unpack_from('>5I',tag_rel)
    if len(tag_data)+len(tag_rel)+0x20>=0xC000:raise ValueError('Tag staging exceeds fixture reservation')
    tag_loaded=relocate_verified_data(SimpleNamespace(ram=0x8086F310,resident_bytes=len(tag_data),sections=tag_sections),tag_data,tag_rel,tag)
    call(0x800262D0,[0x3950000,0x3950000+len(tag_data),0x8086F310,0x8086F310+len(tag_data),tag,tag+len(tag_data),len(tag_rel)])
    check('complete cartridge-loaded tag owner',tag,tag_loaded)
    raw=bytearray();entries={}
    for row in receipt['callbacks']:
        if balloons and row['action']==81:
            row=next(r for r in resources['player_actions']['balloon_release']['callbacks'] if r['consumer']==row['consumer'])
        key=(row['consumer'],row['action']);target=int.from_bytes(debug.read_memory(equipment.RAM+row['offset'],4),'big')
        if target!=row['after']:raise ValueError('Changed actual deferred callback')
        entries[key]=bridge+len(raw);raw.extend(struct.pack('>4I',0x08000000|(target>>2&0x3FFFFFF),0,0,0))
    close=bridge+len(raw)
    raw.extend(struct.pack('>9I',0x3C080000|((counts+0x8000)>>16),0x25080000|(counts&65535),
        0x8D090000,0x25290001,0xAD090000,0xAD040004,0xAD050008,0x03E00008,0))
    debug.write_memory(bridge,raw);call(0x8002FE00,[bridge,len(raw)]);call(0x80034CE0,[bridge,len(raw)])
    bridge_proof=(bridge,bytes(raw));edge=b'V3RX'*4
    guards=(allocation,overlay-16,hand-16,submenu-16,menu-16,bridge-16,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    put(submenu+0x2C,overlay);put(overlay+0x106D4,hand);put(overlay+0x106B0,close)
    debug.write_memory(hand+0x264,b'\xFF');debug.write_memory(pos,struct.pack('>3f',0,0,0))
    state=bytearray(saved[0x8046C000]);selection=next(r for r in resources['parent_readers']['rows'] if r['item_id']=='223B')
    def profile(enabled,done=False):
        p=bytearray(saved[0x80460020]);p[selection['profile_byte']]&=~selection['profile_mask']
        if enabled:p[selection['profile_byte']]|=selection['profile_mask']
        state[0x10:0xD0]=p;state[0x350:0x380]=bytes(48);state[0x358]=8 if done else 0
        debug.write_memory(0x80460020,p);debug.write_memory(0x8046C000,state)
    def prepare():
        put(actor+0xCF0,7);put(actor+0xD00,7,0,0,0);debug.write_memory(actor+0xD58,b'\xA5'*32)
    def callback(table,index):return call(entries[(table,index)],[actor,game],bridge_proof)
    try:
        put(0x80136FD8,0x80126EC0);debug.write_memory(0x8013767D,bytes(2));debug.write_memory(0x80127908,b'\0')
        debug.write_memory(actor+0xE64,b'\1');profile(True)
        for action in (() if balloons else (7,63,81,118)):
            prepare();player(0x808B3334,[game,action,31])
            check('ordinary request clears flag only for deferred actions',actor+0xD70,bytes(4) if action in (63,81) else b'\xA5'*4)
        for entry,args in (() if balloons else ((0x800B2008,[pos,0]),(0x800B2060,[123,0x2301]),(0x800B20A8,[1]))):
            debug.write_memory(0x80143910,b'\xA5'*0x50);call(entry,args)
            check('ordinary submenu request clears deferred flag',0x80143930,bytes(4))
        for enabled,done in (() if balloons else ((True,False),(True,True),(False,False))):
            profile(enabled,done);flag=enabled and not done
            for item in (0,0x2301,0x2D01):
                debug.write_memory(hand+0x23C,struct.pack('>H',item));put(menu+0x3C,0x223B);put(counts,0,0,0)
                debug.write_memory(0x80143910,b'\xA5'*0x50)
                a,b=0x80873ADC-0x8086F310,0x80873C88-0x8086F310
                call(tag+a,[submenu,menu],(tag+a,tag_loaded[a:b]))
                check('actual tag route selects correct action',0x80143910,struct.pack('>2I',(118 if flag else 7) if not item else 81,1))
                check('tag route carries reward only to deferred action',0x80143930,struct.pack('>I',int(flag and bool(item))))
                check('test close callback receives native menu and direction',counts,struct.pack('>3I',1,menu,0))
        profile(True)
        for index,entry,transition in (() if balloons else ((63,0x800B2008,0x808D2774),(81,0x800B2060,0x808D7814))):
            for flag in (0,1):
                prepare();call(entry,[pos,0] if index==63 else [123,0x2301]);put(0x80143930,flag)
                callback(0x808DD874,index)
                check('registered submenu preserves native request priority',actor+0xD00,struct.pack('>3I',index,31,1))
                check('accepted submenu carries requested flag',actor+0xD70,struct.pack('>I',flag))
                if index==81:put(actor+0xD6C,actor) # Existing release actor; do not spawn into this component fixture.
                callback(0x808DDA18,index)
                check('actual native setup selects deferred action',actor+0xCF0,struct.pack('>I',index))
                check('registered setup retains deferred flag',actor+0xD20,struct.pack('>I',flag))
                put(actor+0xD00,7,0,0,0)
                if index==81:
                    debug.write_memory(actor+0xD18,struct.pack('>f',40));player(transition,[actor,game])
                    check('release waits before boundary',actor+0xD08,bytes(4))
                    player(transition,[actor,game]);check('release timer clamps at source-equivalent boundary',actor+0xD18,struct.pack('>f',42))
                else:
                    if flag:
                        player(transition,[actor,game,0]);check('bury reward waits for animation end',actor+0xD08,bytes(4))
                    player(transition,[actor,game,1])
                check('finished deferred action requests correct continuation',actor+0xD00,struct.pack('>3I',118 if flag else 7,34 if flag else 1,1))
                if flag:check('deferred reward type',actor+0xD58,struct.pack('>I',3))
            prepare();put(actor+0xD00,7,40,1);put(actor+0xD70,77);callback(0x808DD874,index)
            check('rejected submenu does not overwrite requested flag',actor+0xD70,struct.pack('>I',77))
        if balloons:
            put(0x80104F94,0);debug.write_memory(0x80126EC0+0x3EC,bytes(2))
            for shape in (0,7):
                for flag in (0,1):
                    prepare();debug.write_memory(hand+0x23C,struct.pack('>H',0x2244+shape));put(hand+0x2E4,0)
                    put(menu+0x3C,0x223B if flag else 0x1234);put(counts,0,0,0)
                    debug.write_memory(0x80143910,b'\xA5'*0x50)
                    a,b=0x80873ADC-0x8086F310,0x80873C88-0x8086F310
                    call(tag+a,[submenu,menu],(tag+a,tag_loaded[a:b]))
                    check('tag exchange queues complete selected balloon union',0x80143910,struct.pack('>9I',81,1,2,shape,0,0,0,0,flag))
                    check('successful flight exchange closes native menu',counts,struct.pack('>3I',1,menu,0))
                    callback(0x808DD874,81);callback(0x808DDA18,81)
                    check('exchange reaches real release action',actor+0xCF0,struct.pack('>I',81))
                    check('exchange starts the owned flying actor',balloon+0x450,struct.pack('>2I',1,shape))
                    check('exchange setup preserves deferred reward',actor+0xD20,struct.pack('>I',flag))
                    put(actor+0xD00,7,0,0,0);put(actor+0x13A4,1)
                    debug.write_memory(actor+0xD18,struct.pack('>f',41));player(0x808D7814,[actor,game])
                    check('finished balloon exchange selects continuation',actor+0xD00,struct.pack('>3I',118 if flag else 7,34 if flag else 1,1))
        check('reward completion remains unset until settlement',0x8046C000,state)
        check('module remains unchanged',equipment.RAM,module)
        for at in guards:check('deferred reward guard',at,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(actor,actor_before)
        for at,value in banks.items():debug.write_memory(at,value)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    check('live actor restored',actor,actor_before)
    for at,value in banks.items():check('live bank restored',at,value)
    for at,value in saved.items():check('live state restored',at,value)
    return dict(native_reward_exchange=True,native_balloon_exchange=balloons,assertions=assertions,actual_tag_empty_fish_insect=not balloons,
        actual_registered_callbacks=2 if balloons else 4,registered_callbacks_verified=4,
        test_only_jump_bridges=True,test_only_close_callback=True,
        bury_item_zero=not balloons,release_existing_actor=not balloons,ordinary_placement_tested=False,
        ordinary_gameplay_tested=False,balloon_release_tested=balloons,hardware_tested=False,
        flash_written=False,requires_checkpoint_restore=True)


def reward_pickup(debug,rom_path,record):
    """Actual collection transition entries, with source flags and native requests."""
    import v3_equipment_runtime as equipment
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed reward-pickup cartridge')
    resources=report['equipment_resources'];receipt=resources['player_actions']['reward_pickup']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(reward_pickup_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(actual),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Reward pickup mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None,want=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None:
            if result['return_value']!=want:raise ValueError('Unexpected reward pickup return')
            assertions+=1
        return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    def pointer(at,size):
        value=int.from_bytes(debug.read_memory(at,4),'big')
        if value&3 or not MODULE_RAM+0x8000<=value<=0x80400000-size:raise ValueError('Invalid pickup fixture pointer')
        return value
    start=resources['blob_offset'];module=blob[start:start+resources['bytes']]
    check('complete installed reward module',equipment.RAM,module)
    constructor=int.from_bytes(debug.read_memory(0x80143900,4),'big');owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data,rel=(files[v].extract(image) for v in (equipment.PLAYER_VROM,equipment.PLAYER_RELOC))
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):raise ValueError('Missing live player owner')
    sections=struct.unpack_from('>5I',rel)
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete actual relocated player code',owner,expected[:sections[0]])
    game=pointer(0x8010EF90,0x1E00);actor_bytes=resources['held_rig_actions']['player_allocation']['bytes']
    actor=pointer(game+0x1C90,actor_bytes);actor_before=debug.read_memory(actor,actor_bytes)
    saved={at:debug.read_memory(at,size) for at,size in ((0x80460020,192),
        (0x8046C000,report['save_runtime']['state_bytes']),(0x80126EA0,0xF980),(0x80136FD8,4),(0x8013767D,2))}
    selection=next(r for r in resources['parent_readers']['rows'] if r['item_id']=='223B')
    allocation=call(0x8009BFC0,[64])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-64:raise ValueError('Pickup query bridge allocation failed')
    bridge=allocation+16;query=receipt['code']['symbols']['af_v3_reward_completed']
    raw=struct.pack('>4I',0x08000000|(query>>2&0x3FFFFFF),0,0,0)
    debug.write_memory(bridge,raw);call(0x8002FE00,[bridge,len(raw)]);call(0x80034CE0,[bridge,len(raw)])
    proof=(bridge,raw);edge=b'V3RP'*4;guards=(allocation,allocation+48,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    state=bytearray(saved[0x8046C000]);state[0x350:0x380]=bytes(48)
    def select(enabled):
        profile=bytearray(saved[0x80460020]);profile[selection['profile_byte']]&=~selection['profile_mask']
        if enabled:profile[selection['profile_byte']]|=selection['profile_mask']
        state[0x10:0xD0]=profile;debug.write_memory(0x80460020,profile);debug.write_memory(0x8046C000,state)
    def prepare(row,item=0x223B,enabled=True,done=False,priority=0,pending=0):
        state[0x350:0x380]=bytes(48);state[0x358]=8 if done else 0;select(enabled)
        put(0x80136FD8,0x80126EC0);put(actor+0xCF0,row['action']);put(actor+0xD00,7,priority,pending,0)
        debug.write_memory(actor+0xD10,bytes(0x48));debug.write_memory(actor+0xD58,b'\xA5'*16)
        debug.write_memory(actor+0xD10,struct.pack('>3f',11,22,33))
        debug.write_memory(actor+row['item_offset'],struct.pack('>H',item))
    def transition(row,end=1):
        first,last=row['entry']-equipment.PLAYER_RAM,row['end']-equipment.PLAYER_RAM
        return call(owner+first,[actor,game,end],(owner+first,expected[first:last]))
    try:
        debug.write_memory(0x8013767D,bytes(2));debug.write_memory(0x80127908,b'\0');debug.write_memory(actor+0xE64,b'\1')
        select(True)
        for slot in range(4):
            put(0x80136FD8,0x80126EC0+slot*0xBD0)
            for type in range(4):
                state[0x350:0x380]=bytes(48);state[0x358+12*slot]=1<<type
                debug.write_memory(0x8046C000,state);call(bridge,[type],proof,1)
                call(bridge,[(type+1)%4],proof,0)
        call(bridge,[4],proof,0xFFFFFFFF);put(0x80136FD8,0x80126EC1);call(bridge,[3],proof,0xFFFFFFFF)
        for row in receipt['bindings']['paths']:
            label=str(row['action'])
            prepare(row);before=debug.read_memory(actor,actor_bytes);transition(row,0)
            check(label+' unfinished animation retains actor',actor,before)
            transition(row);check(label+' first shovel requests celebration',actor+0xD00,struct.pack('>3I',118,34,1))
            check(label+' shovel request type',actor+0xD58,struct.pack('>I',3))
            check(label+' request does not mark completion',0x8046C000,state)
            for item,enabled,done,description in ((0x223B,True,True,'completed shovel'),
                    (0x223B,False,False,'unselected shovel'),(0x2202,True,False,'ordinary item')):
                prepare(row,item,enabled,done);transition(row)
                check(label+' '+description+' returns to idle',actor+0xD00,struct.pack('>3I',7,1,1))
                check(label+' original wait arguments',actor+0xD58,struct.pack('>fI',-5,0))
            prepare(row,priority=40,pending=1);before=debug.read_memory(actor,actor_bytes);transition(row)
            check(label+' high-priority request rejects reward without fallback',actor,before)
            if row['action']!=62:
                prepare(row);exchange_offset=0xD3C if row['action']==32 else 0xD40
                put(actor+exchange_offset,1);transition(row)
                check(label+' full pockets retain original exchange request',actor+0xD00,struct.pack('>3I',33,21,1))
                check(label+' exchange retains position and item',actor+0xD58,struct.pack('>3fH',11,22,33,0x223B))
        check('callback module unchanged',equipment.RAM,module)
        check('native save payload unchanged apart from fixture flag',0x80126EA0,
            saved[0x80126EA0][:0xA68]+b'\0'+saved[0x80126EA0][0xA69:])
        for at in guards:check('pickup guard',at,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(actor,actor_before)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    check('live actor restored',actor,actor_before)
    for at,value in saved.items():check('live state restored',at,value)
    return dict(native_reward_pickup=True,assertions=assertions,actual_transition_entries=4,
        reward_requests=True,repeat_suppression=True,selection_rejection=True,full_pocket_requests=3,
        direct_component_calls=True,test_only_query_bridge=True,putaway_submenu_execution=False,
        ordinary_acquisition_tested=False,ordinary_gameplay_tested=False,hardware_tested=False,
        flash_written=False,requires_checkpoint_restore=True)


def reward_actions(debug,rom_path,record):
    """Registered native transitions, including axe wait and persistent settlement."""
    import v3_equipment_runtime as equipment
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed reward-action cartridge')
    resources=report['equipment_resources'];actions=resources['player_actions'];receipt=actions['reward_actions']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(reward_action_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(actual),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Reward action mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None,want=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None:
            if result['return_value']!=want:raise ValueError('Unexpected reward action return')
            assertions+=1
        return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    def pointer(at,size):
        value=int.from_bytes(debug.read_memory(at,4),'big')
        if value&3 or not MODULE_RAM+0x8000<=value<=0x80400000-size:raise ValueError('Invalid reward action fixture pointer')
        return value
    start=resources['blob_offset'];module=blob[start:start+resources['bytes']]
    check('complete installed callback module',equipment.RAM,module)
    constructor=int.from_bytes(debug.read_memory(0x80143900,4),'big');owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data,rel=(files[v].extract(image) for v in (equipment.PLAYER_VROM,equipment.PLAYER_RELOC))
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):raise ValueError('Missing live player owner')
    sections=struct.unpack_from('>5I',rel)
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete actual player code',owner,expected[:sections[0]])
    proofs={}
    for row in actions['tables']:
        if row['native_entry'] in (0x808DDA18,0x808DDB5C):
            first,last=row['native_entry']-equipment.PLAYER_RAM,row['native_end']-equipment.PLAYER_RAM
            proofs[row['native_entry']]=(owner+first,expected[first:last])
    def dispatch(entry):
        proof=proofs[entry];return call(proof[0],[actor,game],proof,want=1 if entry==0x808DDA18 else None)
    game=pointer(0x8010EF90,0x1E00);actor_bytes=resources['held_rig_actions']['player_allocation']['bytes']
    actor=pointer(game+0x1C90,actor_bytes);actor_before=debug.read_memory(actor,actor_bytes)
    saved={at:debug.read_memory(at,size) for at,size in ((0x80123E10,0x154),(0x801458A0,64),
        (0x8046C000,report['save_runtime']['state_bytes']),(0x80126EA0,0xF980),(0x80136FD8,4),(0x8013767D,2))}
    banks={}
    for index in struct.unpack_from('>2h',actor_before,0xDA0):
        if not 0<=index<8:raise ValueError('Invalid live reward bank')
        address=pointer(game+0x114+84*index,equipment.PLAYER_CAPACITY)
        banks[address]=debug.read_memory(address,equipment.PLAYER_CAPACITY)
    allocation=call(0x8009BFC0,[128])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-128:raise ValueError('Reward bridge allocation failed')
    bridge=allocation+16;raw=bytearray();entries={}
    for name in ('af_v3_reward_request','af_v3_reward_event','af_v3_reward_axe_wait_request'):
        entries[name]=bridge+len(raw);raw.extend(struct.pack('>4I',0x08000000|(receipt['requests']['symbols'][name]>>2&0x3FFFFFF),0,0,0))
    debug.write_memory(bridge,raw);call(0x8002FE00,[bridge,len(raw)]);call(0x80034CE0,[bridge,len(raw)])
    proof=(bridge,bytes(raw));edge=b'V3RA'*4
    guards=(allocation,allocation+112,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    def request(name,args,want=1):return call(entries['af_v3_reward_'+name],args,proof,want)
    expected_state=bytearray(saved[0x8046C000]);expected_state[0x350:0x380]=bytes(48)
    def finish(type):
        # Message rendering/timing has separate passing evidence. Simulate its
        # completed phase here to exercise the real request/settle transition.
        debug.write_memory(actor+0xD10,struct.pack('>f2I',42.0,3,type))
        dispatch(0x808DDB5C)
        check('completed report requests ordinary wait',actor+0xD00,struct.pack('>3I',7,1,1))
        dispatch(0x808DDA18);expected_state[0x358]|=1<<type
        check('registered settlement records the active celebration',0x8046C000,expected_state)
        check('returned to native wait',actor+0xCF0,struct.pack('>I',7))
    try:
        debug.write_memory(0x8046C000,expected_state);put(0x80136FD8,0x80126EC0)
        debug.write_memory(0x8013767D,bytes(2));debug.write_memory(0x80127908,b'\0')
        debug.write_memory(actor+0xE64,b'\1');put(actor+0xCF0,7);put(actor+0xD00,7,0,0)
        call(0x8005EB74,[0x80123E10])
        request('request',[game,118,3,31])
        check('first reward request data',actor+0xD00,struct.pack('>3I',118,31,1))
        check('first reward requested type',actor+0xD58,struct.pack('>I',3))
        request('request',[game,119,2,30],0)
        check('lower-priority request is rejected without changing type',actor+0xD58,struct.pack('>I',3))
        dispatch(0x808DDA18);check('actual first reward setup selected',actor+0xCF0,struct.pack('>I',118))
        dispatch(0x808DDB5C);check('real reward frame advances message timer',actor+0xD10,struct.pack('>f',2.0))
        finish(3)
        request('event',[game,1]);dispatch(0x808DDA18)
        check('actual second reward setup selected',actor+0xCF0,struct.pack('>I',119));finish(1)
        request('axe_wait_request',[game]);dispatch(0x808DDA18)
        check('actual axe wait selected',actor+0xCF0,struct.pack('>I',120))
        check('axe timer starts clear',actor+0xD10,bytes(4))
        dispatch(0x808DDB5C);check('native axe timer interval',actor+0xD10,struct.pack('>f',2.0))
        debug.write_memory(actor+0xD10,struct.pack('>f',318.0));dispatch(0x808DDB5C)
        check('axe reaches full source delay',actor+0xD10,struct.pack('>f',320.0))
        check('axe still waits at delay boundary',actor+0xCF0,struct.pack('>I',120))
        dispatch(0x808DDB5C)
        check('axe wait requests event celebration',actor+0xD00,struct.pack('>3I',119,34,1))
        dispatch(0x808DDA18);check('axe celebration selected',actor+0xCF0,struct.pack('>I',119));finish(0)
        check('callback tables and all installed code stay unchanged',equipment.RAM,module)
        for at in guards:check('reward action guard',at,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(actor,actor_before)
        for at,value in banks.items():debug.write_memory(at,value)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    check('live actor restored',actor,actor_before)
    for at,value in banks.items():check('live motion bank restored',at,value)
    for at,value in saved.items():check('live state restored',at,value)
    return dict(native_reward_actions=True,registered_indices=[118,119,120],assertions=assertions,
        temporary_callback_slots=False,test_only_jump_wrappers=True,simulated_report_completion=True,
        sampled_axe_delay=True,persistent_settlement_tested=True,ordinary_acquisition_tested=False,
        ordinary_gameplay_tested=False,hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)


def reward_controls(debug,rom_path,record):
    """Actual player setup/frame and fanfare requests through a retained native dispatcher."""
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed reward-control cartridge')
    resources=report['equipment_resources'];actions=resources['player_actions'];receipt=actions['reward_controls']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(reward_control_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(actual),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Reward control mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    def pointer(at,size):
        value=int.from_bytes(debug.read_memory(at,4),'big')
        if value&3 or not MODULE_RAM+0x8000<=value<=0x80400000-size:
            raise ValueError('Reward control fixture pointer outside native heap')
        return value
    start=resources['blob_offset'];module=blob[start:start+resources['bytes']]
    check('complete installed module',equipment.RAM,module)
    constructor=int.from_bytes(debug.read_memory(0x80143900,4),'big')
    owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data=files[equipment.PLAYER_VROM].extract(image);rel=files[equipment.PLAYER_RELOC].extract(image)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):
        raise ValueError('Reward controls need the actual loaded player owner')
    sections=struct.unpack_from('>5I',rel)
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete actual loaded player code',owner,expected[:sections[0]])
    dispatch=next(r for r in actions['tables'] if r['native_entry']==0x808DD9B4)
    footprint=next(r for r in actions['tables'] if r['native_entry']==0x808B828C)
    check('reward action has no settlement footprint callback',footprint['ram']+118,b'\0')
    slot=dispatch['ram']+118*4;original_slot=debug.read_memory(slot,4)
    if original_slot!=bytes(4):raise ValueError('Reward fixture requires a disabled callback slot')
    first,last=dispatch['native_entry']-equipment.PLAYER_RAM,dispatch['native_end']-equipment.PLAYER_RAM
    proof=(owner+first,expected[first:last])
    game=pointer(0x8010EF90,0x1E00);actor_bytes=resources['held_rig_actions']['player_allocation']['bytes']
    actor=pointer(game+0x1C90,actor_bytes);actor_before=debug.read_memory(actor,actor_bytes)
    bgm=0x80123E10
    saved={at:debug.read_memory(at,size) for at,size in
        ((bgm,0x154),(0x801458A0,64),(0x8046C000,864),(0x80126EC0,4*0xBD0))}
    banks={}
    for index in struct.unpack_from('>2h',actor_before,0xDA0):
        if not 0<=index<8:raise ValueError('Invalid live animation-bank selector')
        address=pointer(game+0x114+84*index,equipment.PLAYER_CAPACITY)
        banks[address]=debug.read_memory(address,equipment.PLAYER_CAPACITY)
    def routine(name):
        put(slot,receipt['code']['symbols']['af_v3_reward_'+name])
        return call(owner+first,[actor,game],proof)
    motion=next(r for r in resources['player_motion']['records'] if r['index']==258)
    segments=bytearray(saved[0x801458A0])
    try:
        # One representative exercises the shared native calls and restoration;
        # retain the recorded four-type evidence and host mapping checks.
        for kind,bgm_id in enumerate(receipt['fanfares']['type_bgms'][:1]):
            call(0x8005EB74,[bgm])
            debug.write_memory(actor+0xE64,b'\x01')
            put(actor+0xCF0,118);put(actor+0xD00,118,1,1);put(actor+0xD58,kind)
            routine('setup')
            check('setup preserves segment bases',0x801458A0,segments)
            check('reward action selected by real Base setup',actor+0xCF0,struct.pack('>I',118))
            check('reward state reset',actor+0xD10,struct.pack('>f2I',0.0,0,kind))
            check('complete native reward frame control',actor+0x174,struct.pack('>5fI',1,53,53,1,1,0))
            for bank in banks:
                check('complete source reward motion in native bank',bank,
                    blob[motion['blob_offset']:motion['blob_offset']+motion['bytes']])
            check('native fanfare request count',bgm+0xF0,struct.pack('>I',1))
            check('native source-selected fanfare number',bgm,bytes([bgm_id]))
            check('native source stop type',bgm+6,struct.pack('>H',0x168))
            check('native fanfare category and lifetime',bgm+8,struct.pack('>IhHB',0,-1,0,255))
            if kind==0:
                routine('main')
                check('actual animation advances once',actor+0x184,struct.pack('>f',2.0))
                check('message uses one native interval',actor+0xD10,struct.pack('>f2I',2.0,0,kind))
                check('reward remains active before its message',actor+0xCF0,struct.pack('>I',118))
                # Unchanged native cKF_SkeletonInfo_R_combine_play supplies
                # segment six for both layers. Its restoration helper writes
                # the second layer's prior base last: the lower animation bank.
                # This is normal native animation behaviour, not corruption.
                # Assert the exact bank and every other unchanged segment.
                lower=int.from_bytes(debug.read_memory(actor+0xDA4,4),'big')
                if lower not in banks:raise ValueError('Reward lower animation escaped its native bank')
                struct.pack_into('>I',segments,6*4,lower&0x1FFFFFFF)
                check('frame retains native lower-bank segment semantics',0x801458A0,segments)
            routine('stop_fanfare')
            check('native deletion retains selected fanfare identity',bgm,bytes([bgm_id]))
            check('native deletion stop type',bgm+4,struct.pack('>H',0x168))
            check('native deletion flag',bgm+14,struct.pack('>H',1))
        for at in (0x8046C000,0x80126EC0):check('saved data untouched',at,saved[at])
        check('only native animation segment selection changes',0x801458A0,segments)
    finally:
        debug.write_memory(slot,original_slot);debug.write_memory(actor,actor_before)
        for bank,value in banks.items():debug.write_memory(bank,value)
        debug.write_memory(bgm,saved[bgm])
        debug.write_memory(0x801458A0,saved[0x801458A0])
    check('complete shared module restored',equipment.RAM,module)
    check('live player restored',actor,actor_before)
    for bank,value in banks.items():check('live animation bank restored',bank,value)
    check('native BGM state restored',bgm,saved[bgm])
    check('fixture segment bases restored',0x801458A0,saved[0x801458A0])
    check('no CPU fault',0x8003CE34,bytes(4));check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    return dict(native_reward_setup=True,native_reward_main_frames=1,native_fanfare_requests=1,
        assertions=assertions,temporary_callback_slot=True,code_uploaded=False,
        balloon_reward_setup_tested=False,audio_output_auditioned=False,persistent_settlement_tested=False,
        ordinary_reward_event_tested=False,hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)


def reward_messages(debug,rom_path,record):
    """Run cartridge message callbacks through the existing native table dispatcher."""
    from aflib import CODE_RAM,CODE_VROM
    from textbanks import Bank
    from v3_event_text import MESSAGE,TABLE
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed reward-message cartridge')
    resources=report['equipment_resources'];actions=resources['player_actions'];receipt=actions['reward_messages']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);core=files[CODE_VROM].extract(image)
    messages=Bank('message',0,0,files[MESSAGE].extract(image),files[TABLE].extract(image)).entries()
    boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(reward_message_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(actual),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Reward message mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None,proof=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:
            result['assertion']='passed' if result['return_value']==want else 'failed';assertions+=1
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError(f'Reward message call {at:08X} mismatch')
        return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    at=resources['blob_offset'];module=blob[at:at+resources['bytes']]
    check('complete installed module',equipment.RAM,module)
    check('native demo pointer',0x80104A70,struct.pack('>I',0x80139C40))
    window=call(0x8009D1F0);demo=0x80139C40
    if window!=0x80142410:raise ValueError('Changed reward message window')
    saved={address:debug.read_memory(address,size) for address,size in
        ((demo,0x330),(window,0x330),(0x8046C000,864),(0x80126EC0,4*0xBD0))}
    constructor=int.from_bytes(debug.read_memory(0x80143900,4),'big')
    owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data=files[equipment.PLAYER_VROM].extract(image);rel=files[equipment.PLAYER_RELOC].extract(image)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):
        raise ValueError('Reward messages need the actual loaded player owner')
    sections=struct.unpack_from('>5I',rel)
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete actual loaded player code',owner,expected[:sections[0]])
    dispatch=next(r for r in actions['tables'] if r['native_entry']==0x808BE620)
    slot=dispatch['ram']+118*4;original_slot=debug.read_memory(slot,4)
    if original_slot!=bytes(4):raise ValueError('Reward fixture requires a disabled action slot')
    first,last=dispatch['native_entry']-equipment.PLAYER_RAM,dispatch['native_end']-equipment.PLAYER_RAM
    proof=(owner+first,expected[first:last])
    size=0x1C00;allocation=call(0x8009BFC0,[size]);actor=allocation+16;message=allocation+0x1500
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Reward-message allocation outside native heap')
    edge=b'V3RM'*4;guards=(allocation,actor+0x1400,message-16,message+0x410,allocation+size-16)
    for address in guards:debug.write_memory(address,edge)
    def routine(name,want=None):
        # This existing one-argument dispatcher leaves a1=1 for a valid index.
        # It exercises reset(type=net) and update(animation_ended=true); host
        # checks cover arbitrary second arguments and the unfinished animation.
        put(slot,receipt['code']['symbols']['af_v3_reward_message_'+name])
        return call(owner+first,[actor],want,proof)
    initial=bytearray(b'\xA5'*0x1400);struct.pack_into('>I',initial,0xCF0,118)
    try:
        for kind,number in enumerate(receipt['text']['type_messages']):
            value=bytearray(initial);struct.pack_into('>f2I',value,0xD10,42.0,0,kind)
            debug.write_memory(actor,value);demo_value=bytearray(0x330)
            struct.pack_into('>2I',demo_value,0xE0,actor,9);debug.write_memory(demo,demo_value)
            debug.write_memory(window,saved[window]);routine('begin')
            for offset,v in ((0xC,1),(0x2F8,5),(0x300,number),(0x30C,0)):
                struct.pack_into('>I',demo_value,offset,v)
            demo_value[0x318:0x31C]=bytes((185,245,80,255))
            check('official message and demo settings',demo,demo_value)
            window_value=bytearray(saved[window]);struct.pack_into('>I',window_value,0x2D0,1)
            struct.pack_into('>I',window_value,0x230,0xFFFFFFFF)
            check('native continue lock and cleared selection',window,window_value)
            check('begin retains complete actor',actor,value)
            debug.write_memory(message,b'\xA5'*0x410)
            call(0x8009E558,[message,number,0],1)
            check('complete actual cartridge message load',message,
                struct.pack('>4I',1,number,len(messages[number]),0)+messages[number])
        debug.write_memory(actor,initial);debug.write_memory(demo,bytes(0x330));routine('reset',1)
        value=bytearray(initial);struct.pack_into('>f2I',value,0xD10,0.0,0,1)
        check('native bounded reset',actor,value)
        for frame in range(21):
            routine('update',0);struct.pack_into('>f',value,0xD10,(frame+1)*2.0)
            check('native source-equivalent delay',actor,value)
        check('delay does not request a demo',demo,bytes(0x330))
        routine('update',0)
        check('actual report request',demo+0xF0,struct.pack('>3If',actor,9,
            receipt['code']['symbols']['af_v3_reward_message_begin'],1.0))
        check('request count and priority',demo+0x2F0,struct.pack('>2I',1,9))
        put(demo+0xE0,actor,9);routine('begin');routine('update',0)
        check('accepted report phase',actor+0xD14,struct.pack('>I',1))
        check('acceptance retains animation lock',window+0x2D0,struct.pack('>I',1))
        routine('update',0);check('finished animation releases lock',window+0x2D0,bytes(4))
        check('waiting for message close',actor+0xD14,struct.pack('>I',2))
        routine('update',0);check('open report retains waiting phase',actor+0xD14,struct.pack('>I',2))
        put(demo+0xE0,0,0);routine('update',0);routine('update',1)
        struct.pack_into('>f2I',value,0xD10,42.0,3,1)
        check('completed phase changes only reward state',actor,value)
        index=message+0x420;debug.write_memory(index,b'\xA5'*16)
        call(0x8009E388,[len(messages),index,index+4]);check('new count guard',index,bytes(8)+b'\xA5'*8)
        for address in guards:check('allocation guard',address,edge)
        for address in (0x8046C000,0x80126EC0):check('saved data untouched',address,saved[address])
    finally:
        debug.write_memory(slot,original_slot)
        for address in (demo,window):debug.write_memory(address,saved[address])
        call(0x8009C040,[allocation])
    check('complete shared module restored',equipment.RAM,module)
    for address in (demo,window):check('native message state restored',address,saved[address])
    check('no CPU fault',0x8003CE34,bytes(4));check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    return dict(native_reward_messages=True,complete_messages_loaded=4,assertions=assertions,
        temporary_callback_slot=True,animation_unfinished_tested=False,ordinary_reward_event_tested=False,
        hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)


def reward_motion(debug,rom_path,record):
    """Complete new motion DMA and native per-frame facial animation; no event claim."""
    from aflib import CODE_RAM,CODE_VROM
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed reward-motion cartridge')
    resources=report['equipment_resources'];motion=resources['player_motion'];faces=motion['faces']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);core=files[CODE_VROM].extract(image)
    boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(reward_motion_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(actual),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Reward motion mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None,proof=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:
            result['assertion']='passed' if result['return_value']==want else 'failed';assertions+=1
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError(f'Reward motion call {at:08X} mismatch')
        return result['return_value']
    def core_call(at,n,args=(),want=None):return call(at,args,want,(at,core[at-CODE_RAM:at-CODE_RAM+n]))
    at=resources['blob_offset'];check('complete installed module',equipment.RAM,blob[at:at+resources['bytes']])
    saved=debug.read_memory(0x8046C000,864);segments=debug.read_memory(0x801458A0,64)
    check('native segment zero remains absolute',0x801458A0,bytes(4))
    constructor=struct.unpack('>I',debug.read_memory(0x80143900,4))[0]
    owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data=files[equipment.PLAYER_VROM].extract(image);rel=files[equipment.PLAYER_RELOC].extract(image)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):
        raise ValueError('Reward motions need the actual game-loaded player owner')
    sections=struct.unpack_from('>5I',rel)
    expected=relocate_verified_data(SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections),data,rel,owner)
    check('complete actual loaded player code',owner,expected[:sections[0]])
    def owner_call(first,last,args=(),want=None):
        address=owner+first-equipment.PLAYER_RAM
        return call(address,args,want,(address,expected[first-equipment.PLAYER_RAM:last-equipment.PLAYER_RAM]))
    size=0x2600;allocation=call(0x8009BFC0,[size]);actor=allocation+16;target=allocation+0x1600
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Reward-motion fixture allocation outside native heap')
    edge=b'V3RM'*4;guards=(allocation,actor+0x1400,target-16,target+equipment.PLAYER_CAPACITY,allocation+size-16)
    for address in guards:debug.write_memory(address,edge)
    frames_checked=0
    try:
        for row in motion['reward_motion']['records']:
            index=row['index'];fill=b'\xA5'*equipment.PLAYER_CAPACITY;debug.write_memory(target,fill)
            owner_call(0x808B468C,0x808B46C4,[index],row['pointer'])
            owner_call(0x808B5B38,0x808B5B60,[index],row['type'])
            for entry,want in ((0x800B11B0,row['bytes']),(0x800B1264,0),(0x800B1D68,row['vrom'])):
                call(entry,[index],want)
            call(0x800B1D94,[target,index])
            asset=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            check('complete motion DMA and untouched bank tail',target,asset+fill[len(asset):])
            call(0x800B12A0,[index,target],target)
        face_rows={r['source_index']:r for r in faces['rows']}
        # Distinct actual facial timelines, including already installed fall/getup.
        selected={}
        for row in faces['rows']:
            if any(row['pointers']):selected.setdefault(tuple(row['pointers']),row)
        for row in selected.values():
            arrays=[]
            for column,pointer in enumerate(row['pointers']):
                entry=0x800B22A4+column*44;core_call(entry,44,[row['index']],pointer)
                if pointer:
                    offset=at+pointer-equipment.RAM;raw=blob[offset:offset+row['duration']]
                    check('complete resident facial sequence',pointer,raw)
                    core_call(0x8009ADA8,56,[pointer],pointer);arrays.append(raw)
                else:arrays.append(None)
            frames={0,1,row['duration'],row['duration']+1}
            seen=set()
            for frame in range(row['duration']):
                pair=tuple(raw[frame] if raw else None for raw in arrays)
                if pair not in seen:seen.add(pair);frames.add(frame+1)
            for frame in sorted(frames):
                value=bytearray(0x1400)
                struct.pack_into('>f',value,0x17C,float(row['duration']))
                struct.pack_into('>f',value,0x184,float(frame))
                struct.pack_into('>2I',value,0xCE8,7,5)
                struct.pack_into('>I',value,0xDA4,target);struct.pack_into('>I',value,0xDAC,row['index'])
                debug.write_memory(actor,value)
                owner_call(0x808B3828,0x808B3960,[actor])
                wanted=bytearray(value)
                if 1<=frame<=row['duration']:
                    for column,raw in enumerate(arrays):
                        if raw:struct.pack_into('>I',wanted,0xCE8+4*column,raw[frame-1])
                check('native facial frame writes only eye/mouth fields',actor,wanted);frames_checked+=1
                check('native consumer restores all segment bases',0x801458A0,segments)
        for index in (0,129,130,258,260,286,287,0xFFFFFFFF):
            for column,entry in enumerate((0x800B22A4,0x800B22D0)):
                if index<130:
                    table=0x8010C0E8+column*520;want=struct.unpack_from('>I',core,table-CODE_RAM+4*index)[0]
                else:want=face_rows.get(index-130,dict(pointers=[0,0]))['pointers'][column]
                core_call(entry,44,[index],want)
        for address in guards:check('fixture allocation guard',address,edge)
        check('unchanged complete shared module',equipment.RAM,blob[at:at+resources['bytes']])
        check('saved profile unchanged',0x8046C000,saved)
        check('no CPU fault',0x8003CE34,bytes(4));check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    finally:call(0x8009C040,[allocation])
    return dict(native_reward_motion_dma=True,native_facial_frames=frames_checked,assertions=assertions,
                skeletal_playback_tested=False,ordinary_reward_event_tested=False,hardware_tested=False,
                flash_written=False,requires_checkpoint_restore=True)


def player_motion(debug,rom_path,record):
    """Load the actual player owner and exercise its shared animation category."""
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed player-motion cartridge')
    resources=report['equipment_resources'];motion=resources['player_motion']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(player_motion_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Player motion mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None,proof=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:
            result['assertion']='passed' if result['return_value']==want else 'failed';assertions+=1
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError(f'Player motion call {at:08X} mismatch')
        return result['return_value']
    at=resources['blob_offset'];check('complete extended resident module',equipment.RAM,blob[at:at+resources['bytes']])
    saved=debug.read_memory(0x8046C000,864)
    constructor=struct.unpack('>I',debug.read_memory(0x80143900,4))[0]
    owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data=files[equipment.PLAYER_VROM].extract(image);reloc=files[equipment.PLAYER_RELOC].extract(image)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):
        raise ValueError('Native player constructor does not identify a loaded owner')
    controls=resources.get('player_actions',{}).get('fan_control_flow')
    size=0x6100 if controls else 0x1100
    allocation=call(0x8009BFC0,[size]);target=allocation+16
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Player-motion allocation outside native heap')
    sections=struct.unpack_from('>5I',reloc)
    spec=SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections)
    expected=relocate_verified_data(spec,data,reloc,owner)
    edge=b'V3PM'*4;end=target+(0x12D8 if controls else equipment.PLAYER_CAPACITY)
    for address in (allocation,target-16,end,allocation+size-16):debug.write_memory(address,edge)
    try:
        check('actual game-loaded player code and relocations',owner,expected[:sections[0]])
        record(dict(game_loaded_player_owner=f'{owner:08X}',constructor=f'{constructor:08X}'))
        actions=resources.get('player_actions')
        if actions and actions.get('equipment_selection'):
            from aflib import CODE_RAM,CODE_VROM
            selection=actions['equipment_selection'];core=files[CODE_VROM].extract(image)
            parents=resources.get('parent_readers');text_buffer=allocation+0x1800
            if parents:
                reader=report['clothing']['display']['readers']['code']
                check('complete selected parent wrapper',0x80466C00,blob[0x6C00:0x6C00+reader['bytes']])
                parent_rows={r['item_id']:r for r in parents['rows']}
                name_code=files[runtime.MODULE].extract(image)
                name_entry=0x801969C8;name_offset=name_entry-MODULE_RAM
                # Resident entry calls use the harness's linked-module bounds;
                # the separate verified-code escape accepts only other owners.
                check('complete resident public item-name entry',name_entry,
                      name_code[name_offset:name_offset+0x16C])
                price_entry=0x800C0194
                price_proof=(price_entry,core[price_entry-CODE_RAM:price_entry-CODE_RAM+0x2FC])
                def parent_check(row,enabled):
                    item=int(row['item_id'],16);sentinel=b'V3PI'*5
                    debug.write_memory(text_buffer,sentinel)
                    call(name_entry,[text_buffer+2,16,item],int(enabled))
                    want=parent_rows[row['item_id']]['name'].encode('ascii').ljust(16,b' ')
                    check('parent name and adjacent guard' if enabled else 'unselected parent writes nothing',
                          text_buffer,sentinel[:2]+want+sentinel[-2:] if enabled else sentinel)
                    call(price_entry,[item],parent_rows[row['item_id']]['price'] if enabled else 0,price_proof)
            def owner_call(entry,args=(),want=None,end=0x808BD584):
                address=owner+entry-equipment.PLAYER_RAM
                return call(address,args,want,(address,expected[entry-equipment.PLAYER_RAM:end-equipment.PLAYER_RAM]))
            def core_call(entry,end):
                return call(entry,proof=(entry,core[entry-CODE_RAM:end-CODE_RAM]))
            title=core_call(0x8007D90C,0x8007D91C)
            if title:
                pointer=core_call(0x800B593C,0x800B594C);field=pointer+0x3C
            else:
                pointer=struct.unpack('>I',debug.read_memory(0x80136FD8,4))[0];field=pointer+0x3EC
            if pointer&3 or not 0x80000400<=pointer<=field<=0x80400000-2:
                raise ValueError('Current native equipment source is not initialized')
            profile_address=0x80460020;scene_address=0x80126EB4
            before_profile=debug.read_memory(profile_address,192)
            before_item=debug.read_memory(field,2);before_scene=debug.read_memory(scene_address,4)
            debug.write_memory(target,bytes(0x12D8))
            permission=next(r for r in actions['tables'] if r['native_entry']==0x808B63EC)
            kinds=blob[at+permission['offset']:at+permission['offset']+permission['bytes']]
            modes={value:kinds.index(value) for value in (0,1,3)}
            record(dict(selection_source='title-demo' if title else 'player-private',
                        equipped_field=f'{field:08X}',permission_actions=modes))
            def select(item):debug.write_memory(field,struct.pack('>H',item))
            try:
                debug.write_memory(scene_address,bytes(4))
                native_kinds=original_equipment_kinds((runtime.ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
                native_cases=[(item,native_kinds[item-0x2200]) for item in (0x2200,0x2201,0x2202,0x2223)]
                for item,want in native_cases+[(item,0xFFFFFFFF) for item in (0,0x2224,0x2253,0xFFFF)]:
                    select(item);owner_call(0x808BD3F8,want=want)
                for row in selection['rows']:
                    item=int(row['item_id'],16);select(item)
                    owner_call(0x808BD3F8,want=0xFFFFFFFF)
                    if parents:parent_check(row,False)
                    active=bytearray(before_profile);active[row['profile_byte']]|=row['profile_mask']
                    debug.write_memory(profile_address,active)
                    owner_call(0x808BD3F8,want=row['native_kind'])
                    if parents:parent_check(row,True)
                    debug.write_memory(profile_address,before_profile)
                row=selection['rows'][0];select(int(row['item_id'],16))
                active=bytearray(before_profile);active[row['profile_byte']]|=row['profile_mask']
                debug.write_memory(profile_address,active)
                if parents:
                    debug.write_memory(text_buffer,b'V3PI'*5)
                    call(name_entry,[text_buffer+2,15,int(row['item_id'],16)],0)
                    check('undersized parent name destination unchanged',text_buffer,b'V3PI'*5)
                for mode,action in modes.items():
                    owner_call(0x808BD5C4,[target,action],row['native_kind'] if mode in (0,1) else 0xFFFFFFFF,
                               end=0x808BD668)
                debug.write_memory(target+0xE64,b'\x01')
                owner_call(0x808BD5C4,[target,modes[0]],0xFFFFFFFF,end=0x808BD668)
                debug.write_memory(target+0xE65,b'\x01')
                owner_call(0x808BD5C4,[target,modes[0]],0xFFFFFFFF,end=0x808BD668)
                debug.write_memory(target+0xE64,b'\0')
                owner_call(0x808BD5C4,[target,modes[3]],row['native_kind'],end=0x808BD668)
                # No scene permits an out-of-range scene index, even with the
                # demo visibility override. The actual scene getter owns this.
                debug.write_memory(scene_address,struct.pack('>I',35))
                owner_call(0x808BD5C4,[target,modes[0]],0xFFFFFFFF,end=0x808BD668)
            finally:
                debug.write_memory(profile_address,before_profile);debug.write_memory(field,before_item)
                debug.write_memory(scene_address,before_scene)
            check('selected-equipment profile restored',profile_address,before_profile)
            check('native equipment source restored',field,before_item)
            check('native scene restored',scene_address,before_scene)
            check('selected-equipment saved state unchanged',0x8046C000,saved)
            for address in (allocation,end,allocation+size-16):check('selected-equipment scratch guard',address,edge)
            check('selected-equipment no CPU fault',0x8003CE34,bytes(4))
            check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
            check('equipment module footer',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
            return dict(native_selected_equipment=True,native_passive_permissions=True,assertions=assertions,
                native_parent_names_prices=bool(parents),
                selection_source='title-demo' if title else 'player-private',ordinary_inventory_tested=False,
                ordinary_equipped_fan_tested=False,hardware_tested=False,flash_written=False,
                requires_checkpoint_restore=True)
        if actions and actions.get('fan_activation'):
            def owner_call(entry,args=(),want=None,end=None):
                if end is None:end=next(t['native_end'] for t in actions['tables'] if t['native_entry']==entry)
                address=owner+entry-equipment.PLAYER_RAM
                return call(address,args,want,(address,expected[entry-equipment.PLAYER_RAM:end-equipment.PLAYER_RAM]))
            for row in actions['tables']:
                if row['width']==4:
                    check('complete activated action callback table',row['ram'],
                          blob[at+row['offset']:at+row['offset']+row['bytes']])
            for index in (105,120,121,0xFFFFFFFF):
                actor=bytearray(0x12D8);struct.pack_into('>I',actor,0xD00,index);struct.pack_into('>I',actor,0xD08,1)
                debug.write_memory(target,actor)
                owner_call(0x808DDA18,[target,0],0)
                check('unfinished action remains rejected without actor writes',target,actor)
            actor=bytearray(0x12D8);struct.pack_into('>I',actor,0xCF0,109)
            debug.write_memory(target,actor)
            owner_call(0x808BE140,[target],end=0x808BE184)
            reset=debug.read_memory(target,len(actor));debug.write_memory(target,actor)
            owner_call(0x808BE620,[target])
            check('fan dispatch uses the complete original net reset',target,reset)
            real_game=struct.unpack('>I',debug.read_memory(0x8010EF90,4))[0]
            if real_game&3 or not 0x80000400<=real_game<=0x80400000-0x1E00:
                raise ValueError('Fan action dispatch requires the live game')
            real_actor=struct.unpack('>I',debug.read_memory(real_game+0x1C90,4))[0]
            if real_actor&3 or not 0x80000400<=real_actor<=0x80400000-0x12D8:
                raise ValueError('Fan action dispatch requires the initialized live player')
            actor_before=debug.read_memory(real_actor,0x12D8);banks={}
            for index in struct.unpack_from('>2h',actor_before,0xDA0):
                if not 0<=index<8:raise ValueError('Unbounded live animation bank')
                address=struct.unpack('>I',debug.read_memory(real_game+0x114+84*index,4))[0]
                if address&15 or not 0x80000400<=address<=0x80400000-equipment.PLAYER_CAPACITY:
                    raise ValueError('Live animation bank escapes native RAM')
                banks[address]=debug.read_memory(address,equipment.PLAYER_CAPACITY)
            try:
                record(dict(fan_dispatch_original_action=struct.unpack_from('>I',actor_before,0xCF0)[0],
                    original_equipment_kind=struct.unpack_from('>b',actor_before,0x1117)[0]))
                debug.write_memory(real_actor+0xE64,b'\x01')
                debug.write_memory(real_actor+0xD00,struct.pack('>3I',109,4,1))
                debug.write_memory(real_actor+0xD58,struct.pack('>I',1))
                owner_call(0x808DDA18,[real_actor,real_game],1)
                check('native setup dispatcher accepts action 109',real_actor+0xCF0,struct.pack('>I',109))
                check('dispatched fan uses the complete swing',real_actor+0xDAC,struct.pack('>2I',270,0))
                owner_call(0x808DDB5C,[real_actor,real_game])
                check('native main dispatcher advances the fan frame',real_actor+0x184,struct.pack('>f',2))
                check('native main dispatcher advances native morph',real_actor+0x194,struct.pack('>f',-4))
                for _ in range(6):owner_call(0x808DDB5C,[real_actor,real_game])
                check('dispatched complete swing reaches its release frame',real_actor+0x184,struct.pack('>f',8))
                check('dispatched complete swing changes bee state',real_actor+0x11B7,b'\x01')
                next_action=struct.unpack('>I',debug.read_memory(real_actor+0xD00,4))[0]
                if next_action not in (7,8):
                    # With no stick input, the donor's idle event is the last
                    # half-frame. Native playback crosses that event at wrap.
                    owner_call(0x808DDB5C,[real_actor,real_game])
                    next_action=struct.unpack('>I',debug.read_memory(real_actor+0xD00,4))[0]
                record(dict(dispatched_fan_exit_request=next_action,
                    frame=struct.unpack('>f',debug.read_memory(real_actor+0x184,4))[0]))
                if next_action not in (7,8):raise ValueError('Released fan did not request normal movement/idle')
                owner_call(0x808DDB5C,[real_actor,real_game])
                check('native action cycle exits the fan',real_actor+0xCF0,struct.pack('>I',next_action))
                check('native action cycle has no CPU fault',0x8003CE34,bytes(4))
            finally:
                for address,value in banks.items():debug.write_memory(address,value)
                debug.write_memory(real_actor,actor_before)
            check('live actor restored after dispatch cycle',real_actor,actor_before)
            for address,value in banks.items():check('live motion bank restored after dispatch cycle',address,value)
            for address in (allocation,end,allocation+size-16):check('fan dispatch private-memory guard',address,edge)
            check('fan dispatch retains saved profile',0x8046C000,saved)
            check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
            check('equipment module footer',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
            return dict(native_fan_setup_main_net_and_exit_dispatch=True,assertions=assertions,
                ordinary_equipment_selection_tested=False,hardware_tested=False,flash_written=False,
                requires_checkpoint_restore=True)
        if actions and actions.get('held_dispatch'):
            held=actions['held_dispatch'];symbols=actions['code']['symbols']
            bridge=allocation+0x1400;game=allocation+0x2000;graph=allocation+0x2300;commands=allocation+0x2800
            for row in held['tables']:
                check('complete held-item callback category',row['ram'],
                      blob[at+row['offset']:at+row['offset']+row['bytes']])
            actor=bytearray(0x12D8);debug.write_memory(target,actor)
            real_game=struct.unpack('>I',debug.read_memory(0x8010EF90,4))[0]
            if real_game&3 or not 0x80000400<=real_game<=0x80400000-0x1E00:
                raise ValueError('Held dispatcher requires the live game for original common callbacks')
            main=held['tables'][0];address=owner+main['native_entry']-equipment.PLAYER_RAM
            proof=(address,expected[address-owner:main['native_end']-equipment.PLAYER_RAM])
            # The original static callback and imported static category use
            # the same full common path and the new v1 relocation thunk.
            for index in (1,20,21,22,23,24,0xFFFFFFFF):
                debug.write_memory(target+0xCFC,struct.pack('>I',index))
                call(address,[target,real_game],0,proof)
            debug.write_memory(game,struct.pack('>I',graph))
            debug.write_memory(graph,bytes(0x300))
            for p in (bridge-16,bridge+8,commands-16,commands+16):debug.write_memory(p,edge)
            stub=struct.pack('>2I',equipment.jump(symbols['af_v3_player_draw_static_item']),0)
            debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            for bank in (0,1):
                kind=next(r for r in resources['kind_readers']['rows'] if r['native_kind']==107+bank)
                shape=kind['fields'][2];model=next(r for r in resources['records'] if r['index']==shape)
                debug.write_memory(target+0xDEC,struct.pack('>I',bank))
                debug.write_memory(target+0xDDC+bank*4,struct.pack('>I',shape))
                debug.write_memory(target+0xF44,struct.pack('>I',1))
                debug.write_memory(graph+0x298,struct.pack('>I',commands));debug.write_memory(commands,edge)
                call(bridge,[target,game],proof=(bridge,stub))
                check('static held model command and untouched following bytes',commands,
                      struct.pack('>2I',0xDE000000,model['pointer'])+edge[8:])
                check('opaque draw cursor advances once',graph+0x298,struct.pack('>I',commands+8))
                check('static held draw clears rod-tip flag',target+0xF44,bytes(4))
            for bank,shape in ((0,0x7FFF),(2,0),(0xFFFFFFFF,0)):
                debug.write_memory(target+0xDEC,struct.pack('>I',bank))
                debug.write_memory(target+0xDDC,struct.pack('>I',shape))
                debug.write_memory(target+0xF44,struct.pack('>I',1))
                debug.write_memory(graph+0x298,struct.pack('>I',commands));debug.write_memory(commands,edge)
                call(bridge,[target,game],proof=(bridge,stub))
                check('missing model or bank emits no command',commands,edge)
                check('missing model or bank preserves draw cursor',graph+0x298,struct.pack('>I',commands))
                check('missing model or bank still clears rod-tip flag',target+0xF44,bytes(4))
            for p in (bridge-16,bridge+8,commands-16,commands+16,allocation,end,allocation+size-16):
                check('held dispatcher private-memory guard',p,edge)
            check('held dispatcher saved profile unchanged',0x8046C000,saved)
            check('held dispatcher has no CPU fault',0x8003CE34,bytes(4))
            check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
            check('equipment module footer',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
            return dict(native_held_main_dispatch=True,native_static_held_draw_callback=True,
                assertions=assertions,full_scene_render_tested=False,ordinary_equipped_fan_tested=False,
                hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)
        if controls:
            # Exercise new control/setup code in this same category probe.
            # The fake game owns an isolated full-size actor, two native-sized
            # animation banks, and a player pointer. No live actor is edited.
            game=allocation+0x2000;upper=allocation+0x4000;lower=allocation+0x5000
            game_data=bytearray(0x1E00)
            struct.pack_into('>I',game_data,0x1C90,target)
            for index,bank in enumerate((upper,lower)):
                struct.pack_into('>I',game_data,0x114+84*index,bank)
                debug.write_memory(bank,bytes([0xA5])*equipment.PLAYER_CAPACITY)
                debug.write_memory(bank-16,edge);debug.write_memory(bank+equipment.PLAYER_CAPACITY,edge)
            debug.write_memory(game,game_data)
            actor=bytearray(0x12D8)
            struct.pack_into('>I',actor,0xCF0,7)
            struct.pack_into('>2h',actor,0xDA0,0,1)
            for field in (0xDAC,0xDB0,0xDB4):struct.pack_into('>i',actor,field,-1)
            # Suppress held equipment through the real native override flag;
            # fan inventory selection is deliberately not installed yet.
            actor[0xE64]=1
            debug.write_memory(target,actor)
            symbols=actions['code']['symbols'];bridge=allocation+0x1400
            debug.write_memory(bridge-16,edge);debug.write_memory(bridge+8,edge)
            def control_call(name,args,want=None):
                # The existing debugger's verified-call range is low RAM.
                # Its ordinary eight-byte jump bridge reaches the independently
                # compared cartridge-loaded Expansion Pak code above.
                stub=struct.pack('>2I',equipment.jump(symbols[name]),0)
                debug.write_memory(bridge,stub)
                call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
                return call(bridge,args,want,(bridge,stub))
            for trigger in (0,1):control_call('af_v3_player_fan_controller',[game,trigger],0)
            check('missing or hidden fan does not change actor',target,actor)
            control_call('af_v3_player_fan_request',[game,1,4],1)
            check('fan request fields',target+0xD00,struct.pack('>3I',109,4,1))
            check('fan request union',target+0xD58,struct.pack('>2I',1,0))
            rejected=debug.read_memory(target,len(actor))
            control_call('af_v3_player_fan_request',[game,0,4],0)
            check('equal-priority request leaves actor unchanged',target,rejected)
            segment=debug.read_memory(0x801458B8,4)
            control_call('af_v3_player_fan_setup',[target,game])
            check('fan setup and prior action',target+0xCF0,struct.pack('>2I',109,7))
            check('fan eye pattern',target+0xCE8,struct.pack('>I',5))
            check('full upper animation frame control',target+0x174,
                  struct.pack('>5fI',1,9,9,controls['frame_speed'],1,1))
            check('fan upper morph',target+0x194,struct.pack('>f',-5))
            check('fan explicit part mask',target+0x10FC,bytes.fromhex(motion['mask_hex']))
            swing=next(r for r in motion['records'] if r['index']==270)
            check('complete swing DMA inside private bank',upper,
                blob[swing['blob_offset']:swing['blob_offset']+swing['bytes']]+bytes([0xA5])*(equipment.PLAYER_CAPACITY-swing['bytes']))
            check('native segment-six binding restored',0x801458B8,segment)
            debug.write_memory(target+0xD58,bytes(4));debug.write_memory(target+0x1F4,struct.pack('>f',12.5))
            control_call('af_v3_player_fan_setup',[target,game])
            check('repeat preserves lower frame',target+0x1F4,struct.pack('>f',12.5))
            check('repeat removes upper morph',target+0x194,bytes(4))
            check('repeat removes lower morph',target+0x204,bytes(4))
            debug.write_memory(target+0x184,struct.pack('>f',7.5))
            control_call('af_v3_player_fan_finish',[target,game])
            check('fan bee response timing',target+0x11B7,b'\x01')
            # Title-demo movement remains live even though this isolated actor
            # is not in the scene. Match the real controller, not assumed idle.
            if call(0x8007D90C):controller=call(0x800B593C)
            else:controller=struct.unpack('>I',debug.read_memory(0x8010EF90,4))[0]+0xA8
            axes=struct.unpack('>2f',debug.read_memory(controller,8));moving=any(axes)
            record(dict(fan_transition_controller_axes=list(axes),expected_action=8 if moving else 7))
            debug.write_memory(target+0x184,struct.pack('>f',8.5))
            control_call('af_v3_player_fan_finish',[target,game])
            check('released fan respects movement and request priority',target+0xD00,struct.pack('>3I',8 if moving else 7,1,1))
            if moving:check('native walk argument adaptation',target+0xD64,struct.pack('>fI',-5,0))
            else:check('native wait argument adaptation',target+0xD58,struct.pack('>fI',-5,2))
            sound_result=None;frame_result=None
            if actions.get('fan_frame_flow'):
                sound_result=sound_programs_probe(debug,image,resources,check,call,record)
                check('player owner retained across audio frames',0x80143900,struct.pack('>I',constructor))
                real_game=struct.unpack('>I',debug.read_memory(0x8010EF90,4))[0]
                if real_game&3 or not 0x80000400<=real_game<=0x80400000-0x1E00:
                    raise ValueError('Per-frame probe requires the live play-game owner')
                real_actor=struct.unpack('>I',debug.read_memory(real_game+0x1C90,4))[0]
                if real_actor&3 or not 0x80000400<=real_actor<=0x80400000-0x12D8:
                    raise ValueError('Per-frame probe requires the actual initialized player')
                # Collision and skeleton updates require a real actor. The
                # enclosing checkpoint isolates this call; restore its actor
                # and both animation banks before returning to ordinary play.
                actor_before=debug.read_memory(real_actor,0x12D8);banks={}
                for index in struct.unpack_from('>2h',actor_before,0xDA0):
                    if not 0<=index<8:raise ValueError('Unbounded live animation-bank selector')
                    address=struct.unpack('>I',debug.read_memory(real_game+0x114+84*index,4))[0]
                    if address&15 or not 0x80000400<=address<=0x80400000-equipment.PLAYER_CAPACITY:
                        raise ValueError('Live animation bank escapes native RAM')
                    banks[address]=debug.read_memory(address,equipment.PLAYER_CAPACITY)
                try:
                    debug.write_memory(real_actor+0xE64,b'\x01')
                    debug.write_memory(real_actor+0xD00,struct.pack('>3I',109,4,1))
                    debug.write_memory(real_actor+0xD58,struct.pack('>I',1))
                    control_call('af_v3_player_fan_setup',[real_actor,real_game])
                    control_call('af_v3_player_fan_main',[real_actor,real_game])
                    check('per-frame native animation advancement',real_actor+0x184,struct.pack('>f',2))
                    check('per-frame native morph advancement',real_actor+0x194,struct.pack('>f',-4))
                    check('per-frame action remains fan',real_actor+0xCF0,struct.pack('>I',109))
                    check('per-frame callback has no CPU fault',0x8003CE34,bytes(4))
                    frame_result=dict(native_main_called=True,live_collision_and_skeleton=True,
                        action_table_dispatched=False,ordinary_equipped_fan_tested=False)
                finally:
                    for address,value in banks.items():debug.write_memory(address,value)
                    debug.write_memory(real_actor,actor_before)
                check('live player restored after per-frame check',real_actor,actor_before)
                for address,value in banks.items():check('live animation bank restored',address,value)
            for bank in (upper,lower):
                for address in (bank-16,bank+equipment.PLAYER_CAPACITY):check('private animation bank guard',address,edge)
            for address in (bridge-16,bridge+8):check('private call bridge guard',address,edge)
            for address in (allocation,target-16,end,allocation+size-16):check('private actor/game guard',address,edge)
            check('saved profile unchanged',0x8046C000,saved)
            check('no CPU fault',0x8003CE34,bytes(4))
            check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
            check('equipment guard',equipment.RAM+equipment.SIZE-16,struct.pack('>4I',*([equipment.GUARD]*4)))
            check('extended module footer',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
            return dict(native_fan_controls_setup_transitions=True,assertions=assertions,
                shared_sound=sound_result,per_frame_callback=frame_result,
                positive_equipped_controller_tested=False,fan_action_dispatched=False,
                ordinary_gameplay_tested=False,hardware_tested=False,flash_written=False,
                requires_checkpoint_restore=True)
        if actions:
            # Reuse this loaded-owner probe for the shared action-table category.
            # No live player, save, or callback table is edited.
            def owner_call(entry,args=(),want=None):
                finish=next((t['native_end'] for t in actions['tables'] if t['native_entry']==entry),None)
                if finish is None:raise ValueError('Action probe needs a complete consumer binding')
                address=owner+entry-equipment.PLAYER_RAM
                return call(address,args,want,(address,expected[entry-equipment.PLAYER_RAM:finish-equipment.PLAYER_RAM]))
            for entry,missing in ((0x808B35C8,-1),(0x808B63B4,0),(0x808B87C8,0)):
                table=next(t for t in actions['tables'] if t['native_entry']==entry)
                values=blob[at+table['offset']:at+table['offset']+table['bytes']]
                for index in (7,104,105,109,120,121,0xFFFFFFFF):
                    value=values[index] if index<121 else missing
                    if value>=128:value-=256
                    owner_call(entry,[index],value&0xFFFFFFFF)
            for index in (105,109,120,121,0xFFFFFFFF):
                actor=bytearray(equipment.PLAYER_CAPACITY)
                struct.pack_into('>I',actor,0xD00,index);struct.pack_into('>I',actor,0xD08,1)
                debug.write_memory(target,actor)
                owner_call(0x808DDA18,[target,0],0)
                check('unfinished action cannot start or change its actor',target,actor)
            # Compare one real original net dispatch with the same native
            # callback called directly. Its scratch actor uses no live state.
            actor=bytearray(equipment.PLAYER_CAPACITY);struct.pack_into('>I',actor,0xCF0,7)
            debug.write_memory(target,actor)
            linked=struct.unpack_from('>I',data,0x808DF628-equipment.PLAYER_RAM+7*4)[0]
            if linked!=0x808BE140:raise ValueError('Changed representative native action callback')
            callback=owner+linked-equipment.PLAYER_RAM
            call(callback,[target],proof=(callback,expected[callback-owner:callback-owner+68]))
            direct=debug.read_memory(target,len(actor));debug.write_memory(target,actor)
            owner_call(0x808BE620,[target]);check('original callback through relocated shared dispatch',target,direct)
            # Exercise both call-register variants with a native linked target
            # and a resident imported target. Only these 16-byte call bridges
            # are uploaded; all getters and dispatch code come from the ROM.
            bridge=allocation+0x1000
            priority=next(t for t in actions['tables'] if t['native_entry']==0x808B35C8)
            native_want=blob[at+priority['offset']+7]
            extra_want=next(r for r in resources['kind_readers']['rows'] if r['native_kind']==44)['fields'][0]
            for register,name in ((2,'af_v3_player_action_v0'),(25,'af_v3_player_action_t9')):
                for dest,args,want in ((0x808B35C8,[7],native_want),
                        (resources['code']['symbols']['af_v3_equipment_kind_field'],[44,0],extra_want)):
                    stub=struct.pack('>4I',0x3C000000|register<<16|dest>>16,
                        0x34000000|register<<21|register<<16|dest&65535,
                        equipment.jump(actions['code']['symbols'][name]),0)
                    debug.write_memory(bridge,stub)
                    call(0x8002FE00,[bridge,len(stub)]);call(0x80034CE0,[bridge,len(stub)])
                    call(bridge,args,want&0xFFFFFFFF,(bridge,stub))
            check('extended module footer',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
        pointer=owner+0x808B468C-equipment.PLAYER_RAM;part=owner+0x808B5B38-equipment.PLAYER_RAM
        pointer_proof=(pointer,expected[pointer-owner:pointer-owner+56])
        part_proof=(part,expected[part-owner:part-owner+40])
        kinds=resources.get('kind_readers')
        if kinds:
            kind_rows={r['native_kind']:r for r in kinds['rows']}
            for hook in kinds['owner_hooks']:
                address=owner+hook['entry']-equipment.PLAYER_RAM
                proof=(address,expected[address-owner:address-owner+40])
                # Shared reader categories, original tools, and both invalid bounds.
                for kind in (0,1,35,44,99,107,0xFFFFFFFF,115):
                    if kind<36:
                        value=bytes.fromhex(hook['table_hex'])[kind]
                        if hook['field']!='player_animation' and value>=128:value-=256
                    elif kind in kind_rows:value=kind_rows[kind]['fields'][hook['column']]
                    else:value=hook['missing']
                    call(address,[kind],value&0xFFFFFFFF,proof)
        # New transition motions when present; otherwise representative holding,
        # toy, idle, and waving resources. Preserve prior unchanged DMA evidence.
        selected={}
        for row in kinds['new_player_motions'] if kinds else motion['records']:
            key=(bool(row['source']['keyed_channels']),row['type'],row['source']['duration'])
            selected.setdefault(key,row)
        rows=list(selected.values());native=files[0x00B36000].extract(image)
        for index in (0,129):
            origin=motion['bounds'][index]-0x06000000+8;n=motion['bounds'][index+1]-motion['bounds'][index]-8
            rows.append(dict(index=index,origin=origin,bytes=n,vrom=0x00B36000+origin,
                pointer=struct.unpack_from('>I',data,0x808DE268-equipment.PLAYER_RAM+4*index)[0],
                type=data[0x808DE4C4-equipment.PLAYER_RAM+index],expected=native[origin:origin+n]))
        for row in rows:
            index=row['index'];origin=row.get('origin',0)
            call(pointer,[index],row['pointer'],pointer_proof);call(part,[index],row['type'],part_proof)
            for address,want in ((0x800B11B0,row['bytes']),(0x800B1264,origin),(0x800B1D68,row['vrom'])):
                call(address,[index],want)
            fill=bytes([0xA5])*equipment.PLAYER_CAPACITY;debug.write_memory(target,fill)
            call(0x800B1D94,[target,index])
            wanted=row.get('expected')
            if wanted is None:wanted=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            check('complete player animation DMA and untouched tail',target,wanted+fill[len(wanted):])
            call(0x800B12A0,[index,target],target-origin)
        masks=files[0x00B8A000].extract(image)
        for index in range(5):
            debug.write_memory(target,bytes([0xA5])*32);call(0x800B1DE8,[target,index])
            mask=masks[index*28:index*28+27] if index<4 else bytes.fromhex(motion['mask_hex'])
            check('native or donor split-body mask',target,mask+bytes([0xA5])*5)
        for index in (0xFFFFFFFF,130,287):
            call(pointer,[index],0,pointer_proof);call(part,[index],0xFFFFFFFF,part_proof);call(0x800B11B0,[index],0)
        for row in (resources['records'][0],):
            call(0x800B12C8,[row['index']],row['pointer']);call(0x800B131C,[row['index']],row['bytes'])
        call(0x800B12C8,[0],resources['native_contract']['pointers'][0])
        for address in (allocation,target-16,end,allocation+size-16):check('private owner or animation guard',address,edge)
        check('saved profile unchanged',0x8046C000,saved)
        check('no CPU fault',0x8003CE34,bytes(4));check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
        check('equipment guard',equipment.RAM+equipment.SIZE-16,struct.pack('>4I',*([equipment.GUARD]*4)))
    finally:call(0x8009C040,[allocation])
    return dict(native_player_motion_resources=True,representative_transfers=len(rows),part_masks=5,
        assertions=assertions,player_actions_tested=False,ordinary_menu_reload_tested=False,
        kind_readers_tested=bool(resources.get('kind_readers')),
        extended_action_tables_tested=bool(resources.get('player_actions')),
        hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)
