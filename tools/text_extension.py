"""Install complete general message fields and their persistent startup owner."""
from functools import lru_cache
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256, verified_rom
from build_text_extension import IMPORTS, RAM
from check_keyboard_assembly import IMAGE
from code_sections import code_segments
from extended_items import VROM as ITEMS_VROM
from npc_mail_show import relocate_verified_data
from runtime_module import MODULE_VROM, verify_test_module
from shop_item_names import NameActor, jump, verify_imports

ROOT = Path(__file__).resolve().parents[1]
VROM = 0x03A00000
SETTER, SETTER_END = 0x8009D6D0, 0x8009D820
BOOT, BOOT_END, EPILOGUE, TAIL = 0x800D64F0, 0x800D66D0, 0x800D65A8, 0x800D65D0
BOOT_SHA = '9c20b82708856897c19301bb23e35b84335482f9c10d4dd5ba5c3a3f7fb1d10f'
FONT_SHA = '023fc94f20aec96fc90c633816e6bb35543d30aad8d65e95915f99a5817f3fac'
PROFILE = {
    'image_bytes': 1952, 'relocation_bytes': 192, 'blob_bytes': 2144, 'loader_bytes': 216,
    'image_sha256': '4c2fd94b509b1ab364c5e4138b36b147c33be7e8673af934a6aeb6ad7e957ec7',
    'relocation_sha256': 'd453518ea7cd5010537750b9c03f3776b43b1ab39a7ecd937648879f272cb95b',
    'blob_sha256': '3e820846b242ef3f4bd2e74a3253173c45e6dc15ebc1943e810cc901b37ea95a',
    'blob_crc32': 'E1183C55',
    'loader_sha256': 'aa2599aa864047615d83f06da6799645e40d9b82262df14e0a2fb1835d9d74ae',
}
SYMBOLS = {'af_text_extension_init': 0, 'af_free_set': 272, 'insert': 596,
    'af_free_copy': 1116, 'af_free_colour': 1160, 'hook': 1260, 'af_free_item': 1348,
    'af_free_item_nonzero': 1444, 'af_free_item_colour': 1472,
    'CSWTCH.36': 1576, 'colours.0': 1588, 'valid': 1616, 'rows': 1620}
ACTORS = {
    'letter': NameActor(0x008108C0, 0x80918450, 0x00814C50, 0x80919C68, 17296,
        (16512, 704, 80, 0, 203),
        'a4c2c68aa4817360661d6bfd4323530914b5128f826a88cfa47ea4aedaf4a7f5',
        '3d44462fcc32377120cd9e7aa3b2695fea32f536cf6576d8c4ae625abc902f1d'),
    'reserve': NameActor(0x008D8000, 0x80A09330, 0x008D84A0, 0x80A09438, 1184,
        (1104, 80, 0, 0, 19),
        'bf4b372e168c755c62f115cb10130c3d8dd95cdfd45fbcf24cae554312c14fd2',
        'c5c40a3b3d410fc73eb4e5b0cb988a9172c823a80d7a95728efc051916951ceb'),
    'shrine': NameActor(0x008D8EC0, 0x80A0A1F0, 0x008D9FA0, 0x80A0AA6C, 4320,
        (4032, 240, 48, 16, 66),
        'cfa586ecc7a8a140d510ddbf8bfd9b3fed18e987ea2a4438a3cf2f17964e1dfb',
        'f61e4d6369e07443c8df9718ec0c1b892ef4164bfe04c1d6ddb905d5b7887f8b'),
}
CALLS = {
    'letter': (44, '18acbb11ed207bde412fe742e101a86c5682b45087583fac349f4e3ef768a7d4'),
    'reserve': (36, '6f85d662d8948f1d52e968cdcab01a3352a1b21a31527fa64d6ded8ab2394b85'),
    'shrine': (28, 'eb40a926bd45c10f4dbd75950a45580b7734dc8f88915eed0d0f00122c501fbb'),
}
NATIVE_SPANS = ((SETTER, SETTER_END), (0x8009D820, 0x8009D88C),
                (0x800A134C, 0x800A141C), (0x800BB6F0, 0x800BB740),
                (0x8009EA2C, 0x8009EBAC), (0x80107B78, 0x80107B90),
                (0x800903A8, 0x800903CC), (0x8009D1F0, 0x8009D200))


def tail_body():
    # The original success epilogue follows the new initializer/failure check.
    return struct.pack('>9I', jump(SETTER, link=True), 0, 0x1040FFF8, 0,
                       0x8FBF0024, 0x8FB00020, 0x8FB1001C, 0x03E00008, 0x27BD0028)


