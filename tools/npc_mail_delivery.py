"""Source-bound failure gate for complete NPC reply creation.

The caller must bind the creator to a verified six-argument implementation.
This helper does not install hooks or approve a creator by address alone.
"""

import struct

from aflib import sha256
from npc_mail_generation import FUNCTIONS

START,END,DIGEST = FUNCTIONS['delivery']
CREATOR_CALL,FAILURE_BRANCH,ARGUMENT_MOVE = 0x800A915C,0x800A9164,0x800A9168
FAILURE_RETURN,RECEIPT_CALL = 0x800A917C,0x800A916C
STAGING = 0x80142F80


def patch(original,creator):
    if len(original) != END-START or sha256(original) != DIGEST:
        raise ValueError('Changed original NPC reply submission function')
    if (type(creator) is not int or creator&3 or not 0x80000400 <= creator < 0x80400000
            or START <= creator < END):
        raise ValueError('Invalid complete NPC reply creator target')
    result = bytearray(original)
    changes = ((CREATOR_CALL,0x0C000000|((creator>>2)&0x03FFFFFF)),
               (FAILURE_BRANCH,0x10400000|((FAILURE_RETURN-FAILURE_BRANCH-4)//4)),
               (ARGUMENT_MOVE,0x00402025))
    for address,word in changes:
        struct.pack_into('>I',result,address-START,word)
    return bytes(result)


def creator_fixture(log):
    """Test-only o32 leaf: log six arguments and return configured pointer/zero.

    Log words 0..5 are arguments, word 6 counts calls, and word 7 is the desired
    return. Poison v1 so the failure test detects an incorrect epilogue target.
    This is not a real letter creator and has no text, RNG, or allocation code.
    """
    if type(log) is not int or log&15 or not 0x80000400 <= log <= 0x80400000-32:
        raise ValueError('Invalid native creator fixture log')
    words = [0x3C080000|(log>>16),0x35080000|(log&0xFFFF)]
    words += [0xAD000000|(register<<16)|(i*4) for i,register in enumerate(range(4,8))]
    words += [0x8FA90010,0xAD090010,0x8FA90014,0xAD090014,
              0x8D090018,0x25290001,0xAD090018,0x8D02001C,0x03E00008,0x34035A5A]
    return struct.pack('>'+str(len(words))+'I',*words)
