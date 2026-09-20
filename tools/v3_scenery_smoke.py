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


def daily_growth(debug,rom_path,record):
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
        check('complete loaded owner remains unchanged',root,loaded);check('shared packet remains unchanged',r['ram'],code)
        for at in guards:check('fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
        call(0x8002FE00,[r['ram'],8192]);call(0x80034CE0,[r['ram'],8192]);call(0x8009C040,[allocation])
    for at,want in saved.items():check('restored original state',at,want)
    check('complete equipment module restored',e['ram'],module)
    return dict(assertions=assertions,daily_entry_lazy_load=True,actual_native_rng=True,
        isolated_acres=True,full_town_renewal=False,ordinary_acquisition_tested=False,requires_checkpoint_restore=True)


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
