"""Guarded original generation code for isolated native calls, not ROM hooks."""

from pathlib import Path
import struct

from aflib import sha256
from build_mail_generation import IMPORTS,SOURCES,FORTUNE_SOURCES
from runtime_layout import MODULE_RAM,RESERVATION


def validate(code,report,module,*,fortune_slip=False):
    root = Path(__file__).resolve().parents[1]
    sources = FORTUNE_SOURCES if fortune_slip else SOURCES
    if (report.get('version') != 1 or report.get('base') != 0x80200000
            or report.get('bytes') != len(code) or not 0 < len(code) <= 4096
            or len(code)&3 or report.get('sha256') != sha256(code)
            or report.get('sources') != {name:sha256((root/name).read_bytes()) for name in sources}
            or report.get('variant') != ('fortune_slip' if fortune_slip else None)
            or report.get('module_sha256') != module['module_sha256']
            or report.get('imports') != {name:int(module['symbols'][name],16) for name in IMPORTS}):
        raise ValueError('Stale or altered native generation probe')
    required = ('af_mail_capture_reset','af_mail_capture_set','af_mail_generate')
    if fortune_slip: required += ('af_fortune_slip_create',)
    if set(report['symbols']) != set(required) or any(type(v) is not int or v&3 or not 0 <= v < len(code)
                                                     for v in report['symbols'].values()):
        raise ValueError('Invalid native generation entry points')
    relocs = report['jump_relocations']
    if not isinstance(relocs,list) or any(type(i) is not int or i&3 or not 0 <= i < len(code) for i in relocs):
        raise ValueError('Invalid generation relocation locations')
    if len(set(relocs)) != len(relocs): raise ValueError('Duplicate generation relocation')
    seen = set()
    for offset in range(0,len(code),4):
        word = struct.unpack_from('>I',code,offset)[0]
        if word>>26 not in (2,3): continue
        target = 0x80000000|((word&0x3FFFFFF)<<2)
        if 0x80200000 <= target < 0x80200000+len(code):
            seen.add(offset)
        elif target not in report['imports'].values():
            raise ValueError('Unapproved native generation jump')
    if seen != set(relocs): raise ValueError('Generation internal jump inventory differs')


def relocate(code,report,module,base,*,fortune_slip=False):
    validate(code,report,module,fortune_slip=fortune_slip)
    if type(base) is not int or base&15 or not MODULE_RAM+RESERVATION <= base <= 0x80400000-len(code):
        raise ValueError('Invalid native generation allocation base')
    output = bytearray(code)
    for offset in report['jump_relocations']:
        word = struct.unpack_from('>I',code,offset)[0]
        target = 0x80000000|((word&0x3FFFFFF)<<2)
        struct.pack_into('>I',output,offset,(word&0xFC000000)|((base+target-report['base'])&0xFFFFFFF)>>2)
    return bytes(output)
