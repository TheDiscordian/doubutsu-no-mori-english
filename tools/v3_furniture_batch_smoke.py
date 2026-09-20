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
    saved={at:debug.read_memory(at,n) for at,n in ((0x801458B8,4),(0x8046C000,864))}
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
    try:
        call(0x800262D0,[VROM,VROM+len(data),OWNER_RAM,OWNER_RAM+resident,root,root+resident,len(rel)])
        check('complete cartridge-loaded relocated inventory owner',root,loaded)
        # The loader uses the following bytes for relocation scratch. Protect
        # the BSS boundary only once relocation has finished using that space.
        check('native overlay loader scratch guard',root+resident+len(rel),edge)
        debug.write_memory(root+resident,edge)
        put(submenu+0x2C,overlay);put(overlay+0x106DC,bss);put(game,graph)
        initialize(1);check('original tool animation timing retained',bss+0x224+12,struct.pack('>2f',1,2))
        for row in representatives:
            model=resources[row['fields']['shape']];motion=resources[row['fields']['item_animation']]
            fill=b'\xA5'*0x4000;debug.write_memory(bank,fill);initialize(row['preview_kind'])
            wanted=(blob[model['blob_offset']:model['blob_offset']+model['bytes']]+
                    blob[motion['blob_offset']:motion['blob_offset']+motion['bytes']])
            check('complete native model/animation transfers and untouched tail',bank,wanted+fill[len(wanted):])
            speed=row['native_frame_speed']
            check('source-correct preview speed and first frame',bss+0x224+12,struct.pack('>2f',speed,1+speed))
            check('native inventory work and morph pointers',bss+0x224+0x24,
                  struct.pack('>2I',bss+work['joint_offset'],bss+work['morph_offset']))
            put(0x801458B8,word(overlay+0x10030)&0x1FFFFFFF);call(0x800E0284,[identity])
            put(graph+0x298,gfx,gfx+0x1000);put(graph+0x2A8,xlu,xlu+0x600)
            if OWNER_RAM<=row['draw_callback']<OWNER_RAM+SECTIONS[0]:
                call(root+row['draw_callback']-OWNER_RAM,[submenu,game],proof)
            else:
                stub=struct.pack('>2I',jump(row['draw_callback']),0);debug.write_memory(bridge,stub)
                call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
                call(bridge,[submenu,game],(bridge,stub))
            front,back=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
            if not gfx<front<=back<=gfx+0x1000:raise ValueError('Animated inventory escaped graphics arena')
            commands=debug.read_memory(gfx,front-gfx)
            drawn=[p for w,p in struct.iter_unpack('>2I',commands) if w>>24==0xDE]
            expected=[0x06000000+p for p in model['source']['model_offsets'].values()]
            reflection=row['draw_callback']==preview.get('balloon_drawer',{}).get('address')
            allocation_bytes=model['source']['skeleton']['shown_joints']*64+(48 if reflection else 0)
            passed=drawn==expected and back==gfx+0x1000-allocation_bytes
            record(dict(inventory_rig_joint_draws=drawn,expected=expected,
                        assertion='passed' if passed else 'failed',model=model['index']))
            if not passed:raise ValueError('Animated inventory omitted a joint or allocated wrong matrices')
            check('native translucent matrix binding retained',graph+0x2A8,struct.pack('>2I',xlu+8,xlu+0x600))
            check('balanced native matrix stack',0x801462B4,struct.pack('>I',matrix))
            check('unchanged parent transform',matrix,debug.read_memory(identity,64))
            for at in guards:check('inventory rig guard',at,edge)
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
        complete_model_animation_dma=True,original_tool_speed_retained=True,gpu_rendered=False,
        ordinary_inventory_tested=False,parent_selection_tested=False,flash_written=False,requires_checkpoint_restore=True)


