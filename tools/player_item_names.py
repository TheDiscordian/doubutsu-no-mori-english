"""Complete names in player capture/dig messages, with a zero-safe resident bridge."""
from functools import lru_cache
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from code_sections import code_segments
from runtime_module import MODULE_VROM, verify_test_module
from extended_items import VROM as ITEMS_VROM
from shop_item_names import IMPORTS, body as bridge_body, jump, verify_imports, NameActor

BRIDGE, BRIDGE_END = 0x800BB6A8, 0x800BB6F0
BRIDGE_SOURCE_SHA = 'e0dd1b451cc4442b8eea175697464ebca874133f0b96923a3c4be0e4a10e58f6'
SPEC = NameActor(0x007AC420, 0x808B2D50, 0x007D9BA0, 0, 186240,
                 (175872, 9488, 880, 0, 4387),
                 'b204cbd86d1db16317c494c3d59abef721d37ee83331ce22906076295b022e78',
                 'e6b56c2ee8e9df512c619f0e58da7883246039d245238b41e68b845fa06ea4c1')
PATCH_BYTES = 28
# Entry, unchanged source span, original item expression retargeted to a0.
CALLS = {
    'insect': (0x808CD040, '2d5398115c156b3180938597d55ea148232dcf8d5ea85e42fab9a083a0727e3c', 0x94C4021C),
    'fish': (0x808CF9A0, 'add411c9cf9203f13229c731993ffe1803cd28b8fdb919c7f30020d912b8f7fd', 0x3044FFFF),
    'dig': (0x808D309C, 'b5f72e2c6eb05d3f19ce1c7abb86d78bcbb1c0bb104587683503f4a8d18473c9', 0x95C40D1C),
}


def call_body(name):
    return struct.pack('>7I', CALLS[name][2], jump(BRIDGE, link=True), 0x00002825, 0, 0, 0, 0)


def source(native):
    native = verified_rom(native)
    files = by_vrom(native)
    data, reloc = [files[v].extract(native) for v in (SPEC.vrom, SPEC.relocation)]
    code = files[CODE_VROM].extract(native)
    if (sha256(data) != SPEC.file_sha256 or sha256(reloc) != SPEC.relocation_sha256
            or len(data) != SPEC.file_bytes or struct.unpack_from('>5I', reloc) != SPEC.sections
            or sha256(code[BRIDGE-CODE_RAM:BRIDGE_END-CODE_RAM]) != BRIDGE_SOURCE_SHA):
        raise ValueError('Changed native player actor, relocation, or inactive item-wrapper tail')
    for at, digest, _ in CALLS.values():
        if sha256(data[at-SPEC.ram:at-SPEC.ram+PATCH_BYTES]) != digest:
            raise ValueError('Changed player item-name load/set sequence')
    count = SPEC.sections[4]
    if any(word >> 30 == 1 and any(at-SPEC.ram <= (word & 0xFFFFFF) < at-SPEC.ram+PATCH_BYTES
                                  for at, _, _ in CALLS.values())
           for (word,) in struct.iter_unpack('>I', reloc[20:20+count*4])):
        raise ValueError('Player name sequence contains an unexpected relocation')
    return code, data, reloc


