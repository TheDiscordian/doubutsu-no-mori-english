"""Complete source-bound Katrina phrases with one scoped sixteen-byte caller."""

from dataclasses import dataclass
import struct

from aflib import by_vrom, sha256
from textbanks import banks
from textcodec import encode, tokenize

FIRST, END = 0x164, 0x1E4
BASES = (0x1A4, 0x1C4, 0x184, 0x164)
IDS = tuple(f'string:{n:04X}' for n in range(FIRST, END))
VROM, RAM, RELOC_VROM = 0x8BFC40, 0x809DC450, 0x8C0320
SOURCE_SHA256 = 'af30bb28ad7dfe092afd8be6523a8e8ccf810adde08bee8897af7178f51c8717'
RELOC_SHA256 = '0e48922214fbc713ea3d69b0e67a30a8aecc30bfaf49d7b068d18a515c66f1cc'
BANK_HASHES = ('b03ec28615257532d4d989cda116064ab928693c20fada0d071ce84cda91883c',
               '404e038133a7c74622a7cc54c293653c026d090f0f2a74cb9a5b91da5ebcdeed')
VALUES_SHA256 = '482decf774ec977a2b13643c6998411a962a1a64438b11e68b8c54a74ec9de8d'
STRING_RELOCATION = (0x02600000, 0x800C3F1C, '3C1800D127186000', '3C18026027180000')
CHANGES = ((0x809DC590, 0x27BDFFD0, 0x27BDFFC8),
           (0x809DC598, 0xAFA40030, 0xAFA40038),
           (0x809DC5AC, 0x8FB80030, 0x8FB80038),
           (0x809DC5C8, 0x2405000A, 0x24050010),
           (0x809DC5E8, 0x8FA50030, 0x8FA50038),
           (0x809DC5F4, 0x2407000A, 0x24070010),
           (0x809DC5FC, 0x27BD0030, 0x27BD0038))


@dataclass(frozen=True)
class FortunePermit:
    source_sha256: str
    encoded_sha256: str


def source_entries(rom):
    bank = next(b for b in banks(rom) if b.name == 'string')
    if (sha256(bank.data), sha256(bank.table)) != BANK_HASHES:
        raise ValueError('Changed native fortune string bank')
    return bank.entries()


def verify_values(values, info):
    if (len(values) != END-FIRST
            or any(not 1 <= len(value) <= 16
                   or any(t.kind != 'text' for t in tokenize(value, info)) for value in values)
            or sha256(b''.join(struct.pack('>H', len(value))+value for value in values)) != VALUES_SHA256):
        raise ValueError('Fortunes require all 128 complete English phrases in native order')


def candidates(rom, references, inventory, info):
    """Require actual complete donor/legacy agreement, not just matching indices."""
    originals = source_entries(rom)
    result, values = {}, []
    for id in IDS:
        native = originals[int(id[7:], 16)]
        row, reference = inventory.get(id), references.get(id)
        if not row or not reference:
            raise ValueError('Missing fortune inventory or reference')
        value = encode(reference['text'], info)
        if (row['id'] != id or reference['id'] != id
                or row['source_sha256'] != sha256(native)
                or reference['sha256'] != sha256(value)
                or encode(row['legacy'], info) != value):
            raise ValueError('Stale or incomplete fortune source/legacy/reference agreement')
        values.append(value)
        result[id] = {'id': id, 'source_sha256': sha256(native),
                      'translation': reference['text'], 'control_policy': 'exact',
                      'status': 'mechanically_validated_candidate_not_reviewed',
                      'provenance': {'source': 'user-supplied GAFE01 revision 0 disc',
                          'reference_id': id, 'reference_sha256': reference['sha256'],
                          'match_basis': 'native_fortune_family_and_complete_legacy_agreement'}}
    verify_values(values, info)
    return result


def permits(rom, edits, info):
    originals = source_entries(rom)
    selected = [edit for edit in edits if edit.get('id') in IDS]
    if len(selected) != len(IDS) or {e['id'] for e in selected} != set(IDS):
        raise ValueError('English fortunes require the complete unique phrase group')
    by_id = {e['id']: e for e in selected}
    values = [encode(by_id[id]['translation'], info) for id in IDS]
    verify_values(values, info)
    result = {}
    for id, value in zip(IDS, values):
        digest = sha256(originals[int(id[7:], 16)])
        if by_id[id].get('source_sha256') != digest or by_id[id].get('control_policy', 'exact') != 'exact':
            raise ValueError('Changed native fortune source or control policy')
        result[id] = FortunePermit(digest, sha256(value))
    return result


def patch(data, reloc):
    if sha256(data) != SOURCE_SHA256 or sha256(reloc) != RELOC_SHA256:
        raise ValueError('Changed native fortune overlay or relocation')
    if struct.unpack_from('>4I', data, 0x809DCAB0-RAM) != BASES:
        raise ValueError('Native fortune selection families changed')
    count = struct.unpack_from('>I', reloc, 16)[0]
    rows = struct.unpack_from('>'+str(count)+'I', reloc, 20)
    output = bytearray(data)
    for address, before, after in CHANGES:
        at = address-RAM
        if struct.unpack_from('>I', data, at)[0] != before or any(r & 0xFFFFFF == at for r in rows):
            raise ValueError('Unexpected native fortune instruction or relocation overlap')
        struct.pack_into('>I', output, at, after)
    return bytes(output)


def install(rom, replacements):
    files = by_vrom(rom)
    data, reloc = files[VROM].extract(rom), files[RELOC_VROM].extract(rom)
    output = patch(data, reloc)
    if (replacements.get(VROM, data) != data or replacements.get(RELOC_VROM, reloc) != reloc):
        raise ValueError('English fortune preparation overlaps another patch')
    replacements[VROM] = output
