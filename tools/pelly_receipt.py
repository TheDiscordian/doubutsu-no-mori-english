"""Guard Pelly's receipt result and append two original English error messages."""

import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_npc import POST_CALL
from mail_storage import PELLY_VROM, PELLY_RAM, pelly_evidence, pocket_send_evidence
from mail_storage import TAG_VROM, TAG_RAM, TAG_SEND
from runtime_module import MODULE_RAM, MODULE_VROM, LINKED_LIMIT
from textbanks import Bank

DATA_VROM, TABLE_VROM, COUNT = 0x00BD4000,0x00CF9000,11752
RELOC_VROM = 0x008A8A10
LIMITS = {0x8009E3A4:0x2A012DE8,0x8009E668:0x28A12DE8}
RESULT_SHIM = bytes.fromhex('14400005241900058FA6001C240700042409000127FF000C03E0000800000000')
INDEX_SHIM = bytes.fromhex('2403000414E3000224E300012403000203E0000800000000')
HANDBACK_SHIM = bytes.fromhex('2401000415C10002000E7880240F000403E0000800000000')
# Original translation-port errors, not replacements for GameCube dialogue.
# Order nine lets the original refusal-after handler resume post-office choices.
MESSAGES = (
    b"I'm sorry, but this letter\xcdcouldn't be sent.\xcdI've returned it to you.\x7f\x09\x09\x00\x01\xcd\x7f\x01",
    b"This letter couldn't be sent.\xcdHere, take it back.\x7f\x09\x09\x00\x01\xcd\x7f\x01",
)


def append_messages(data,table):
    entries = Bank('message',DATA_VROM,TABLE_VROM,data,table).entries()
    if len(entries) != COUNT or table[COUNT*4:COUNT*4+12] != bytes(12):
        raise ValueError('Pelly error messages require the native count and three unused table words')
    end = sum(map(len,entries))
    if any(data[end:]): raise ValueError('Unexpected nonzero message-bank tail')
    new_data = data[:end]+b''.join(MESSAGES)
    new_data += bytes(-len(new_data)%16)
    result = bytearray(table)
    for index,message in enumerate(MESSAGES,COUNT):
        end += len(message)
        struct.pack_into('>I',result,index*4,end)
    if Bank('message',DATA_VROM,TABLE_VROM,new_data,bytes(result)).entries() != entries+list(MESSAGES):
        raise ValueError('Pelly message extension changed existing records')
    return new_data,bytes(result)


