"""Check whole-letter storage without claiming normal UI progression or saving."""

from aflib import sha256
from mail_storage import QUEUE, QUEUE_COUNT, LEAFLETS, LEAFLET_FLAGS, HOME_MAILBOX, HOME_STRIDE, HOME_COUNT
from runtime_layout import TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

SOURCE, COPIED, COMPACT = TEST_RETURN+0x300,TEST_RETURN+0x400,TEST_RETURN+0x500
EDGE = b'EDGE'*4


def exercise(debug,request,record):
    def read(address,size): return debug.read_memory(address,size)
    def write(address,data):
        debug.write_memory(address,data)
        record({'storage_test_write':f'{address:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,address,expected):
        observed = read(address,len(expected))
        if observed != expected:
            record({'storage_check':label,'assertion':'failed','address':f'{address:08X}',
                    'expected':expected.hex(),'observed':observed.hex()})
            raise ValueError('Native mail storage mismatch: '+label)
        record({'storage_check':label,'assertion':'passed','bytes':len(expected),'sha256':sha256(observed)})
    def call(address,args,expected=None):
        result = debug.call(f'{address:08X}',args)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Native mail storage return at {address:08X}: {result["return_value"]} != {expected}')
    for address,value in request['guards'].items(): check('instructions',int(address,16),bytes.fromhex(value))
    write(TEST_STACK-0xC00,EDGE)
    write(TEST_STACK+0x30,EDGE)
    write(COPIED-16,EDGE+b'!'*164+EDGE)
    call(0x8009C384,[COPIED])
    cleared = read(COPIED,164)
    if cleared[38] != 255 or cleared[42:] != b' '*122:
        raise ValueError('Unexpected native cleared-letter representation')
    # Preserve the entire post-office tested region and all four home arrays,
    # including untouched adjacent bytes. A full checkpoint is restored too.
    regions = [(QUEUE-16,LEAFLET_FLAGS+4+16-(QUEUE-16))]
    regions += [(HOME_MAILBOX+i*HOME_STRIDE-16,HOME_COUNT*164+32) for i in range(4)]
    originals = [(address,read(address,size)) for address,size in regions]
    checks = 0
    for wire in request['letters']:
        mail = bytes.fromhex(wire)
        if len(mail) != 164 or mail[39] != 128:
            raise ValueError('Storage fixture must be a complete tagged letter')
        # The split marker must not affect status/attachment predicates.
        for split in (0,128):
            for font in (0,1,2,3,4,5,7,128,255):
                probe = bytearray(mail); probe[38:40] = bytes((font,split))
                write(SOURCE-16,EDGE+probe+EDGE)
                for function,expected in ((0x8009C414,int(font==255)),(0x8009C89C,int(font==1)),
                                          (0x8009C8C0,int(font in (1,3,4)))):
                    call(function,[SOURCE],expected)
                check('metadata predicates preserve complete source',SOURCE-16,EDGE+probe+EDGE)
                checks += 1
        write(SOURCE-16,EDGE+mail+EDGE)
        write(COMPACT-16,EDGE+b'!'*132+EDGE)
        call(0x800A82C8,[COMPACT,SOURCE])
        compact = mail[38:39]+mail[41:42]+mail[36:38]+mail[39:40]+mail[42:]+b'!'*5
        check('complete NPC compact representation',COMPACT-16,EDGE+compact+EDGE)
        write(COPIED-16,EDGE+b'!'*164+EDGE)
        call(0x800A8344,[COPIED,COMPACT,0,0])
        restored = b'!'*36+mail[36:40]+b'!'+mail[41:]
        check('complete NPC round trip; type and identities not copied',COPIED-16,EDGE+restored+EDGE)
        for mode,destination in enumerate(LEAFLETS,1):
            before = read(QUEUE-16,regions[0][1])
            expected = bytearray(before)
            offset = destination-(QUEUE-16)
            expected[offset:offset+164] = mail
            flag = LEAFLET_FLAGS+2*(mode-1)-(QUEUE-16)
            expected[flag:flag+2] = b'\0'*2
            call(0x800B6A3C,[SOURCE,mode],1)
            check('leaflet storage and only selected flags',QUEUE-16,bytes(expected))
            check('leaflet source retained',SOURCE-16,EDGE+mail+EDGE)
            checks += 1
        # Exercise every queue position, then the full-queue failure.
        occupied = bytearray(cleared); occupied[38] = 3
        for free in range(QUEUE_COUNT+1):
            array = bytearray(bytes(occupied)*QUEUE_COUNT)
            if free < QUEUE_COUNT: array[free*164:(free+1)*164] = cleared
            write(QUEUE,bytes(array)); write(SOURCE-16,EDGE+mail+EDGE)
            before = read(QUEUE-16,regions[0][1])
            expected = bytearray(before)
            if free < QUEUE_COUNT: expected[16+free*164:16+(free+1)*164] = mail
            call(0x800B67C0,[SOURCE],int(free < QUEUE_COUNT))
            check('queue slot and unrelated post-office state',QUEUE-16,bytes(expected))
            check('queue clear on success; retain on full',SOURCE-16,EDGE+(cleared if free < QUEUE_COUNT else mail)+EDGE)
            checks += 1
        # Every slot of all four home mailboxes, plus full-mailbox failures.
        write(SOURCE-16,EDGE+mail+EDGE)
        for home in range(4):
            address = HOME_MAILBOX+home*HOME_STRIDE
            for free in range(HOME_COUNT+1):
                array = bytearray(bytes(occupied)*HOME_COUNT)
                if free < HOME_COUNT: array[free*164:(free+1)*164] = cleared
                write(address,bytes(array))
                before = read(address-16,HOME_COUNT*164+32)
                expected = bytearray(before)
                if free < HOME_COUNT: expected[16+free*164:16+(free+1)*164] = mail
                call(0x800B6AC8,[home,SOURCE],int(free < HOME_COUNT))
                check('home mailbox selected slot and neighbours',address-16,bytes(expected))
                check('home copy retains source',SOURCE-16,EDGE+mail+EDGE)
                checks += 1
        check('stack lower guard',TEST_STACK-0xC00,EDGE)
        check('stack upper guard',TEST_STACK+0x30,EDGE)
        check('module guard',GUARD_ADDRESS,GUARD_WORD.to_bytes(4,'big')*4)
    for address,value in originals:
        write(address,value)
        check('restored storage and neighbours',address,value)
    return {'native_mail_storage_cases':checks,'letters':len(request['letters']),
            'normal_gameplay':False,'game_save_validation':False,'requires_checkpoint_restore':True}
