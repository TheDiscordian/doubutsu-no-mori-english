"""Silent native conversation loading, secret selection, and complete readback."""
import struct
from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from npc_mail_show import relocate_verified_data,relocated
from post_office_smoke import CACHE_GUARDS
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from secret_actor import (OverlayImage,SPEC,RAM,START,COMPACT,RESIDENT_BYTES,LIMIT,
                          OWNER_RAM,OWNER_VROM)

EDGE = b'EDGE'*4
RNG,RNG_TEMP,FREE = 0x8003C590,0x800419F0,0x80140680


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory;proofs = [];assertions = 0
    def check(label,at,expected):
        nonlocal assertions
        actual = read(at,len(expected))
        record({'secret_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected: raise ValueError('Native secret-letter mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        if proof is None: proof = next(((base,data) for base,data in proofs if base<=at<base+len(data)),None)
        if at in CACHE_GUARDS:
            size,digest = CACHE_GUARDS[at];data = read(at,size)
            if sha256(data)!=digest: raise ValueError('Changed native cache helper')
            proof = at,data
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Secret call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    module,report = request['module'],request['report'];symbols = module['symbols']
    capital = int(symbols['af_mail_generation_capital'],16)
    for at,value in request['guards'].items(): check('unchanged native helpers',int(at,16),bytes.fromhex(value))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((capital,4),(RNG,4),(RNG_TEMP,4),(FREE,200))}
    data,reloc,owner,owner_reloc,original,original_reloc = (bytes.fromhex(request[k]) for k in
        ('data','relocation','owner','owner_relocation','original','original_relocation'))
    size = 0x13000;allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Secret fixture allocation failed')
    owner_at,scratch,manager,base,old,letter,selected,metrics,animal,work,text = (
        allocation+at for at in (0x10,0x3000,0x3500,0x4000,0xC840,0x11000,0x110C0,0x110D0,0x110E0,0x11100,0x12000))
    if (owner_at+len(owner)>scratch or scratch+len(owner_reloc)>manager
            or manager+0x900>base-16 or base+16+LIMIT>old-16
            or old+RESIDENT_BYTES>letter-16 or letter+164>selected
            or work+3552>text-16 or text+1040>allocation+size-16):
        raise ValueError('Secret fixture ranges overlap')
    edges = (allocation,manager-16,base-16,old-16,letter-16,letter+164,
             work-16,work+3552,text+1040,allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    owner_sections = struct.unpack_from('>5I',owner_reloc)
    loaded_owner = relocate_verified_data(OverlayImage(OWNER_RAM,len(owner),owner_sections),owner,owner_reloc,owner_at)
    call(0x800262D0,[OWNER_VROM,OWNER_VROM+len(owner),OWNER_RAM,OWNER_RAM+len(owner),owner_at,scratch,len(owner_reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    check('cartridge quest-manager code and patched metadata',owner_at,loaded_owner)
    proofs.append((owner_at,loaded_owner[:owner_sections[0]]))
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    # Use the actual manager callback twice, with its ordinary-talk selector.
    # It obtains the new overlay and adjacent relocation from cartridge DMA.
    for moved_base in (base,base+16):
        write(manager,bytes(0x900));write(manager+0x8B0,word(moved_base));write(manager+0x8CA,b'\x02')
        write(moved_base,b'!'*LIMIT)
        call(owner_at+0x80955264-OWNER_RAM,[manager],1)
        loaded = relocate_verified_data(OverlayImage(RAM,len(data),struct.unpack_from('>5I',reloc)),data,reloc,moved_base)
        check('native owner loads complete overlay with original BSS offsets',moved_base,loaded)
        check('native owner sets unchanged init-function offset',manager+0x8B4,word(moved_base+0x809218E8-RAM))
        check('native owner does not overwrite allocation tail',moved_base+len(data),b'!'*(LIMIT-len(data)))
        call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('owner releases temporary relocation allocation',metrics,heap)
    base = moved_base
    proofs += [(base,loaded[:SPEC.sections[0]]),(base+RESIDENT_BYTES,loaded[RESIDENT_BYTES:report['code_end']])]
    loaded_original = relocated(SPEC,original,original_reloc,old)
    write(old,loaded_original);proofs.append((old,loaded_original[:SPEC.sections[0]]))
    call(0x8002FE00,[old,RESIDENT_BYTES]);call(0x80034CE0,[old,RESIDENT_BYTES])
    compact,old_compact = base+COMPACT-RAM,old+COMPACT-RAM
    untouched = bytes((i*7+3)&255 for i in range(132))
    write(animal,bytes.fromhex('e000eaaa4f4c4454574e0300'))
    for case in request['cases']:
        write(old_compact,untouched);write(selected,word(0x12345678))
        write(capital,word(case['capital']));write(RNG,word(case['seed']))
        call(old+START-RAM,[selected,0,0,0],old_compact)
        old_result = read(old_compact,132);rng_end = read(RNG,4);rng_temp = read(RNG_TEMP,4)
        check('original clears selected memory',selected,bytes(4))
        write(FREE,globals_before[FREE]);write(RNG_TEMP,globals_before[RNG_TEMP])
        write(compact,untouched);write(selected,word(0x12345678))
        write(capital,word(case['capital']));write(RNG,word(case['seed']))
        call(base+START-RAM,[selected,0,0,0],compact)
        expected = bytearray(untouched);expected[0] = 0;expected[1] = old_result[1];expected[4] = 128
        expected[5:127] = bytes.fromhex(case['wire'])
        check('complete compact secret letter',compact,expected)
        check('original font paper and gift preserved',compact,old_result[:4])
        check('original date and padding preserved',compact+127,old_result[127:])
        check('paper selection consumes original RNG sequence',RNG,rng_end)
        check('paper selection retains original RNG temporary',RNG_TEMP,rng_temp)
        check('successful secret clears selected memory',selected,bytes(4))
        check('complete secret final capitalization',capital,word(bytes.fromhex(case['text'])[14]))
        call(int(symbols['af_mail_restore'],16),[text,compact+5,122,work],1)
        check('complete compact English readback',text,bytes.fromhex(case['text']))
        call(0x8009C384,[letter]);call(0x800A8344,[letter,compact,0,animal])
        check('native conversion retains entire snapshot',letter+42,bytes.fromhex(case['wire']))
        check('native conversion retains font and marker',letter+38,bytes((0,128)))
        call(int(symbols['af_mail_restore'],16),[text,letter+42,122,work],1)
        check('complete converted English readback',text,bytes.fromhex(case['text']))
        check('secret leaves native free fields alone',FREE,globals_before[FREE])
        record({'native_secret_case':case['choice'],'capital':case['capital'],'passed':True})
    first = request['cases'][0]
    for fault in ('capital','null_selected','overlap_selected'):
        write(compact,untouched);write(selected,word(0x12345678));write(RNG,word(first['seed']))
        write(capital,word(2 if fault=='capital' else 0))
        arg = 0 if fault=='null_selected' else compact+4 if fault=='overlap_selected' else selected
        call(base+START-RAM,[arg,0,0,0],0)
        check('rejection retains compact record: '+fault,compact,untouched)
        check('rejection retains selected memory: '+fault,selected,word(0x12345678))
        check('rejection stops before paper RNG: '+fault,RNG,word(first['rng_first']))
        check('rejection retains capital: '+fault,capital,word(2 if fault=='capital' else 0))
        record({'native_secret_rejection':fault,'passed':True})
    write(compact,loaded[COMPACT-RAM:COMPACT-RAM+132]);write(old_compact,loaded_original[COMPACT-RAM:COMPACT-RAM+132])
    check('secret code data and original BSS retained',base,loaded)
    check('original comparison restored',old,loaded_original);check('quest manager retained',owner_at,loaded_owner)
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('secret retains heap accounting',metrics,heap)
    check('secret does not change save',SAVE_RAM,saved)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    for at in edges: check('secret fixture and stack guard',at,EDGE)
    for at,value in globals_before.items(): write(at,value);check('secret global restored',at,value)
    call(0x8009C040,[allocation])
    return {'complete_secret_cases':30,'secret_rejections':3,'owner_loader_bases':2,'secret_assertions':assertions,
            'debugger_uploaded_creator_bytes':0,'original_comparison_bytes':len(loaded_original),
            'normal_conversation':False,'show_window_tested':False,'hardware_verified':False,'requires_checkpoint_restore':True}
