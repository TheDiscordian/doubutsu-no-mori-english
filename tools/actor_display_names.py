"""Full display-name preparations in three festival actors and the reserve actor."""
from functools import lru_cache
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from code_sections import code_segments
from display_names import VROM as NAMES_VROM
from npc_mail_show import relocate_verified_data
from runtime_module import MODULE_VROM, verify_test_module
from shop_item_names import NameActor, MODULE_SHA, jump
import text_extension as t

IMPORTS = {'af_get_display_name': 0x80195D20, 'af_load_display_name': 0x80196044}
NAMES_SHA = '261078b6c8bec7f974255ddffba8c2a570b4a2a0526ea699a3cc62ffc2b4e974'
ACTORS = {
    'tukimi0': NameActor(0x008C3210, 0x809DFA20, 0x008C3930, 0x809DFEB0, 1824,
        (1632, 192, 0, 0, 43),
        'a180acbd745d5173977c1623f48ac20939f74fd633f5da9509d05f2e57cb425b',
        '0b760be529c7e38d06e5a2eeda86fc694d00941ab3d4a753aed9ec8b3896a7db'),
    'tukimi1': NameActor(0x008C3A00, 0x809E0210, 0x008C4230, 0x809E0704, 2096,
        (1872, 224, 0, 0, 45),
        '8565ff4baccfc3962e413e03fffacb59eea6e7b73280864fe0a5a6b6c180e9d9',
        'e9933f3ba1076a9dd3c1c17663e64b452ba2275e33b38400d8ccb2c0a7b10fd6'),
    'turi0': NameActor(0x008C6390, 0x809E2BA0, 0x008C6C50, 0x809E31C4, 2240,
        (2032, 208, 0, 32, 67),
        '9d2de8ef690d0ffb008312e3a55b2b209636f30af24d29fbdfe17c05046507b9',
        '87edbec9debe0f36a5da66788e79a31fc19c1727531bfd9e86da79819eb21eae'),
    'reserve': t.ACTORS['reserve'],
}
FUNCTIONS = {
    'tukimi0': (0x809DFEB0, 0x809DFFB0, 'f1d435889296320cd20995a0b46cd41b4d57a5d977af7adef791c69ea1b87c4b'),
    'tukimi1': (0x809E0704, 0x809E0820, '592d5ddf124dd4038390d0d2579f2fa977892f734ec334124bba0b70c6614be6'),
    'turi0': (0x809E31C4, 0x809E32C4, 'e743b2700d7c07aaac2011725da1991b54e1b17b5ba07e1b5f2d94c2bba2ff18'),
    'reserve': (0x80A0940C, 0x80A094EC, '6ea9c5b4e33346c1be2387403d5d3766c5fdedc5d4a1897ac1622374fa5e29b5'),
}
CALLS = {'tukimi0': (0x809DFF2C, 0x809DFF44, 0x44, 0x50),
         'tukimi1': (0x809E0788, 0x809E07A0, 0x48, 0x58),
         'turi0': (0x809E3230, 0x809E3248, 0x4C, 0x58)}
RESERVE_START, RESERVE_END = 0x80A09458, 0x80A09484


def reserve_body():
    return struct.pack('>11I', 0x27A40024, 0x3406D008,
        jump(IMPORTS['af_load_display_name'], link=True), 0x24050008,
        0x10400006, 0x3C048014, 0x24842410, 0x24050001, 0x27A60024,
        jump(t.SETTER, link=True), 0x24070008)


def patches(name):
    if name == 'reserve': return {RESERVE_START: reserve_body()}
    call, length, _, _ = CALLS[name]
    return {call: struct.pack('>I', jump(IMPORTS['af_get_display_name'], link=True)),
            length: struct.pack('>I', 0x24070008)}


def source(native, name):
    files, spec = by_vrom(verified_rom(native)), ACTORS[name]
    data, reloc = (files[v].extract(native) for v in (spec.vrom, spec.relocation))
    start, end, digest = FUNCTIONS[name]
    if (len(data) != spec.file_bytes or sha256(data) != spec.file_sha256
            or sha256(reloc) != spec.relocation_sha256
            or struct.unpack_from('>5I', reloc) != spec.sections
            or sha256(data[start-spec.ram:end-spec.ram]) != digest):
        raise ValueError('Changed display-name actor, frame, or relocation')
    for address, body in patches(name).items():
        at = address-spec.ram
        if any(w >> 30 == 1 and at <= (w & 0xFFFFFF) < at+len(body)
               for (w,) in struct.iter_unpack('>I', reloc[20:20+spec.sections[4]*4])):
            raise ValueError('Unexpected relocation in a display-name patch')
    return data, reloc


def preceding(native, name):
    data, reloc = source(native, name)
    if name == 'reserve':
        spec = ACTORS[name]; at = spec.entry-spec.ram
        data = data[:at]+t.call_body('reserve')+data[at+t.CALLS['reserve'][0]:]
    return data, reloc