def install(rom,replacements,additions,module):
    original = pelly_evidence(rom)
    pocket = pocket_send_evidence(rom)
    files = by_vrom(rom)
    if not module or sha256(additions.get(MODULE_VROM,b'')) != module['module_sha256']:
        raise ValueError('Pelly receipt requires the unchanged verified resident module')
    if PELLY_VROM in replacements or RELOC_VROM in replacements:
        raise ValueError('Overlapping Pelly receipt overlay patch')
    if TAG_VROM in replacements:
        start,end,digest = TAG_SEND
        if sha256(replacements[TAG_VROM][start-TAG_RAM:end-TAG_RAM]) != digest:
            raise ValueError('Overlapping native pocket-send ownership patch')
    code = bytearray(replacements.get(CODE_VROM,files[CODE_VROM].extract(rom)))
    target = int(module['symbols']['af_mail_post_send'],16)
    if struct.unpack_from('>I',code,POST_CALL-CODE_RAM)[0] != 0x0C000000|((target&0x0FFFFFFF)>>2):
        raise ValueError('Pelly receipt requires the lower-level post-office failure guard')
    linked_end = MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT)
    targets = {}
    for name,expected in (('af_pelly_receipt_result',RESULT_SHIM),('af_pelly_refusal_index',INDEX_SHIM),
                          ('af_pelly_handback_index',HANDBACK_SHIM),
                          ('af_pelly_refusal_messages',struct.pack('>3I',0x2DDA,0x2DDE,COUNT))):
        address = int(module['symbols'].get(name,'0'),16)
        if (address&3 or not MODULE_RAM+0x300 <= address <= linked_end-len(expected)
                or additions[MODULE_VROM][address-MODULE_RAM:address-MODULE_RAM+len(expected)] != expected):
            raise ValueError('Invalid Pelly resident hook or message table: '+name)
        targets[name] = address
    for address,word in LIMITS.items():
        if struct.unpack_from('>I',code,address-CODE_RAM)[0] != word:
            raise ValueError('Unexpected or overlapping message-count limit')
        struct.pack_into('>I',code,address-CODE_RAM,(word&0xFFFF0000)|(COUNT+2))
    data,table = append_messages(replacements.get(DATA_VROM,files[DATA_VROM].extract(rom)),
                                 replacements.get(TABLE_VROM,files[TABLE_VROM].extract(rom)))
    overlay = bytearray(files[PELLY_VROM].extract(rom))
    reason_accesses = {PELLY_RAM+offset for offset in range(0,0x1BE0,4)
                       if (word:=struct.unpack_from('>I',overlay,offset)[0])&0xFFFF == 0x949
                       and word>>26 in (0x20,0x24,0x28)}
    if reason_accesses != {0x809C3F2C,0x809C4820,0x809C4A98}:
        raise ValueError('Unexpected Pelly refusal-reason readers or writers')
    if sha256(overlay[0x809C4A74-PELLY_RAM:0x809C4AD4-PELLY_RAM]) != 'e725bc1f15690888bddd4a338ce85e5aeea42d39e1893a06801bdabdd989ecf5':
        raise ValueError('Unexpected Pelly hand-back introduction initializer')
    # The audited selector is independent of the receive-menu handler hash.
    before = struct.pack('>9I',0x24010002,0x10410005,0x24010003,0x10410005,0x24052DDE,
                          0x10000003,0x24052DDC,0x10000001,0x24052DDA)
    if overlay[0x809C3F30-PELLY_RAM:0x809C3F54-PELLY_RAM] != before:
        raise ValueError('Unexpected Pelly refusal-message selector')
    address = targets['af_pelly_refusal_messages']
    selector = struct.pack('>9I',0x2445FFFE,0x2CA10003,0x10200005,0x00052880,
                           0x3C010000|((address+0x8000)>>16),0x00250821,0x10000002,
                           0x8C250000|(address&0xFFFF),0x24052DDC)
    overlay[0x809C3F30-PELLY_RAM:0x809C3F54-PELLY_RAM] = selector
    struct.pack_into('>2I',overlay,0x809C47C8-PELLY_RAM,
                     0x0C000000|((targets['af_pelly_receipt_result']&0x0FFFFFFF)>>2),0x8FA80030)
    struct.pack_into('>I',overlay,0x809C481C-PELLY_RAM,
                     0x0C000000|((targets['af_pelly_refusal_index']&0x0FFFFFFF)>>2))
    struct.pack_into('>2I',overlay,0x809C4A98-PELLY_RAM,
                     0x0C000000|((targets['af_pelly_handback_index']&0x0FFFFFFF)>>2),0x908E0949)
    relocation = files[RELOC_VROM].extract(rom)
    count = struct.unpack_from('>I',relocation,16)[0]
    records = struct.unpack_from('>'+str(count)+'I',relocation,20)
    changed = set(range(0x809C3F30-PELLY_RAM,0x809C3F54-PELLY_RAM,4))
    changed.update((0x809C47C8-PELLY_RAM,0x809C47CC-PELLY_RAM,0x809C481C-PELLY_RAM,
                    0x809C4A98-PELLY_RAM,0x809C4A9C-PELLY_RAM))
    if any((word>>30)==1 and (word&0xFFFFFF) in changed for word in records):
        raise ValueError('Pelly patched instructions unexpectedly have overlay relocations')
    replacements.update({CODE_VROM:bytes(code),PELLY_VROM:bytes(overlay),DATA_VROM:data,TABLE_VROM:table})
    return {'source_overlay_sha256':original['file_sha256'],'overlay_sha256':sha256(overlay),'pocket_send':pocket,
            'reason_field_accesses':[f'{address:08X}' for address in sorted(reason_accesses)],
            'hook_targets':{name:f'{address:08X}' for name,address in targets.items()},
            'relocations_unchanged':True,'appended_message_ids':[f'{COUNT:04X}',f'{COUNT+1:04X}'],
            'native_messages_unchanged':COUNT,'new_message_count':COUNT+2,
            'status':'Receipt failures use the original pocket-return/refusal flow and an explicit English error; normal gameplay validation remains'}
