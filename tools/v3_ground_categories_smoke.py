"""One bounded probe of all loaded seasonal owners; not a town playthrough."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom,sha256,u32
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,TEST_STACK
from v3_npc_draw_smoke import boot_proofs
from v3_furniture_room_smoke import extend
import v3_ground_categories as ground


def exercise(debug,rom_path,record,*,copy_only=False):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Ground probe requires its exact cartridge')
    equipment=report['equipment_resources'];receipt=equipment['ground_categories']
    categories=equipment['item_categories'];files=by_vrom(image);boot=boot_proofs(image)
    blob=files[ground.BLOB].extract(image);at=equipment['blob_offset'];module=blob[at:at+equipment['bytes']]
    def check(label,at,want):
        passed=debug.read_memory(at,len(want))==want
        record(dict(ground_category_check=label,address=f'{at:08X}',bytes=len(want),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Ground mismatch: '+label)
    def call(at,args=(),want=None,proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Ground native return mismatch')
        return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    check('complete startup module',ground.RAM,module)
    saved={at:debug.read_memory(at,n) for at,n in [(s['slot'],4) for s in receipt['owners']]+[(0x80460020,192)]}
    # Keep executable owners in the debugger's low-RAM proof range. Actor/data
    # fixtures use the checked gap after this module and before model banks.
    scratch,scratch_size=(ground.RAM+equipment['bytes']+0xFFF)&~0xFFF,0x22000
    if not ground.RAM+equipment['bytes']<=scratch<scratch+scratch_size<=report['furniture']['bank_pool']['start']:
        raise ValueError('No verified unowned Expansion Pak fixture space')
    scratch_saved=debug.read_memory(scratch,scratch_size)
    size=0xD000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Seasonal probe allocation outside native heap')
    root,bridge=allocation+16,allocation+0xC000
    actor,graph,gfx,data,stack=(scratch+n for n in (16,0x14800,0x15000,0x16800,0x20000))
    debug.write_memory(allocation,bytes(size));edge=b'V3GC'*4
    debug.write_memory(scratch,bytes(scratch_size))
    guards=(allocation,actor-16,actor+0x14400,graph-16,gfx-16,gfx+0x1000,data-16,bridge-16,bridge+16,
            stack-0x800,stack+0x200,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    stub=struct.pack('>II',ground.jump(receipt['code']['symbols']['af_v3_ground_prepare']),0)
    debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
    parents=equipment['parent_readers']['rows'];parent=parents[-1];item=int(parent['item_id'],16)
    art=next(r for r in categories['objects'] if f'{item:04X}' in r['parent_item_ids'])
    def select(enabled):
        profile=bytearray(saved[0x80460020])
        for p in parents:profile[p['profile_byte']]&=~p['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    def window(start,end,updates,expected_sp=None,waypoint=None):
        before=debug.command('g');regs=[int(before[i:i+16],16) for i in range(0,len(before),16)]
        if len(regs)!=71 or regs[37]&0xFFFFFFFF!=0x800D334C:raise ValueError('Ground window needs paused game frame')
        regs[29]=extend(stack);regs[37]=extend(start)
        for r,v in updates.items():regs[r]=extend(v)
        bp=f'0,{end:x},4'
        if debug.command('Z'+bp)!='OK':raise ValueError('Ground breakpoint refused')
        middle=f'0,{waypoint:x},4' if waypoint is not None else None
        if middle and debug.command('Z'+middle)!='OK':raise ValueError('Ground waypoint refused')
        try:
            if debug.command('G'+''.join(f'{r:016x}' for r in regs))!='OK':raise ValueError('Ground registers refused')
            applied=debug.command('g')
            if any(int(applied[i*16:(i+1)*16],16)!=regs[i] for i in {*updates,29,37}):
                raise ValueError('Ground fixture registers were not applied')
            stopped=debug.command('c');raw=debug.command('g')
            actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
            if middle:
                record(dict(ground_epilogue_waypoint=f'{waypoint:08X}',stop=stopped,
                    actual_pc=f'{actual[37]:016X}',actual_sp=f'{actual[29]:016X}',
                    input_sp=f'{regs[29]:016X}'))
                if actual[37]&0xFFFFFFFF!=waypoint:raise ValueError('Ground epilogue waypoint not reached')
                debug.command('z'+middle);middle=None
                stopped=debug.command('c');raw=debug.command('g')
                actual=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
            passed=stopped[:3] in ('T05','S05') and actual[37]&0xFFFFFFFF==end
            passed &= actual[29]==extend(regs[29] if expected_sp is None else expected_sp)
            record(dict(ground_window=f'{start:08X}',stop=stopped,
                expected_pc=f'{end:08X}',actual_pc=f'{actual[37]:016X}',
                expected_sp=f'{extend(regs[29] if expected_sp is None else expected_sp):016X}',
                actual_sp=f'{actual[29]:016X}',assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Ground continuation/stack mismatch')
            return actual
        finally:
            if middle:debug.command('z'+middle)
            debug.command('z'+bp);debug.command('G'+before)
    def copy_array(spec,loaded,common):
        cap=spec['capacity'];frame=cap['stack_bytes'];destination=actor+cap['index_offset']
        check(spec['role']+' retained incoming common pointer',stack+4,struct.pack('>I',common))
        values=struct.pack('>'+str(cap['count'])+'H',*range(1,cap['count']+1))
        debug.write_memory(stack-frame+44,values)
        # Execute the whole return sequence, observing SP immediately before
        # its increment and at an external return address. A breakpoint on JR
        # itself gives an inconsistent SP in the installed emulator.
        put(stack-frame+28,bridge)
        epilogue=0x5EE8 if spec['role']=='winter' else 0x5EC8
        if u32(loaded,epilogue)!=(0x27BD0000|frame):
            raise ValueError('Changed complete ground epilogue increment')
        window(root+0x5E78,bridge,{29:stack-frame},stack,root+epilogue)
        check(spec['role']+' complete extended start copy',destination,values)
        check(spec['role']+' next index array remains untouched',destination+len(values),bytes(cap['index_stride']))
        check(spec['role']+' copy completion flag',common+0x4850,struct.pack('>H',1))
    try:
        if not copy_only:
            select(False);call(0x800A5630,[item],0)
            select(True);call(0x800A5630,[item],art['native_category'])
            # Category fallback bypasses the core entry; original items must not recurse.
            original_stub=struct.pack('>II',ground.jump(0x8046744C),0)
            debug.write_memory(bridge,original_stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            native_type=call(bridge,[0x2200],proof=(bridge,original_stub))
            call(0x800A5630,[0x2200],native_type)
            debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        for variant,spec in enumerate(receipt['owners']):
            owner,rel=(files[spec[k]].extract(image) for k in ('vrom','reloc'))
            sections=struct.unpack_from('>5I',rel);cap=spec['capacity'];resident=cap['resident_bytes']
            loaded=relocate_verified_data(SimpleNamespace(ram=spec['ram'],resident_bytes=resident,sections=sections),owner,rel,root)
            call(0x800262D0,[spec['vrom'],spec['vrom']+len(owner),spec['ram'],spec['ram']+resident,root,root+resident,len(rel)])
            check(spec['role']+' complete loaded owner and BSS',root,loaded);put(spec['slot'],root)
            proof=(root,loaded[:sections[0]])
            if copy_only:
                # Resume the unresolved operation without replaying category
                # discovery, constructors, or graphics setup. Real cartridge
                # code owns the local array, matrix clear, copy, and epilogue.
                debug.write_memory(actor,bytes(cap['actor_bytes']))
                common=actor+spec['common'];destination=actor+cap['index_offset']
                put(common+0x4848,destination)
                frame=cap['stack_bytes'];put(stack+16,0)
                window(root+0x5E14,root+0x5E70,{5:common,7:data},stack-frame)
                check(spec['role']+' zeroed complete local array',stack-frame+44,bytes(cap['count']*2))
                copy_array(spec,loaded,common)
                continue
            call(bridge,[variant],root,(bridge,stub))
            table=root+cap['table_offset'];parts=root+cap['parts_offset']
            expected=bytearray(cap['resident_bytes']-cap['table_offset'])
            old_at=spec['table']-spec['ram'];expected[:spec['count']*8]=loaded[old_at:old_at+spec['count']*8]
            for index in range(spec['count'],cap['count']):
                struct.pack_into('>I',expected,index*8,root+cap['empty_offset'])
            for i,row in enumerate(categories['objects']):
                part=parts+i*52;index=cap['type_base']+row['native_category']
                struct.pack_into('>2I',expected,index*8,part,0x00010000)
                material,geometry=[(row['ram']&0x1FFFFFFF)+row['model_offsets'][key] for key in ('material','geometry')]
                struct.pack_into('>13I',expected,part-table,part+32,1,part+48,0,0,0,0,0,
                                 material,geometry,root+cap['callback_offset'],0x00010000,part+40)
            check(spec['role']+' all scenery rows and complete imported parts',table,expected)
            debug.write_memory(actor,bytes(cap['actor_bytes']));common=actor+spec['common']
            # Execute actual constructor index writes, before unrelated terrain setup.
            if spec['role']=='ordinary':
                window(root+0x80914E34-spec['ram'],root+0x80914E78-spec['ram'],{23:actor,20:common,2:common+2*0x4854})
            elif spec['role']=='cherry':
                window(root+0x808F3ADC-spec['ram'],root+0x808F3B38-spec['ram'],{3:actor,4:actor+0x10000})
            elif spec['role']=='winter':
                regs=window(root+0x808FEAD0-spec['ram'],root+0x808FEAD4-spec['ram'],{})
                window(root+0x808FEAF8-spec['ram'],root+0x808FEB54-spec['ram'],{22:actor,4:actor+0x10000,5:regs[5]})
            else:
                window(root+0x80909978-spec['ram'],root+0x80909B28-spec['ram'],{16:actor,23:common})
                for block in range(4):
                    base=actor+0x174+block*0x484
                    lights=b''.join(struct.pack('>HH',0 if i==0 else (((i-1)&15)+(((i-1)>>4)&15))%3,0) for i in range(257))
                    check('Christmas original light records',base,lights)
                    nodes=debug.read_memory(common+block*0x4854,257*72)
                    if any(u32(nodes,i*72+64)!=base+i*4 for i in range(257)):
                        raise ValueError('Christmas matrix light pointers moved')
            for block in range(4):
                check(spec['role']+' constructor index pointer/count',common+block*0x4854+0x4848,
                      struct.pack('>IH',actor+cap['index_offset']+block*cap['index_stride'],cap['count']))
            # Full native clear/matrix initialization and copy windows; classification
            # is tested separately below without fabricating a terrain/collision world.
            frame=cap['stack_bytes'];put(stack+16,0)
            window(root+0x5E14,root+0x5E70,{5:common,7:data},stack-frame)
            check(spec['role']+' entire local start array',stack-frame+44,bytes(cap['count']*2))
            nodes=debug.read_memory(common,257*72)
            if any(struct.unpack_from('>h',nodes,i*72+68)[0]!=256 for i in range(257)):
                raise ValueError('Ground matrix-list sentinel initialization failed')
            copy_array(spec,loaded,common)
            # Both native ID paths share the global category reader and new type hooks.
            put(data,*([data+32]*4));debug.write_memory(data+32,bytes(12))
            furniture=int(report['furniture']['imports'][0]['item_id'],16)
            for value in (item,furniture,0x2200):
                expected_type=cap['type_base']+call(0x800A5630,[value])
                call(root+0x47A8,[value,data+64,data+96,data],proof=proof)
                check(spec['role']+' native foreground category',data+66,struct.pack('>H',expected_type))
            # Actual material -> matrix -> geometry list generation, not GPU proof.
            part=parts+categories['objects'].index(art)*52
            node=common+72
            matrix=struct.pack('>16f',*[float(i%5==0) for i in range(16)])
            debug.write_memory(node,matrix+bytes(4)+struct.pack('>hBB',-1,0,0))
            put(graph+0x298,gfx,gfx+0x1000);put(data+128,gfx)
            call(root+cap['callback_offset'],[graph,data+128,part+40,node,part+32],proof=proof)
            head=u32(debug.read_memory(data+128,4),0);tail=u32(debug.read_memory(graph+0x29C,4),0)
            if not gfx<head<tail<=gfx+0x1000:raise ValueError('Ground graphics arena bounds failed')
            lists=[p for op,p in struct.iter_unpack('>2I',debug.read_memory(gfx,head-gfx)) if op==0xDE000000]
            want=[(art['ram']&0x1FFFFFFF)+art['model_offsets'][key] for key in ('material','geometry')]
            record(dict(ground_draw_lists=lists,expected=want,assertion='passed' if lists==want else 'failed'))
            if lists!=want:raise ValueError('Ground material/matrix/geometry order failed')
            # The preserved NONE category can have a populated start index.
            # Execute the same native body which the initial title scene faulted in.
            put(data+128,gfx)
            call(root+cap['callback_offset']+0x274,[graph,data+128,root+cap['empty_offset'],node],proof=proof)
            check(spec['role']+' NONE descriptor emits no graphics',data+128,struct.pack('>I',gfx))
        check('complete equipment module retained',ground.RAM,module)
        for at in guards:check('ground fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,data_saved in saved.items():debug.write_memory(at,data_saved)
        debug.write_memory(scratch,scratch_saved)
        call(0x8009C040,[allocation])
    for at,want in saved.items():check('restored owner/profile',at,want)
    check('restored Expansion Pak scratch',scratch,scratch_saved)
    return dict(seasonal_owners=4,constructed_index_arrays=0 if copy_only else 16,
        imported_descriptors=0 if copy_only else 36,setter_copy_only=copy_only,
        gpu_rendered=False,ordinary_gameplay_tested=False,save_reload_tested=False,requires_checkpoint_restore=True)