def room_rigs(debug,rom_path,record):
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
    check('complete startup-loaded room module',RAM,module)
    saved={at:debug.read_memory(at,n) for at,n in ((0x801458B8,4),(0x8046C000,864))}
    size=0x6200;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Room-rig fixture outside native heap')
    actor,other,graph,game,identity,bridge,bank,gfx,xlu=(allocation+n for n in
        (16,0x800,0x1500,0x1900,0x1A00,0x1B00,0x2000,0x4600,0x5800))
    debug.write_memory(allocation,bytes(size));edge=b'V3RR'*4
    guards=(allocation,actor+0x740,other-16,other+0x740,graph-16,graph+0x300,
            game-16,game+0xB0,identity-16,identity+64,bridge-16,bridge+32,
            bank-16,bank+9216,gfx-16,gfx+0x1000,xlu-16,xlu+0x800,
            allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    names=('ct','mv','dw');symbols=rigs['code']['symbols']
    jumps=b''.join(struct.pack('>2I',jump(symbols['af_v3_room_rig_'+name]),0) for name in names)
    debug.write_memory(bridge,jumps)
    call(0x8002FE00,[bridge,len(jumps)]);call(0x80034CE0,[bridge,len(jumps)])
    def callback(name,target):
        args=[target,bank] if name=='ct' else [target,0,game,bank]
        return call(bridge+names.index(name)*8,args,(bridge,jumps))
    matrix=call(0x800E02AC);matrix_before=debug.read_memory(matrix,64)
    debug.write_memory(identity,struct.pack('>16f',*(1 if i%5==0 else 0 for i in range(16))))
    rows=rigs['rows'];selected=[min(rows,key=lambda r:r['bytes']),max(rows,key=lambda r:r['bytes'])]
    put(game,graph)
    try:
        for iteration,row in enumerate(selected):
            fill=b'\xA5'*9216;debug.write_memory(bank,fill)
            call(0x80026B44,[bank,row['vrom'],row['bytes']])
            data=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            check('complete cartridge DMA and untouched bank tail',bank,data+fill[len(data):])
            put(0x801458B8,bank&0x1FFFFFFF)
            for target in (actor,other):
                debug.write_memory(target,b'\xA5'*0x740)
                debug.write_memory(target,struct.pack('>H',row['runtime_index']))
                debug.write_memory(target+0x12D,bytes(1));callback('ct',target)
                check('initial per-instance speed and target',target+0x204,struct.pack('>2f',0,.5))
                check('native work vectors belong to this instance',target+0x158,
                      struct.pack('>2I',target+0x1A4,target+0x1DA))
                check('stationary initial frame one',target+0x140,struct.pack('>2f',0,1))
            independent=debug.read_memory(other,0x740)
            debug.write_memory(actor+0x12D,b'\x01');callback('mv',actor)
            actual=[floating(actor+p) for p in (0x204,0x208,0x144)]
            passed=all(abs(a-b)<.00001 for a,b in zip(actual,(.02,1.25,1.03)))
            record(dict(room_rig_switch_response=actual,assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Room rig lost source two-step switch response')
            assertions+=1
            check('native owner retains switch pulse',actor+0x12D,b'\x01')
            check('second room instance remains independent',other,independent)
            debug.write_memory(actor+0x12D,bytes(1))
            debug.write_memory(actor+0x204,struct.pack('>2f',1.24,1.25));callback('mv',actor)
            check('source speed peak switches back to idle',actor+0x204,struct.pack('>2f',1.24,.5))
            put(game+0xA0,iteration);call(0x800E0284,[identity])
            put(graph+0x298,gfx,gfx+0x1000);put(graph+0x2A8,xlu,xlu+0x800)
            callback('dw',actor)
            front,back=struct.unpack('>2I',debug.read_memory(graph+0x298,8))
            if not gfx<front<=back<=gfx+0x1000:raise ValueError('Room rig escaped graphics arena')
            commands=debug.read_memory(gfx,front-gfx)
            drawn=[b for a,b in struct.iter_unpack('>2I',commands) if a>>24==0xDE]
            expected=[0x06000000+p for p in row['source']['model_offsets'].values()]
            passed=drawn==expected and back==gfx+0x1000-64 and len(commands)==96
            record(dict(room_rig_draw=row['source_item_id'],lists=drawn,expected=expected,
                        assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Room rig omitted complete models or misused graphics allocation')
            assertions+=1
            check('translucent stream only binds skeleton matrices',graph+0x2A8,struct.pack('>2I',xlu+8,xlu+0x800))
            check('untouched opposite matrix bank',actor+0x210+(1-iteration)*0x280,b'\xA5'*0x280)
            check('unused matrix slots retain their bytes',actor+0x210+iteration*0x280+5*64,b'\xA5'*(5*64))
            check('native tail fields retain their bytes',actor+0x710,b'\xA5'*0x30)
            check('unused morph-vector bytes retain their bytes',actor+0x20C,b'\xA5'*4)
            check('balanced matrix stack',0x801462B4,struct.pack('>I',matrix))
            check('unchanged parent transform',matrix,debug.read_memory(identity,64))
            for at in guards:check('room-rig work/graphics/stack guard',at,edge)
        check('save/profile unchanged',0x8046C000,saved[0x8046C000])
        check('complete room module unchanged',RAM,module)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(matrix,matrix_before)
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    return dict(native_room_rigs=True,representatives=len(selected),assertions=assertions,
        complete_model_animation_dma=True,independent_instances=True,gpu_rendered=False,
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


def held_collection(debug,rom_path,record):
    """Actual acquisition/collection with four isolated resident records; no Flash writes."""
    from runtime_layout import TEST_STACK
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed collection cartridge')
    equipment=report['equipment_resources'];receipt=equipment['collection']
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
            call(0x800B8B8C,[private,other_item,1])
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
    return dict(native_held_collection=True,players=4,flash_written=False,
        ordinary_gameplay_tested=False,catalogue_screen_tested=False,requires_checkpoint_restore=True)


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


def tool_controls(debug,rom_path,record,*,transitions=False,capture=False):
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
    return dict(native_shared_tool_controls=not transitions and not capture,native_tool_transitions=transitions,
        native_net_capture=capture,
        assertions=assertions,title_demo_input=bool(title),
        code_uploaded=False,synthetic_equipment_data=True,ordinary_gameplay_tested=False,
        golden_net_geometry_tested=capture,golden_effects_tested=False,flash_written=False,requires_checkpoint_restore=True)


def exercise(debug, rom_path, record, *, section='automatic_furniture'):
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
    size = 0x21000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + 0x8000 <= allocation <= 0x80400000 - size:
        raise ValueError('Furniture fixture allocation outside native heap')
    owner, scratch, bridge = allocation + 16, allocation + 0x20000, allocation + 0x20F00
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
            for route in reward['routes']+reward.get('trade_routes',[]):
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
