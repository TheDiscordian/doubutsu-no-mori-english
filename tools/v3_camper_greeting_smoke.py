"""Actual summer owner loading, greeting selection, and installed gift hooks."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from aflib import by_vrom,sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs
import v3_camper_greeting as runtime


def exercise(debug,rom_path,record,*,remaining=False):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=80:
        raise ValueError('Summer greeting probe requires the current ABI 80 cartridge')
    files=by_vrom(rom);g=report['camper_greeting'];boot=boot_proofs(rom)
    def check(label,address,value):
        observed=debug.read_memory(address,len(value))
        record(dict(camper_greeting_check=label,address=f'{address:08X}',bytes=len(value),
            assertion='passed' if observed==value else 'failed',expected_sha256=sha256(value),
            observed_sha256=sha256(observed)))
        if observed!=value:raise ValueError('Native summer greeting mismatch: '+label)
    def call(address,args,allowed=None):
        if address>=0x80400000:
            if not greeting<=address<greeting+g['bytes'] or len(args)>4:
                raise ValueError('Upper-memory call escapes verified greeting owner')
            values={4+i:value for i,value in enumerate(args)};values[31]=MODULE_RAM+0x6480
            regs=window('complete summer selector call',address,MODULE_RAM+0x6480,values)
            result=dict(test_only_function_call=f'{address:08X}',arguments=args,return_value=regs[2]&0xFFFFFFFF)
        else:
            result=debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,verified_code=boot.get(address))
        if allowed is not None:result['assertion']='passed' if result['return_value'] in allowed else 'failed'
        record(result)
        if result.get('assertion')=='failed':raise ValueError('Unexpected native summer greeting result')
        return result['return_value']
    words=runtime.words
    scratch,length=0x80580000,0x18000;pool=report['furniture']['bank_pool']
    if not pool['start']<=scratch<scratch+length<=pool['end']:
        raise ValueError('Greeting probe scratch escapes existing model pool')
    prior_pool=debug.read_memory(scratch,length);saved=debug.read_memory(0x80126EA0,65536)
    private_before=debug.read_memory(0x80136FD8,4);hour_before=debug.read_memory(0x80136FBE,1)
    gift_before=debug.read_memory(runtime.LAST_GIFT,2)
    quest,greeting,normal,manager,actor,animal,private,message,stack=(scratch+o for o in
        (0x10,0x4000,0xD000,0x12800,0x13200,0x13400,0x13A00,0x13C00,0x14800))
    edge=b'V3CG'*4
    for at in (scratch,scratch+length-16,private+0x80,message+0x410,stack+0x200):
        debug.write_memory(at,edge)
    before=debug.command('g')
    if len(before)!=71*16 or int(before[37*16:38*16],16)&0xFFFFFFFF!=0x800D334C:
        raise ValueError('Greeting probe requires a paused native frame')
    original=[int(before[i:i+16],16) for i in range(0,len(before),16)]
    def window(label,start,end,values):
        regs=original.copy();regs[29]=extend(stack);regs[37]=extend(start)
        for i,value in values.items():regs[i]=extend(value)
        bp=f'0,{end:x},4'
        if debug.command('Z'+bp)!='OK':raise ValueError('Greeting window breakpoint refused')
        try:
            if debug.command('G'+''.join(f'{n:016x}' for n in regs))!='OK':
                raise ValueError('Greeting register setup refused')
            try:
                stopped=debug.command('c');raw=debug.command('g')
            except TimeoutError:
                debug.command('?');raw=debug.command('g')
                record(dict(camper_greeting_timeout=label,registers=raw,
                    thread=debug.thread_snapshot(),faulted_thread=debug.read_memory(0x8003CE34,4).hex()))
                raise
            pc=int(raw[37*16:38*16],16)&0xFFFFFFFF
            passed=stopped[:3] in ('T05','S05') and pc==end
            record(dict(camper_greeting_window=label,pc=f'{pc:08X}',assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Native greeting caller window failed: '+label)
            return [int(raw[i:i+16],16) for i in range(0,len(raw),16)]
        finally:
            debug.command('z'+bp);debug.command('G'+before)
    for v,rv,ram,target in ((runtime.QUEST,runtime.QUEST_RELOC,runtime.QUEST_RAM,quest),
                            (runtime.NORMAL,runtime.NORMAL_RELOC,runtime.NORMAL_RAM,normal)):
        data,rel=files[v].extract(rom),files[rv].extract(rom);sections=struct.unpack_from('>5I',rel)
        resident=len(data)+sections[3]
        call(0x800262D0,[v,v+len(data),ram,ram+resident,target,target+resident,len(rel)])
        expected=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=resident,sections=sections),
            data,rel,target,memory_end=0x80800000)
        check('complete native owner and relocation',target,expected)
    debug.write_memory(manager,bytes(0x8D8));debug.write_memory(actor,bytes(0x200))
    debug.write_memory(animal,bytes(0x528));debug.write_memory(stack,bytes(0x200))
    debug.write_memory(actor+2,b'\x03');debug.write_memory(actor+6,bytes.fromhex('D08F'))
    debug.write_memory(actor+0x174,words(animal));debug.write_memory(stack+0x150,words(actor))
    debug.write_memory(manager+0x178,words(stack+0x150));debug.write_memory(manager+0x8B0,words(greeting))
    debug.write_memory(stack+0x30,words(manager))
    window('actual quest caller loads expanded greeting owner',quest+0x11C,quest+0x158,{})
    data,rel=files[runtime.VROM].extract(rom),files[runtime.RELOC].extract(rom)
    expected=relocate_verified_data(SimpleNamespace(ram=runtime.RAM,resident_bytes=len(data),sections=g['sections']),
        data,rel,greeting,memory_end=0x80800000)
    check('complete greeting loaded through actual manager',greeting,expected)
    timer=quest+0x809551C8-runtime.QUEST_RAM
    entry=greeting+g['code']['symbols']['af_v3_camper_greeting']-runtime.RAM
    debug.write_memory(0x80136FD8,words(private))
    def pockets(items=(),bells=0,conditions=0,ignore=0):
        payload=bytearray(0x80);struct.pack_into('>15H',payload,0x14,*(list(items)+[0]*(15-len(items))))
        struct.pack_into('>2I',payload,0x34,conditions,bells);debug.write_memory(private,payload)
        debug.write_memory(runtime.LAST_GIFT,struct.pack('>H',ignore))
    pockets()
    for looks,hour in enumerate(() if remaining else (2,7,12,18,23,4)):
        debug.write_memory(animal+11,bytes([looks]));debug.write_memory(0x80136FBE,bytes([hour]))
        kind=3 if hour<5 else 0 if hour<10 else 1 if hour<17 else 2
        first=11754+looks*12+kind*3
        selected=call(entry,[actor,timer,0],range(first,first+3))
        call(0x8009E558,[message,selected,0],(1,))
        check('native selected summer text header',message,words(1,selected))
        call(entry,[actor,timer,1],(g['repeat_messages'][looks],))
    debug.write_memory(animal+11,b'\x04');base=g['repeat_messages'][4]
    imported=int(report['camping']['imports'][0]['item_id'],16)
    cases=(
        ('below Bell threshold',(),2999,0,0,(0,)),
        ('Bell game',(),3000,0,0,(1,)),
        ('full pockets deny Bell game',[0x2200]*15,99999,0,0,(0,)),
        ('native furniture',[0x1000],0,0,0,(2,)),
        ('imported furniture',[imported],0,0,0,(2,)),
        ('both games',[imported],3000,0,0,(1,2)),
        ('wrapped item excluded',[imported],0,1,0,(0,)),
        ('quest item excluded',[imported],0,2,0,(0,)),
        ('last gift excluded',[imported],0,0,imported,(0,)),
        ('later pocket still eligible',[imported,0x2600],0,0,imported,(2,)),
        ('wall eligible',[0x2700],0,0,0,(2,)),
        ('unsupported import excluded',[0x3FFC],0,0,0,(0,)),
        ('shirt excluded',[0x2400],0,0,0,(0,)))
    for label,items,bells,conditions,ignore,offsets in (() if remaining else cases):
        pockets(items,bells,conditions,ignore)
        result=call(entry,[actor,timer,1],tuple(base+n for n in offsets))
        record(dict(summer_eligibility=label,message=result))
    # The changed dispatch window, not only the suffix's standalone entry.
    pockets();debug.write_memory(stack+0x34,words(timer))
    window('installed summer dispatch',greeting+0xC58,greeting+0xC88,{7:actor,6:1})
    debug.write_memory(actor+6,bytes.fromhex('D05E'))
    call(entry,[actor,timer,1],(6394,))
    # Execute both real give-call windows. Use native bzero as a deliberately
    # bounded callback to prove original a0/a1 and return-PC transport; this is
    # not an NPC handover animation or a completed trade.
    for hook,item in ((0x8091F56C,imported),(0x80920AB8,0x2600)):
        debug.write_memory(manager,b'\xA5'*8)
        window('actual normal give hook',normal+hook-runtime.NORMAL_RAM-8,
            normal+hook-runtime.NORMAL_RAM+8,{16:manager,24:item,25:0x8002F4C0})
        check('full last-gift identity',runtime.LAST_GIFT,struct.pack('>H',item))
        check('original callback receives manager and six',manager,bytes(6)+b'\xA5'*2)
        check('original target item store',manager+0x1D8,struct.pack('>H',item))
    debug.write_memory(manager+0x8CC,b'\xA5'*8)
    window('actual constructor last-gift reset',quest+0x8095703C-runtime.QUEST_RAM,
        quest+0x80957048-runtime.QUEST_RAM,{16:manager})
    check('last gift reset',runtime.LAST_GIFT,bytes(2))
    check('original constructor clear retained',manager+0x8CC,bytes(5)+b'\xA5'*3)
    debug.write_memory(0x80136FD8,private_before);debug.write_memory(0x80136FBE,hour_before)
    debug.write_memory(runtime.LAST_GIFT,gift_before)
    check('saved town unchanged',0x80126EA0,saved)
    for at in (scratch,scratch+length-16,private+0x80,message+0x410,stack+0x200):
        check('fixture guard',at,edge)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4))
    debug.write_memory(scratch,prior_pool);check('borrowed pool restored',scratch,prior_pool)
    return dict(complete_owner_loads=3,first_greeting_personalities=0 if remaining else 6,
        repeat_cases=0 if remaining else len(cases)+6,remaining_only=remaining,
        actual_gift_call_windows=2,actual_constructor_reset=True,actual_greeting_loader=True,
        ordinary_conversation_or_trade=False,save_reload_or_hardware=False,requires_checkpoint_restore=True)
