"""Guarded original generation code for isolated native calls, not ROM hooks."""

from pathlib import Path
import struct

from aflib import sha256
from build_mail_generation import (IMPORTS,SOURCES,FORTUNE_SOURCES,LEAFLET_IMPORTS,LEAFLET_SOURCES,
                                   EVENT_LEAFLET_IMPORTS,EVENT_LEAFLET_SOURCES,EVENT_NATIVE_IMPORTS)
from runtime_layout import MODULE_RAM,RESERVATION


def validate(code,report,module,*,fortune_slip=False,leaflets=False,event_leaflets=False):
    root = Path(__file__).resolve().parents[1]
    if sum((fortune_slip,leaflets,event_leaflets)) > 1: raise ValueError('Select one generation probe variant')
    sources = EVENT_LEAFLET_SOURCES if event_leaflets else LEAFLET_SOURCES if leaflets else FORTUNE_SOURCES if fortune_slip else SOURCES
    names = EVENT_LEAFLET_IMPORTS if event_leaflets else LEAFLET_IMPORTS if leaflets else IMPORTS
    imports = {name:int(module['symbols'][name],16) for name in names}
    if event_leaflets: imports.update(EVENT_NATIVE_IMPORTS)
    if (report.get('version') != 1 or report.get('base') != 0x80200000
            or report.get('bytes') != len(code) or not 0 < len(code) <= 4096
            or len(code)&3 or report.get('sha256') != sha256(code)
            or report.get('sources') != {name:sha256((root/name).read_bytes()) for name in sources}
            or report.get('variant') != ('event_leaflets' if event_leaflets else 'leaflets' if leaflets else 'fortune_slip' if fortune_slip else None)
            or report.get('module_sha256') != module['module_sha256']
            or report.get('imports') != imports):
        raise ValueError('Stale or altered native generation probe')
    required = ('af_mail_capture_reset','af_mail_capture_set','af_mail_generate')
    if fortune_slip: required += ('af_fortune_slip_create',)
    if leaflets or event_leaflets: required += ('af_leaflet_create','af_leaflet_hour')
    if event_leaflets: required += ('af_event_leaflet_publish',)
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


def relocate(code,report,module,base,*,fortune_slip=False,leaflets=False,event_leaflets=False):
    validate(code,report,module,fortune_slip=fortune_slip,leaflets=leaflets,event_leaflets=event_leaflets)
    if type(base) is not int or base&15 or not MODULE_RAM+RESERVATION <= base <= 0x80400000-len(code):
        raise ValueError('Invalid native generation allocation base')
    output = bytearray(code)
    for offset in report['jump_relocations']:
        word = struct.unpack_from('>I',code,offset)[0]
        target = 0x80000000|((word&0x3FFFFFF)<<2)
        struct.pack_into('>I',output,offset,(word&0xFC000000)|((base+target-report['base'])&0xFFFFFFF)>>2)
    return bytes(output)
