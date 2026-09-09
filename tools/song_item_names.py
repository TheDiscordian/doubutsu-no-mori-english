"""Complete selected song titles through the existing full item-field wrapper."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
import credits_strings as credits
from extended_items import HEADER, VROM as ITEMS_VROM
from runtime_layout import MODULE_RAM, MODULE_VROM, LINKED_LIMIT
from runtime_module import verify_test_module

START, END, WRAPPER = 0x80AA4794, 0x80AA47E8, 0x800BB6A0
SOURCE_HASH = '5b15d2a4dfd5d3542a2529d83a22f530e714337da11be24c429671e7e26f248d'
# u8 song index; preserve the caller's full-width slot; tail-call the installed
# item-ID wrapper. No temporary name, stack frame, or added resident code.
WORDS = (0x30A800FF, 0x00802825, 0x08000000 | ((WRAPPER >> 2) & 0x03FFFFFF), 0x25042A00)
PATCH = struct.pack('>4I', *WORDS)+bytes(END-START-16)


def patch(data, relocation):
    if (len(data) != credits.FILE_BYTES or
            sha256(data[START-credits.RAM:END-credits.RAM]) != SOURCE_HASH):
        raise ValueError('Changed native song-title setter')
    count = struct.unpack_from('>I', relocation, 16)[0]
    entries = struct.unpack_from(f'>{count}I', relocation, 20)
    if any(START-credits.RAM <= (entry & 0xFFFFFF) < END-credits.RAM for entry in entries):
        raise ValueError('Unexpected relocation inside the song-title setter')
    output = bytearray(data)
    output[START-credits.RAM:END-credits.RAM] = PATCH
    return bytes(output)


def dependencies(code, module):
    try:
        target = int(module['symbols']['af_quest_set_item'], 16)
    except (KeyError, TypeError, ValueError):
        raise ValueError('Song names require the complete item-field runtime') from None
    expected = struct.pack('>2I', 0x08000000 | ((target >> 2) & 0x03FFFFFF), 0)
    if (target % 4 or not MODULE_RAM <= target < MODULE_RAM+LINKED_LIMIT or
            code[WRAPPER-CODE_RAM:WRAPPER-CODE_RAM+8] != expected):
        raise ValueError('Song names require the installed complete item-ID wrapper')


def install(native, replacements, additions, module):
    files = by_vrom(native)
    expected, relocation = credits.patch(files[credits.VROM].extract(native), files[credits.RELOCATION].extract(native))
    if (replacements.get(credits.VROM) != expected or replacements.get(credits.RELOCATION) != relocation or
            MODULE_VROM not in additions or additions.get(ITEMS_VROM, b'')[:32] != HEADER):
        raise ValueError('Song names require unchanged English credits, runtime, and complete item resource')
    dependencies(replacements.get(CODE_VROM, b''), module)
    output = patch(expected, relocation)
    replacements[credits.VROM] = output
    return {'vrom':f'{credits.VROM:08X}', 'entry':f'{START:08X}',
            'source_setter_sha256':SOURCE_HASH, 'overlay_sha256':sha256(output),
            'relocation_sha256':sha256(relocation), 'setter_sha256':sha256(PATCH),
            'wrapper':f'{WRAPPER:08X}', 'item_bytes':16, 'new_resident_bytes':0,
            'new_saved_bytes':0, 'song_request_input_expanded':False}


def verify_installation(native, built, report):
    module = report['runtime_module']
    verify_test_module(built, module)
    source, files = by_vrom(native), by_vrom(built)
    expected, relocation = credits.patch(source[credits.VROM].extract(native), source[credits.RELOCATION].extract(native))
    output = patch(expected, relocation)
    dependencies(files[CODE_VROM].extract(built), module)
    if (files[credits.VROM].extract(built) != output or files[credits.RELOCATION].extract(built) != relocation or
            files[ITEMS_VROM].extract(built)[:32] != HEADER or
            report.get('song_item_names', {}).get('overlay_sha256') != sha256(output)):
        raise ValueError('Complete song-title caller is not installed')