def call_body(name):
    words = {
        'letter': (0x00A02025, 0x24060002, jump(0x800BB700, link=True), 0x24050002),
        'reserve': (0x94A45DF8, jump(0x800BB6F8, link=True), 0x24050000),
        'shrine': (0x972400E0, jump(0x800BB6F8, link=True), 0x24050000),
    }[name]
    return struct.pack('>'+str(len(words))+'I', *words).ljust(CALLS[name][0], b'\0')


def source(native, name):
    files, spec = by_vrom(verified_rom(native)), ACTORS[name]
    data, reloc = [files[v].extract(native) for v in (spec.vrom, spec.relocation)]
    length, digest = CALLS[name]
    at = spec.entry-spec.ram
    if (len(data) != spec.file_bytes or sha256(data) != spec.file_sha256
            or sha256(reloc) != spec.relocation_sha256
            or struct.unpack_from('>5I', reloc) != spec.sections
            or sha256(data[at:at+length]) != digest):
        raise ValueError('Changed free-item actor, sequence, or relocation')
    if any(word >> 30 == 1 and at <= (word & 0xFFFFFF) < at+length
           for (word,) in struct.iter_unpack('>I', reloc[20:20+spec.sections[4]*4])):
        raise ValueError('Unexpected relocation in a free-item adapter')
    return data, reloc


def image_spec(image, reloc):
    return NameActor(VROM, RAM, 0, RAM, len(image), struct.unpack_from('>5I', reloc),
                     sha256(image), sha256(reloc))


def artifact_profile(artifact):
    if 'choices' in artifact:
        if artifact['choices'] is not True:
            raise ValueError('Invalid text-extension choice capability')
        from text_choices import PROFILE as profile, SYMBOLS as symbols, ELF_SHA
        from build_text_extension import CHOICE_IMPORTS
        return profile, symbols, {**IMPORTS, **CHOICE_IMPORTS}, ELF_SHA
    return PROFILE, SYMBOLS, IMPORTS, 'ee4d355d470cee436e3fcd4fb5c3b06e766761a49f415473205fff90ed9b83a3'


def validate(blob, loader, artifact):
    profile, symbols, imports, elf_sha = artifact_profile(artifact)
    image, reloc = blob[:profile['image_bytes']], blob[profile['image_bytes']:]
    for key, value in profile.items():
        if artifact.get(key) != value: raise ValueError('Unapproved text-extension profile: '+key)
    for name, value in (('image', image), ('relocation', reloc), ('blob', blob), ('loader', loader)):
        if len(value) != profile[name+'_bytes'] or sha256(value) != profile[name+'_sha256']:
            raise ValueError('Changed text-extension artifact: '+name)
    sources = {p.name: sha256(p.read_bytes()) for p in sorted((ROOT/'overlays/text_extension').iterdir()) if p.is_file()}
    if artifact.get('choices'):
        sources.update({'choices/'+p.name: sha256(p.read_bytes())
                        for p in sorted((ROOT/'overlays/text_choices').iterdir()) if p.is_file()})
    if (artifact.get('sources') != sources or artifact.get('imports') != imports
            or artifact.get('symbols') != symbols or artifact.get('compiler_image') != IMAGE
            or artifact.get('blob_crc32') != f'{zlib.crc32(blob):08X}'
            or sha256(json.dumps(artifact.get('elf_relocations'), sort_keys=True).encode())
            != elf_sha):
        raise ValueError('Unbound text-extension source, imports, symbols, or relocations')
    if (any(image[symbols['valid']:]) or struct.unpack_from('>4I', reloc) != (len(image), 0, 0, 0)
            or struct.unpack_from('>I', reloc, len(reloc)-4)[0] != len(reloc)):
        raise ValueError('Text-extension state or allocation is not initialized')
    for base in (0x801A0010, 0x803F0010):
        relocate_verified_data(image_spec(image, reloc), image, reloc, base)
    return image, reloc


