"""Real cartridge loading without debugger-uploaded creator code or resources."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_catalog import templates
from mail_format import format_letter
from mail_record import unpack,pack
from mail_runtime_test_scenario import output_bytes
from npc_mail_capture import WORD_HASH,ALIAS_HASH
from npc_mail_generation import GROUPS,BAD_BASES
from npc_mail_loader import CONFIG_OFFSET,WORK_BYTES
from npc_mail_names import unpack_aliases
from npc_mail_words import unpack_words
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4
FREE,RNG = 0x80140680,(0x8003C590,0x800419F0)


def exercise(debug,request,record):
    read = debug.read_memory
    def write(at,data):
        debug.write_memory(at,data)
        record({'npc_loader_fixture_write':f'{at:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,at,expected):
        observed = read(at,len(expected))
        record({'npc_loader_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if observed == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(observed)})
        if observed != expected: raise ValueError('NPC cartridge loader mismatch: '+label)
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'NPC loader {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    module = request['module'];symbols = module['symbols']
    loader,session,capital = (int(symbols[name],16) for name in
                              ('af_npc_mail_load','af_npc_mail_session','af_mail_generation_capital'))
    configured = struct.pack('>8I',*module['npc_mail_loader']['configuration'])
    check('installed approved creator configuration',MODULE_RAM+CONFIG_OFFSET,configured)
    check('no prior capture session',session,bytes(4))
    for at,value in request['guards'].items(): check('guarded actual native helper',int(at,16),bytes.fromhex(value))
    hooks = [(at,bytes.fromhex(before),bytes.fromhex(after)) for at,before,after in request['hooks']]
    def flush():
        for at in (0x8002FE00,0x80034CE0):
            call(at,[0x800A8C48,0x398],proof=(at,bytes.fromhex(request['guards'][f'{at:08X}'])))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((FREE,200),(0x80142CF0,0x34C),(capital,4),*((at,4) for at in RNG))}
    allocation = call(0x8009BFC0,[8192])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-8192:
        raise ValueError('Native loader fixture allocation failed')
    stage,destination,player,animal,remail = (allocation+at for at in (16,208,400,432,464))
    metrics,work,text = (allocation+at for at in (512,544,4112))
    guards = (allocation,stage+176,destination+176,player+16,animal+16,remail+32,
              work-16,work+3552,text-16,text+1040,allocation+8176)
    for at in set(guards): write(at,EDGE)
    write(TEST_STACK-0x1000,EDGE);write(TEST_STACK+0x30,EDGE)
    catalog,blob = bytes.fromhex(request['catalog']),bytes.fromhex(request['blob'])
    exports = module['npc_mail_loader']['overlay']['symbols']
    words = unpack_words(blob[exports['af_npc_word_data']:exports['af_npc_alias_data']],WORD_HASH)
    aliases = unpack_aliases(blob[exports['af_npc_alias_data']:module['npc_mail_loader']['configuration'][2]],ALIAS_HASH)
    by_name = {row.npc_index:row.name for row in aliases}
    population = read(0x80130DB8,0x528*15)
    identity = next((population[i:i+12] for i in range(0,len(population),0x528)
                     if 0xE000 <= int.from_bytes(population[i:i+2],'big') < 0xE0D8),None)
    if identity is None: raise ValueError('Cartridge loader test needs a populated isolated town')
    sender = int.from_bytes(identity[:2],'big')-0xE000
    key = next(row.key for row in aliases if row.npc_index == sender)
    pid = b'PLAYER'+identity[4:10]+identity[2:4]+b'\x30\x01';write(player,pid)
    town = read(call(0x800950D8),6)
    write(stage,bytes(164));call(0x8009C384,[stage]);cleared = read(stage,164)
    def heap():
        call(0x8009C0C0,[metrics,metrics+4,metrics+8])
        return read(metrics,12)
    original_heap = heap()
    record({'npc_loader_initial_heap':list(struct.unpack('>3I',original_heap)),
            'creator_allocation_bytes':len(blob)+WORK_BYTES+15})
    def fixture(index):
        foreign,condition,looks,initial = index//24,(index//12)%2,(index//2)%6,index%2
        write(animal,identity[:11]+bytes((looks,)))
        write(remail,bytes(4)+key+b'AWAY  '+bytes((looks,0)))
        write(stage,cleared);write(destination,b'!'*164);write(FREE,b'!'*200)
        write(RNG[0],((0x12345678+index*0x12345)&0xFFFFFFFF).to_bytes(4,'big'));write(RNG[1],bytes(4))
        return foreign,condition,looks,initial,[destination,player,animal,remail if foreign else 0,condition,foreign]
    # Original comparisons run before restored production capture hooks.
    for at,before,after in hooks:
        check('installed capture call before original baselines',at,after);write(at,before)
    flush()
    baselines = {}
    for index in range(48):
        *_,args = fixture(index);call(0x800A9028,[stage,*args[1:]])
        baselines[index] = read(stage,164),read(FREE,200),{at:read(at,4) for at in RNG}
    for at,before,after in hooks: write(at,after)
    flush()
    def created(index,initial,args,label):
        result=call(loader,args)
        if result!=destination:
            # Preserve useful failure evidence before the isolated process exits.
            # This distinguishes unavailable allocation from capture/formatting
            # failure without rerunning the already completed dialogue batch.
            record({'npc_loader_failure':label,'source_case':index,'return_value':result,
                    'heap':list(struct.unpack('>3I',heap())),
                    'temporary_fields_changed':read(FREE,200)!=b'!'*200,
                    'rng':[read(at,4).hex() for at in RNG],
                    'capital':read(capital,4).hex(),'session':read(session,4).hex(),
                    'assertion':'failed'})
            raise ValueError('Cartridge NPC creator rejected the fixture; see recorded heap/capture evidence')
        native,fields,rng = baselines[index]
        result = read(destination,164)
        snapshot = unpack(result[42:],expected_catalog=request.get('catalog_id',2))
        if (snapshot.kind != args[4] or snapshot.initial_capital != bool(initial)):
            raise ValueError('Cartridge creator selected an incorrect kind or initial capital')
        foreign,condition,looks = args[5],args[4],(index//2)%6
        if condition:
            group = GROUPS[foreign][looks]
            if any(not group <= part < group+32 for part in snapshot.templates):
                raise ValueError('Cartridge creator selected an incorrect composite group')
        elif not BAD_BASES[foreign]+looks*3 <= snapshot.templates[0] < BAD_BASES[foreign]+looks*3+3:
            raise ValueError('Cartridge creator selected an incorrect classic group')
        names = {0:pid[:6],1:by_name[sender],14:b'AWAY  ',15:town}
        matches = [i for i,value in enumerate(request['native_names']) if bytes.fromhex(value) == fields[20:26]]
        if len(matches) != 1: raise ValueError('Native selected other villager is not uniquely identified')
        names[2] = by_name[matches[0]]
        for slot,field in snapshot.fields:
            if field.article: raise ValueError('Unexpected NPC capture article')
            if slot in names:
                if field.text != names[slot]: raise ValueError('Incomplete cartridge-loaded English name')
            elif 3 <= slot <= 13:
                matches = [row for row in words if row.slot == slot and row.text.ljust(16,b' ') == field.text]
                if not any(bytes.fromhex(request['native_words'][row.native_id])[:10].ljust(10,b' ')
                           == fields[slot*10:(slot+1)*10] for row in matches):
                    raise ValueError('Complete English word differs from original native selection')
            else: raise ValueError('Unexpected cartridge-generated field slot')
        expected = bytearray(native);expected[39] = 128;expected[42:] = pack(snapshot)
        check('complete original metadata and English snapshot',destination,expected)
        check('original native temporary fields retained',FREE,fields)
        for at,value in rng.items(): check('original RNG state retained',at,value)
        parts = templates(catalog,snapshot)
        call(int(symbols['af_mail_restore'],16),[text,destination+42,122,work],1)
        check('complete cartridge-generated English reconstruction',text,output_bytes(snapshot,parts))
        check('shared final capital',capital,int(format_letter(snapshot,parts).final_capital).to_bytes(4,'big'))
        check('capture scope detached before heap release',session,bytes(4))
        check('entire save retained',SAVE_RAM,saved)
        if heap() != original_heap: raise ValueError('Cartridge creator leaked or changed native heap allocation')
        record({'native_npc_loader_case':label,'source_case':index,'selected_ids':list(snapshot.templates),
                'gift':native[36:38].hex(),'heap_retained':True,'passed':True})
    for index in range(48):
        *_,initial,args = fixture(index);write(capital,initial.to_bytes(4,'big'))
        created(index,initial,args,index)
    write(capital,(1).to_bytes(4,'big'))
    for sequence,index in enumerate((14,15,38,39,0,1,24,25)):
        initial = int.from_bytes(read(capital,4),'big');*_,args = fixture(index)
        created(index,initial,args,f'sequence-{sequence}')
    for fault in ('disabled','crc','entry','already_active','capital','foreign_name','catalog','allocation'):
        *_,args = fixture(24);write(capital,(1).to_bytes(4,'big'))
        if fault == 'disabled': write(MODULE_RAM+CONFIG_OFFSET,bytes(4))
        if fault == 'crc': write(MODULE_RAM+CONFIG_OFFSET+24,bytes(value^255 for value in configured[24:28]))
        if fault == 'entry': write(MODULE_RAM+CONFIG_OFFSET+16,b'\xff'*4)
        if fault == 'already_active': write(session,player.to_bytes(4,'big'))
        if fault == 'capital': write(capital,(2).to_bytes(4,'big'))
        if fault == 'foreign_name': write(remail+4,b'??????')
        if fault == 'catalog': write(MODULE_RAM+0x44,bytes(4))
        reserves = []
        try:
            if fault == 'allocation':
                required = (len(blob)+WORK_BYTES+30)&~15
                for _ in range(128):
                    largest = int.from_bytes(heap()[:4],'big')
                    if largest < required: break
                    reserved = call(0x8009BFC0,[largest])
                    if not reserved: raise ValueError('Controlled heap exhaustion could not reserve a free block')
                    reserves.append(reserved)
                else: raise ValueError('Controlled heap exhaustion exceeded its block limit')
            old_rng = {at:read(at,4) for at in RNG}
            call(loader,args,0)
            check('failed cartridge creator retains full destination',destination,b'!'*164)
            check('failed cartridge creator retains capital',capital,(2 if fault == 'capital' else 1).to_bytes(4,'big'))
            check('failed loader preserves prior scope or detaches its own',session,player.to_bytes(4,'big') if fault == 'already_active' else bytes(4))
            if fault not in ('foreign_name','catalog'):
                for at,value in old_rng.items(): check('pre-creation failure retains RNG',at,value)
            check('failed loader retains entire save',SAVE_RAM,saved)
        finally:
            for reserved in reversed(reserves): call(0x8009C040,[reserved])
        write(MODULE_RAM+CONFIG_OFFSET,configured);write(MODULE_RAM+0x44,(0x03000000).to_bytes(4,'big'))
        write(session,bytes(4))
        if heap() != original_heap: raise ValueError('Cartridge failure did not release its complete allocation')
        record({'native_npc_loader_rejection':fault,'passed':True})
    for at,value in globals_before.items(): write(at,value);check('original global restored',at,value)
    for at,before,after in hooks: check('installed cartridge capture hook restored',at,after)
    check('installed creator configuration restored',MODULE_RAM+CONFIG_OFFSET,configured)
    for at in set(guards): check('fixture heap guard',at,EDGE)
    check('lower stack guard',TEST_STACK-0x1000,EDGE);check('upper stack guard',TEST_STACK+0x30,EDGE)
    check('module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'native_npc_loader_comparisons':48,'native_npc_loader_successive_letters':8,
            'native_npc_loader_rejections':8,'cartridge_loading_tested':True,
            'debugger_uploaded_creator_bytes':0,'delivery_tested':False,'requires_checkpoint_restore':True}
