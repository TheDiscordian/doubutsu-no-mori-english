"""Guarded whole-record NPC send and cached quest-grade entry hooks."""

import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_grading import VROM as GRADING_VROM
from runtime_module import MODULE_RAM, MODULE_VROM, LINKED_LIMIT

ENTRIES = (
    (0x800A8868,0x800A8AB4,'877c0a68c685a594f482316e7661a6964590ef0f38e158a288d6a9ad5dc54f58',
     (0x27BDFF98,0xAFBF0014),'af_mail_send_npc','af_mail_send_original'),
    (0x800A8614,0x800A86C4,'e0075f0d31071ebd5e785c2b1fed3ad2307dcdd369e84e706c5cb79ea62cd81c',
     (0x27BDFFD8,0xAFBF0014),'af_mail_grade_length','af_mail_length_original'),
)
POST_START, POST_END, POST_CALL = 0x800B690C,0x800B6A3C,0x800B69BC
POST_SHA256 = '469d58f3b17f22a970ee84225b883080c7afea34edf54e7f7ebf97d32f9e4da8'
POST_SHIM = bytes.fromhex('14400003000000000802DA8900001825080270E100000000')


def install(rom,replacements,additions,module):
    if not module or sha256(additions.get(MODULE_VROM,b'')) != module['module_sha256']:
        raise ValueError('Snapshot NPC consumers require the unchanged verified resident module')
    grading = replacements.get(GRADING_VROM,b'')
    if grading[16:32] != struct.pack('>4I',0x41464D47,1,96,1024):
        raise ValueError('Snapshot NPC consumers require the installed English grading overlay')
    original = by_vrom(rom)[CODE_VROM].extract(rom)
    code = bytearray(replacements.get(CODE_VROM,original))
    symbols = module['symbols']
    ordinary = int(symbols['af_mail_grade_native'],16)
    if struct.unpack_from('>2I',code,0x800A86C4-CODE_RAM) != (0x08000000|((ordinary&0x0FFFFFFF)>>2),0):
        raise ValueError('Snapshot NPC consumers require the installed ordinary grade hook')
    installed = []
    for start,end,digest,words,wrapper,trampoline in ENTRIES:
        offset = start-CODE_RAM
        if sha256(original[offset:end-CODE_RAM]) != digest or struct.unpack_from('>2I',original,offset) != words:
            raise ValueError('Unexpected native NPC mail function')
        if code[offset:offset+8] != original[offset:offset+8]:
            raise ValueError('Overlapping NPC mail entry hook')
        addresses = [int(symbols.get(name,'0'),16) for name in (wrapper,trampoline)]
        if any(address&3 or not MODULE_RAM+0x300 <= address <= MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT)-16
               for address in addresses):
            raise ValueError('NPC mail hook/trampoline is outside the resident module')
        target,bridge = addresses
        expected = struct.pack('>4I',*words,0x08000000|(((start+8)&0x0FFFFFFF)>>2),0)
        if additions[MODULE_VROM][bridge-MODULE_RAM:bridge-MODULE_RAM+16] != expected:
            raise ValueError('NPC mail original-entry trampoline mismatch')
        struct.pack_into('>2I',code,offset,0x08000000|((target&0x0FFFFFFF)>>2),0)
        installed.append({'entry':f'{start:08X}','target':f'{target:08X}','trampoline':f'{bridge:08X}',
                          'source_sha256':digest})
    if (sha256(original[POST_START-CODE_RAM:POST_END-CODE_RAM]) != POST_SHA256
            or struct.unpack_from('>4I',original,POST_CALL-CODE_RAM-8) !=
               (0x0C02A21A,0x02002025,0x0C0270E1,0x02002025)):
        raise ValueError('Unexpected native post-office NPC send/clear path')
    if code[POST_CALL-CODE_RAM:POST_CALL-CODE_RAM+4] != original[POST_CALL-CODE_RAM:POST_CALL-CODE_RAM+4]:
        raise ValueError('Overlapping post-office NPC result hook')
    post_target = int(symbols.get('af_mail_post_send','0'),16)
    if (post_target&3 or not MODULE_RAM+0x300 <= post_target <= MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT)-24
            or additions[MODULE_VROM][post_target-MODULE_RAM:post_target-MODULE_RAM+24] != POST_SHIM):
        raise ValueError('Invalid post-office NPC result shim')
    struct.pack_into('>I',code,POST_CALL-CODE_RAM,0x0C000000|((post_target&0x0FFFFFFF)>>2))
    replacements[CODE_VROM] = bytes(code)
    return {'hooks':installed,'native_mail_bytes':164,'scoped_context_bytes':16,
            'post_send':{'call':f'{POST_CALL:08X}','target':f'{post_target:08X}','failure_continuation':'800B6A24'},
            'status':'Whole-record snapshot decoding before native send; generation and actual saving remain disabled/unverified'}
