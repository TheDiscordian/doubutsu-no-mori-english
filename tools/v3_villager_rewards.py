"""Checked native house-gift selection without compacting imported identities."""
import struct

from aflib import CODE_RAM, sha256

ABI, CODE, LIMIT = 26, 0x3A00, 0x4000
ENTRY, END = 0x800AB8A0, 0x800ABA14
SOURCE_SHA = '6558d0ca7358772bea7d49409830dae3517e231134fa261e9c79fb87058bda04'
FILTER_START, FILTER_END = 0x800AB80C, ENTRY
FILTER_SHA = 'b508118eb4214220288a378845f42484556a6012cdb303b708175ff69c950df7'
SOURCES = ('tools/v3_villager_rewards.py', 'overlays/v3/villager_rewards.c',
           'overlays/v3/villager_rewards.ld')


def install(code, blob, helper, symbols):
    at, end = ENTRY-CODE_RAM, END-CODE_RAM
    if sha256(code[at:end]) != SOURCE_SHA or sha256(code[FILTER_START-CODE_RAM:at]) != FILTER_SHA:
        raise ValueError('Changed native house-reward selection or exclusion filter')
    if len(blob) != 0xC000 or not 0 < len(helper) <= LIMIT-CODE or any(blob[CODE:LIMIT]):
        raise ValueError('House reward code overlaps resident code/data')
    target = symbols['af_v3_house_reward']
    if target != 0x80460000+CODE:
        raise ValueError('Changed public house-reward entry')
    before = bytes(code[at:at+8])
    struct.pack_into('>II', code, at, 0x08000000 | ((target >> 2) & 0x3FFFFFF), 0)
    blob[CODE:CODE+len(helper)] = helper
    return {'entry': f'{ENTRY:08X}', 'end': f'{END:08X}', 'before': before.hex(),
            'after': bytes(code[at:at+8]).hex(), 'native_function_sha256': SOURCE_SHA,
            'native_filter_sha256': FILTER_SHA, 'compiled_bytes': len(helper),
            'compiled_sha256': sha256(helper), 'saved_layout_changed': False,
            'ordinary_gift_dialogue_tested': False}