@lru_cache(maxsize=2)
def audit_references(native, choices=False):
    verified_rom(native)
    segments, definitions = code_segments()
    regions = [(CODE_VROM, SETTER, SETTER_END), (CODE_VROM, 0x800BB6F0, 0x800BB740),
               (CODE_VROM, 0x800A1394, 0x800A141C), (CODE_VROM, BOOT-16, BOOT_END)]
    regions += [(s.vrom, s.entry, s.entry+CALLS[name][0]) for name, s in ACTORS.items()]
    if choices:
        from text_choices import ENTRY, END
        regions.append((CODE_VROM, ENTRY, END))
    if len(segments) < 100 or any(v not in segments for v, _, _ in regions):
        raise ValueError('Incomplete text-extension executable inventory')
    for vrom, file in by_vrom(native).items():
        if file.pstart == 0xFFFFFFFF: continue
        data, segment = file.extract(native), segments.get(vrom)
        for offset in range(0, len(data)-3, 4):
            pc = segment.ram+offset if segment else None
            word = struct.unpack_from('>I', data, offset)[0]
            targets = [word] if word & 0x80000000 else []
            if segment and segment.is_text(offset):
                op = word >> 26
                if op in (2, 3): targets.append(((pc+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2))
                if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or op == 17 and (word >> 21) & 31 == 8:
                    displacement = (word & 65535)-(65536 if word & 32768 else 0)
                    targets.append(pc+4+displacement*4)
            for owner, start, end in regions:
                if vrom == owner and pc is not None and start <= pc < end: continue
                if any(start < target < end for target in targets):
                    raise ValueError(f'External reference into reclaimed text at {vrom:08X}+{offset:X}')
    return {'external_interior_references': [], 'definition_sha256': definitions,
            'scope': 'Aligned literals and direct jumps/relative branches in pinned executable ranges'}


def install(native, replacements, additions, relocations, module, directory=None, *, artifact_data=None):
    native = verified_rom(native)
    files = by_vrom(native)
    original = files[CODE_VROM].extract(native)
    current = replacements.get(CODE_VROM, original)
    verify_imports(current, additions.get(MODULE_VROM, b''), additions.get(ITEMS_VROM, b''), module)
    font = module.get('extended_font', {})
    if (font.get('blob_sha256') != FONT_SHA or sha256(additions.get(0x03400000, b'')) != FONT_SHA
            or module.get('bootstrap_sha256') != BOOT_SHA):
        raise ValueError('Text extension requires the approved startup and font owner')
    for start, end in NATIVE_SPANS:
        if current[start-CODE_RAM:end-CODE_RAM] != original[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError(f'Overlapping text-extension native dependency at {start:08X}')
    attribute = int(module['symbols']['af_code_attribute'], 16)
    if current[0x800903CC-CODE_RAM:0x800903D4-CODE_RAM] != struct.pack('>2I', jump(attribute), 0):
        raise ValueError('Text extension requires the installed command attributes')
    bootstrap = current[BOOT-CODE_RAM:BOOT_END-CODE_RAM]
    if (sha256(bootstrap[:212]) != BOOT_SHA or any(bootstrap[212:])
            or current[0x800D6720-CODE_RAM:0x800D6724-CODE_RAM] != struct.pack('>I', jump(BOOT, link=True))):
        raise ValueError('Changed text-extension startup or unused bootstrap tail')
    if artifact_data is None:
        artifact_data = ((directory/'blob.bin').read_bytes(), (directory/'loader.bin').read_bytes(),
                         json.loads((directory/'extension.json').read_text()))
    blob, loader, artifact = artifact_data
    validate(blob, loader, artifact)
    choice_evidence = None
    if artifact.get('choices'):
        from text_choices import verify_dependencies
        choice_evidence = verify_dependencies(native, replacements, additions, module)
    intervals = [(relocations.get(v, v), relocations.get(v, v)+len(replacements.get(v, b'')))
                 if v in replacements else (f.vstart, f.vend) for v, f in files.items()]
    intervals += [(v, v+len(data)) for v, data in additions.items()]
    if (VROM in relocations or VROM in relocations.values()
            or any(a < VROM+len(blob) and VROM < b for a, b in intervals)):
        raise ValueError('Text extension overlaps an existing cartridge allocation')
    first = DMA_START+len(files)*16
    end = first+(len(additions)+2)*16
    if end > DMA_END or native[first:end] != bytes(end-first):
        raise ValueError('Text extension lacks unused DMA capacity')
    pending, actors = {}, {}
    for name, spec in ACTORS.items():
        data, reloc = source(native, name)
        if (replacements.get(spec.vrom, data) != data or replacements.get(spec.relocation, reloc) != reloc
                or any(v in relocations for v in (spec.vrom, spec.relocation))):
            raise ValueError('Overlapping free-item actor or relocation changes')
        result = bytearray(data); at = spec.entry-spec.ram
        result[at:at+CALLS[name][0]] = call_body(name)
        for base in (0x801A0010, 0x802F8010):
            moved = relocate_verified_data(spec, result, reloc, base)
            if moved[at:at+CALLS[name][0]] != call_body(name):
                raise ValueError('Relocation changed a fixed free-item bridge')
        pending[spec.vrom] = bytes(result)
        actors[name] = {'vrom': f'{spec.vrom:08X}', 'installed_sha256': sha256(result),
                        'relocation_sha256': sha256(reloc), 'file_bytes': len(data), 'bss_bytes': spec.sections[3]}
    audit = audit_references(native, bool(choice_evidence))
    code = bytearray(current)
    code[SETTER-CODE_RAM:SETTER_END-CODE_RAM] = loader.ljust(SETTER_END-SETTER, b'\0')
    code[EPILOGUE-CODE_RAM:EPILOGUE-CODE_RAM+8] = struct.pack('>2I', jump(TAIL), 0)
    code[TAIL-CODE_RAM:TAIL-CODE_RAM+36] = tail_body()
    pending[CODE_VROM] = bytes(code)
    replacements.update(pending)
    additions[VROM] = blob
    evidence = {'vrom': f'{VROM:08X}', 'artifact': artifact, 'actors': actors,
            'additional_system_allocation_bytes': len(blob)+15, 'main_window': '80142410',
            'field_count': 20, 'field_bytes': 16, 'saved_layout_changes': False,
            'bootstrap_tail': f'{TAIL:08X}', 'reference_audit': audit,
            'scope': 'Complete main-message general fields and item adapters; shared choices remain pending'}
    if choice_evidence:
        evidence['choices'] = choice_evidence
        evidence['scope'] = 'Complete general fields, item adapters, and bounded full-English choice substitutions'
    return evidence


def verify_installation(built, native, report):
    entry, module = report.get('text_extension'), report.get('runtime_module')
    if not entry or not module: raise ValueError('Missing text-extension application evidence')
    verify_test_module(built, module)
    files, originals = by_vrom(built), by_vrom(native)
    if VROM not in files: raise ValueError('Missing persistent text extension')
    code = files[CODE_VROM].extract(built)
    profile, _, _, _ = artifact_profile(entry['artifact'])
    loader = code[SETTER-CODE_RAM:SETTER-CODE_RAM+profile['loader_bytes']]
    normalized = bytearray(code)
    original = originals[CODE_VROM].extract(native)
    normalized[SETTER-CODE_RAM:SETTER_END-CODE_RAM] = original[SETTER-CODE_RAM:SETTER_END-CODE_RAM]
    normalized[EPILOGUE-CODE_RAM:EPILOGUE-CODE_RAM+8] = bytes.fromhex('8fbf00248fb00020')
    normalized[TAIL-CODE_RAM:TAIL-CODE_RAM+36] = bytes(36)
    replacements = {CODE_VROM: bytes(normalized)}
    additions = {v: files[v].extract(built) for v in (MODULE_VROM, ITEMS_VROM, 0x03400000)}
    if entry['artifact'].get('choices'):
        from text_choices import ACTOR_VROMS, RESOURCE_HASHES
        replacements.update({v: files[v].extract(built) for v in ACTOR_VROMS})
        additions.update({v: files[v].extract(built) for v in RESOURCE_HASHES})
    evidence = install(native, replacements, additions, {}, module,
        artifact_data=(files[VROM].extract(built), loader, entry['artifact']))
    if report.get('actor_display_names'):
        # The complete later integration may consume only its explicitly
        # approved reserve-name sequence, including the adapter's final NOP.
        from actor_display_names import verify_installation as verify_actor_names, patches
        verify_actor_names(built, native, report)
        spec = ACTORS['reserve']
        result = bytearray(replacements[spec.vrom])
        for address, body in patches('reserve').items():
            at = address-spec.ram
            result[at:at+len(body)] = body
        replacements[spec.vrom] = bytes(result)
    for vrom, expected in replacements.items():
        if files[vrom].extract(built) != expected:
            raise ValueError('Incomplete installed text-extension code or actor')
    for spec in ACTORS.values():
        if (sha256(files[spec.relocation].extract(built)) != spec.relocation_sha256
                or files[spec.vrom].index != originals[spec.vrom].index
                or files[spec.relocation].index != originals[spec.relocation].index):
            raise ValueError('Changed text-extension actor relocation or allocation')
    if entry != evidence: raise ValueError('Changed text-extension application evidence')
    return evidence
