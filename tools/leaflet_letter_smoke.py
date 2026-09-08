"""Complete leaflet creation/readback without modifying native delivery state."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_generate_probe import relocate
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    saved,rng,free = read(SAVE_RAM,SAVE_BYTES),read(0x8003C590,4),read(0x80140680,200)
    code,report,module = bytes.fromhex(request['code']),request['probe'],request['module']
    assertions = 0
    def check(label,at,expected):
        nonlocal assertions
        actual = read(at,len(expected))
        record({'leaflet_letter_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual != expected: raise ValueError('Native leaflet creation check failed: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Leaflet call returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    size = 0x4000;allocation = call(0x8009BFC0,[size]);base = allocation+16
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native leaflet fixture allocation failed')
    choice = (base+len(code)+31)&~15
    items,capital,mail,work,arena = (choice+x for x in (32,112,144,336,5648))
    if arena+32 > allocation+size-16: raise ValueError('Leaflet fixture exceeds owned allocation')
    guards = (allocation,choice-16,choice+16,items+64,capital+16,mail+176,work+5280,
              arena+16,allocation+size-16,TEST_STACK-0xA00,TEST_STACK+0x30)
    for at in guards: write(at,EDGE)
    loaded = relocate(code,report,module,base,leaflets=True);write(base,loaded)
    entry = base+report['symbols']['af_leaflet_create']
    call(0x8009C0C0,[arena,arena+4,arena+8]);heap = read(arena,12)
    for case in request['cases']:
        selected,values = bytes.fromhex(case['choice']),bytes.fromhex(case['items'])
        write(choice,selected);write(items,values.ljust(60,b'!'))
        write(capital,case['capital'].to_bytes(4,'big'));write(mail,bytes(range(164))+b'!'*12)
        write(work,b'!'*5280)
        call(entry,[mail,164,choice,items if values else 0,capital,work],1,(base,loaded))
        check('complete saved leaflet and metadata',mail,bytes.fromhex(case['mail'])+b'!'*12)
        check('complete English leaflet text',work+560+3552,bytes.fromhex(case['text']))
        check('selected native values retained',choice,selected)
        check('complete selected name inputs retained',items,values.ljust(60,b'!'))
        check('capitalization state',capital,case['capital'].to_bytes(4,'big'))
        # Independently reconstruct the final saved envelope through the resident
        # cartridge reader, after clearing all previous formatting output.
        write(work,b'!'*5280)
        call(int(module['symbols']['af_mail_restore'],16),[work+560+3552,mail+42,122,work+560],1)
        check('complete saved leaflet reader restoration',work+560+3552,bytes.fromhex(case['text']))
        check('saved leaflet retained after reading',mail,bytes.fromhex(case['mail'])+b'!'*12)
        for at in guards: check('owned fixture guard',at,EDGE)
    selected = bytes.fromhex(request['cases'][0]['choice'])
    invalid = []
    for offset,value in ((0,0),(1,18),(4,0),(5,32),(6,24),(7,4)):
        bad = bytearray(selected);bad[offset] = value
        if bytes(bad) != selected: invalid.append(bytes(bad))
    invalid += [struct.pack('>HH4B3H',24,1901,1,1,0,0,0,0,0)]
    for selected in invalid:
        write(choice,selected);write(mail,bytes(range(164)));write(capital,b'\0\0\0\1')
        call(entry,[mail,164,choice,items,capital,work],0,(base,loaded))
        check('rejected leaflet retains complete mail',mail,bytes(range(164)))
        check('rejected leaflet retains capital',capital,b'\0\0\0\1')
    first = request['cases'][0];write(choice,bytes.fromhex(first['choice']))
    write(items,bytes.fromhex(first['items']))
    config = 0x80194924;check('installed catalogue configuration',config,bytes.fromhex('03000000'))
    write(config,bytes(4))
    call(entry,[mail,164,choice,items,capital,work],0,(base,loaded))
    check('disabled catalogue retains complete mail',mail,bytes(range(164)))
    check('disabled catalogue retains capital',capital,b'\0\0\0\1')
    write(config,bytes.fromhex('03000000'))
    call(0x8009C0C0,[arena,arena+4,arena+8]);check('heap accounting unchanged',arena,heap)
    check('complete live save unchanged',SAVE_RAM,saved)
    check('original RNG unchanged',0x8003C590,rng)
    check('original handbill fields unchanged',0x80140680,free)
    check('complete creator code retained',base,loaded)
    check('module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    for at in guards: check('final fixture guard',at,EDGE)
    call(0x8009C040,[allocation])
    return {'complete_leaflet_cases':len(request['cases']),'rejected_leaflet_choices':len(invalid),
            'leaflet_letter_assertions':assertions,'full_saved_reader_restoration':True,
            'native_delivery_hook_installed':False,'normal_delivery':False,
            'item_names':'synthetic complete inputs, not native source lookup evidence',
            'requires_checkpoint_restore':True}
