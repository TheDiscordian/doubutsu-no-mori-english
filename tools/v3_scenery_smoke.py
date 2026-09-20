"""Bounded current-cartridge seasonal loading and actual renderer components."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,TEST_STACK
from v3_asset_loader import BLOB
from v3_import_storage import jump
from v3_npc_draw_smoke import boot_proofs


def felling_camera(debug,rom_path,record):
    """New felling branch/arguments and actual loaded seasonal callbacks.

    The stump result is injected; stop before terrain/foreground mutation.
    This does not simulate a full axe swing or claim its effects/acquisition.
    """
    import v3_scenery_player as player
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed felling/camera cartridge')
    e=report['equipment_resources'];r=e['scenery'];files=by_vrom(image);boot=boot_proofs(image);assertions=0
    def check(label,okay,**detail):
        nonlocal assertions
        record(dict(felling_camera_check=label,**detail,assertion='passed' if okay else 'failed'))
        if not okay:raise ValueError('Felling/camera mismatch: '+label)
        assertions+=1
    def memory(label,at,want):
        got=debug.read_memory(at,len(want));check(label,got==want,address=f'{at:08X}',
            expected_sha256=sha256(want),observed_sha256=sha256(got))
    def call(at,args=(),proof=None,want=None):
        result=debug.call(f'{at:08X}',[v&0xffffffff for v in args],return_address=MODULE_RAM+0x6480,
            verified_code=proof or boot.get(at));record(result)
        if want is not None:check('native result',result['return_value']==want,entry=f'{at:08X}',expected=want,actual=result['return_value'])
        return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+'I'*len(values),*values))
    def flush(at,n):call(0x8002FE00,[at,n]);call(0x80034CE0,[at,n])
    def regs(raw):return [int(raw[i:i+16],16) for i in range(0,len(raw),16)]
    def extend(v):return v|(0xffffffff00000000 if v&0x80000000 else 0)
    def setregs(values):
        if debug.command('G'+''.join(f'{v:016x}' for v in values))!='OK':raise ValueError('Felling registers rejected')
    regions=[(o['config'][0],4) for o in r['owners']]+[(r['ram'],r['additional_fixed_resident_bytes']),
        (r['tree_states']['cache_word'],4),(0x80460020,192),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16)]
    saved={at:debug.read_memory(at,n) for at,n in regions};module=debug.read_memory(e['ram'],e['bytes'])
    save_data=debug.read_memory(0x8046C000,864)
    # Complete owner + relocation, with separate tiny bridge/position buffers.
    extent=max(o['resident_bytes']+len(files[o['reloc']].extract(image)) for o in r['owners'])
    extent=(extent+31)&~15;size=extent+0x300
    allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:raise ValueError('Camera fixture allocation failed')
    root=allocation+16;bridge=allocation+extent+0x40;position=bridge+0x40
    edge=b'AFFC'*4;guards=[allocation,bridge-16,bridge+16,position-16,position+16,allocation+size-16,
        TEST_STACK-0x800,TEST_STACK+0x40]
    debug.write_memory(allocation,bytes(size))
    for at in guards:debug.write_memory(at,edge)
    parent=next(row for row in e['player_actions']['equipment_selection']['rows'] if row['item_id']=='223B')
    def select(enabled):
        profile=bytearray(saved[0x80460020]);profile[parent['profile_byte']]&=~parent['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    data=files[player.VROM].extract(image);rel=files[player.RELOC].extract(image)
    owner=int.from_bytes(debug.read_memory(0x80143900,4),'big')-(0x808DD748-player.RAM)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):raise ValueError('Missing actual player owner')
    p=r['player_queries'];loaded=relocate_verified_data(SimpleNamespace(ram=player.RAM,resident_bytes=p['resident_bytes'],
        sections=struct.unpack_from('>5I',rel)),data,rel,owner)
    memory('complete actual player text',owner,loaded[:p['sections'][0]])
    def felling(item,enabled,want):
        select(enabled);before=debug.command('g');values=regs(before);sp=TEST_STACK-0x100
        if values[37]&0xffffffff!=0x800D334C:raise ValueError('Felling needs paused native frame')
        put(position,0x41A00000,0,0x41A00000);put(sp+0x28,position)
        values[2]=item;values[16]=extend(position-0x28);values[29]=extend(sp)
        values[37]=extend(owner+0x808CA548-player.RAM)
        stops=[owner+a-player.RAM for a in (0x808CA598,0x808CA600,0x808CA5C8)]
        for at in stops:
            if debug.command(f'Z0,{at:x},4')!='OK':raise ValueError('Felling breakpoint rejected')
        try:
            setregs(values);stopped=debug.command('c');actual=regs(debug.command('g'))
            target=stops[0] if want else stops[1]
            check('actual final stump branch',stopped[:3] in ('T05','S05') and actual[37]&0xffffffff==target,
                item=f'{item:04X}',selected=enabled,expected_pc=f'{target:08X}',actual_pc=f'{actual[37]&0xffffffff:08X}')
            if want:
                check('native neutral stump height and original position',
                    [actual[i]&0xffffffff for i in (4,5,6,7)]==[0x41A00000,0,0x41A00000,0]
                    and actual[2]&0xffffffff==0x8010B478)
                memory('real stump identity retained on stack',sp+0x36,struct.pack('>H',item))
                # Terrain mutation is outside this bounded fixture. Resume after
                # that existing call, then inspect the actual foreground call.
                actual[37]=extend(owner+0x808CA5A0-player.RAM);setregs(actual)
                stopped=debug.command('c');actual=regs(debug.command('g'))
                check('foreground commit receives actual gold/native stump',
                    stopped[:3] in ('T05','S05') and actual[37]&0xffffffff==stops[2]
                    and [actual[i]&0xffffffff for i in (4,5,6,7)]==[item,0x41A00000,0,0x41A00000])
                memory('native foreground update flag retained',sp+16,struct.pack('>I',1))
        finally:
            for at in stops:debug.command(f'z0,{at:x},4')
            debug.command('G'+before)
    try:
        put(r['tree_states']['cache_word'],0)
        for item,enabled,want in ((0x7B,True,True),(0x7E,True,True),(0x7E,False,False),(4,False,True),(0x867,True,False)):
            felling(item,enabled,want)
        blob=files[BLOB].extract(image);packet=blob[r['blob_offset']:r['blob_offset']+r['bytes']]
        memory('final felling entry lazy-loads complete packet',r['ram'],packet)
        for variant,(o,binding) in enumerate(zip(r['owners'],r['felling_camera']['owners'],strict=True)):
            data,rel=(files[o[k]].extract(image) for k in ('vrom','reloc'));n=o['resident_bytes'];sections=struct.unpack_from('>5I',rel)
            loaded_season=relocate_verified_data(SimpleNamespace(ram=o['ram'],resident_bytes=n,sections=sections),data,rel,root)
            call(0x800262D0,[o['vrom'],o['vrom']+len(data),o['ram'],o['ram']+n,root,root+n,len(rel)])
            memory(o['role']+' complete loaded camera owner',root,loaded_season);put(o['config'][0],root)
            high=u32(debug.read_memory(root+binding['hi'],4),0)&65535
            low=struct.unpack('>h',debug.read_memory(root+binding['lo']+2,2))[0];target=(high<<16)+low
            check(o['role']+' actual callback points to shared code',target==r['code']['symbols'][f'af_v3_tree_talk{variant}'])
            stub=struct.pack('>2I',jump(target),0);debug.write_memory(bridge,stub);flush(bridge,len(stub))
            proof=(root,loaded_season[:sections[0]]);first=o['config'][8]
            select(True)
            for index in binding['indices']:call(bridge,[index],(bridge,stub),1)
            for enabled,index in ((False,first+2),(True,first),(True,first+1),(True,first+5),(True,5),(True,24)):
                select(enabled);want=call(root+binding['entry'],[index],proof)
                call(bridge,[index],(bridge,stub),want)
        memory('complete player text retained',owner,loaded[:p['sections'][0]])
        memory('saved data unchanged',0x8046C000,save_data)
        for at in guards:memory('fixture guard',at,edge)
        memory('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        flush(r['ram'],r['additional_fixed_resident_bytes']);call(0x8009C040,[allocation])
    for at,value in saved.items():memory('restored state',at,value)
    memory('equipment unchanged',e['ram'],module)
    return dict(assertions=assertions,actual_felling_branch_and_commit_arguments=True,
        stump_result_injected=True,terrain_and_foreground_mutation_not_executed=True,
        actual_seasonal_callbacks=4,ordinary_acquisition_tested=False,requires_checkpoint_restore=True)


def player_queries(debug,rom_path,record,*,consumers_only=False):
    """Actual player call sites and bee/cut consumers; callbacks are isolated."""
    import v3_scenery_player as player
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed player-tree cartridge')
    e=report['equipment_resources'];r=e['scenery'];p=r['player_queries'];files=by_vrom(image);boot=boot_proofs(image)
    assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));okay=got==want
        record(dict(player_tree_check=label,address=f'{at:08X}',expected_sha256=sha256(want),
            observed_sha256=sha256(got),assertion='passed' if okay else 'failed'))
        if not okay:raise ValueError('Player-tree mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None,want=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',[v&0xffffffff for v in args],return_address=MODULE_RAM+0x6480,
            verified_code=proof or boot.get(at))
        if want is not None:
            result['assertion']='passed' if result['return_value']==want else 'failed';assertions+=1
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Player-tree return mismatch')
        return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+'I'*len(values),*values))
    def flush(at,n):call(0x8002FE00,[at,n]);call(0x80034CE0,[at,n])
    data=files[player.VROM].extract(image);rel=files[player.RELOC].extract(image)
    owner=int.from_bytes(debug.read_memory(0x80143900,4),'big')-(0x808DD748-player.RAM)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):raise ValueError('Missing actual player owner')
    loaded=relocate_verified_data(SimpleNamespace(ram=player.RAM,resident_bytes=p['resident_bytes'],
        sections=struct.unpack_from('>5I',rel)),data,rel,owner)
    check('complete actual relocated player text',owner,loaded[:p['sections'][0]])
    regions=[(0x80460020,192),(0x80136F20,4),(r['ram'],r['additional_fixed_resident_bytes']),
        (r['tree_states']['cache_word'],4),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16)]
    saved={at:debug.read_memory(at,n) for at,n in regions};module=debug.read_memory(e['ram'],e['bytes'])
    save_data=debug.read_memory(0x8046C000,864)
    allocation=call(0x8009BFC0,[0x1800])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FE800:raise ValueError('Player-tree fixture allocation failed')
    actor,out,clip,bridge=allocation+0x100,allocation+0x14C0,allocation+0x1540,allocation+0x1600
    edge=b'AFPT'*4;guards=[allocation,actor-16,actor+0x13A0,out-16,out+96,clip-16,clip+64,
        bridge-16,allocation+0x17F0,TEST_STACK-0x800,TEST_STACK+0x40]
    occupied=sorted([(actor,0x13A0),(out,96),(clip,64),(bridge,0xB0)]+[(at,16) for at in guards
                    if allocation<=at<allocation+0x1800])
    if any(a+n>b for (a,n),(b,_) in zip(occupied,occupied[1:])):
        raise ValueError('Player-tree fixture buffers/guards overlap')
    debug.write_memory(allocation,bytes(0x1800))
    for at in guards:debug.write_memory(at,edge)
    def li(reg,value):return [0x3C000000|reg<<16|value>>16,0x34000000|reg<<21|reg<<16|value&65535]
    def emit(at,words):put(at,*words)
    emit(bridge,li(8,out)+[0xAD040000,0xAD050004,0xAD060008,0xAD07000C,
        0x3C093F80,0xACE90000,0xACE90004,0xACE90008,0x03E00008,0x00001025])
    emit(bridge+0x80,li(8,out+32)+[0xAD040000,0xAD050004,0xAD060008,0x8D020010,0x03E00008,0])
    flush(bridge,0xB0)
    parent=next(row for row in e['player_actions']['equipment_selection']['rows'] if row['item_id']=='223B')
    def select(enabled):
        profile=bytearray(saved[0x80460020]);profile[parent['profile_byte']]&=~parent['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    def regs(raw):return [int(raw[i:i+16],16) for i in range(0,len(raw),16)]
    def extend(v):return v|(0xffffffff00000000 if v&0x80000000 else 0)
    def query(row,item,want):
        nonlocal assertions
        before=debug.command('g');initial=regs(before)
        if len(initial)!=71 or initial[37]&0xffffffff!=0x800D334C:raise ValueError('Player query needs paused native frame')
        pc=owner+row['address']-player.RAM;values=initial[:]
        for i in (*range(1,16),24,25):values[i]=0x10203000+i
        values[row['source']]=item;values[29]=extend(TEST_STACK);values[37]=extend(pc)
        values[33]=0x13572468;values[34]=0x24681357
        stop=f'0,{pc+8:x},4'
        if debug.command('Z'+stop)!='OK':raise ValueError('Player query breakpoint rejected')
        try:
            if debug.command('G'+''.join(f'{v:016x}' for v in values))!='OK':raise ValueError('Player query registers rejected')
            stopped=debug.command('c');actual=regs(debug.command('g'))
            expected=values[:];expected[row['result']]=want;expected[31]=extend(pc+8);expected[37]=extend(pc+8)
            compared=(*range(1,32),33,34,*range(38,71))
            bad=[i for i in compared if actual[i]&0xffffffff!=expected[i]&0xffffffff]
            okay=stopped[:3] in ('T05','S05') and actual[37]&0xffffffff==pc+8 and not bad
            record(dict(player_tree_query=row,item=f'{item:04X}',result=actual[row['result']]&0xffffffff,
                expected=want,mismatched_registers=bad,actual_pc=f'{actual[37]&0xffffffff:08X}',
                assertion='passed' if okay else 'failed'))
            if not okay:raise ValueError('Actual player query result/register preservation failed')
            assertions+=1
        finally:
            debug.command('z'+stop);debug.command('G'+before)
    def native(start,end,args,want=None):
        at=owner+start-player.RAM
        return call(at,args,(at,loaded[start-player.RAM:end-player.RAM]),want)
    try:
        select(True);put(r['tree_states']['cache_word'],0)
        if consumers_only:
            call(0x800A5970,[0x800,0,4],want=0x801)
        else:
            for row in p['calls']:query(row,0x7e if row['query']==3 else 0x81 if row['query']==2 else 0x867,1)
        blob=files[BLOB].extract(image);packet=blob[r['blob_offset']:r['blob_offset']+r['bytes']]
        check('lazy-loaded complete query packet',r['ram'],packet)
        if not consumers_only:
            select(False);query(p['calls'][0],0x867,0);query(p['calls'][0],0x804,1)
            select(True);query(p['calls'][4],0x864,0);query(p['calls'][4],0x865,1)
        put(0x80136F20,clip);put(clip+12,bridge+0x80);put(clip+56,bridge)
        put(actor+0x28,0x3F800000,0,0x3F800000);debug.write_memory(actor+0xDE,b'\x12\x34')
        for enabled,item,x,want in ((True,0x81,2,1),(False,0x81,2,0),(False,0x5e,2,1),(True,0x80,2,0),(True,0x81,-1,0)):
            select(enabled);debug.write_memory(out,bytes(96));put(out+64,0xA5A5A5A5)
            native(0x808BAE38,0x808BAF40,[actor,item,x,3,out+64],want)
            check('actual common bee callback keeps item and coordinates',out,
                struct.pack('>3I',item,x,3) if want else bytes(12))
            check('bee orientation/fallback output bounds',out+64,b'\x12\x34\xA5\xA5' if want else b'\xA5'*4)
        select(True)
        for count in (1,0):
            debug.write_memory(out,bytes(96));put(out+48,count)
            native(0x808CA400,0x808CA4C8,[actor,0,0x867,2,3],0x867 if count else 0x7e)
            check('actual axe drop forwards full gold identity',out,struct.pack('>3I',0x867,2,3))
            check('actual axe decrement forwards game and coordinates',out+32,struct.pack('>3I',0,2,3))
        debug.write_memory(out,bytes(96));put(out+48,1);put(actor+0xD30,0)
        allowed=call(0x800B5CD4)
        native(0x808CA400,0x808CA4C8,[actor,0,0x81,2,3],0x81)
        check('bee axe hit does not drop before its native timer',out,bytes(16))
        check('native permission controls the unchanged five-frame bee timer',actor+0xD30,struct.pack('>I',5 if allowed else 0))
        check('saved data unchanged',0x8046C000,save_data)
        check('complete actual player text unchanged',owner,loaded[:p['sections'][0]])
        for at in guards:check('fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        flush(r['ram'],r['additional_fixed_resident_bytes']);call(0x8009C040,[allocation])
    for at,value in saved.items():check('restored state',at,value)
    check('complete equipment unchanged',e['ram'],module)
    return dict(assertions=assertions,actual_player_queries=0 if consumers_only else len(p['calls']),actual_common_bee_and_axe_consumers=True,
        drop_and_cut_callbacks_stubbed=True,ordinary_acquisition_tested=False,requires_checkpoint_restore=True)


def interactions(debug,rom_path,record):
    """Native seasonal control flow with bounded field/landing/actor test doubles."""
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed tree-interaction cartridge')
    e=report['equipment_resources'];r=e['scenery'];files=by_vrom(image);boot=boot_proofs(image)
    capacity=r['additional_fixed_resident_bytes'];blob=files[BLOB].extract(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(tree_interaction_check=label,address=f'{at:08X}',bytes=len(want),
            expected_sha256=sha256(want),observed_sha256=sha256(got),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Tree-interaction mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None,want=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Tree-interaction return mismatch')
        return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+'I'*len(values),*values))
    def flush(at,n):call(0x8002FE00,[at,n]);call(0x80034CE0,[at,n])
    def li(reg,value):return [0x3C000000|reg<<16|value>>16,0x34000000|reg<<21|reg<<16|value&65535]
    def emit(at,words):put(at,*words);return struct.pack('>'+'I'*len(words),*words)
    regions=[(o['config'][0],4) for o in r['owners']]+[(r['ram'],capacity),(r['tree_states']['cache_word'],4),
        (0x80460020,192),(0x80136FD8,4),(0x8011EF90,4),(0x8008A410,8),
        (0x8003C590,4),(0x800419F0,4),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16)]
    saved={at:debug.read_memory(at,n) for at,n in regions};module=debug.read_memory(e['ram'],e['bytes'])
    size=0x17000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Tree-interaction fixture allocation failed')
    root=allocation+16;bridge=allocation+0x14000;out=allocation+0x14800
    cells=allocation+0x14A00;attributes=allocation+0x14D00;player=allocation+0x15000;game=allocation+0x16000
    land,commit,actor,new_actor,deleted,selection=out,out+32,out+64,out+96,out+128,out+160
    position=out+176;mode=out+192;actor_value=out+196;edge=b'AFTI'*4
    result_spans=[(land,24),(commit,24),(new_actor,24),(deleted,24),(selection,4),(position,12),(mode,4),(actor_value,4)]
    if any(a+n>b for (a,n),(b,_) in zip(result_spans,result_spans[1:])):
        raise ValueError('Tree-interaction result buffers overlap')
    guards=[allocation,bridge-16,out-16,out+224,cells-16,cells+512,attributes-16,attributes+256,
            player-16,game-16,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40]
    debug.write_memory(allocation,bytes(size))
    for at in guards:debug.write_memory(at,edge)
    def capture(dest):
        return li(8,dest)+[0xAD040000,0xAD050004,0xAD060008,0xAD07000C,0x8FA90010,0xAD090010,0x8FA90014,0xAD090014]
    # Controlled landing captures all six native arguments and supplies a chosen
    # success/failure position. No item is created and no live foreground changes.
    land_code=capture(land)+li(8,mode)+[0x8D0A0000,0x8FA90010,0xAD2A0000,0xAD2A0004,0xAD2A0008,0x03E00008,0x00001025]
    emit(bridge,land_code);emit(bridge+0x100,capture(commit)+[0x03E00008,0])
    emit(bridge+0x180,capture(new_actor)+li(8,actor_value)+[0x8D020000,0x03E00008,0])
    emit(bridge+0x200,capture(deleted)+[0x03E00008,0])
    emit(bridge+0x280,li(8,selection)+[0x8FA90018,0xAD090000,0x24091088,0xA4A90000,0x03E00008,0])
    emit(bridge+0x300,[0x44800000,0x03E00008,0])
    field_stub=emit(bridge+0x340,li(2,cells)+[0x03E00008,0]);flush(bridge,0x380)
    parent=next(x for x in e['player_actions']['equipment_selection']['rows'] if x['item_id']=='223B')
    def select(enabled):
        profile=bytearray(saved[0x80460020]);profile[parent['profile_byte']]&=~parent['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    try:
        call(0x800A5970,[0x800,0,4],want=0x801)
        code=blob[r['blob_offset']:r['blob_offset']+r['bytes']];check('complete loaded interaction packet',r['ram'],code)
        put(0x80136FD8,player);put(0x8011EF90,game)
        put(0x8008A410,jump(bridge+0x340),0);flush(0x8008A410,8)
        native_drops=r['interactions']['drops'][:13]
        values=[0x800,0x801,0x804,0x863,0x864,0x865,0x866,0x867,0x868,0x869,0x7B,0x7F,0x80,0x81]+[0]*242
        rawcells=struct.pack('>256H',*values);debug.write_memory(cells,rawcells)
        for variant,o in enumerate(r['owners']):
            data,rel=(files[o[k]].extract(image) for k in ('vrom','reloc'));sections=struct.unpack_from('>5I',rel);n=o['resident_bytes']
            if root+n+len(rel)>=bridge-16:raise ValueError('Tree-interaction owner overlaps test work')
            loaded=relocate_verified_data(SimpleNamespace(ram=o['ram'],resident_bytes=n,sections=sections),data,rel,root)
            call(0x800262D0,[o['vrom'],o['vrom']+len(data),o['ram'],o['ram']+n,root,root+n,len(rel)])
            check(o['role']+' complete actual relocated owner',root,loaded);put(o['config'][0],root)
            fixture=bytearray(loaded)
            # Only callbacks at the ends of the tested control flow are doubled.
            for offset,target in ((0x2100,bridge),(0x2824,bridge+0x100),(0x29D4,bridge+0x180),
                    (0x2A44,bridge+0x200),(0x274C,bridge+0x280),(0x27F0,bridge+0x300)):
                struct.pack_into('>I',fixture,offset,jump(target,link=offset!=0x2100))
                if offset==0x2100:struct.pack_into('>I',fixture,offset+4,0)
            debug.write_memory(root,fixture);flush(root,sections[0]);proof=(root,bytes(fixture[:sections[0]]))
            for enabled in (False,True):
                select(enabled);debug.write_memory(attributes,b'?'*256)
                target=u32(data,r['interactions']['owners'][variant]['calls'][0])&0x03FFFFFF
                stub=emit(bridge+0x3C0,[jump(0x80000000|target<<2),0]);flush(bridge+0x3C0,8)
                call(bridge+0x3C0,[1,1,attributes],(bridge+0x3C0,stub))
                native_cut_at=r['interactions']['owners'][variant]['cut_table']
                counts=dict(struct.iter_unpack('>2H',data[native_cut_at:native_cut_at+240]))
                if enabled:counts.update(r['interactions']['cuts'])
                check(o['role']+' selected/native axe hit counts',attributes,bytes(counts.get(v,255) for v in values))
                check('cut initialization never changes foreground identities',cells,rawcells)
            select(True)
            for fg,want,luck in ((0x867,0x223B,0),(0x7F,0x2103,0),(0x7F,0x2100,4),(0x80,0x1088,0),(0x81,0x62,0),
                    (0x80C,0x2800,0)):
                debug.write_memory(out,bytes(208));put(mode,0x3F800000);put(actor_value,actor)
                debug.write_memory(player+0xA8E,bytes([luck]));call(root+0x2940,[fg,16,16,position],proof)
                native=next((row for row in native_drops if row[0]==fg),None)
                after,count=(native[2],native[3]) if native else (0x868,1)
                check(o['role']+' exact drop arguments including parent and stack',land,
                    struct.pack('>6I',want,16,16,count,position,actor if fg==0x81 else 0))
                check(o['role']+' retained family after drop',commit,struct.pack('>5I',after,0x44250000,0,0x44250000,1))
                check('drop outcome position',position,struct.pack('>3I',*[0x3F800000]*3))
                if fg==0x81:check('bee native actor profile',new_actor+8,struct.pack('>I',0xA4))
                check('successful drops do not delete bee actor',deleted,bytes(4))
            # One season suffices for shared failure/selection branches after the
            # four distinct seasonal relocations above are exercised.
            if variant==3:
                for success_actor,success_drop,enabled in ((True,False,True),(False,False,True),(True,True,False)):
                    debug.write_memory(out,bytes(208));put(mode,0x3F800000 if success_drop else 0xBF800000)
                    put(actor_value,actor if success_actor else 0);select(enabled)
                    call(root+0x2940,[0x81,16,16,position],proof)
                    check('bee deletion only after failed landing',deleted,struct.pack('>I',actor if success_actor and enabled and not success_drop else 0))
                    if not enabled or not success_actor:check('no drop or foreground change without actor/profile',land,bytes(56))
                select(False);debug.write_memory(out,bytes(208));call(root+0x2940,[0x867,16,16,position],proof)
                check('unselected shovel tree cannot emit an item',land,bytes(56))
            check(o['role']+' control flow does not modify loaded code',root,bytes(fixture[:sections[0]]))
        check('complete packet unchanged',r['ram'],code)
        for at in guards:check('fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        flush(0x8008A410,8);flush(r['ram'],capacity);call(0x8009C040,[allocation])
    for at,want in saved.items():check('restored state/code',at,want)
    check('restored complete equipment module',e['ram'],module)
    return dict(assertions=assertions,seasonal_owners=4,actual_drop_control_flow=True,
        field_and_landing_stubs=True,actor_and_furniture_selection_stubs=True,terrain_height_stub=True,
        ordinary_acquisition_tested=False,requires_checkpoint_restore=True)


def world_queries(debug,rom_path,record):
    """Current core entries, terrain calculation, and guarded collision records."""
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed tree-world cartridge')
    e=report['equipment_resources'];r=e['scenery'];files=by_vrom(image)
    blob=files[BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(tree_world_check=label,address=f'{at:08X}',bytes=len(want),
            expected_sha256=sha256(want),observed_sha256=sha256(got),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Tree-world mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None):
        result=debug.call(f'{at:08X}',[v&0xffffffff for v in args],return_address=MODULE_RAM+0x6480,verified_code=boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Tree-world native return mismatch')
        return result['return_value']
    regions=[(r['ram'],8192),(r['tree_states']['cache_word'],4),(0x80460020,192),
        (TEST_STACK-0x800,16),(TEST_STACK+0x40,16)]
    saved={at:debug.read_memory(at,n) for at,n in regions};module=debug.read_memory(e['ram'],e['bytes'])
    allocation=call(0x8009BFC0,[0x400])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FFC00:raise ValueError('Tree-world fixture allocation failed')
    unit=allocation+0x40;column=allocation+0xC0;item=allocation+0x120
    guards=[allocation,unit-16,unit+48,column-16,column+32,item-16,item+16,allocation+0x3F0,TEST_STACK-0x800,TEST_STACK+0x40]
    edge=b'AFWQ'*4;debug.write_memory(allocation,bytes(0x400))
    for at in guards:debug.write_memory(at,edge)
    parent=next(row for row in e['player_actions']['equipment_selection']['rows'] if row['item_id']=='223B')
    def select(enabled):
        profile=bytearray(saved[0x80460020]);profile[parent['profile_byte']]&=~parent['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    def collision(value,low=0xffff,high=0,want=1):
        data=bytearray(b'\xa5'*48);struct.pack_into('>2i',data,32,16,16);struct.pack_into('>H',data,46,value)
        debug.write_memory(unit,data);debug.write_memory(column,b'\xa5'*32)
        call(0x8006C980,[column,unit,0,low,high],want)
        check('collision unit retains its original identity and fields',unit,bytes(data))
        return debug.read_memory(column,32)
    try:
        select(True);debug.write_memory(r['ram'],bytes(8192));debug.write_memory(r['tree_states']['cache_word'],bytes(4))
        call(0x8002FE00,[r['ram'],8192]);call(0x80034CE0,[r['ram'],8192])
        # First entry must load the packet and preserve the fifth stack argument.
        collision(0x864)
        code=blob[r['blob_offset']:r['blob_offset']+r['bytes']]
        check('core column entry loads the complete packet',r['ram'],code)
        check('world-query packet cache',r['tree_states']['cache_word'],struct.pack('>I',r['crc32']))
        reference={i:collision(i) for i in (1,2,3,4,0x801,0x802,0x803,0x804)}
        for imported,native in ((0x864,0x801),(0x865,0x802),(0x866,0x803),(0x867,0x804),(0x868,0x804),
                (0x7F,0x804),(0x80,0x804),(0x81,0x804),(0x7B,1),(0x7C,2),(0x7D,3),(0x7E,4)):
            collision(imported);check('gold collision equals the complete matching native geometry',column,reference[native])
        # Exclusion is applied to the real item, not its temporary geometry ID.
        collision(0x864,0x800,0x804);check('native-ID exclusion does not exclude imported identity',column,reference[0x801])
        collision(0x864,0x863,0x869,0);check('real imported-ID exclusion retains output',column,b'\xa5'*32)
        for value in (0x863,0x869):
            collision(value,want=0);check('sapling/dead sapling has no trunk column',column,b'\xa5'*32)
        for value,want in ((0x863,1),(0x869,1),(0x7B,1),(0x7E,1),(0x864,0),(0x867,0),(0x800,1)):
            raw=struct.pack('>H',value)+bytes(14);debug.write_memory(item,raw)
            call(0x8008C964,[item,0x3f800000,0x40000000,0x40400000],want)
            check('dig classification does not mutate foreground',item,raw)
        for value,want in ((0x863,1),(0x869,0),(0x867,0),(0x800,1)):call(0x8008D7B0,[value],want)
        # Existing entry dispatches were rebound when the bootstrap grew.
        call(0x800A5970,[0x863,0,4],0x864);call(0x800A56F0,[0x867,0],0x7E)
        select(False);collision(0x864,want=0);check('unselected tree keeps original collision behaviour',column,b'\xa5'*32)
        debug.write_memory(item,struct.pack('>H',0x863));call(0x8008C964,[item,0,0,0],0);call(0x8008D7B0,[0x863],0)
        collision(0x801);check('native geometry remains unchanged without selection',column,reference[0x801])
        check('complete packet remains unchanged',r['ram'],code)
        for at in guards:check('fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
        call(0x8002FE00,[r['ram'],8192]);call(0x80034CE0,[r['ram'],8192]);call(0x8009C040,[allocation])
    for at,want in saved.items():check('restored original state',at,want)
    check('complete equipment module restored',e['ram'],module)
    return dict(assertions=assertions,actual_native_terrain=True,all_gold_collision_states=True,
        real_core_entries=True,world_identity_unchanged=True,ordinary_world_interaction=False,requires_checkpoint_restore=True)


def daily_growth(debug,rom_path,record,*,contents=False):
    """Native daily consumers on isolated acres, preserving live town state."""
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed daily-growth cartridge')
    e=report['equipment_resources'];r=e['scenery'];d=r['daily_growth'];files=by_vrom(image)
    blob=files[BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(daily_tree_check=label,address=f'{at:08X}',bytes=len(want),
            expected_sha256=sha256(want),observed_sha256=sha256(got),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Daily-growth mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None,want=None):
        result=debug.call(f'{at:08X}',[v&0xFFFFFFFF for v in args],
            return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Daily-growth native return mismatch')
        return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+'I'*len(values),*[v&0xFFFFFFFF for v in values]))
    def short(at,value):debug.write_memory(at,struct.pack('>H',value))
    regions=[(0x80100C5C,4),(r['ram'],8192),(r['tree_states']['cache_word'],4),
        (0x80460020,192),(0x80126EB4,4),(0x8003C590,4),(0x800419F0,4),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16)]
    if contents:regions.append((0x8012D148,30*512))
    saved={at:debug.read_memory(at,n) for at,n in regions};module=debug.read_memory(e['ram'],e['bytes'])
    size=0x7000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Daily-growth fixture allocation failed')
    root=allocation+16;bridge=allocation+0x5800;info=allocation+0x5900;cells=allocation+0x5A00
    adjacent=allocation+0x5D00;bits=allocation+0x6000;counts=allocation+0x6040
    edge=b'AFDT'*4;guards=[allocation,bridge-16,info-16,info+0x44,cells-16,cells+512,
        adjacent-16,adjacent+512,bits-16,bits+32,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40]
    debug.write_memory(allocation,bytes(size))
    for at in guards:debug.write_memory(at,edge)
    helpers=['af_v3_tree_daily_plant','af_v3_tree_near','af_v3_tree_set_info','af_v3_tree_reset_info','af_v3_tree_thin']
    if contents:helpers=['af_v3_tree_count_eligible','af_v3_tree_change_content','af_v3_tree_count_money']
    stubs=b''.join(struct.pack('>2I',jump(r['code']['symbols'][name]),0) for name in helpers)
    debug.write_memory(bridge,stubs);call(0x8002FE00,[bridge,len(stubs)]);call(0x80034CE0,[bridge,len(stubs)])
    def resident(name,args=(),want=None):return call(bridge+8*helpers.index(name),args,(bridge,stubs),want)
    parent=next(row for row in e['player_actions']['equipment_selection']['rows'] if row['item_id']=='223B')
    def select(enabled):
        profile=bytearray(saved[0x80460020]);profile[parent['profile_byte']]&=~parent['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    def field(item,cap=4,days=1,x=8,z=8):
        debug.write_memory(cells,bytes(512));debug.write_memory(info,bytes(0x44))
        put(info+0x10,cap,days,0);put(info+0x28,x,z)
        at=cells+2*(x+16*z);short(at,item);return at
    try:
        data,rel=(files[d[k]].extract(image) for k in ('vrom','reloc'))
        n=d['resident_bytes'];sections=struct.unpack_from('>5I',rel)
        if root+n+len(rel)>=bridge-16:raise ValueError('Daily owner overlaps fixture')
        loaded=relocate_verified_data(SimpleNamespace(ram=d['ram'],resident_bytes=n,sections=sections),data,rel,root)
        call(0x800262D0,[d['vrom'],d['vrom']+len(data),d['ram'],d['ram']+n,root,root+n,len(rel)])
        check('complete cartridge-loaded daily owner and BSS',root,loaded);put(0x80100C5C,root)
        proof=(root,loaded[:sections[0]])
        # Execute real renewal dispatch and displaced prologue with its native
        # non-field early return, so no live town renewal can run in this fixture.
        put(0x80126EB4,0);put(r['tree_states']['cache_word'],0);debug.write_memory(r['ram'],bytes(8192))
        call(0x8002FE00,[r['ram'],8192]);call(0x80034CE0,[r['ram'],8192])
        call(root+0x475C,[info,counts],proof)
        code=blob[r['blob_offset']:r['blob_offset']+r['bytes']]
        check('daily entry loads and verifies the entire shared packet',r['ram'],code)
        check('daily packet CRC cache',r['tree_states']['cache_word'],struct.pack('>I',r['crc32']))
        debug.write_memory(0x80126EB4,saved[0x80126EB4])
        check('registered daily plant callback',root+0x4ABC,struct.pack('>I',r['code']['symbols']['af_v3_tree_daily_plant']))
        select(True)
        if contents:
            contents_cases(debug,record,call,resident,check,put,short,root,proof,info,cells,select)
        else:
            for item,cap,days,want in ((0x863,4,0,0x863),(0x863,4,1,0x864),(0x864,4,3,0x867),
                    (0x863,2,5,0x865),(0x868,4,5,0x868),(0x863,0,1,0x869),(0x869,4,1,0),
                    (0x863,-1,1,0),(0x800,4,1,0x801)):
                at=field(item,cap,days);resident('af_v3_tree_daily_plant',[at,info],1)
                check('daily plant outcome',at,struct.pack('>H',want))
            for current,near,want in ((0x863,0x804,0x869),(0x800,0x864,0x84E),(0x800,0x804,0x84E)):
                at=field(current);short(at-2,near);resident('af_v3_tree_daily_plant',[at,info],1)
                check('native/imported neighbours interact',at,struct.pack('>H',want))
                check('neighbour identity never changed',at-2,struct.pack('>H',near))
            for z,neighbour_value,present,want in ((1,0x863,True,0x869),(0,0x863,True,0x864),(1,0x867,False,0x864)):
                at=field(0x863,x=0,z=z);debug.write_memory(adjacent,bytes(512))
                short(adjacent+2*(z*16+15),neighbour_value);put(info+8,adjacent if present else 0)
                resident('af_v3_tree_daily_plant',[at,info],1);check('cross-acre sapling rule',at,struct.pack('>H',want))
            # Source thinning counts adult gold trees and removes native saplings
            # first, then gold saplings, using the actual native RNG.
            acre=[0x867]*32+[0x800,0x863]+[0]*222
            debug.write_memory(cells,struct.pack('>256H',*acre));debug.write_memory(bits,bytes(32));put(counts,0)
            resident('af_v3_tree_set_info',[bits,cells]);wanted=bytes(4)+b'\x00\x03'+bytes(26)
            check('gold/native saplings recorded together',bits,wanted)
            resident('af_v3_tree_reset_info',[bits,counts,counts+1,cells]);check('native and imported candidate counts',counts,b'\x01\x01\x00\x00')
            resident('af_v3_tree_thin',[cells,bits,1,1]);acre[32:34]=[0x84E,0x869]
            check('complete acre after two source-priority removals',cells,struct.pack('>256H',*acre));check('removed candidate flags',bits,bytes(32))
            debug.write_memory(bits,wanted);put(counts,0);resident('af_v3_tree_reset_info',[bits,counts,counts+1,cells])
            check('both dead sapling types leave the candidate set',bits,bytes(32));check('dead saplings are not counted',counts,bytes(4))
            select(False);at=field(0x863);resident('af_v3_tree_daily_plant',[at,info],0)
            check('unselected imported tree retains native fallback',at,struct.pack('>H',0x863))
        check('complete loaded owner code/data remains unchanged',root,loaded[:sum(sections[:3])] if contents else loaded)
        check('shared packet remains unchanged',r['ram'],code)
        for at in guards:check('fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
        call(0x8002FE00,[r['ram'],8192]);call(0x80034CE0,[r['ram'],8192]);call(0x8009C040,[allocation])
    for at,want in saved.items():check('restored original state',at,want)
    check('complete equipment module restored',e['ram'],module)
    return dict(assertions=assertions,daily_entry_lazy_load=True,actual_native_rng=True,
        isolated_acres=True,hidden_contents=contents,temporary_world_restored=contents,
        full_town_renewal=False,ordinary_acquisition_tested=False,requires_checkpoint_restore=True)


def contents_cases(debug,record,call,resident,check,put,short,root,proof,info,cells,select):
    """Actual native scheduling on a temporary grove, restored by the caller."""
    from collections import Counter
    world=0x8012D148
    initial=[]
    for _ in range(30):initial.extend([0x804,0x868,0x804,0x868,0x867,0x863]+[0]*250)
    debug.write_memory(world,struct.pack('>7680H',*initial));debug.write_memory(info,bytes(0x44))
    put(0x8003C590,0x13579BDF)
    # Both native callback arrays must reach the same new money counter.
    for at in (0x4AA8,0x4AD4):
        if debug.read_memory(root+at,4)!=debug.read_memory(root+0x4AA8,4):
            raise ValueError('Daily content callback arrays disagree')
    for native_offset,hidden,field in ((0xC6C,0x81,0x40),(0xCA8,0x80,0x41)):
        short(cells,hidden);put(info+0x20,3)
        call(root+native_offset,[cells,info],proof,1)
        check('native callback records imported hidden content',info+field,b'\x08')
    short(cells,0x7F);resident('af_v3_tree_count_money',[cells,info],1)
    check('native money record offset',info+0x34,struct.pack('>I',1))
    resident('af_v3_tree_count_eligible',[world],4)
    # These are the cartridge's complete schedulers, not rewritten test loops.
    call(root+0xEC0,[0],proof);call(root+0xF34,[0],proof);call(root+0x1110,[0],proof)
    actual=struct.unpack('>7680H',debug.read_memory(world,30*512));totals=Counter(actual)
    outcomes=(totals[0x5E]+totals[0x81],totals[0x5F]+totals[0x80],totals[0x69]+totals[0x7F])
    record(dict(hidden_content_totals=dict(bees=outcomes[0],furniture=outcomes[1],bells=outcomes[2]),
        assertion='passed' if outcomes==(5,2,30) else 'failed'))
    if outcomes!=(5,2,30):raise ValueError('Native hidden-content quantities changed')
    bee_columns=set();ftr_columns=set();native_changed=gold_changed=0
    for i,(before,after) in enumerate(zip(initial,actual,strict=True)):
        permitted={0x804,0x5E,0x5F,0x69} if before==0x804 else {0x868,0x81,0x80,0x7F} if before==0x868 else {before}
        if after not in permitted:raise ValueError('Hidden content changed tree family or protected cell')
        if before!=after:
            native_changed+=before==0x804;gold_changed+=before==0x868
        col=(i//256)%5
        if after in (0x5E,0x81):bee_columns.add(col)
        if after in (0x5F,0x80):ftr_columns.add(col)
    if len(bee_columns)!=5 or len(ftr_columns)!=2 or not native_changed or not gold_changed:
        raise ValueError('Mixed-tree native acre distribution missing')
    record(dict(native_changed=native_changed,gold_changed=gold_changed,
        bee_columns=sorted(bee_columns),furniture_columns=sorted(ftr_columns),assertion='passed'))
    retained=debug.read_memory(world,30*512);seed=debug.read_memory(0x8003C590,4)
    call(root+0xEC0,[0x3E],proof)
    call(root+0xF34,[sum(1<<(x+1) for x in ftr_columns)],proof)
    call(root+0x1110,[30],proof)
    check('existing quantities prevent duplicate refill',world,retained)
    check('no RNG consumed when quotas are met',0x8003C590,seed)
    select(False);debug.write_memory(cells,bytes(512));short(cells,0x868);short(cells+2,0x804)
    resident('af_v3_tree_count_eligible',[cells],1)
    resident('af_v3_tree_change_content',[cells,0x5E,1])
    check('unselected refill uses original native family',cells,struct.pack('>2H',0x868,0x5E))
    debug.write_memory(info,bytes(0x44));short(cells,0x81);put(info+0x20,3)
    call(root+0xC6C,[cells,info],proof,0);check('unselected hidden tree is not recorded',info+0x40,bytes(1))


def tree_states(debug,rom_path,record):
    """Actual lazy loading and shared helpers, not an ordinary world playthrough."""
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed tree-state cartridge')
    equipment=report['equipment_resources'];r=equipment['scenery'];t=r['tree_states'];files=by_vrom(image)
    blob=files[BLOB].extract(image);core=files[CODE_VROM].extract(image);boot=boot_proofs(image);assertions=0
    for row in t['core_consumers']:
        a,b=row['start'],row['end'];boot[a]=(a,core[a-CODE_RAM:b-CODE_RAM])
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(tree_state_check=label,address=f'{at:08X}',bytes=len(want),
            expected_sha256=sha256(want),observed_sha256=sha256(got),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Tree-state mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None,want=None):
        result=debug.call(f'{at:08X}',[v&0xFFFFFFFF for v in args],
            return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Tree-state native return mismatch')
        return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+'I'*len(values),*values))
    saved={at:debug.read_memory(at,n) for at,n in [(o['config'][0],4) for o in r['owners']]+
        [(r['ram'],4096),(t['cache_word'],4),(0x80460020,192),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16)]}
    module=debug.read_memory(equipment['ram'],equipment['bytes'])
    size=0x15000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Tree-state fixture allocation failed')
    root=allocation+16;bridge=allocation+0x14000;output=allocation+0x14100;position=output+64
    edge=b'AFTS'*4;guards=[allocation,bridge-16,output-16,output+16,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40]
    debug.write_memory(allocation,bytes(size))
    for at in guards:debug.write_memory(at,edge)
    parent=next(x for x in equipment['player_actions']['equipment_selection']['rows'] if x['item_id']=='223B')
    def select(enabled):
        profile=bytearray(saved[0x80460020]);profile[parent['profile_byte']]&=~parent['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    def resident(name,args=(),want=None):
        stub=struct.pack('>2I',jump(r['code']['symbols'][name]),0)
        debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        return call(bridge,args,(bridge,stub),want)
    try:
        # Town loading can query growth before the first seasonal actor exists.
        for owner in r['owners']:put(owner['config'][0],0)
        debug.write_memory(r['ram'],bytes(4096));put(t['cache_word'],0);select(False)
        call(0x8002FE00,[r['ram'],4096]);call(0x80034CE0,[r['ram'],4096])
        call(0x800A5970,[0x800,0,4],want=0x801)
        code=blob[r['blob_offset']:r['blob_offset']+r['bytes']]
        check('first native growth query loads entire packet without an owner',r['ram'],code)
        check('successful CRC cached',t['cache_word'],struct.pack('>I',r['crc32']))
        call(0x800A56F0,[0x804,0],want=4)
        call(0x800A5970,[0x863,3,4],want=0x863)
        call(0x800A56F0,[0x864,0],want=0x864)
        select(True)
        for item,days,cap,want in ((0x863,-1,4,0x863),(0x863,0,4,0x864),
                (0x863,2,4,0x866),(0x863,3,4,0x867),(0x863,100,2,0x865),
                (0x863,0x7FFFFFFF,4,0x867),(0x868,100,4,0x868),(0x869,3,4,0x869)):
            call(0x800A5970,[item,days,cap],want=want)
        for item,want in ((0x863,0x863),(0x864,0x7B),(0x865,0x7C),(0x866,0x7D),
                          (0x867,0x7E),(0x868,0x7E),(0x7F,0x7E),(0x80,0x7E),(0x81,0x7E)):
            call(0x800A56F0,[item,0],want=want)
        call(0x800A56F0,[0x864,1],want=0x864)
        call(0x800A5970,[0x800,0,4],want=0x801)
        for variant,o in enumerate(r['owners']):
            owner,rel=(files[o[k]].extract(image) for k in ('vrom','reloc'))
            sections=struct.unpack_from('>5I',rel);n=o['resident_bytes']
            if root+n+len(rel)>=bridge-16:raise ValueError('Tree-state owner overlaps fixture')
            loaded=relocate_verified_data(SimpleNamespace(ram=o['ram'],resident_bytes=n,sections=sections),owner,rel,root)
            call(0x800262D0,[o['vrom'],o['vrom']+len(owner),o['ram'],o['ram']+n,root,root+n,len(rel)])
            check(o['role']+' complete loaded planting owner',root,loaded);put(o['config'][0],root)
            cases=((True,0x2202,0x5D,0x863,1),(False,0x2202,0x5D,0x2202,0),
                   (True,0x2202,0,0x2202,0),(True,0x2800,0,0x805,1))
            for enabled,item,hole,want,action in cases:
                select(enabled);debug.write_memory(output,b'?'*16)
                xyz=struct.pack('>3f',1,2,3);debug.write_memory(position,xyz)
                resident(f'af_v3_tree_bury{variant}',[item,hole,position,output+2],action)
                check(o['role']+' bounded bury result',output,b'??'+struct.pack('>H',want)+b'?'*12)
                check('bury position unchanged',position,xyz)
        check('loaded shared code unchanged',r['ram'],code)
        for at in guards:check('fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
        call(0x8002FE00,[r['ram'],4096]);call(0x80034CE0,[r['ram'],4096]);call(0x8009C040,[allocation])
    for at,want in saved.items():check('restored original state',at,want)
    check('entire resident equipment module restored',equipment['ram'],module)
    return dict(assertions=assertions,owner_loads=4,planting_cases=16,lazy_loading_before_owner=True,
        code_uploaded=False,profile_enabled_only_in_paused_ram=True,ordinary_acquisition_tested=False,
        requires_checkpoint_restore=True)


def exercise(debug,rom_path,record):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed scenery cartridge')
    equipment=report['equipment_resources'];r=equipment['scenery'];files=by_vrom(image)
    blob=files[BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(scenery_check=label,address=f'{at:08X}',bytes=len(want),
            expected_sha256=sha256(want),observed_sha256=sha256(got),assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Scenery mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None,want=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Scenery native return mismatch')
        return result['return_value']
    def put(at,*words):debug.write_memory(at,struct.pack('>'+str(len(words))+'I',*words))
    saved={at:debug.read_memory(at,n) for at,n in [(o['config'][0],4) for o in r['owners']]+
        [(r['ram'],4096),(0x80460020,192),(TEST_STACK-0x800,16),(TEST_STACK+0x40,16)]}
    size=0x17000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Scenery native fixture allocation failed')
    root=allocation+16;bridge=allocation+0x14000;data=allocation+0x14100
    graph=allocation+0x14400;anchor=allocation+0x14800;node=anchor+72;gfx=allocation+0x15000
    guards=[allocation,bridge-16,graph-16,anchor-16,gfx-16,gfx+0x1000,allocation+size-16,
            TEST_STACK-0x800,TEST_STACK+0x40];edge=b'AFSC'*4
    debug.write_memory(allocation,bytes(size))
    for at in guards:debug.write_memory(at,edge)
    def resident(name,args=(),want=None):
        code=struct.pack('>2I',jump(r['code']['symbols'][name]),0)
        debug.write_memory(bridge,code);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        return call(bridge,args,(bridge,code),want)
    parent=next(x for x in equipment['player_actions']['equipment_selection']['rows'] if x['item_id']=='223B')
    selection=equipment['player_actions']['equipment_selection']
    entry=selection['table_ram']+16+0x3B*8
    # This component enables only the existing profile bit in paused RAM. It
    # does not change readiness, an on-disk save, or available browser choices.
    check('complete ready shovel row',entry,struct.pack('>HbBHBB',0x223B,parent['native_kind'],0,
        parent['profile_byte'],parent['profile_mask'],1))
    def select(enabled):
        profile=bytearray(saved[0x80460020]);profile[parent['profile_byte']]&=~parent['profile_mask']
        if enabled:profile[parent['profile_byte']]|=parent['profile_mask']
        debug.write_memory(0x80460020,profile)
    try:
        call(0x80026B44,[r['ram'],r['vrom'],r['bytes']],want=0)
        code=blob[r['blob_offset']:r['blob_offset']+r['bytes']]
        check('complete cartridge-loaded scene code',r['ram'],code)
        call(0x80195938,[r['ram'],len(code)],want=r['crc32'])
        call(0x8002FE00,[r['ram'],len(code)]);call(0x80034CE0,[r['ram'],len(code)])
        term=call(0x800CA070);term=term if term<18 else 0
        for variant,o in enumerate(r['owners']):
            owner,rel=(files[o[k]].extract(image) for k in ('vrom','reloc'))
            sections=struct.unpack_from('>5I',rel);n=o['resident_bytes'];cfg=o['config']
            if root+n+len(rel)>=bridge-16:raise ValueError('Scenery fixture overlaps complete loaded owner')
            loaded=relocate_verified_data(SimpleNamespace(ram=o['ram'],resident_bytes=n,sections=sections),owner,rel,root)
            call(0x800262D0,[o['vrom'],o['vrom']+len(owner),o['ram'],o['ram']+n,root,root+n,len(rel)])
            check(o['role']+' complete loaded owner/BSS',root,loaded);put(cfg[0],root)
            stub=struct.pack('>2I',jump(equipment['ground_categories']['code']['symbols']['af_v3_ground_prepare']),0)
            debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            call(bridge,[variant],(bridge,stub),root)
            table_before=debug.read_memory(root+cfg[6],cfg[7]*8)
            bank=next(b for b in r['banks'] if b['season']==o['role']);bank_at=root+o['bank_offset']
            original=blob[bank['blob_offset']:bank['blob_offset']+bank['bytes']]
            call(0x80026B44,[bank_at,bank['vrom'],bank['bytes']],want=0)
            check(o['role']+' complete raw resource DMA',bank_at,original)
            resident('af_v3_scenery_relocate',[root,variant],1)
            expected=bytearray(original);h=struct.unpack_from('>32I',original)
            for k in (4,6):
                for i in range(h[k+1]):
                    at=u32(original,h[k]+4*i);value=u32(original,at)+(bank_at if k==4 else bank_at&0x1FFFFFFF)
                    struct.pack_into('>I',expected,at,value)
            for i in range(h[9]):
                at,kind=struct.unpack_from('>II',original,h[8]+8*i)
                target=root+cfg[10] if kind else r['code']['symbols'][f'af_v3_scenery_body{variant}']
                struct.pack_into('>I',expected,at,target)
            for i in range(h[13]):
                at=h[12]+16*i+4;struct.pack_into('>I',expected,at,u32(original,at)+cfg[8])
            struct.pack_into('>4I',expected,h[17],0x27BDFFE0,0xAFB00018,jump(root+cfg[11]+8),0)
            pal=h[14]+original[h[16]+term]*32;expected[h[15]:h[15]+32]=original[pal:pal+32]
            struct.pack_into('>I',expected,12,0x53434E31);struct.pack_into('>I',expected,72,term)
            check(o['role']+' every relocated resource and active palette',bank_at,expected)
            table=bytearray(table_before);table[cfg[8]*8:(cfg[8]+10)*8]=expected[h[10]:h[10]+80]
            check(o['role']+' original, equipment, NONE, and imported rows',root+cfg[6],table)
            proof=(root,loaded[:sections[0]]);select(True)
            for i in range(h[13]):
                at=h[12]+16*i;fg=u32(original,at);debug.write_memory(data,edge+bytes(12)+edge)
                call(root+cfg[11],[fg,data+16,0,root+o['native_type_table']['offset']],proof)
                check(o['role']+f' selected foreground {fg:04X}',data,edge+expected[at+4:at+16]+edge)
            select(False)
            # Use a bounded, clear collision record for native low-ID fallback.
            native_types=data+64;put(native_types,*([data+96]*6));debug.write_memory(data+96,bytes(12))
            debug.write_memory(data+192,bytes(64))
            call(root+cfg[11],[0x863,data+16,data+192,native_types],proof)
            check(o['role']+' disabled import uses safe native empty row',data+16,bytes(12))
            native_category=call(0x800A5630,[0x2200])
            call(root+cfg[11],[0x2200,data+16,data+192,native_types],proof)
            check(o['role']+' ordinary tool retains native category',data+18,struct.pack('>H',cfg[7]-71+native_category))
            select(True)
            # Execute the real native body loop through its palette callback.
            part=u32(expected,h[10]);lists=u32(debug.read_memory(part+8,4),0)
            draw=u32(debug.read_memory(lists,4),0);display=u32(debug.read_memory(part,4),0)
            debug.write_memory(anchor,bytes(68)+struct.pack('>hBB',256,0,0))
            matrix=struct.pack('>16f',*[float(i%5==0) for i in range(16)])
            debug.write_memory(node,matrix+bytes(4)+struct.pack('>hBB',-1,0,0))
            put(graph+0x298,gfx,gfx+0x1000);put(data+128,gfx)
            resident(f'af_v3_scenery_body{variant}',[graph,data+128,draw,node,display])
            head=u32(debug.read_memory(data+128,4),0);tail=u32(debug.read_memory(graph+0x29C,4),0)
            if not gfx<head<tail<=gfx+0x1000:raise ValueError('Scenery graphics arena bounds failed')
            lists=[p for op,p in struct.iter_unpack('>II',debug.read_memory(gfx,head-gfx)) if op==0xDE000000]
            indices=debug.read_memory(draw+4,2)
            wanted=[u32(debug.read_memory(display+i*4,4),0) for i in indices]
            if lists!=wanted:raise ValueError('Scenery material/matrix/geometry ordering failed')
            record(dict(scenery_draw=o['role'],lists=lists,assertion='passed'))
        for at in guards:check('fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,data_saved in saved.items():debug.write_memory(at,data_saved)
        call(0x8002FE00,[r['ram'],4096]);call(0x80034CE0,[r['ram'],4096])
        call(0x8009C040,[allocation])
    for at,want in saved.items():check('restored original state',at,want)
    return dict(seasons=4,foreground_cases=56,assertions=assertions,actual_body_drawers=4,
        gpu_rendered=False,ordinary_acquisition_tested=False,requires_checkpoint_restore=True)
