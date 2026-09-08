"""Complete leaflet date fields with source-bound temporary lifetimes."""

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256,verified_rom
from code_sections import code_segments
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT,RESERVATION

ROOT = Path(__file__).resolve().parents[1]
HOUR,HOUR_END = 0x800C4228,0x800C42E8
HOUR_HASH = '28a4a689459d0dee61a0aec446831ad1875e90e4aca9aa3e900f1f2df8ab4ac3'
HOUR_CODE_HASH = 'eeb382edeeda4fb8ab3f7c070118a40ae224ee647b5a36b17294c924bec3bfaf'
HOUR_CALLS = ((CODE_VROM,0x8009F0C4-CODE_RAM),(0x850680,0x29C),(0x850680,0x324))
SOURCES = ('overlays/leaflet_dates/hour.c','overlays/leaflet_dates/hour.ld')


@dataclass(frozen=True)
class LeafletActor:
    vrom: int
    ram: int
    relocation: int
    file_bytes: int
    sections: tuple
    file_sha256: str
    relocation_sha256: str

    @property
    def resident_bytes(self):
        return self.file_bytes+self.sections[3]


ACTORS = {
    'renewal': LeafletActor(0x84D180,0x809583B0,0x84E000,3712,(3216,496,0,0,23),
        '412cc3f59962c1c5276fecb6081ffe3d3c7f6e69f201b152e6277a1fd1f57258',
        '8e2dd79ceec1961a5bdee84fb01c9189e1532872b44efe64ce68603da28b462a'),
    'event': LeafletActor(0x850680,0x8095B8B0,0x857100,27264,(25424,1808,32,304,362),
        '6883daac345e8aefd3c35ca1da307a3d198b76a470cee25b99e92aa0f030707d',
        '515aa6085bb16b56ea051bfc2afe8e04551eca176a7f47bb6f0140b08fc73c49'),
}
CALLS = {
    'renewal': ((0x809584B8,0x800C40F8,'af_format_month'),
                (0x809584D4,0x800C41B8,'af_format_day'),
                (0x809584F0,0x800C4084,'af_format_year')),
    'event': ((0x8095BB0C,0x800C40F8,'af_format_month'),
              (0x8095BB2C,0x800C41B8,'af_format_day'),
              (0x8095BB94,0x800C40F8,'af_format_month'),
              (0x8095BBB4,0x800C41B8,'af_format_day')),
}
SCRATCH_CHANGES = ((0x8095BB90,0x27A40028,0x27A40018),
                   (0x8095BBA0,0x27A50028,0x27A50018))


def source_hashes():
    return {name:sha256((ROOT/name).read_bytes()) for name in SOURCES}


def jal(target):
    return 0x0C000000 | ((target & 0x0FFFFFFF) >> 2)


def validate_hour(data, report):
    if (report.get('version') != 1 or report.get('ram') != HOUR
            or report.get('bytes') != len(data) or not 0 < len(data) <= HOUR_END-HOUR
            or len(data)&3 or report.get('sha256') != sha256(data) or sha256(data) != HOUR_CODE_HASH
            or report.get('sources') != source_hashes() or report.get('imports') != []
            or report.get('relocations') != [] or report.get('destination_bytes') != 7):
        raise ValueError('Changed, oversized, or stale leaflet hour code')
    for (word,) in struct.iter_unpack('>I',data):
        if word>>26 in (2,3) or word>>26 == 0 and word&63 == 9:
            raise ValueError('Leaflet hour unexpectedly calls or jumps to another function')
    return data.ljust(HOUR_END-HOUR,b'\0')


def source(rom, name):
    spec = ACTORS[name]
    files = by_vrom(rom)
    data,reloc = files[spec.vrom].extract(rom),files[spec.relocation].extract(rom)
    if (len(data) != spec.file_bytes or sha256(data) != spec.file_sha256
            or sha256(reloc) != spec.relocation_sha256 or struct.unpack_from('>5I',reloc) != spec.sections):
        raise ValueError('Changed native leaflet actor or scratch-lifetime evidence')
    return data,reloc


