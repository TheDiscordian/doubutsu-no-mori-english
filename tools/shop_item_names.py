"""Complete shop/Redd item-name preparation through the existing bounded resident rows."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from code_sections import code_segments
from extended_items import HEADER, COUNTS, WIDTH, VROM as ITEMS_VROM
from runtime_module import MODULE_VROM
from shop_units import SHOPS

ROOT = Path(__file__).resolve().parents[1]
BODY_BYTES = 72
BODY_SHA = '6815f91a000a4ce1acb4fe1f51992aa5a74ea64f1e17f5cae08a400263b87620'
MODULE_SHA = '493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6'
IMPORTS = {'af_set_item_str': 0x801965AC, 'af_quest_set_item': 0x80196814,
           'af_copy_item_string': 0x801966AC, 'af_load_item_name': 0x801969C8}


@dataclass(frozen=True)
class NameActor:
    vrom: int
    ram: int
    relocation: int
    entry: int
    file_bytes: int
    sections: tuple
    file_sha256: str
    relocation_sha256: str

    @property
    def resident_bytes(self):
        return self.file_bytes+self.sections[3]


ACTORS = {name: NameActor(spec.vrom, spec.ram, spec.relocation, spec.handler-0x98,
                         spec.file_bytes, spec.sections, spec.file_sha256, spec.relocation_sha256)
          for name, spec in SHOPS.items()}
ACTORS['redd'] = NameActor(0x008BBAA0, 0x809D82B0, 0x008BD250, 0x809D8560,
                          6064, (5760, 288, 16, 0, 134),
                          'a3aa6a9ff4709e1284e3e560e4a644de26e124beb8c0a911f0f7ca2edbb3505f',
                          '45bf7222af27740244a58eaa7fda93665f466e5a8c5e9fa42f2eeb93021cf9eb')


def start(spec):
    return spec.entry


def jump(address, *, link=False):
    return (0x0C000000 if link else 0x08000000) | ((address >> 2) & 0x3FFFFFF)


def body():
    # Independently assembled from overlays/shop/item_name.s in the focused test.
    return struct.pack('>10I', 0x3084FFFF, 0x14800006, 0, 0x3C048014, 0x24842410,
                       0x00803025, jump(IMPORTS['af_set_item_str']), 0x00003825,
                       jump(IMPORTS['af_quest_set_item']), 0).ljust(BODY_BYTES, b'\0')


def verify_source(spec, data, reloc):
    if (spec not in ACTORS.values() or len(data) != spec.file_bytes
            or sha256(data) != spec.file_sha256 or sha256(reloc) != spec.relocation_sha256
            or struct.unpack_from('>5I', reloc) != spec.sections):
        raise ValueError('Changed native shop actor or relocation')
    at = start(spec)-spec.ram
    if sha256(data[at:at+BODY_BYTES]) != BODY_SHA:
        raise ValueError('Changed native shop item-name helper')
    count = struct.unpack_from('>I', reloc, 16)[0]
    if any(word >> 30 == 1 and at <= (word & 0xFFFFFF) < at+BODY_BYTES
           for (word,) in struct.iter_unpack('>I', reloc[20:20+count*4])):
        raise ValueError('Shop item-name helper has an unexpected relocation')


@lru_cache(maxsize=1)
def audit_references(native):
    native = verified_rom(native)
    segments, definitions = code_segments()
    regions = [(s.vrom, start(s), start(s)+BODY_BYTES) for s in ACTORS.values()]
    if len(segments) < 100 or any(vrom not in segments for vrom, _, _ in regions):
        raise ValueError('Incomplete native shop executable inventory')
    lower, upper = min(r[1] for r in regions), max(r[2] for r in regions)
    entries = []
    for vrom, file in by_vrom(native).items():
        if file.pstart == 0xFFFFFFFF: continue
        data, segment = file.extract(native), segments.get(vrom)
        for offset in range(0, len(data)-3, 4):
            pc = segment.ram+offset if segment else None
            word = struct.unpack_from('>I', data, offset)[0]
            targets = [word] if lower <= word < upper else []
            if segment and segment.is_text(offset):
                op = word >> 26
                if op in (2, 3):
                    target = ((pc+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2)
                    if lower <= target < upper: targets.append(target)
                if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or op == 17 and (word >> 21) & 31 == 8:
                    displacement = (word & 65535)-(65536 if word & 32768 else 0)
                    target = pc+4+displacement*4
                    if lower <= target < upper: targets.append(target)
            for target in targets:
                for owner, first, end in regions:
                    if first < target < end:
                        raise ValueError('Unexpected shop helper interior reference')
                    if target == first:
                        entries.append([f'{vrom:08X}', f'{offset:06X}', f'{target:08X}'])
    if {int(row[2], 16) for row in entries} != {r[1] for r in regions}:
        raise ValueError('Native shop helper lacks an identified caller')
    return {'entry_references': entries, 'external_interior_references': [],
            'definition_sha256': definitions,
            'scope': 'Aligned literals, direct jumps, and relative branches in pinned executable ranges'}


def verify_imports(code, module_data, items, module):
    if (not module or module.get('module_sha256') != MODULE_SHA
            or {name: int(module['symbols'].get(name, '0'), 16) for name in IMPORTS} != IMPORTS):
        raise ValueError('Shop names require the exact complete resident imports')
    baseline = bytearray(module_data)
    if len(baseline) != 32768:
        raise ValueError('Shop names require the complete resident allocation')
    baseline[56:0x88] = bytes(0x88-56)
    if sha256(baseline) != MODULE_SHA:
        raise ValueError('Changed shop-name resident implementation')
    if (struct.unpack_from('>I', module_data, 56)[0] != ITEMS_VROM
            or items[:32] != HEADER or len(items) != 32+sum(COUNTS)*WIDTH):
        raise ValueError('Shop names require the enabled complete item resource')
    for at, expected in ((0x8009D88C, jump(IMPORTS['af_set_item_str'])),
                         (0x800A1820, jump(IMPORTS['af_copy_item_string'], link=True))):
        if struct.unpack_from('>I', code, at-CODE_RAM)[0] != expected:
            raise ValueError('Shop names require the installed full item setter and message reader')


def install(native, replacements, additions, module):
    native = verified_rom(native)
    files = by_vrom(native)
    code = replacements.get(CODE_VROM, files[CODE_VROM].extract(native))
    verify_imports(code, additions.get(MODULE_VROM, b''), additions.get(ITEMS_VROM, b''), module)
    evidence = audit_references(native)
    pending, actors = {}, {}
    for name, spec in ACTORS.items():
        data = replacements.get(spec.vrom, files[spec.vrom].extract(native))
        reloc = replacements.get(spec.relocation, files[spec.relocation].extract(native))
        verify_source(spec, data, reloc)
        at = start(spec)-spec.ram
        result = data[:at]+body()+data[at+BODY_BYTES:]
        pending[spec.vrom] = result
        actors[name] = {'vrom': f'{spec.vrom:08X}', 'entry': f'{start(spec):08X}',
                        'source_sha256': sha256(data), 'installed_sha256': sha256(result),
                        'relocation_sha256': sha256(reloc), 'file_bytes': len(result)}
    replacements.update(pending)
    return {'actors': actors, 'imports': IMPORTS, 'module_sha256': MODULE_SHA,
            'item_resource_sha256': sha256(additions[ITEMS_VROM]), 'helper_bytes': BODY_BYTES,
            'complete_name_bytes': WIDTH, 'extra_allocation_bytes': 0, 'saved_layout_changes': False,
            'empty_item_clears_field': True, 'reference_audit': evidence}


def verify_installation(built, native, report):
    from runtime_module import verify_test_module
    module = report.get('runtime_module')
    if not module: raise ValueError('Shop names lack a resident module')
    verify_test_module(built, module)
    files = by_vrom(built)
    expected = {CODE_VROM: files[CODE_VROM].extract(built)}
    additions = {vrom: files[vrom].extract(built) for vrom in (MODULE_VROM, ITEMS_VROM)}
    evidence = install(native, expected, additions, module)
    for spec in ACTORS.values():
        if (files[spec.vrom].extract(built) != expected[spec.vrom]
                or sha256(files[spec.relocation].extract(built)) != spec.relocation_sha256):
            raise ValueError('Complete shop name helper or retained relocation is not installed')
    if report.get('shop_item_names') != evidence:
        raise ValueError('Missing or changed shop-name application evidence')
    return evidence
