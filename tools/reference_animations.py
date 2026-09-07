"""Individually approved resident NPC0 animation delivery in complete references."""

from dataclasses import dataclass
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from textcodec import encode, tokenize

NPC_VROM, NPC_RAM, NPC_RELOCATION = 0x8681F0, 0x809735B0, 0x878550
NPC_SHA256 = '460777a8c6d6b57e9c83a7c9f3efe02593fd01b75f9a4e108db5b9c2a54a18e3'
RELOCATION_SHA256 = '177536da108299742fb608a2e8d0a26bef9cd2ecf1f4a18e93213f3a01ecee6c'
SECTIONS = (58256, 7808, 336, 69488, 1235)
CONSUMER, CONSUMER_END, ANIMATION_INIT = 0x80976284, 0x809763DC, 0x809749D0
TABLES = (0x80982B14, 0x80982BBC, 0x80982C64, 0x80982D0C, 0x80982DB4, 0x80982E5C)
# Item-table base before adding twice the bounded D01E/D03A/D03B/D03C item ID,
# and the exclusive end of the native two-buffer initialization loop.
RELOCATION_CONSTANTS = (0x80969690, 0x80994880)
# These ordinary standing expressions and TALK reset exist in every native
# held-item variant. Sitting/singing resets and later animation codes are not
# covered by this approval, even where another native caller uses them.
ALLOWED_VALUES = frozenset(range(1, 24)) | {0xFF}


@dataclass(frozen=True)
class ResidentAnimationPermit:
    source_sha256: str
    encoded_sha256: str
    context: str


def is_resident_animation(command):
    return len(command) == 5 and command[:3] == bytes.fromhex('7F0900')


def validate_animation_approval(record):
    if 'resident_animations' not in record:
        return
    rule = record['resident_animations']
    if (not isinstance(rule, dict) or set(rule) != {'context', 'adapted_sha256'}
            or not record['id'].startswith('message:')
            or any(key in record for key in ('controller', 'native_choices', 'native_actor_request',
                                             'available_fields', 'speaker_catchphrase', 'native_equivalent_id'))
            or rule['context'] != 'native_resident_talk'
            or not isinstance(rule['adapted_sha256'], str)
            or not re.fullmatch(r'[0-9a-f]{64}', rule['adapted_sha256'])):
        raise ValueError('Invalid reviewed resident-animation approval')


def verify_animation_reference(reference, source, record, info):
    if not record or 'resident_animations' not in record:
        return
    validate_animation_approval(record)
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    if (sha256(source) != record['source_sha256'] or reference['id'] != record['reference_id']
            or reference['sha256'] != record['reference_sha256']
            or sha256(encode(reference['text'], reference_info)) != record['reference_sha256']):
        raise ValueError('Stale reviewed resident-animation source or reference')


def animation_permit(id, source, candidate, matches):
    record = matches.get(id)
    if not record or 'resident_animations' not in record:
        return None
    validate_animation_approval(record)
    rule = record['resident_animations']
    if sha256(source) != record['source_sha256'] or sha256(candidate) != rule['adapted_sha256']:
        raise ValueError('Reviewed animation candidate differs from its complete approval')
    return ResidentAnimationPermit(record['source_sha256'], rule['adapted_sha256'], rule['context'])


def verify_animation_values(original, replacement, info):
    def expressions(data):
        return [t.data for t in tokenize(data, info) if t.kind == 'cmd' and is_resident_animation(t.data)]
    before, after = expressions(original), expressions(replacement)
    if before == after:
        raise ValueError('Resident-animation approval requires a changed expression sequence')
    if any(int.from_bytes(c[3:], 'big') not in ALLOWED_VALUES for c in before+after):
        raise ValueError('Resident animation is outside the approved standing-expression set')


def verify_native_consumer(rom, replacements=None):
    files = by_vrom(rom)
    data, reloc = files[NPC_VROM].extract(rom), files[NPC_RELOCATION].extract(rom)
    if (sha256(data) != NPC_SHA256 or sha256(reloc) != RELOCATION_SHA256
            or len(data) != sum(SECTIONS[:3]) or len(reloc) != 4976
            or struct.unpack_from('>5I', reloc) != SECTIONS):
        raise ValueError('Native resident-animation overlay or relocations changed')
    replacements = replacements or {}
    if any(replacements.get(vrom, original) != original
           for vrom, original in ((NPC_VROM, data), (NPC_RELOCATION, reloc))):
        raise ValueError('Resident-animation approvals require the unchanged native consumer')
    code = files[CODE_VROM].extract(rom)
    if sha256(code) != '2639d08d6a3de000fa270ebd3837f86d546041cd4a00d40fbf817a63f7b13810':
        raise ValueError('Resident animation original main code changed')
    actual = replacements.get(CODE_VROM, code)
    for start, end in ((0x8007B44C, 0x8007B4EC), (0x8009DF1C, 0x8009DFBC),
                       (0x800A08F8, 0x800A0A04), (0x80107CD8, 0x80107CEC)):
        if actual[start-CODE_RAM:end-CODE_RAM] != code[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Resident animation native order dispatch changed')
    return data, reloc
