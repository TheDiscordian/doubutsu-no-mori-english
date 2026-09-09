"""Full names in home, lost-property, and visiting/opening shop conversations."""
from dataclasses import dataclass
from functools import lru_cache
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from code_sections import code_segments
from extended_items import VROM as ITEMS_VROM
from player_item_names import BRIDGE, BRIDGE_END
from runtime_module import MODULE_VROM, verify_test_module
from shop_item_names import NameActor, IMPORTS, body as bridge_body, jump, verify_imports

ACTORS = {
    'room': NameActor(0x0082D7F0, 0x80936710, 0x00844400, 0, 93200,
        (69200, 23520, 480, 8944, 1543),
        '4c67db43a7cebe9a35119621a13bac2fe8cb977cd7ab894b6b5e6b08e1d296a0',
        '418c53a6dc9d7a2e76eb87054394348fa03db0a4a6385251308dd808b438a71f'),
    'police': NameActor(0x008A5760, 0x809C1F70, 0x008A6A60, 0, 4864,
        (4608, 224, 32, 0, 100),
        '2d66ecc0dfda9559511db61f68217019e26f898e56b3799753920c84b130317b',
        'f1b4823b5d6c5478f4ca5113f1c597bc295b776345a131c1f3ae5dd380ef8aab'),
    'angler': NameActor(0x008B8FC0, 0x809D57D0, 0x008BA290, 0, 4816,
        (4672, 144, 0, 0, 63),
        '1de725e71a17f9fc56a9b78e4f48650ab837b07a179e057fb32d86f75f4330a2',
        'b0f511d58bbff2bdf8a0b6a7d1f7bc57631e94c3072f1c1f2d7d310ae3e42572'),
    'redd_outside': NameActor(0x008BAE60, 0x809D7670, 0x008BB990, 0, 2864,
        (2704, 144, 16, 0, 60),
        '0536b00497225d700c8006bcb7c35ca71ec912adda805032d2eff078b0d42596',
        '05536ade24497f0f903db4e1ae69cb39f7e3acbcbed06ac6f0ee27b1084a724f'),
    'saharah': NameActor(0x008BD480, 0x809D9C90, 0x008BE570, 0, 4336,
        (4064, 272, 0, 0, 66),
        'be55e68d7b9d3fa250f543151fb6b3ade939ffe0fdbbf4f8afc9c540e411e0e5',
        '803c99524caf5f41b8b4ab3bb290e5245b9787c388c22eb76c9db1758142f684'),
    'opening_nook': NameActor(0x0092C850, 0x80A6C5B0, 0x0092E960, 0, 8464,
        (7664, 800, 0, 0, 177),
        'ffa9184b4deab92e5e702e2d2773c2d6f4944095adec398cc67832f1b5786962',
        'eb541b24ebf65bbe948b15231e6d277eb2887d2c1dcf2d994e83f8097a3312ac'),
}


@dataclass(frozen=True)
class Call:
    actor: str
    address: int
    size: int
    source_sha256: str
    item_expression: int
    slot: int = 0


CALLS = {
    'room_first': Call('room', 0x8093931C, 36,
        'f4957a998e73b2db078f8d338649dd25bc87f89441e2720b061023c6905e9bbf', 0x00A02025),
    'room_second': Call('room', 0x80939994, 36,
        'f4957a998e73b2db078f8d338649dd25bc87f89441e2720b061023c6905e9bbf', 0x00A02025),
    'police': Call('police', 0x809C28BC, 36,
        '6fa94630b1b4b24e464150206e05e72451b57e7494c0a6ab2a6599c8103dcfdb', 0x94A46294),
    'angler': Call('angler', 0x809D608C, 28,
        '563fe0dd1d16936186cb70412e4bf83e7820b36c3f172b63fae6095e6be84964', 0x96040944),
    'redd_outside': Call('redd_outside', 0x809D7F74, 36,
        '3faab34b417d6001d98af8856f280011a2f5cfd9842bd980b25a5e18940fb992', 0x00A02025, 2),
    'saharah': Call('saharah', 0x809DA8F4, 28,
        'ce088d7a8f1afb0a058606c0982eb0ec768e2e337442eb9f61b5a6237a5ee9e9', 0x97A4003A),
    'opening_nook': Call('opening_nook', 0x80A6D054, 36,
        'd10319bf19d534bb308f861a03943620b4de9a0dee7da2362d3011b09ca96452', 0x00A02025),
}


def call_body(name):
    call = CALLS[name]
    return struct.pack('>3I', call.item_expression, jump(BRIDGE, link=True),
                       0x24050000 | call.slot).ljust(call.size, b'\0')


