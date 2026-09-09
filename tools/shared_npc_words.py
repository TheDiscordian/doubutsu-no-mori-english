"""Complete shared reply words, published only after both consumers are installed."""

from functools import lru_cache
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from code_sections import code_segments
from fortune_strings import STRING_RELOCATION, source_entries
from npc_mail_capture import WORD_HASH, WORD_PROFILES, call_patches
from npc_mail_generation import native_evidence
from npc_mail_words import COUNT, Word, identity, pack_words
from resident_words import (SPEC, IDS as RESIDENT_IDS, caller_evidence as resident_evidence,
                            patch as resident_patch, verify_values as verify_resident_values)
from npc_mail_show import source
from textbanks import Bank
from textcodec import encode, tokenize

IDENTITIES = tuple(identity(i) for i in range(COUNT))
IDS = tuple(f'string:{native:04X}' for native, _, _ in IDENTITIES)
ORDINARY_BASES = (0x1E5, 0x219, 0x2F4, 0x314, 0x334)
# Entire-ROM aligned literal references and direct jumps in pinned text sections.
# These are the original entry references, not a claim about arbitrary computed pointers.
ENTRY_REFERENCES = {
    0x800A8B84: ((CODE_VROM, 0x5748C, 'jump'),),
    0x800A8C48: ((CODE_VROM, 0x573C8, 'jump'), (CODE_VROM, 0x574EC, 'jump')),
    0x800A8DB4: ((CODE_VROM, 0xB9E14, 'literal'),),
    0x800A8F30: ((CODE_VROM, 0xB9E10, 'literal'),),
    0x800A9028: ((CODE_VROM, 0x576DC, 'jump'),),
}


