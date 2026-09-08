"""Bounded native call-site, mode-two receipt, complete reader, and retry batch."""

import struct

from aflib import sha256
from event_actor import ActorImage,RAM,NEW_VROM,METADATA
from flash_mail import SAVE_RAM,SAVE_BYTES
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4
SOURCE,FLAG,MAIL,FLAGS = 0x80135C44,0x80135CE1,0x801361E4,0x8013628A


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0
    def check(label,at,expected):
        nonlocal assertions
        actual = read(at,len(expected))
        record({'event_actor_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected: raise ValueError('Native event check failed: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Event call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def words(*values): return struct.pack('>'+str(len(values))+'I',*values)
    def jump(at): return 0x08000000|((at>>2)&0x3FFFFFF)
    saved = read(SAVE_RAM,SAVE_BYTES)
    module,report = request['module'],request['report'];symbols = report['symbols']
    capital = int(module['symbols']['af_mail_generation_capital'],16)
    globals_before = {at:read(at,size) for at,size in ((capital,4),(0x8003C590,4),(0x80140680,200))}
    data,reloc = bytes.fromhex(request['data']),bytes.fromhex(request['relocation'])
    size = 0xE000;allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Event fixture allocation failed')
    base = allocation+16;relocation_at = base+len(data)
    sale,redd,gate,arena,work = (allocation+at for at in (0xB000,0xB040,0xB080,0xB100,0xC000))
    if relocation_at+len(reloc)+16>sale or work+4720+16>allocation+size-16:
        raise ValueError('Event fixture exceeds owned allocation')
    edges = (allocation,relocation_at+len(reloc),sale-16,gate+48,arena-16,arena+16,
             work-16,work+4720,allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    spec = ActorImage(RAM,len(data),struct.unpack_from('>5I',reloc))
    loaded = relocate_verified_data(spec,data,reloc,base)
    check('installed native event ownership',METADATA,bytes.fromhex(request['metadata']))
    call(0x800262D0,[NEW_VROM,NEW_VROM+len(data),RAM,RAM+len(data),base,relocation_at,len(reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    check('complete native cartridge event relocation',base,loaded)
    check('complete native event relocation table',relocation_at,reloc)
    # Enter the actual selected-template JAL/delay slot with its original frame.
    # Stock/date selection is deliberately outside this batch's fixture boundary.
    sale_code = words(0x27BDFF40,0xAFBF0024,jump(base+0x8095C080-RAM),0)
    redd_code = words(0x27BDFFE0,0xAFBF0014,jump(base+0x8095BC48-RAM),0)
    write(sale,sale_code);write(redd,redd_code)
    # Exercise the real schedule flag gate and patched wrapper call. Leave at
    # its end through two owned test-only instructions, before unrelated events.
    gate_code = words(0x27BDFF78,0xAFBF0034,0x24020001,jump(base+0x80961904-RAM),0,
                      0x8FBF0034,0x03E00008,0x27BD0088)
    write(gate,gate_code)
    exit_at = 0x80961934-RAM
    patched = bytearray(loaded[:report['text_bytes']]);patched[exit_at:exit_at+8] = words(jump(gate+20),0)
    write(base+exit_at,patched[exit_at:exit_at+8])
    proof = (base,bytes(patched))
    call(0x8009C0C0,[arena,arena+4,arena+8]);heap = read(arena,12)

    def fixture(case):
        before = bytearray(i%251 for i in range(SAVE_BYTES))
        before[SOURCE-SAVE_RAM:SOURCE-SAVE_RAM+156] = bytes.fromhex(case['source'])
        before[FLAG-SAVE_RAM] = 1
        write(SAVE_RAM,before);write(capital,words(case['capital']))
        write(base+symbols['af_event_pending'],bytes(172))
        write(base+symbols['af_event_busy'],bytes(4))
        if case['count']:
            call(base+symbols['af_event_sale_fields'],[SOURCE,case['count']],proof=proof)
            check('captured original selected item count',base+symbols['af_event_count'],words(case['count']))
        return before

    def publish(case,expected):
        is_sale = case['count']!=0;at,code = (sale,sale_code) if is_sale else (redd,redd_code)
        call(at,[case['template'],55 if is_sale else 54,2 if is_sale else 3],expected,(at,code))

    def complete(case,before):
        expected = bytearray(before);expected[FLAG-SAVE_RAM] = 0
        expected[MAIL-SAVE_RAM:MAIL-SAVE_RAM+164] = bytes.fromhex(case['mail'])
        expected[FLAGS-SAVE_RAM:FLAGS-SAVE_RAM+2] = bytes(2)
        check('whole save contains only complete selected letter and receipt flags',SAVE_RAM,expected)
        call(int(module['symbols']['af_mail_restore'],16),[work+3552,MAIL+42,122,work],1)
        check('complete saved notice restores English header body and footer',work+3552,bytes.fromhex(case['text']))
        call(gate,expected=1,proof=(gate,gate_code))
        check('native cleared schedule gate prevents duplicate publication',SAVE_RAM,expected)
        check('source capitalization retained',capital,words(case['capital']))
        for at in edges: check('owned event fixture guard',at,EDGE)

    for case in request['cases']:
        before = fixture(case);publish(case,1);complete(case,before)
    config = MODULE_RAM+68
    for case in (request['cases'][0],request['cases'][-1]):
        before = fixture(case)
        check('enabled full event catalogue',config,words(0x03000000));write(config,bytes(4))
        publish(case,0)
        pending = bytearray(before);pending[FLAG-SAVE_RAM] = case['flag']
        check('failed registration retains source and old letter with exact pending selector',SAVE_RAM,pending)
        call(gate,expected=0,proof=(gate,gate_code))
        check('actual schedule gate retries without rerolling selection',SAVE_RAM,pending)
        write(base+symbols['af_event_pending'],bytes(172))
        write(config,words(0x03000000))
        call(gate,expected=1,proof=(gate,gate_code))
        complete(case,before)
    call(0x8009C0C0,[arena,arena+4,arena+8]);check('native heap accounting retained',arena,heap)
    check('event executable code retained including owned test-only exit',base,bytes(patched))
    write(base+exit_at,loaded[exit_at:exit_at+8])
    check('event executable restored to installed code',base,loaded[:report['text_bytes']])
    check('resident module guard',GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    check('native RNG untouched',0x8003C590,globals_before[0x8003C590])
    for at,value in globals_before.items(): write(at,value);check('live global restored',at,value)
    call(0x8009C040,[allocation])
    return {'complete_event_cases':len(request['cases']),'event_actor_assertions':assertions,
            'actual_registration_calls':True,'actual_pending_flag_gate':True,'cache_loss_retries':2,
            'normal_stock_selection':False,'flash_save_reload':False,'normal_scheduling':False,
            'hardware_verified':False,'requires_checkpoint_restore':True}
