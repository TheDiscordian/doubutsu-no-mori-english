"""Complete festival-stall item choices and source-bound English cancellation."""
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from code_sections import code_segments
from english_runtime import GuardedCode, ChoiceLayout, verify_english_runtime, split_address
from extended_items import VROM as ITEMS_VROM
from gc_names import symbol_data
from runtime_module import MODULE_VROM, verify_test_module
from shop_item_names import NameActor, IMPORTS, jump, verify_imports

ROOT = Path(__file__).resolve().parents[1]
SPEC = NameActor(0x00932B60, 0x80A728C0, 0x00933DB0, 0x80A72DB8, 4688,
    (4528, 160, 0, 0, 77),
    'ff22384a08b037e5b5de2ffcf1e0b6c6aa75959df901cb56d47438e9d66c2a90',
    '648b8d6cb310431db58221ce54deceb41b55e7f734c210192b185c6abfad9ecd')
NEW_VROM, NEW_RELOC = 0x03990000, 0x03998000
SIZE, FUNCTION_END = 4720, 0x80A72FA4
METADATA = 0x80101BB0
METADATA_BYTES = bytes.fromhex('00932b6000933db080a728c080a73b100000000080a73a700000000000000000')
LOAD_START, LOAD_END = 0x80A72E5C, 0x80A72E7C
LABELS = (
    ('not_buying', 0x80A73ABC, bytes.fromhex('05c11401'),
     'new_player_str$529', b"I'm not buying! "),
    ('not_wanted', 0x80A73AC0, bytes.fromhex('097e191d0b071401'),
     'new_player_str2$530', b"I don't want it!"),
)
GC_HASHES = {
    'aEYMS_set_choise_data': '36825e121926bd9cd8974fa058b5446c40e65c6b56737414dd75671db2e4b230',
    'new_player_str$529': '46d8bbb57ec61c8953d185775bfb81cb54fd2a039befcf448997318cbb22bb73',
    'new_player_str2$530': '73813ecf78cff3e46f8af2b64cdb4f58b1215efadb181065301b1618d431b432',
}


def references():
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if (sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
            or sha256(symbols.encode()) != 'e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'):
        raise ValueError('Changed supplied English stall reference')
    for name, digest in GC_HASHES.items():
        if sha256(symbol_data(rel, symbols, name)) != digest:
            raise ValueError('Changed complete English stall function or label')
    for _, _, _, symbol, english in LABELS:
        if symbol_data(rel, symbols, symbol) != english or len(english) != 16:
            raise ValueError('Incomplete English stall cancellation label')
    return b''.join(row[4] for row in LABELS)


def source(native):
    files = by_vrom(verified_rom(native))
    data, reloc = [files[v].extract(native) for v in (SPEC.vrom, SPEC.relocation)]
    code = files[CODE_VROM].extract(native)
    if (len(data) != SPEC.file_bytes or sha256(data) != SPEC.file_sha256
            or sha256(reloc) != SPEC.relocation_sha256
            or struct.unpack_from('>5I', reloc) != SPEC.sections
            or files[SPEC.relocation].index != files[SPEC.vrom].index+1
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES):
        raise ValueError('Changed native stall actor, relocation, or allocation metadata')
    for _, at, raw, _, _ in LABELS:
        if data[at-SPEC.ram:at-SPEC.ram+len(raw)] != raw:
            raise ValueError('Changed native stall label')
    return data, reloc


def loader_body():
    # Row address + saved pointer + unsigned original item + bounded full loader.
    return struct.pack('>8I', 0x0011C100, 0x0011C880, 0x02D94021, 0x02B82021,
                       0xAD040000, 0x96460000, jump(IMPORTS['af_load_item_name'], link=True), 0x24050010)


