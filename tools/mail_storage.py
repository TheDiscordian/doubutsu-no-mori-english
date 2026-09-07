"""Verified native mail metadata predicates and opaque storage operations."""

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256

FUNCTIONS = {
    'unused': (0x8009C414,0x8009C438,'e5b0400e6ced8d6da09d67da8b80e96142f377308af59a33be43b9cb3b4e8dd7'),
    'sendable': (0x8009C89C,0x8009C8C0,'b8645f99115ac96511958c5bbab1536599d0797f725c41af61d3cb1b7f2fcf66'),
    'attachable': (0x8009C8C0,0x8009C8F4,'c919698b6412ed116817e4c3bdcb389788c88d881587ac77754869834385d774'),
    'to_npc': (0x800A82C8,0x800A8344,'bdb7d835e688de036dbece62389fc980c30d7d7ccb363fa14ceef11aa7588374'),
    'from_npc': (0x800A8344,0x800A83F0,'33bed4dce3ee8af469493035c119c200fef01b4d0ed3425898a8a9dffbd930ed'),
    'receipt': (0x800B6A3C,0x800B6AC8,'032319ed0866342abee88c99f07298dfe958ad6e3fb83fae8e20da2b70b2ae70'),
    'keep_queue': (0x800B67C0,0x800B6838,'bff680a556bacfde8dbbc129d2042442266c59b6ae8e58ddb3c40958e8a94c12'),
    'copy_home': (0x800B6AC8,0x800B6B94,'da36ae83aedf2509b8ff0f98db3574dc5a2e6ed8f6bec2e35293125f2933c388'),
}
QUEUE, QUEUE_COUNT = 0x80135E0C,5
LEAFLETS, LEAFLET_FLAGS = (0x80136140,0x801361E4),0x80136288
HOME_MAILBOX, HOME_STRIDE, HOME_COUNT = 0x8012A8A0,0xB48,10
PELLY_VROM, PELLY_RAM = 0x008A6C10,0x809C3420
PELLY_RECEIVE = (0x809C471C,0x809C4884,'c29e3901cf539f63a16043228bccc787ec14fbf4a58613db350a06f9618b0e73')


def pelly_evidence(rom):
    data = by_vrom(rom)[PELLY_VROM].extract(rom)
    start,end,digest = PELLY_RECEIVE
    if sha256(data[start-PELLY_RAM:end-PELLY_RAM]) != digest:
        raise ValueError('Unexpected Pelly receive-menu handler')
    return {'vrom':f'{PELLY_VROM:08X}','ram':f'{PELLY_RAM:08X}',
            'file_sha256':sha256(data),'receive_sha256':digest,
            'receipt_call':'809C47C0','unconditional_clear':'809C4828',
            'return_copy_call':'809C480C','private_mail_offset':0x40A,'selected_slot_submenu_offset':0xDF,
            'status':'UNFIXED: UI ignores receipt failure, takes success path, and clears staged letter; existing refusal path returns it to the selected player slot'}


def evidence(rom):
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    functions = {}
    for name,(start,end,digest) in FUNCTIONS.items():
        data = code[start-CODE_RAM:end-CODE_RAM]
        if sha256(data) != digest:
            raise ValueError('Unexpected native mail storage function: '+name)
        functions[name] = {'start':f'{start:08X}','end':f'{end:08X}','sha256':digest}
    return {'functions':functions,'mail_bytes':164,'compact_bytes':132,
            'font_offset':38,'split_offset':39,'compact_split_offset':4,
            'unused_fonts':[255],'sendable_fonts':[1],'attachable_fonts':[1,3,4],
            'post_queue':{'address':f'{QUEUE:08X}','slots':QUEUE_COUNT},
            'leaflets':[f'{address:08X}' for address in LEAFLETS],
            'leaflet_flags':f'{LEAFLET_FLAGS:08X}',
            'home_mailboxes':{'first':f'{HOME_MAILBOX:08X}','stride':HOME_STRIDE,'homes':4,'slots':HOME_COUNT},
            'status':'Verified selected native predicates and opaque copies; not an exhaustive metadata/reader or FlashRAM audit'}
