"""Real cartridge message/choice reads, count guards, and a summer continuation."""
import json
from pathlib import Path
import struct
from aflib import by_vrom,sha256
from runtime_layout import MODULE_RAM
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import tokenize
import v3_camper_text as runtime


def exercise(debug,rom_path,record):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=79:
        raise ValueError('Summer text probe requires the current ABI 79 cartridge')
    files=by_vrom(rom);info=module_command_info(rom)
    messages=Bank('message',runtime.MESSAGE,runtime.TABLE,files[runtime.MESSAGE].extract(rom),
                  files[runtime.TABLE].extract(rom)).entries()
    choices=Bank('select',runtime.CHOICES,runtime.CHOICE_TABLE,files[runtime.CHOICES].extract(rom),
                 files[runtime.CHOICE_TABLE].extract(rom)).entries()
    def words(*values):return struct.pack('>'+str(len(values))+'I',*values)
    def check(label,address,value):
        actual=debug.read_memory(address,len(value))
        record(dict(camper_text_check=label,address=f'{address:08X}',bytes=len(value),
            assertion='passed' if actual==value else 'failed',expected_sha256=sha256(value),
            observed_sha256=sha256(actual)))
        if actual!=value:raise ValueError('Native summer text mismatch: '+label)
    def call(address,args,want=None):
        result=debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480)
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError('Native summer text return mismatch')
        return result['return_value']
    saved=debug.read_memory(0x80126EA0,65536)
    allocation=call(0x8009BFC0,[0x1000])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FF000:
        raise ValueError('Summer text fixture allocation failed')
    message,window,choice,output,index=(allocation+i for i in (0x20,0x500,0x860,0xA00,0xB00))
    edge=b'V3CT'*4
    for at in (allocation,message+0x410,window+0x330,output-16,output+32,allocation+0xFF0):
        debug.write_memory(at,edge)
    debug.write_memory(window,bytes(0x330));debug.write_memory(window+12,words(message))
    debug.write_memory(choice,bytes(0x100))
    numbers=(0,11753,11754,11755,11754+72,11754+73,11754+149,12006)
    for number in numbers:
        debug.write_memory(message,b'\xA5'*0x410)
        call(0x8009E558,[message,number,0],1)
        check('complete native old/new message load',message,words(1,number,len(messages[number]),0)+messages[number])
        check('message upper guard',message+0x410,edge)
    # Last summer record has a real four-card menu and a continuing target.
    link=next(t for t in tokenize(messages[12006],info) if t.kind=='cmd' and t.data[1]==14)
    next_id=int.from_bytes(link.data[2:],'big');debug.write_memory(index,words(link.offset))
    call(0x800A21C0,[window,index],0)
    check('native summer continuation target',window+0x2C4,words(next_id))
    check('native branch cursor advance',index,words(link.offset+4))
    call(0x8009E658,[window,next_id],1)
    check('full native continuing summer message',message,words(1,next_id,len(messages[next_id]),0)+messages[next_id])
    retained=debug.read_memory(message,0x410)
    call(0x8009E658,[window,len(messages)],0)
    check('invalid next-message count retains current message',message,retained)
    for number in (0,461,462,463,510,511):
        debug.write_memory(output,b'\xA5'*32)
        call(0x80065D90,[choice,output,number,0])
        expected=choices[number].ljust(20,b' ')+b'\xA5'*12 if number<len(choices) else b'\xA5'*32
        check('complete old/new choice and count rejection',output,expected)
    for number in (11754,12006,12007,0xFFFFFFFF):
        debug.write_memory(index,b'\xA5'*16)
        call(0x8009E388,[number,index,index+4])
        expected=words(runtime.MESSAGE+sum(map(len,messages[:number])),len(messages[number])) if number<len(messages) else bytes(8)
        check('actual message directory address length and count guard',index,expected+b'\xA5'*8)
    check('complete saved town untouched',0x80126EA0,saved)
    for at in (allocation,message+0x410,window+0x330,output-16,output+32,allocation+0xFF0):
        check('fixture guard',at,edge)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4));call(0x8009C040,[allocation])
    return dict(complete_message_loads=9,complete_choice_reads=5,native_continuation=True,
        native_count_rejection=True,summer_selector_or_trade_operations=False,
        ordinary_conversations_or_persistence=False,requires_checkpoint_restore=True)
