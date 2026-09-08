"""Own and release a native allocation for exact English glyph draw checks."""

from aflib import sha256
from build_extended_font_probe import RAM, relocate
from extended_font_test_scenario import native_actions
from flash_mail import SAVE_RAM, SAVE_BYTES
from runtime_layout import MODULE_RAM, RESERVATION


def exercise(debug,request,record):
    saved = debug.read_memory(SAVE_RAM,SAVE_BYTES)
    native_font = debug.read_memory(0x8013A680,0x6000)
    native_widths = debug.read_memory(0x80106AF4,256)
    allocation_result = debug.call('8009BFC0',[0x2000])
    record(allocation_result)
    allocation = allocation_result['return_value']
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-0x2000:
        raise ValueError('Native font probe allocation failed')
    base = allocation+16
    report = request['report']
    relocated = relocate(bytes.fromhex(request['binary']),report,base)
    immutable = relocated[:report['symbols']['__font_bss_start']-RAM]
    actions = native_actions(request,base)
    record({'font_allocation':f'{allocation:08X}','bytes':0x2000,
            'relocated_code_sha256':sha256(relocated),'native_actions':len(actions)})
    for action in actions:
        if 'write' in action:
            address,encoded = action['write'];value = bytes.fromhex(encoded)
            debug.write_memory(int(address,16),value)
            record({'test_only_ram_write':address,'bytes':len(value),'data':encoded})
        elif 'read' in action:
            address,length = action['read'];expected = action['expect']
            observed = debug.read_memory(int(address,16),length).hex()
            record({'font_read':address,'bytes':length,'data':observed,'expect':expected,
                    'assertion':'passed' if observed==expected else 'failed'})
            if observed!=expected: raise ValueError('Native font memory differs at '+address)
        elif 'call' in action:
            call = action['call'];target = int(call['address'],16);proof = None
            if base<=target<base+len(immutable): proof = (base,immutable)
            elif target in (0x8002FE00,0x80034CE0):
                proof = (target,bytes.fromhex(request['guards'][f'{target:08X}']))
            result = debug.call(call['address'],call['arguments'],verified_code=proof)
            record(result)
            if 'expect_return' in call and result['return_value']!=call['expect_return']:
                raise ValueError(f'Native font {target:08X} returned {result["return_value"]}, '
                                 f'expected {call["expect_return"]}')
        else: raise ValueError('Unexpected native font action')
    for label,at,expected in (('live save payload',SAVE_RAM,saved),
                              ('complete native font',0x8013A680,native_font),
                              ('approved widths',0x80106AF4,native_widths),
                              ('immutable probe code',base,immutable)):
        observed = debug.read_memory(at,len(expected))
        record({'font_retained':label,'bytes':len(expected),'expected_sha256':sha256(expected),
                'observed_sha256':sha256(observed),'assertion':'passed' if observed==expected else 'failed'})
        if observed!=expected: raise ValueError('Native font probe changed '+label)
    record(debug.call('8009C040',[allocation]))
    return {'native_font_draws':26,'paths':['rectangle','polygon'],
            'allocation_released':True,'production_installed':False,'requires_checkpoint_restore':True}