@lru_cache(maxsize=1)
def caller_evidence(rom):
    rom = verified_rom(rom)
    ordinary = resident_evidence(rom)
    files = by_vrom(rom)
    native = native_evidence(files[CODE_VROM].extract(rom))
    segments, definitions = code_segments()
    references = {address: [] for address in ENTRY_REFERENCES}
    jumps = {op | ((target & 0x0FFFFFFF) >> 2): target
             for target in references for op in (0x08000000, 0x0C000000)}
    for vrom, entry in files.items():
        if entry.pstart == 0xFFFFFFFF:
            continue
        data = entry.extract(rom)
        segment = segments.get(vrom)
        for index, (word,) in enumerate(struct.iter_unpack('>I', data[:len(data)//4*4])):
            offset = index*4
            if word in references:
                references[word].append((vrom, offset, 'literal'))
            if word in jumps and segment and segment.is_text(offset):
                references[jumps[word]].append((vrom, offset, 'jump'))
    if any(tuple(sorted(references[target])) != expected
           for target, expected in ENTRY_REFERENCES.items()):
        raise ValueError('Changed shared-word NPC creator entry references')
    from catchphrases import native_table
    from display_names import special_table
    selected = {native for native, _, _ in IDENTITIES}
    if (selected & {row[1] for row in native_table(rom)}
            or selected & {row[2] for row in special_table(rom)}):
        raise ValueError('Shared words overlap a saved catchphrase or special-name destination')
    return {'ordinary': ordinary, 'native_mail': native, 'definition_sha256': definitions,
            'entry_references': {f'{target:08X}': [[f'{vrom:08X}', f'{at:06X}', kind]
                for vrom, at, kind in rows] for target, rows in references.items()},
            'ordinary_word_count': 160, 'mail_word_count': COUNT,
            'saved_catchphrase_and_special_name_ids_disjoint': True}


def verify_values(values):
    if len(values) != COUNT:
        raise ValueError('Shared NPC words require all 352 complete English values')
    rows = [Word(native, reference, slot, value)
            for (native, reference, slot), value in zip(IDENTITIES, values)]
    digest = sha256(pack_words(rows))
    if digest not in WORD_PROFILES:
        raise ValueError('Shared NPC words differ from the complete approved word resource')
    return digest


def candidates(rom, references, inventory, info):
    caller_evidence(rom)
    originals = source_entries(rom)
    result, values = {}, []
    for native, reference, slot in IDENTITIES:
        id, reference_id = f'string:{native:04X}', f'string:{reference:04X}'
        row, donor = inventory.get(id), references.get(reference_id)
        if not row or not donor:
            raise ValueError('Missing complete shared-word source')
        value = encode(donor['text'], info)
        if (row['id'] != id or donor['id'] != reference_id
                or row['source_sha256'] != sha256(originals[native])
                or donor['sha256'] != sha256(value) or encode(row['legacy'], info) != value):
            raise ValueError('Changed complete shared-word native/reference/legacy agreement')
        from native_species import correct_word, SOURCE
        corrected = correct_word(native, originals[native], value)
        is_original = corrected != value
        value = corrected
        values.append(value)
        result[id] = {'id': id, 'source_sha256': sha256(originals[native]),
            'translation': donor['text'], 'control_policy': 'exact',
            'status': 'mechanically_validated_candidate_not_reviewed',
            'provenance': {'source': 'user-supplied GAFE01 revision 0 disc',
                'reference_id': reference_id, 'reference_sha256': donor['sha256'],
                'native_mail_slot': slot, 'word_resource_sha256': WORD_HASH,
                'match_basis': 'verified_native_family_and_complete_legacy_agreement'}}
        if is_original:
            result[id].update(translation=value.decode('ascii'), status='source_reviewed_original_translation')
            result[id]['provenance'].update(source=SOURCE, reference_id='native:'+id,
                reference_sha256=sha256(value), match_basis='reviewed_native_species_correction')
    digest = verify_values(values)
    for row in result.values(): row['provenance']['word_resource_sha256'] = digest
    return result


def validated_values(rom, edits, info):
    """A complete source-bound group, not a generic text-buffer capacity permit."""
    caller_evidence(rom)
    originals = source_entries(rom)
    selected = [edit for edit in edits if edit.get('id') in IDS]
    if len(selected) != COUNT or {edit['id'] for edit in selected} != set(IDS):
        raise ValueError('Shared NPC words require the complete unique 352-record group')
    by_id = {edit['id']: edit for edit in selected}
    values = []
    for id, (native, _, _) in zip(IDS, IDENTITIES):
        edit = by_id[id]
        if (edit.get('source_sha256') != sha256(originals[native])
                or edit.get('control_policy', 'exact') != 'exact'
                or any(t.kind != 'text' for t in tokenize(originals[native], info))):
            raise ValueError('Changed shared-word native source or control policy')
        values.append(encode(edit['translation'], info))
    verify_values(values)
    return dict(zip(IDS, values))


def verify_consumers(rom, replacements, additions, module, *, expected_word_hash=None):
    from mail_catalog import VROM as CATALOG_VROM, verify_registered
    from mail_view_patch import install as install_reader
    from npc_mail_delivery import START, END, patch as gate
    from npc_mail_loader import VROM, CONFIG_OFFSET, CONFIG_BYTES, verify_configuration
    from runtime_layout import MODULE_VROM, RESERVATION
    from runtime_module import runtime_source_hashes
    if (not module or module.get('source_sha256') != sha256(rom)
            or module.get('runtime_sources') != runtime_source_hashes(Path(__file__).resolve().parents[1]/'runtime')
            or MODULE_VROM not in additions or VROM not in additions or CATALOG_VROM not in additions):
        raise ValueError('Shared words require the complete current cartridge NPC creator and catalog')
    binary = additions[MODULE_VROM]
    if len(binary) != RESERVATION:
        raise ValueError('Changed shared-word resident reservation')
    verify_configuration(binary, additions[VROM], module)
    if expected_word_hash is not None and (
            not isinstance(expected_word_hash, str) or expected_word_hash not in WORD_PROFILES
            or module['npc_mail_loader']['overlay'].get('word_sha256') != expected_word_hash):
        raise ValueError('Shared bank words require the matching installed NPC word profile')
    baseline = bytearray(binary)
    baseline[CONFIG_OFFSET:CONFIG_OFFSET+CONFIG_BYTES] = bytes(CONFIG_BYTES)
    for offset, vrom in ((56, 0x02A00000), (60, 0x02C00000), (64, 0x02E00000), (68, CATALOG_VROM)):
        value = struct.unpack_from('>I', baseline, offset)[0]
        if value and (value != vrom or value not in additions):
            raise ValueError('Unverified shared-word resident resource pointer')
        baseline[offset:offset+4] = bytes(4)
    if sha256(baseline) != module['module_sha256'] or struct.unpack_from('>I', binary, 68)[0] != CATALOG_VROM:
        raise ValueError('Changed shared-word resident code or catalog configuration')
    verify_registered(additions[CATALOG_VROM])
    reader = {}
    install_reader(rom, reader, {MODULE_VROM: bytes(baseline)}, module, snapshots=True)
    if any(replacements.get(vrom) != data for vrom, data in reader.items()):
        raise ValueError('Shared words require the complete installed snapshot reader')
    data, reloc = source(rom, 'ordinary')
    current = (replacements.get(SPEC.vrom), replacements.get(SPEC.relocation, reloc))
    if current not in (resident_patch(data, reloc, module=module),
                       resident_patch(data, reloc, module=module, dates=True)):
        raise ValueError('Shared words require the complete sixteen-byte resident caller')
    original = by_vrom(rom)[CODE_VROM].extract(rom)
    code = bytearray(replacements.get(CODE_VROM, original))
    for at, before, after in call_patches(original, module):
        offset = at-CODE_RAM
        if code[offset:offset+4] != after:
            raise ValueError('Shared words require every complete NPC capture hook')
        code[offset:offset+4] = before
    start, end = START-CODE_RAM, END-CODE_RAM
    if code[start:end] != gate(original[start:end], int(module['symbols']['af_npc_mail_load'], 16)):
        raise ValueError('Shared words require the exact NPC creation failure gate')
    code[start:end] = original[start:end]
    native_evidence(bytes(code))
    at = STRING_RELOCATION[1]-CODE_RAM
    if code[at:at+8] != bytes.fromhex(STRING_RELOCATION[3]):
        raise ValueError('Shared words require the relocated general-string loader')


def install(rom, replacements, additions, module, edits, info):
    values = validated_values(rom, edits, info)
    digest = verify_values(list(values.values()))
    verify_consumers(rom, replacements, additions, module, expected_word_hash=digest)
    if 0xD16000 not in replacements or 0xD18000 not in replacements:
        raise ValueError('Shared words require the prepared resident-word string bank')
    bank = Bank('string', 0xD16000, 0xD18000, replacements[0xD16000], replacements[0xD18000])
    entries, originals = bank.entries(), source_entries(rom)
    if len(entries) != len(originals):
        raise ValueError('Shared words cannot change native string identities')
    verify_resident_values([entries[int(id[7:], 16)] for id in RESIDENT_IDS], info)
    for id, (native, _, _) in zip(IDS, IDENTITIES):
        if entries[native] != originals[native]:
            raise ValueError('Shared words must remain native until all consumers are installed')
        entries[native] = values[id]
    data, table = bank.rebuild(entries, allow_expand=True)
    data += bytes(-len(data) % 16)
    # No publication until the entire group, both consumers, and bank rebuild pass.
    replacements[0xD16000], replacements[0xD18000] = data, table
    return {'translation_edits': COUNT, 'word_resource_sha256': digest,
            'ordinary_word_count': 160, 'mail_word_count': COUNT,
            'words_exceeding_ten_bytes': sum(len(value) > 10 for value in values.values()),
            'string_data_bytes': len(data), 'string_data_sha256': sha256(data),
            'string_table_sha256': sha256(table), 'callers': caller_evidence(rom),
            'scope': 'Complete shared bank values; ordinary sixteen-byte fields and full NPC snapshots; normal gameplay and review remain'}