@lru_cache(maxsize=1)
def audit_references(native):
    verified_rom(native)
    segments, definitions = code_segments()
    if len(segments) < 100 or ACTORS['reserve'].vrom not in segments:
        raise ValueError('Incomplete display-name executable inventory')
    for vrom, file in by_vrom(native).items():
        if file.pstart == 0xFFFFFFFF: continue
        data, segment = file.extract(native), segments.get(vrom)
        for offset in range(0, len(data)-3, 4):
            word = struct.unpack_from('>I', data, offset)[0]
            targets = [word] if RESERVE_START < word < RESERVE_END else []
            if segment and segment.is_text(offset):
                pc, op = segment.ram+offset, word >> 26
                if op in (2, 3): targets.append(((pc+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2))
                if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or op == 17 and (word >> 21) & 31 == 8:
                    displacement = (word & 65535)-(65536 if word & 32768 else 0)
                    targets.append(pc+4+displacement*4)
            if any(RESERVE_START < target < RESERVE_END for target in targets):
                raise ValueError('Native reference into the replaced reserve-name sequence')
    return {'external_interior_references': [], 'definition_sha256': definitions,
            'scope': 'Aligned literals and direct jumps/relative branches in pinned executable ranges'}


def install(native, replacements, additions, module):
    native = verified_rom(native)
    code, binary = replacements.get(CODE_VROM, b''), additions.get(MODULE_VROM, b'')
    normalized = bytearray(binary); normalized[56:0x88] = bytes(0x88-56)
    if (len(binary) != 32768 or sha256(normalized) != MODULE_SHA
            or module.get('module_sha256') != MODULE_SHA
            or any(int(module['symbols'].get(k, '0'), 16) != v for k, v in IMPORTS.items())
            or struct.unpack_from('>I', binary, 60)[0] != NAMES_VROM
            or sha256(additions.get(NAMES_VROM, b'')) != NAMES_SHA
            or code[0x8009D1F0-CODE_RAM:0x8009D200-CODE_RAM]
            != bytes.fromhex('3c0280142442241003e0000800000000')):
        raise ValueError('Actor names require the approved resident names and main-window singleton')
    original_code = by_vrom(native)[CODE_VROM].extract(native)
    if code[0x8010B510-CODE_RAM:0x8010B810-CODE_RAM] != original_code[0x8010B510-CODE_RAM:0x8010B810-CODE_RAM]:
        raise ValueError('Changed special-character identity table')
    pending, actors = {}, {}
    for name, spec in ACTORS.items():
        before, reloc = preceding(native, name)
        # Reserve's existing item adapter is mandatory, not silently invented.
        current = replacements.get(spec.vrom, b'' if name == 'reserve' else before)
        if current != before or replacements.get(spec.relocation, reloc) != reloc:
            raise ValueError('Overlapping actor-name changes or missing preceding reserve adapter')
        result = bytearray(before)
        for address, body in patches(name).items():
            at = address-spec.ram
            result[at:at+len(body)] = body
        for base in (0x801A0010, 0x802F8010):
            moved = relocate_verified_data(spec, result, reloc, base)
            for address, body in patches(name).items():
                at = address-spec.ram
                if moved[at:at+len(body)] != body:
                    raise ValueError('Relocation changed a fixed display-name patch')
        pending[spec.vrom] = bytes(result)
        actors[name] = {'vrom': f'{spec.vrom:08X}', 'installed_sha256': sha256(result),
                        'preceding_sha256': sha256(before), 'relocation_sha256': sha256(reloc),
                        'file_bytes': len(result), 'bss_bytes': spec.sections[3]}
    audit = audit_references(native)
    replacements.update(pending)
    return {'actors': actors, 'imports': IMPORTS, 'name_resource_sha256': NAMES_SHA,
            'complete_name_bytes': 8, 'extra_allocation_bytes': 0, 'saved_layout_changes': False,
            'festival_slots': [1, 2, 3, 4, 5], 'reserve_slot': 1, 'reserve_identity': 'D008',
            'reference_audit': audit}


def verify_installation(built, native, report):
    if not report.get('text_extension'):
        raise ValueError('Actor display names require the preceding persistent text integration')
    module = report['runtime_module']; verify_test_module(built, module)
    files, originals = by_vrom(built), by_vrom(native)
    expected = {CODE_VROM: files[CODE_VROM].extract(built),
                ACTORS['reserve'].vrom: preceding(native, 'reserve')[0]}
    additions = {v: files[v].extract(built) for v in (MODULE_VROM, NAMES_VROM)}
    evidence = install(native, expected, additions, module)
    for spec in ACTORS.values():
        if (files[spec.vrom].extract(built) != expected[spec.vrom]
                or sha256(files[spec.relocation].extract(built)) != spec.relocation_sha256
                or any((files[v].index, files[v].vstart, files[v].vend)
                       != (originals[v].index, originals[v].vstart, originals[v].vend)
                       for v in (spec.vrom, spec.relocation))):
            raise ValueError('Incomplete actor display-name application or changed allocation')
    if report.get('actor_display_names') != evidence:
        raise ValueError('Missing or changed actor display-name application evidence')
    return evidence