@lru_cache(maxsize=1)
def audit_references(native):
    source(native)
    segments, definitions = code_segments()
    if len(segments) < 100 or SPEC.vrom not in segments or CODE_VROM not in segments:
        raise ValueError('Incomplete player-name executable inventory')
    for vrom, file in by_vrom(native).items():
        if file.pstart == 0xFFFFFFFF: continue
        data, segment = file.extract(native), segments.get(vrom)
        for offset in range(0, len(data)-3, 4):
            pc = segment.ram+offset if segment else None
            # Its entry is already a verified unconditional resident jump.
            # The original wrapper's internal branch cannot reach its old tail.
            if vrom == CODE_VROM and BRIDGE-8 <= pc < BRIDGE_END: continue
            word = struct.unpack_from('>I', data, offset)[0]
            targets = [word] if 0x80000000 <= word < 0x81000000 else []
            if segment and segment.is_text(offset):
                op = word >> 26
                if op in (2, 3): targets.append(((pc+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2))
                if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or op == 17 and (word >> 21) & 31 == 8:
                    displacement = (word & 65535)-(65536 if word & 32768 else 0)
                    targets.append(pc+4+displacement*4)
            for target in targets:
                if BRIDGE <= target < BRIDGE_END:
                    raise ValueError('Inactive item-wrapper tail has an external native reference')
                if any(at < target < at+PATCH_BYTES for at, _, _ in CALLS.values()):
                    raise ValueError('Player item-name sequence has an interior native reference')
    return {'external_interior_references': [], 'definition_sha256': definitions,
            'reclaimed_span': [f'{BRIDGE:08X}', f'{BRIDGE_END:08X}'],
            'scope': 'Aligned literals and direct jumps/relative branches in pinned executable ranges'}


def install(native, replacements, additions, module):
    original_code, original, reloc = source(native)
    code = replacements.get(CODE_VROM, original_code)
    data = replacements.get(SPEC.vrom, original)
    verify_imports(code, additions.get(MODULE_VROM, b''), additions.get(ITEMS_VROM, b''), module)
    if code[BRIDGE-8-CODE_RAM:BRIDGE-CODE_RAM] != struct.pack('>2I', jump(IMPORTS['af_quest_set_item']), 0):
        raise ValueError('Original item wrapper does not unconditionally bypass the reclaimed tail')
    if (code[BRIDGE-CODE_RAM:BRIDGE_END-CODE_RAM] != original_code[BRIDGE-CODE_RAM:BRIDGE_END-CODE_RAM]
            or data != original or replacements.get(SPEC.relocation, reloc) != reloc):
        raise ValueError('Player item-name installation would replace unapproved changes')
    evidence = audit_references(native)
    actor = bytearray(data)
    for name, (at, _, _) in CALLS.items():
        actor[at-SPEC.ram:at-SPEC.ram+PATCH_BYTES] = call_body(name)
    if len(bridge_body()) != BRIDGE_END-BRIDGE:
        raise ValueError('Zero-safe item bridge exceeds its inactive code span')
    current = bytearray(code)
    current[BRIDGE-CODE_RAM:BRIDGE_END-CODE_RAM] = bridge_body()
    replacements.update({CODE_VROM: bytes(current), SPEC.vrom: bytes(actor)})
    return {'actor_vrom': f'{SPEC.vrom:08X}', 'actor_source_sha256': SPEC.file_sha256,
            'actor_sha256': sha256(actor), 'relocation_sha256': SPEC.relocation_sha256,
            'bridge_ram': f'{BRIDGE:08X}', 'bridge_sha256': sha256(bridge_body()),
            'callers': {name: f'{at:08X}' for name, (at, _, _) in CALLS.items()},
            'complete_name_bytes': 16, 'extra_allocation_bytes': 0, 'saved_layout_changes': False,
            'empty_item_clears_field': True, 'reference_audit': evidence}


def verify_installation(built, native, report):
    module = report.get('runtime_module')
    if not module: raise ValueError('Player names lack a resident module')
    verify_test_module(built, module)
    files = by_vrom(built)
    current = files[CODE_VROM].extract(built)
    normalised = bytearray(current)
    original = by_vrom(native)[CODE_VROM].extract(native)
    normalised[BRIDGE-CODE_RAM:BRIDGE_END-CODE_RAM] = original[BRIDGE-CODE_RAM:BRIDGE_END-CODE_RAM]
    expected = {CODE_VROM: bytes(normalised)}
    additions = {v: files[v].extract(built) for v in (MODULE_VROM, ITEMS_VROM)}
    evidence = install(native, expected, additions, module)
    if (expected[CODE_VROM] != current or expected[SPEC.vrom] != files[SPEC.vrom].extract(built)
            or sha256(files[SPEC.relocation].extract(built)) != SPEC.relocation_sha256):
        raise ValueError('Complete player name callers and zero-safe bridge are not installed')
    if report.get('player_item_names') != evidence:
        raise ValueError('Missing or changed player-name application evidence')
    return evidence
