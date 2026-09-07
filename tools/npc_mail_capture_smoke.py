"""Compare original NPC creators with scoped full-source capture on native MIPS.

The test owns all temporary allocations, restores native instructions/state,
and requires a complete emulator checkpoint restoration. It does not send mail.
"""

from dataclasses import replace
import struct

from aflib import sha256
from audit_mail_templates import template_fields
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
from npc_mail_capture import RAM,WORD_HASH,ALIAS_HASH,relocate,validate
from npc_mail_generation import GROUPS,BAD_BASES
from npc_mail_names import unpack_aliases
from npc_mail_words import unpack_words
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4
FREE = 0x80140680
RNG = (0x8003C590,0x800419F0)


def exercise(debug,request,record):
    read = debug.read_memory
    def write(at,value):
        debug.write_memory(at,value)
        record({'npc_capture_fixture_write':f'{at:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,at,expected):
        value = read(at,len(expected))
        record({'npc_capture_check':label,'address':f'{at:08X}','bytes':len(value),
                'assertion':'passed' if value == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value != expected: raise ValueError('NPC capture mismatch: '+label)
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'NPC capture {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    data,reloc = bytes.fromhex(request['code']),bytes.fromhex(request['relocations'])
    report,module = request['report'],request['module']
    validate(data,reloc,report,module)
    symbols = report['symbols']
    session = int(module['symbols']['af_npc_mail_session'],16)
    check('no older capture session',session,bytes(4))
    for at,value in request['guards'].items(): check('verified native helper',int(at,16),bytes.fromhex(value))
    hooks = [(at,bytes.fromhex(before),bytes.fromhex(after)) for at,before,after in request['hooks']]
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((FREE,200),(0x80142CF0,0x34C),*((at,4) for at in RNG))}
    whole = request.get('whole_creator',False)
    size = 0xA000
    allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('NPC capture test allocation failed')
    base = allocation+16
    relocation_at = base+len(data)+16
    state = (relocation_at+len(reloc)+31)&~15
    if whole:
        stage,generation = state+448,state+624
        player,animal,remail,probe = state+5360,state+5392,state+5424,state+5488
        destination,capital_at = state+5552,state+5728
    else:
        stage,player,animal,remail = state+464,state+656,state+688,state+720
        generation = state+768
        probe = generation+4736
        destination,capital_at = stage,0
    if max(probe+64,destination+176,capital_at+32) > allocation+size-16:
        raise ValueError('NPC capture fixture exceeds allocation')
    guards = (allocation,base+len(data),state-16,player+16,animal+16,remail+32,probe+48,allocation+size-16)
    guards += (state+5344,destination-16,capital_at+16) if whole else (state+448,stage+176,generation+4720)
    for at in guards: write(at,EDGE)
    write(TEST_STACK-0x1000,EDGE);write(TEST_STACK+0x30,EDGE)
    loaded = relocate(data,reloc,base,report['imports'].values())
    write(base,data);write(relocation_at,reloc)
    call(0x8002B9C0,[base,relocation_at,RAM],proof=(0x8002B9C0,bytes.fromhex(request['guards']['8002B9C0'])))
    # Relocation writes instructions through the CPU data cache. Match the
    # original loader's writeback/instruction-invalidation sequence before
    # executing the image; debugger-visible bytes alone are not sufficient.
    def flush(at,size):
        for function in (0x8002FE00,0x80034CE0):
            call(function,[at,size],proof=(function,bytes.fromhex(request['guards'][f'{function:08X}'])))
    flush(base,len(data))
    check('native relocation agrees with independent complete-image model',base,loaded)
    check('relocation input retained',relocation_at,reloc)
    text_size = int.from_bytes(reloc[:4],'big')
    def native(name,args,expected=None):
        return call(base+symbols[name],args,expected,proof=(base,loaded[:text_size]))
    words_at,aliases_at = base+symbols['af_npc_word_data'],base+symbols['af_npc_alias_data']
    word_data = data[symbols['af_npc_word_data']:symbols['af_npc_alias_data']]
    alias_data = data[symbols['af_npc_alias_data']:]
    words = unpack_words(word_data,WORD_HASH)
    aliases = unpack_aliases(alias_data,ALIAS_HASH)
    by_name = {row.npc_index:row.name for row in aliases}
    native('af_npc_mail_sources_init',[state+32,words_at,11328,aliases_at,6368],1)
    sources = struct.pack('>3I',words_at,aliases_at,0x41464353)
    check('complete borrowed source descriptor',state+32,sources)
    # Failed whole-resource validation must not publish even one descriptor byte.
    write(words_at+11327,b'!')
    native('af_npc_mail_sources_init',[state+32,words_at,11328,aliases_at,6368],0)
    check('changed resource retains prior descriptor',state+32,sources)
    write(words_at+11327,word_data[-1:])
    native('af_npc_mail_sources_init',[state+32,words_at,11328,aliases_at,6368],1)
    for row in words[::32]+words[31::32]:
        write(probe,b'!'*18)
        native('af_npc_mail_source_word',[probe,state+32,row.slot,row.native_id],1)
        check('complete sixteen-byte phrase and padding',probe,b'\x10\0'+row.text.ljust(16,b' '))
    for index in (0,1,62,107,150,178,200,215):
        native('af_npc_mail_source_name',[probe,state+32,0xE000+index],1)
        check('full English identity lookup',probe,b'\x08\0'+by_name[index]+bytes(8))
        row = next(row for row in aliases if row.npc_index == index)
        write(probe+32,row.key)
        native('af_npc_mail_source_alias',[probe,state+32,probe+32],1)
        check('full English saved-key lookup',probe,b'\x08\0'+row.name+bytes(8))
    write(probe,b'!'*18)
    write(probe+32,b'??????')
    native('af_npc_mail_source_alias',[probe,state+32,probe+32],0)
    check('unknown alias retains destination',probe,b'!'*18)
    # Use one real saved NPC identity and the real town population for native
    # other-villager selection. Only the private copy's personality varies.
    population = read(0x80130DB8,0x528*15)
    identity = next((population[i:i+12] for i in range(0,len(population),0x528)
                     if 0xE000 <= int.from_bytes(population[i:i+2],'big') < 0xE0D8),None)
    if identity is None: raise ValueError('NPC capture needs a populated isolated town')
    sender = int.from_bytes(identity[:2],'big')-0xE000
    key = next(row.key for row in aliases if row.npc_index == sender)
    pid = b'PLAYER'+identity[4:10]+identity[2:4]+b'\x30\x01'
    if len(pid) != 16: raise ValueError('NPC capture player fixture size changed')
    write(player,pid)
    town = read(call(0x800950D8),6)
    cleared = bytearray(164)
    write(stage,cleared)
    call(0x8009C384,[stage])
    cleared = read(stage,164)
    successes,failures,with_gifts = 0,0,0
    catalog = bytes.fromhex(request['catalog'])
    def fixture(index):
        foreign,condition,looks,capital = index//24,(index//12)%2,(index//2)%6,index%2
        anm = identity[:11]+bytes((looks,))
        rem = bytes(4)+key+b'AWAY  '+bytes((looks,0))
        write(animal,anm);write(remail,rem)
        args = [stage,player,animal,remail if foreign else 0,condition,foreign]
        seed = (0x12345678+index*0x12345)&0xFFFFFFFF
        write(stage,cleared);write(FREE,b'!'*200)
        write(RNG[0],seed.to_bytes(4,'big'));write(RNG[1],bytes(4))
        return foreign,condition,looks,capital,args
    # Finish all original baselines before installing a single hook. This
    # avoids alternating self-modifying code and keeps baseline execution
    # genuinely original, including the original preparation calls.
    baselines = {}
    for index in range(48):
        *_,args = fixture(index)
        call(0x800A9028,args)
        baselines[index] = read(stage,164),read(FREE,200),{at:read(at,4) for at in RNG}
        check('original creator retains complete save',SAVE_RAM,saved)
    for at,before,after in hooks:
        check('unpatched call before scoped installation',at,before)
        write(at,after)
    flush(0x800A8C48,0x398)
    for index in range(48):
        foreign,condition,looks,capital,args = fixture(index)
        baseline,baseline_fields,baseline_rng = baselines[index]
        prefix = struct.pack('>8I',base+symbols['af_npc_mail_capture_event'],*args[:4],condition,foreign,capital)
        write(state,prefix+sources+bytes(400))
        if whole:
            write(destination,b'!'*164);write(capital_at,capital.to_bytes(4,'big'))
            created = native('af_npc_mail_create',[state,destination,session,capital_at])
            check('whole creator releases session before returning',session,bytes(4))
        else:
            write(session,state.to_bytes(4,'big'))
            call(0x800A9028,args)
            write(session,bytes(4))
        captured = read(state+44,368)
        selection = read(state+412,14)
        record({'npc_capture_state':index,'state':read(state+428,16).hex(),
                'captured_fields':captured.hex(),'selection':selection.hex()})
        check('complete ordered capture',state+428,struct.pack('>4I',3,0,11,1 if foreign else 2))
        for at,expected in baseline_rng.items(): check('same final original RNG state',at,expected)
        check('unchanged native ten-byte fields',FREE,baseline_fields)
        check('unchanged identity gift and received status',stage,baseline[:39])
        check('unchanged native mail type and paper',stage+40,baseline[40:42])
        check('creator capture retains entire save',SAVE_RAM,saved)
        mask = int.from_bytes(captured[:4],'big')
        initial = int.from_bytes(read(state+28,4) if whole else captured[4:8],'big')
        if (mask,initial) != (0xFFFF if foreign else 0x3FFF,capital):
            raise ValueError('NPC capture field mask/capital mismatch')
        fields = {}
        for slot in range(20):
            raw = captured[8+slot*18:8+(slot+1)*18]
            length,article = raw[:2]
            if mask&(1<<slot): fields[slot] = Field(raw[2:2+length],article)
            elif any(raw): raise ValueError('Unused captured field is not cleared')
            if article or length > 16 or any(raw[2+length:]): raise ValueError('Invalid captured field encoding')
        expected = {0:pid[:6],1:by_name[sender]}
        other_key = baseline_fields[20:26]
        matching = [i for i,name in enumerate(request['native_names']) if bytes.fromhex(name) == other_key]
        if len(matching) != 1: raise ValueError('Native selected other name is not uniquely identified')
        expected[2] = by_name[matching[0]]
        if foreign: expected.update({14:b'AWAY  ',15:town})
        for slot in range(3,14):
            matches = [row for row in words if row.slot == slot and row.text.ljust(16,b' ') == fields[slot].text]
            if not matches: raise ValueError('Complete word is not an approved source')
            native_values = [bytes.fromhex(request['native_words'][row.native_id])[:10].ljust(10,b' ') for row in matches]
            if baseline_fields[slot*10:(slot+1)*10] not in native_values:
                raise ValueError('Captured word does not match original selected native source')
        if any(fields[slot].text != value for slot,value in expected.items()):
            raise ValueError('Captured full saved/selected name differs')
        catalog_id,kind,reserved,*ids = struct.unpack('>HBB5H',selection)
        if (catalog_id,kind,reserved) != (2,condition,0): raise ValueError('Incorrect captured template kind')
        if condition:
            group = GROUPS[foreign][looks]
            if any(not group <= i < group+32 for i in ids): raise ValueError('Incorrect composite personality group')
        elif not BAD_BASES[foreign]+looks*3 <= ids[0] < BAD_BASES[foreign]+looks*3+3 or any(ids[1:]):
            raise ValueError('Incorrect classic selection')
        selected = Record(2,kind,tuple(ids if kind else ids[:1]),tuple(sorted(fields.items())),bool(capital))
        before = b'!'*164 if whole else read(stage,164)
        after_capture = bytearray(captured)
        try:
            parts = templates(catalog,selected)
            needed = set().union(*(template_fields(part) for part in parts.parts))
            selected = replace(selected,fields=tuple((slot,field) for slot,field in selected.fields if slot in needed))
            expected_mail = bytearray(baseline if whole else before)
            expected_mail[39] = 128;expected_mail[42:] = pack(selected)
            full_text = output_bytes(selected,parts)
            after_capture[4:8] = int(format_letter(selected,parts).final_capital).to_bytes(4,'big')
            success = True
        except ValueError:
            expected_mail,success = before,False
        if whole:
            if created != int(success): raise ValueError('Whole creator returned incorrect publication result')
            check('shared capital advances only after complete publication',capital_at,
                  after_capture[4:8] if success else capital.to_bytes(4,'big'))
        else: native('af_mail_generate',[stage,164,state+44,state+412,generation],int(success))
        check('complete generated or retained letter',destination,expected_mail)
        check('capture updates only successful capital state',state+44,after_capture)
        check('selected template IDs retained',state+412,selection)
        if success:
            check('complete English text from actual original creator selections',generation+3552,full_text)
            successes += 1
        else: failures += 1
        if baseline[36:38] != bytes(2): with_gifts += 1
        check('generation retains entire save',SAVE_RAM,saved)
        record({'native_npc_capture_case':index,'foreign':foreign,'good':condition,'looks':looks,
                'initial_capital':capital,'selected_ids':list(selected.templates),'generated':success,
                'gift':baseline[36:38].hex(),'paper':baseline[41],'passed':True})
    if whole:
        # Keep one actual shared capital word across successive creations;
        # deliberately stale work cannot supply the next initial state.
        write(capital_at,(1).to_bytes(4,'big'))
        for sequence,index in enumerate((14,15,38,39,0,1,24,25)):
            initial = int.from_bytes(read(capital_at,4),'big')
            foreign,condition,looks,_,args = fixture(index)
            write(state,struct.pack('>8I',0,0,*args[1:4],condition,foreign,999)+b'!'*400)
            write(destination,b'!'*164)
            native('af_npc_mail_create',[state,destination,session,capital_at],1)
            captured = read(state+44,368)
            selected = struct.unpack('>HBB5H',read(state+412,14))
            fields = []
            mask = int.from_bytes(captured[:4],'big')
            for slot in range(20):
                if mask&(1<<slot):
                    at = 8+slot*18
                    fields.append((slot,Field(captured[at+2:at+2+captured[at]],captured[at+1])))
            snapshot = Record(2,selected[1],tuple(selected[3:] if selected[1] else selected[3:4]),tuple(fields),bool(initial))
            parts = templates(catalog,snapshot)
            needed = set().union(*(template_fields(part) for part in parts.parts))
            snapshot = replace(snapshot,fields=tuple((slot,field) for slot,field in snapshot.fields if slot in needed))
            expected = bytearray(baselines[index][0]);expected[39] = 128;expected[42:] = pack(snapshot)
            check('successive creator preserves exact complete metadata and snapshot',destination,expected)
            check('successive creator reads shared initial capital',state+28,initial.to_bytes(4,'big'))
            check('successive creator advances shared final capital',capital_at,
                  int(format_letter(snapshot,parts).final_capital).to_bytes(4,'big'))
            check('successive complete English text',generation+3552,output_bytes(snapshot,parts))
            check('successive creation releases its session',session,bytes(4))
            check('successive creation retains complete save',SAVE_RAM,saved)
            record({'native_npc_creator_sequence':sequence,'initial_capital':initial,'passed':True})
        # Failures must not expose private metadata or an older caller letter.
        for fault in ('source','catalog','foreign_name','already_active','work_alias_capital','work_alias_session'):
            foreign,condition,looks,capital,args = fixture(24)
            write(state,struct.pack('>8I',0,0,*args[1:4],condition,foreign,999)+b'!'*400)
            write(destination,b'!'*164);write(capital_at,(1).to_bytes(4,'big'))
            if fault == 'source': write(words_at+11327,b'!')
            if fault == 'catalog': write(MODULE_RAM+0x44,bytes(4))
            if fault == 'foreign_name': write(remail+4,b'??????')
            if fault == 'already_active': write(session,state.to_bytes(4,'big'))
            before_rng = {at:read(at,4) for at in RNG}
            supplied = capital_at if fault == 'work_alias_capital' else session if fault == 'work_alias_session' else state
            native('af_npc_mail_create',[supplied,destination,session,capital_at],0)
            check('failed whole creator retains complete destination',destination,b'!'*164)
            check('failed whole creator retains shared capital',capital_at,(1).to_bytes(4,'big'))
            check('rejection retains or releases original session correctly',session,
                  state.to_bytes(4,'big') if fault == 'already_active' else bytes(4))
            if fault == 'source': write(words_at+11327,word_data[-1:])
            if fault == 'catalog': write(MODULE_RAM+0x44,(0x03000000).to_bytes(4,'big'))
            if fault in ('source','already_active','work_alias_capital','work_alias_session'):
                for at,value in before_rng.items(): check('pre-creation rejection retains native RNG state',at,value)
            write(session,bytes(4))
            check('whole-creator failure retains entire save',SAVE_RAM,saved)
            record({'native_npc_creator_rejection':fault,'passed':True})
    for at,before,after in hooks:
        check('exact scoped native call hook retained',at,after)
        write(at,before)
    flush(0x800A8C48,0x398)
    for at,before,after in hooks: check('original call restored',at,before)
    for at,value in globals_before.items():
        write(at,value);check('original global restored',at,value)
    check('session detached',session,bytes(4))
    check('source code and both resources retained',base,loaded)
    check('entire save unchanged',SAVE_RAM,saved)
    for at in guards: check('heap guard',at,EDGE)
    check('lower stack guard',TEST_STACK-0x1000,EDGE);check('upper stack guard',TEST_STACK+0x30,EDGE)
    check('module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'native_npc_capture_cases':48,'generated_english_letters':successes,'rejected_generations':failures,
            'original_gifts_retained':with_gifts,'production_hooks_installed':False,
            'whole_creator_tested':whole,'whole_creator_rejections':6 if whole else 0,
            'whole_creator_successive_letters':8 if whole else 0,
            'cartridge_loading_tested':False,'requires_checkpoint_restore':True}
