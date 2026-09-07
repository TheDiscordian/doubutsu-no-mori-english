"""Source-verified English scoring tables and guarded native overlay installation."""

from pathlib import Path
import json
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from gc_names import symbol_data

ROOT = Path(__file__).resolve().parents[1]
VROM, RELOC_VROM, RAM, SIZE, RELOC_SIZE = 0x00954D30, 0x009563E0, 0x80A94AC0, 5808, 592
SOURCE_SHA256 = '5399742f7f455ca6e3705470a8487d54e372ee3367139badc25e157a98872d06'
RELOC_SHA256 = '426c9b64e81d7fa69d8c7ce8fd73ba4a34ed3c8b4ba377738289dbf538fde63f'
REL_SHA256 = '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
SYMBOLS_SHA256 = 'e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'
GC_SOURCE_SHA256 = 'e19211a7944ff1aef7ff2be1ef39c7e8b9ed983624af1a58ffa11fff500bdc21'
NATIVE_GRADE_SHA256 = '7b8155585b301d0acf9a2f7c2663fe56dfb55305a103aedb04ae14ad72ae905e'


def load_prefixes(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols.encode()) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English mail-grading reference')
    counts, payload, report = [0], bytearray(), {}
    for char in 'abcdefghijklmnopqrstuvwxyz':
        data = symbol_data(rel, symbols, 'str_'+char+'_table')
        if not data or len(data) % 2 or any(c not in b" abcdefghijklmnopqrstuvwxyz'" for c in data):
            raise ValueError('Unexpected English prefix-table data')
        payload.extend(data)
        counts.append(len(payload)//2)
        report[char] = {'pairs': len(data)//2, 'sha256': sha256(data)}
    if counts[-1] != 776:
        raise ValueError('Incomplete English prefix tables')
    data = struct.pack('>27H', *counts)+payload
    return data, {'tables': report, 'pairs': counts[-1], 'bytes': len(data), 'sha256': sha256(data),
                  'semantics': 'Bounded per-letter tables; do not reproduce GAFE01 unterminated-table overreads'}


def source_hashes():
    paths = sorted((ROOT/'overlays/mail_check').iterdir())+[ROOT/'runtime/mail/grade.h']
    return {p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()) for p in paths if p.is_file()}


def relocate(data, reloc, base):
    """Validate and model the three native relocation types used by this overlay."""
    if len(data) != SIZE or len(reloc) != RELOC_SIZE or base & 15 or not 0x80000000 <= base <= 0x80400000-SIZE:
        raise ValueError('Invalid mail-check relocation buffer')
    text, writable, rodata, bss, count = struct.unpack_from('>5I',reloc)
    if (text+writable+rodata > SIZE or bss or count > (RELOC_SIZE-24)//4
            or any(n % 16 for n in (text,writable,rodata)) or not text
            or any(reloc[20+count*4:-4]) or struct.unpack_from('>I',reloc,RELOC_SIZE-4)[0] != RELOC_SIZE):
        raise ValueError('Invalid mail-check relocation header')
    result, hi, previous, jumps = bytearray(data),{},-1,set()
    for record in struct.unpack_from('>'+str(count)+'I',reloc,20):
        section, kind, offset = record >> 30,(record >> 24)&63,record&0xFFFFFF
        if section != 1 or offset & 3 or offset+4 > text or offset <= previous:
            raise ValueError('Unexpected mail-check relocation section/order')
        previous = offset
        word = struct.unpack_from('>I',data,offset)[0]
        if kind == 4:
            target = 0x80000000 | ((word&0x3FFFFFF)<<2)
            if word >> 26 not in (2,3) or not RAM <= target < RAM+text:
                raise ValueError('Invalid mail-check relocated jump')
            word = (word&0xFC000000)|(((base+target-RAM)&0x0FFFFFFF)>>2)
            jumps.add(offset)
        elif kind == 5:
            if word >> 26 != 15: raise ValueError('Invalid mail-check high relocation')
            register = (word>>16)&31
            if register in hi: raise ValueError('Unpaired mail-check high relocation')
            hi[register] = offset,word
            continue
        elif kind == 6:
            register = (word>>21)&31
            if register not in hi or word >> 26 != 9:
                raise ValueError('Unpaired mail-check low relocation')
            high_offset,high = hi.pop(register)
            value = ((high&0xFFFF)<<16)+(word&0xFFFF)-(0x10000 if word&0x8000 else 0)
            if not RAM <= value < RAM+text+writable+rodata:
                raise ValueError('Mail-check relocation points outside linked content')
            value += base-RAM
            struct.pack_into('>I',result,high_offset,(high&0xFFFF0000)|(((value+0x8000)>>16)&0xFFFF))
            word = (word&0xFFFF0000)|(value&0xFFFF)
        else:
            raise ValueError('Unsupported mail-check relocation type')
        struct.pack_into('>I',result,offset,word)
    if hi or not {0,8,0x24C} <= jumps:
        raise ValueError('Incomplete mail-check relocations')
    return bytes(result)


def install(rom, replacements, additions, module, directory):
    from runtime_module import MODULE_RAM, MODULE_VROM, LINKED_LIMIT
    files = by_vrom(rom)
    for vrom, digest in ((VROM, SOURCE_SHA256), (RELOC_VROM, RELOC_SHA256)):
        if sha256(files[vrom].extract(rom)) != digest:
            raise ValueError('Unexpected native mail-check overlay')
        if vrom in replacements:
            raise ValueError('Overlapping mail-check overlay replacements')
    if not module or MODULE_VROM not in additions or sha256(additions[MODULE_VROM]) != module['module_sha256']:
        raise ValueError('English mail grading requires the unchanged verified resident module')
    report = json.loads((directory/'overlay.json').read_text())
    data, reloc = (directory/'overlay.bin').read_bytes(), (directory/'relocation.bin').read_bytes()
    if (report.get('source_sha256') != sha256(rom) or report.get('sources') != source_hashes()
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_sha256') != sha256(reloc)
            or len(data) != SIZE or len(reloc) != RELOC_SIZE):
        raise ValueError('Stale or mismatched English mail-check overlay')
    if data[16:32] != struct.pack('>4I', 0x41464D47, 1, 96, 1024):
        raise ValueError('Unexpected English mail-check ABI')
    for base in (0x801A0000,0x802F8010):
        relocate(data,reloc,base)
    target = int(module.get('symbols', {}).get('af_mail_grade_native', '0'), 16)
    if not MODULE_RAM+0x300 <= target < MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT) or target & 3:
        raise ValueError('English mail grader is outside the resident module')
    original = files[CODE_VROM].extract(rom)
    if (sha256(original[0x800A86C4-CODE_RAM:0x800A86E8-CODE_RAM]) != NATIVE_GRADE_SHA256
            or report.get('native_grade_sha256') != NATIVE_GRADE_SHA256):
        raise ValueError('Unexpected native ordinary-reply grading entry')
    code = bytearray(replacements.get(CODE_VROM,original))
    offset = 0x800A86C4-CODE_RAM
    if code[offset:offset+8] != original[offset:offset+8]:
        raise ValueError('Overlapping ordinary-reply grading hook')
    struct.pack_into('>2I', code, offset, 0x08000000 | ((target & 0x0FFFFFFF) >> 2), 0)
    replacements.update({CODE_VROM: bytes(code), VROM: data, RELOC_VROM: reloc})
    return {**report, 'hook_ram': '800A86C4', 'target_ram': f'{target:08X}',
            'status': 'English ordinary-body reply scorer and bounded quest word tables; generated snapshot delivery remains disabled'}