@lru_cache(maxsize=1)
def native_evidence(rom):
    rom = verified_rom(rom)
    files = by_vrom(rom)
    for name in ACTORS:
        source(rom,name)
    code = files[CODE_VROM].extract(rom)
    if sha256(code[HOUR-CODE_RAM:HOUR_END-CODE_RAM]) != HOUR_HASH:
        raise ValueError('Changed original hour formatter')
    segments,definitions = code_segments()
    refs = []
    for vrom,file in files.items():
        if file.pstart == 0xFFFFFFFF:
            continue
        data = file.extract(rom);segment = segments.get(vrom)
        for i,(word,) in enumerate(struct.iter_unpack('>I',data[:len(data)//4*4])):
            at = i*4
            if vrom == CODE_VROM and HOUR-CODE_RAM <= at < HOUR_END-CODE_RAM:
                continue
            if HOUR <= word < HOUR_END:
                raise ValueError('Unreviewed literal pointer to the native hour formatter')
            if segment and segment.is_text(at) and word>>26 in (2,3):
                target = 0x80000000 | ((word&0x3FFFFFF)<<2)
                if HOUR <= target < HOUR_END:
                    if target != HOUR:
                        raise ValueError('External reference enters the native hour formatter interior')
                    refs.append((vrom,at))
    if tuple(sorted(refs)) != HOUR_CALLS:
        raise ValueError('Unreviewed native hour formatter caller')
    return {'hour_callers':[[f'{v:08X}',f'{at:06X}'] for v,at in refs],
            'external_interior_or_literal_references':0,'definition_sha256':definitions}


def changes(name, module):
    result = []
    used = module.get('linked_bytes',0)
    if type(used) is not int or not 0x300 < used <= LINKED_LIMIT:
        raise ValueError('Leaflet dates require the bounded current resident formatter')
    for address,old,symbol in CALLS[name]:
        target = int(module.get('symbols',{}).get(symbol,'0'),16)
        if target&3 or not MODULE_RAM+0x300 <= target < MODULE_RAM+used:
            raise ValueError('Leaflet date import lies outside resident code')
        result.append((address,jal(old),jal(target)))
    return result + (list(SCRATCH_CHANGES) if name == 'event' else [])


def patched(rom,name,module):
    data,reloc = source(rom,name);spec = ACTORS[name]
    rows = struct.unpack_from('>'+str(spec.sections[4])+'I',reloc,20)
    result = bytearray(data)
    for address,before,after in changes(name,module):
        offset = address-spec.ram
        if struct.unpack_from('>I',data,offset)[0] != before or any(row&0xFFFFFF == offset for row in rows):
            raise ValueError('Leaflet date instruction or relocation conflicts with the patch')
        struct.pack_into('>I',result,offset,after)
    return bytes(result),reloc


def relocated(rom,name,module,base):
    data,reloc = source(rom,name);spec = ACTORS[name]
    result = bytearray(relocate_verified_data(spec,data,reloc,base))
    for address,_,after in changes(name,module):
        struct.pack_into('>I',result,address-spec.ram,after)
    return bytes(result)


def verify_installation(rom,native,module,directory):
    files = by_vrom(rom)
    native_evidence(native)
    for name,spec in ACTORS.items():
        data,reloc = patched(native,name,module)
        if files[spec.vrom].extract(rom) != data or files[spec.relocation].extract(rom) != reloc:
            raise ValueError('Installed leaflet actor differs from the complete guarded patch')
    hour = validate_hour((directory/'hour.bin').read_bytes(),json.loads((directory/'hour.json').read_text()))
    code = files[CODE_VROM].extract(rom)
    if code[HOUR-CODE_RAM:HOUR_END-CODE_RAM] != hour:
        raise ValueError('Installed leaflet hour differs from compiled source')
    if struct.unpack_from('>I',code,0x8009F0C4-CODE_RAM)[0] != jal(int(module['symbols']['af_format_hour'],16)):
        raise ValueError('Numeric-only dialogue hour must retain its separate formatter')


def install(rom,replacements,additions,relocations,module,directory):
    from runtime_module import runtime_source_hashes,verify_test_module
    if (not module or module.get('source_sha256') != sha256(rom)
            or module.get('runtime_sources') != runtime_source_hashes(ROOT/'runtime')
            or MODULE_VROM not in additions):
        raise ValueError('Leaflet dates require the current resident module')
    binary = bytearray(additions[MODULE_VROM])
    if len(binary) != RESERVATION:
        raise ValueError('Invalid leaflet resident reservation')
    binary[56:0x88] = bytes(0x88-56)
    if sha256(binary) != module['module_sha256']:
        raise ValueError('Changed leaflet resident formatter code')
    evidence = native_evidence(rom)
    changed = dict(replacements)
    for name,spec in ACTORS.items():
        data,reloc = source(rom,name)
        if (replacements.get(spec.vrom,data) != data or replacements.get(spec.relocation,reloc) != reloc
                or any(v in additions or v in relocations for v in (spec.vrom,spec.relocation))):
            raise ValueError('Leaflet date patch overlaps another actor change')
        changed[spec.vrom] = patched(rom,name,module)[0]
    hour_report = json.loads((directory/'hour.json').read_text())
    hour = validate_hour((directory/'hour.bin').read_bytes(),hour_report)
    code = bytearray(changed.get(CODE_VROM,by_vrom(rom)[CODE_VROM].extract(rom)))
    if sha256(code[HOUR-CODE_RAM:HOUR_END-CODE_RAM]) != HOUR_HASH:
        raise ValueError('Leaflet hour replacement overlaps another code change')
    code[HOUR-CODE_RAM:HOUR_END-CODE_RAM] = hour
    changed[CODE_VROM] = bytes(code)
    prospective = replace_dma(rom,changed,relocations,additions)
    verify_test_module(prospective,module)
    verify_installation(prospective,rom,module,directory)
    replacements.update({v:changed[v] for v in (CODE_VROM,*(s.vrom for s in ACTORS.values()))})
    return {'hour':hour_report,'evidence':evidence,
            'changes':{name:[{'ram':f'{a:08X}','before':f'{b:08X}','after':f'{c:08X}'}
                            for a,b,c in changes(name,module)] for name in ACTORS},
            'saved_layout_changed':False,'resident_growth_bytes':0,
            'scope':'Complete leaflet date fields; full letter creation/publication and normal delivery remain separate work'}