def source(native, name):
    files, spec = by_vrom(verified_rom(native)), ACTORS[name]
    data, reloc = [files[v].extract(native) for v in (spec.vrom, spec.relocation)]
    if (len(data) != spec.file_bytes or sha256(data) != spec.file_sha256
            or sha256(reloc) != spec.relocation_sha256
            or struct.unpack_from('>5I', reloc) != spec.sections):
        raise ValueError('Changed native event/home item-name actor or relocation')
    for call in (c for c in CALLS.values() if c.actor == name):
        offset = call.address-spec.ram
        if sha256(data[offset:offset+call.size]) != call.source_sha256:
            raise ValueError('Changed native event/home name sequence')
        if any(word >> 30 == 1 and offset <= (word & 0xFFFFFF) < offset+call.size
               for (word,) in struct.iter_unpack('>I', reloc[20:20+spec.sections[4]*4])):
            raise ValueError('Event/home name sequence has an unexpected relocation')
    return data, reloc


@lru_cache(maxsize=1)
def audit_references(native):
    verified_rom(native)
    segments, definitions = code_segments()
    if len(segments) < 100 or any(s.vrom not in segments for s in ACTORS.values()):
        raise ValueError('Incomplete event/home executable inventory')
    regions = [(c.address, c.address+c.size) for c in CALLS.values()]
    lower, upper = min(a for a, b in regions), max(b for a, b in regions)
    for vrom, file in by_vrom(native).items():
        if file.pstart == 0xFFFFFFFF: continue
        data, segment = file.extract(native), segments.get(vrom)
        for offset in range(0, len(data)-3, 4):
            word = struct.unpack_from('>I', data, offset)[0]
            targets = [word] if lower < word < upper else []
            if segment and segment.is_text(offset):
                pc, op = segment.ram+offset, word >> 26
                if op in (2, 3): targets.append(((pc+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2))
                if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or op == 17 and (word >> 21) & 31 == 8:
                    displacement = (word & 65535)-(65536 if word & 32768 else 0)
                    targets.append(pc+4+displacement*4)
            if any(a < target < b for target in targets for a, b in regions):
                raise ValueError('Event/home name sequence has an interior native reference')
    return {'external_interior_references': [], 'definition_sha256': definitions,
            'scope': 'Aligned literals and direct jumps/relative branches in pinned executable ranges'}


def install(native, replacements, additions, module):
    native = verified_rom(native)
    files = by_vrom(native)
    code = replacements.get(CODE_VROM, files[CODE_VROM].extract(native))
    verify_imports(code, additions.get(MODULE_VROM, b''), additions.get(ITEMS_VROM, b''), module)
    if (code[BRIDGE-CODE_RAM:BRIDGE_END-CODE_RAM] != bridge_body()
            or code[BRIDGE-8-CODE_RAM:BRIDGE-CODE_RAM] != struct.pack('>2I', jump(IMPORTS['af_quest_set_item']), 0)
            or code[0x8009D1F0-CODE_RAM:0x8009D200-CODE_RAM]
            != bytes.fromhex('3c0280142442241003e0000800000000')):
        raise ValueError('Event/home names require the installed zero-safe bridge and main-window singleton')
    pending, actors = {}, {}
    for name, spec in ACTORS.items():
        original, reloc = source(native, name)
        if (replacements.get(spec.vrom, original) != original
                or replacements.get(spec.relocation, reloc) != reloc):
            raise ValueError('Event/home names would replace unapproved actor changes')
        result = bytearray(original)
        for label, call in CALLS.items():
            if call.actor != name: continue
            offset = call.address-spec.ram
            result[offset:offset+call.size] = call_body(label)
        pending[spec.vrom] = bytes(result)
        actors[name] = {'vrom': f'{spec.vrom:08X}', 'source_sha256': spec.file_sha256,
                        'installed_sha256': sha256(result), 'relocation_sha256': spec.relocation_sha256,
                        'file_bytes': len(result), 'bss_bytes': spec.sections[3]}
    evidence = audit_references(native)
    replacements.update(pending)
    return {'actors': actors, 'bridge_ram': f'{BRIDGE:08X}', 'bridge_sha256': sha256(bridge_body()),
            'callers': {name: {'ram': f'{c.address:08X}', 'slot': c.slot, 'bytes': c.size}
                        for name, c in CALLS.items()},
            'complete_name_bytes': 16, 'extra_allocation_bytes': 0, 'saved_layout_changes': False,
            'empty_item_clears_field': True, 'reference_audit': evidence}


def verify_installation(built, native, report):
    module = report.get('runtime_module')
    if not module: raise ValueError('Event/home names lack a resident module')
    verify_test_module(built, module)
    files = by_vrom(built)
    expected = {CODE_VROM: files[CODE_VROM].extract(built)}
    additions = {v: files[v].extract(built) for v in (MODULE_VROM, ITEMS_VROM)}
    evidence = install(native, expected, additions, module)
    for spec in ACTORS.values():
        if (files[spec.vrom].extract(built) != expected[spec.vrom]
                or sha256(files[spec.relocation].extract(built)) != spec.relocation_sha256):
            raise ValueError('Complete event/home name callers or retained relocation are not installed')
    if report.get('event_item_names') != evidence:
        raise ValueError('Missing or changed event/home name application evidence')
    return evidence