def patch_actor(native):
    original, relocation = source(native)
    code = GuardedCode(original, original, SPEC.ram, SPEC.file_sha256)
    code.grow_stack(SPEC.entry, FUNCTION_END, 168, 160, 24)
    for at, old, new in (
            (0x80A72E08, 40, 64), (0x80A72E4C, 10, 16), (0x80A72EA0, 10, 16),
            (0x80A72EE0, 4, 16), (0x80A72F08, 8, 16),
            (0x80A72F3C, 10, 16), (0x80A72F40, 10, 16),
            (0x80A72F44, 10, 16), (0x80A72F5C, 10, 16)):
        code.immediate(at, old, new)
    code.write(LOAD_START, loader_body())
    for high_at, low_at, old, new in (
            (0x80A72EAC, 0x80A72EB0, 0x80A73ABC, SPEC.ram+SPEC.file_bytes),
            (0x80A72F00, 0x80A72F04, 0x80A73AC0, SPEC.ram+SPEC.file_bytes+16)):
        high, low = split_address(new)
        code.immediate(high_at, split_address(old)[0], high)
        code.immediate(low_at, split_address(old)[1], low)
    slots = [(w >> 30, (w >> 24) & 63, w & 0xFFFFFF)
             for (w,) in struct.iter_unpack('>I', relocation[20:20+SPEC.sections[4]*4])]
    if any(section == 1 and LOAD_START-SPEC.ram <= at < LOAD_END-SPEC.ram for section, _, at in slots):
        raise ValueError('Stall name sequence contains an unexpected relocation')
    for at, kind in ((0x80A72EAC, 5), (0x80A72EB0, 6), (0x80A72F00, 5), (0x80A72F04, 6)):
        if slots.count((1, kind, at-SPEC.ram)) != 1:
            raise ValueError('Stall English label lacks its original relocation')
    reloc = bytearray(relocation)
    struct.pack_into('>I', reloc, 4, SPEC.sections[1]+32)
    return bytes(code.data)+references(), bytes(reloc), code.changes


@lru_cache(maxsize=1)
def audit_references(native):
    source(native)
    segments, definitions = code_segments()
    if SPEC.vrom not in segments or len(segments) < 100:
        raise ValueError('Incomplete stall executable inventory')
    for vrom, file in by_vrom(native).items():
        if file.pstart == 0xFFFFFFFF: continue
        data, segment = file.extract(native), segments.get(vrom)
        for offset in range(0, len(data)-3, 4):
            word = struct.unpack_from('>I', data, offset)[0]
            targets = [word] if LOAD_START < word < LOAD_END else []
            if segment and segment.is_text(offset):
                pc, op = segment.ram+offset, word >> 26
                if op in (2, 3): targets.append(((pc+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2))
                if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or op == 17 and (word >> 21) & 31 == 8:
                    displacement = (word & 65535)-(65536 if word & 32768 else 0)
                    targets.append(pc+4+displacement*4)
            if any(LOAD_START < target < LOAD_END for target in targets):
                raise ValueError('Stall item sequence has an interior native reference')
    return {'external_interior_references': [], 'definition_sha256': definitions,
            'scope': 'Aligned literals and direct jumps/relative branches in pinned executable ranges'}


def metadata():
    row = bytearray(METADATA_BYTES)
    struct.pack_into('>4I', row, 0, NEW_VROM, NEW_VROM+SIZE, SPEC.ram, SPEC.ram+SIZE)
    return bytes(row)


def verify_dependencies(native, code, additions, module, replacements):
    verify_imports(code, additions.get(MODULE_VROM, b''), additions.get(ITEMS_VROM, b''), module)
    layout = ChoiceLayout(*struct.unpack_from('>4I', additions[MODULE_VROM], 40))
    if layout.capacity != 20: raise ValueError('Stall choices require the complete resident choice runtime')
    verify_english_runtime(native, {**replacements, CODE_VROM: code}, layout)


def install(native, replacements, additions, relocations, module):
    original, original_reloc = source(native)
    files = by_vrom(native)
    code = bytearray(replacements.get(CODE_VROM, files[CODE_VROM].extract(native)))
    verify_dependencies(native, bytes(code), additions, module, replacements)
    if ((replacements.get(SPEC.vrom, original), replacements.get(SPEC.relocation, original_reloc))
            != (original, original_reloc) or any(v in relocations for v in (SPEC.vrom, SPEC.relocation))
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES):
        raise ValueError('Overlapping stall actor or allocation changes')
    if any(v in files or v in replacements or v in additions or v in relocations or v in relocations.values()
           for v in (NEW_VROM, NEW_RELOC)):
        raise ValueError('Overlapping stall DMA ranges')
    data, reloc, changes = patch_actor(native)
    audit = audit_references(native)
    if len(data) != SIZE: raise ValueError('Incomplete stall allocation extent')
    code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] = metadata()
    replacements.update({SPEC.vrom: data, SPEC.relocation: reloc, CODE_VROM: bytes(code)})
    relocations.update({SPEC.vrom: NEW_VROM, SPEC.relocation: NEW_RELOC})
    return {'vrom': f'{NEW_VROM:08X}', 'relocation_vrom': f'{NEW_RELOC:08X}',
            'actor_sha256': sha256(data), 'relocation_sha256': sha256(reloc),
            'source_sha256': SPEC.file_sha256, 'reference_hashes': GC_HASHES,
            'actor_bytes': SIZE, 'additional_actor_bytes': 32, 'additional_stack_bytes': 24,
            'name_bytes': 16, 'saved_layout_changes': False, 'instructions': changes,
            'labels': {name: {'offset': SPEC.file_bytes+i*16, 'sha256': sha256(english)}
                       for i, (name, _, _, _, english) in enumerate(LABELS)}, 'reference_audit': audit}


