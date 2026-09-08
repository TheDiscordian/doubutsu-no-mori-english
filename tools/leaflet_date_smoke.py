"""Silent native leaflet preparation with complete fields and owned actor fixtures."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from leaflet_dates import ACTORS,HOUR,changes
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

FREE,EDGE = 0x80140680,b'EDGE'*4


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions,hours,preparations = 0,0,{'renewal':0,'sale':0,'redd':0}
    def check(label,at,expected):
        nonlocal assertions
        actual = read(at,len(expected))
        record({'leaflet_date_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual != expected:
            raise ValueError('Native leaflet date mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Leaflet routine {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value):
        return struct.pack('>I',value)
    saved,free = read(SAVE_RAM,SAVE_BYTES),read(FREE,200)
    hour_code = bytes.fromhex(request['hour'])
    check('complete installed leaflet hour',HOUR,hour_code)
    check('unchanged native handbill setter',0x80092D10,bytes.fromhex(request['setter']))
    fields = request['fields']
    def date_words(month,day,hour,year=2000):
        h = hour if hour < 24 else 0
        return (fields['months'][(month if 1 <= month <= 12 else 1)-1].encode(),
                fields['days'][(day if 1 <= day <= 31 else 1)-1].encode(),
                f'{h%12 or 12} {fields["ampm"][int(h>=12)]}'.encode(),
                str(year if 1901 <= year <= 2099 else 2000).encode())
    def date_bytes(month,day,hour,year=2000):
        return bytes((0,0,hour,day,0,month))+struct.pack('>H',year)
    baseline = bytes(i%251 for i in range(200))
    def table(values):
        output = bytearray(baseline)
        for slot,value in values.items():
            if len(value)>10:
                raise ValueError('Leaflet expected field exceeds native storage')
            output[slot*10:(slot+1)*10] = value.ljust(10,b' ')
        return output
    for name,spec in ACTORS.items():
        size = 0x9000;allocation = call(0x8009BFC0,[size])
        if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
            raise ValueError('Leaflet fixture allocation failed')
        base = allocation+16;reloc_at = base+spec.resident_bytes
        stage,output,arena,shim = (allocation+x for x in (0x7800,0x7900,0x7A00,0x7B00))
        source = request['actors'][name];original,reloc = bytes.fromhex(source['original']),bytes.fromhex(source['reloc'])
        if sha256(original) != spec.file_sha256 or sha256(reloc) != spec.relocation_sha256:
            raise ValueError('Changed source leaflet actor fixture')
        loaded = bytearray(relocate_verified_data(spec,original,reloc,base))
        for address,_,after in changes(name,request['module']):
            struct.pack_into('>I',loaded,address-spec.ram,after)
        edges = (allocation,reloc_at+len(reloc),stage-16,stage+64,output-16,output+32,
                 arena-16,arena+16,shim-16,shim+96,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x30)
        for at in edges:
            write(at,EDGE)
        call(0x800262D0,[spec.vrom,spec.vrom+spec.file_bytes,spec.ram,spec.ram+spec.resident_bytes,
                        base,reloc_at,len(reloc)],proof=(0x800262D0,bytes.fromhex(request['loader'])))
        check('complete cartridge-loaded leaflet actor',base,loaded)
        check('complete unchanged leaflet relocations',reloc_at,reloc)
        call(0x8009C0C0,[arena,arena+4,arena+8]);heap = read(arena,12)
        if name == 'renewal':
            # Run the original date block with its actual frame/local offsets,
            # without its surrounding mailbox mutation and letter creation.
            # Two owned test-only instructions leave the block at its end.
            prefix = [0x27BDFEB8,0xAFBF0044,0xAFBE0040,0xAFB7003C,
                      0x8C880000,0xAFA80074,0x8C880004,0xAFA80078,
                      0x27B7008C,0x27BE0088,0x02E02025,
                      0x08000000|(((base+0x108)>>2)&0x3FFFFFF),0]
            epilogue = shim+len(prefix)*4
            code = struct.pack('>'+str(len(prefix)+5)+'I',*prefix,
                               0x8FBF0044,0x8FBE0040,0x8FB7003C,0x03E00008,0x27BD0148)
            write(shim,code)
            struct.pack_into('>2I',loaded,0x158,0x08000000|((epilogue>>2)&0x3FFFFFF),0)
            write(base+0x158,loaded[0x158:0x160])
            for month in range(1,13):
                year,day = (1901,2099)[month%2],month+19
                fixture = date_bytes(month,day,0,year)+b'!'*56
                write(stage,fixture);write(FREE,baseline)
                call(shim,[stage],proof=(shim,code))
                m,d,_,y = date_words(month,day,0,year)
                check('renewal complete month day and year fields',FREE,table({0:m,1:d,2:y}))
                check('renewal date input retained',stage,fixture)
                check('renewal day and subsequent year local retained',TEST_STACK-0x148+0x88,
                      d.ljust(4,b' ')+m.ljust(9,b' ')[:4]+y.ljust(6,b' '))
                for at in edges:
                    check('renewal allocation and stack guard',at,EDGE)
                preparations['renewal'] += 1
            check('owned renewal test-only exit retained',base,loaded)
        else:
            proof = (base,bytes(loaded[:spec.sections[0]]))
            # Cover every hour input with the actual fixed-address native code.
            for hour in range(256):
                write(output,b'!'*32)
                expected = date_words(1,1,hour)[2]
                call(HOUR,[output+1,hour],len(expected),proof=(HOUR,hour_code))
                check('complete AM/PM time with unaligned destination',output,b'!'+expected+b'!'*(31-len(expected)))
                hours += 1
            call(HOUR,[0,12],0xFFFFFFFF,proof=(HOUR,hour_code))
            dates = [(i%12+1,i+1,i%24) for i in range(31)]+[(0,0,24),(13,32,255)]
            for month,day,hour in dates:
                fixture = date_bytes(month,day,hour)+b'!'*56
                write(stage,fixture);write(FREE,baseline)
                call(base+0x2D0,[stage],proof=proof)
                m,d,h,_ = date_words(month,day,hour)
                check('Redd complete month day and AM/PM fields',FREE,table({0:m,1:d,2:h}))
                check('Redd event pointer input retained',stage,fixture)
                for at in edges:
                    check('Redd allocation and stack guard',at,EDGE)
                preparations['redd'] += 1
            for month in range(1,13):
                day,hour,count = month+19,month+11,month%4
                fixture = bytearray(b'!'*64)
                fixture[12:20] = date_bytes(month,day,hour)
                items = (0x1000,0x2000,0x2200)
                for i,item in enumerate(items):
                    struct.pack_into('>H',fixture,28+i*2,item)
                write(stage,fixture);write(output,b'!'*32)
                call(0x8009264C,[output,count,1,1,0]);count_text = read(output,1)
                values = {0:count_text}
                for i,item in enumerate(items[:count]):
                    call(0x80096740,[output,item]);values[7+i] = read(output,10)
                m,d,h,_ = date_words(month,day,hour);values.update({17:m,18:d,19:h})
                write(FREE,baseline)
                call(base+0x1B0,[stage,count],proof=proof)
                check('sale complete dates and original count/item fields',FREE,table(values))
                check('sale event and item inputs retained',stage,fixture)
                for at in edges:
                    check('sale allocation and stack guard',at,EDGE)
                preparations['sale'] += 1
            check('complete event actor and BSS retained',base,loaded)
        call(0x8009C0C0,[arena,arena+4,arena+8])
        check('native heap accounting retained',arena,heap)
        check('complete live save retained',SAVE_RAM,saved)
        check('leaflet hour retained',HOUR,hour_code)
        check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
        write(FREE,free);check('restored shared handbill fields',FREE,free)
        call(0x8009C040,[allocation])
    return {'leaflet_hour_cases':hours,'leaflet_preparations':preparations,'leaflet_assertions':assertions,
            'renewal_scope':'original date block with owned test-only entry/exit; not mailbox publication',
            'sale_and_redd_scope':'complete original preparation functions',
            'full_letter_publication':False,'normal_delivery':False,'requires_checkpoint_restore':True}