def verify_installation(built, native, report):
    module = report.get('runtime_module')
    if not module: raise ValueError('Stall choices lack the resident module')
    verify_test_module(built, module)
    files, originals = by_vrom(built), by_vrom(native)
    if (SPEC.vrom in files or SPEC.relocation in files or NEW_VROM not in files or NEW_RELOC not in files
            or files[NEW_VROM].index != originals[SPEC.vrom].index
            or files[NEW_RELOC].index != originals[SPEC.relocation].index):
        raise ValueError('Missing stall actor and adjacent relocation')
    code = files[CODE_VROM].extract(built)
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != metadata():
        raise ValueError('Incomplete stall allocation metadata')
    normalised = bytearray(code)
    normalised[METADATA-CODE_RAM:METADATA-CODE_RAM+32] = METADATA_BYTES
    from english_runtime import QUEST_VROM, PLAYER_SELECT_VROM
    expected = {CODE_VROM: bytes(normalised),
                **{v: files[v].extract(built) for v in (QUEST_VROM, PLAYER_SELECT_VROM)}}
    additions = {v: files[v].extract(built) for v in (MODULE_VROM, ITEMS_VROM)}
    evidence = install(native, expected, additions, {}, module)
    if (expected[CODE_VROM] != code or expected[SPEC.vrom] != files[NEW_VROM].extract(built)
            or expected[SPEC.relocation] != files[NEW_RELOC].extract(built)):
        raise ValueError('Complete stall choices and English labels are not installed')
    if report.get('stall_choices') != evidence:
        raise ValueError('Missing or changed stall choice application evidence')
    for old, new in ((SPEC.vrom, NEW_VROM), (SPEC.relocation, NEW_RELOC)):
        if report.get('vrom_relocations', {}).get(f'{old:08X}') != f'{new:08X}':
            raise ValueError('Missing stall DMA movement evidence')
    return evidence


def relocated_spec():
    return replace(SPEC, file_bytes=SIZE, sections=(4528, 192, 0, 0, 77))


def measure_labels(ledger, native, built, report):
    source(native)
    applied = bool(report.get('stall_choices'))
    if applied:
        verify_installation(built, native, report)
    for name, _, raw, _, english in LABELS:
        identity = 'ui_stall_choice:'+name
        ledger.add(identity, raw)
        if applied:
            ledger.credit(identity, english, 'stall_choices')
