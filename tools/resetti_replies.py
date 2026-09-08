"""Source-bound English reply dictionary and the original substring matcher."""

from dataclasses import dataclass
import struct

from aflib import by_vrom, sha256
from fortune_strings import source_entries, STRING_RELOCATION
from textcodec import encode, tokenize

FIRST, END = 0x4C0, 0x4E0
IDS = tuple(f'string:{n:04X}' for n in range(FIRST, END))
VROM, RAM, RELOC_VROM = 0x898220, 0x809B4A10, 0x899040
SOURCE_SHA256 = '220453f1963d907eaac00119f48360ee029615688ea53ce6829762740956992f'
RELOC_SHA256 = 'ba390ba830cd952b1430879f293a603f9975b7cc2278505a1178e3d84fc5ce06'
VALUES_SHA256 = '219407f63d8f310bc35973b7d075529eb45cf074002cb582293e1a9268a7435b'
TRANSITIONS = (1,2,4,8,10,17,24,28)
TABLE = bytes((*TRANSITIONS,255)).ljust(24,b'\0')
TABLE_RAM = 0x809B572C
CHANGES = ((0x809B4C68,0x8EEF0000,0x92EF0000), (0x809B4C80,0x26F70004,0x26F70001))


@dataclass(frozen=True)
class ResettiReplyPermit:
    source_sha256: str
    encoded_sha256: str


def verify_values(values, info):
    expected_lengths = [2+sum(index >= edge for edge in TRANSITIONS) for index in range(32)]
    if (list(map(len,values)) != expected_lengths
            or any(t.kind != 'text' for value in values for t in tokenize(value,info))
            or sha256(b''.join(struct.pack('>H',len(value))+value for value in values)) != VALUES_SHA256):
        raise ValueError('Resetti requires the complete ordered 32-reply English dictionary')


def candidates(rom, references, inventory, info):
    originals, result, values = source_entries(rom), {}, []
    for id in IDS:
        row, reference = inventory.get(id), references.get(id)
        if not row or not reference: raise ValueError('Missing Resetti reply inventory or reference')
        original = originals[int(id[7:],16)]
        value = encode(reference['text'],info)
        if (row['id'] != id or reference['id'] != id or row['source_sha256'] != sha256(original)
                or reference['sha256'] != sha256(value) or encode(row['legacy'],info) != value):
            raise ValueError('Stale or incomplete Resetti source/legacy/reference agreement')
        values.append(value)
        result[id] = {'id':id,'source_sha256':sha256(original),'translation':reference['text'],
            'control_policy':'exact','status':'mechanically_validated_candidate_not_reviewed',
            'provenance':{'source':'user-supplied GAFE01 revision 0 disc','reference_id':id,
                'reference_sha256':reference['sha256'],
                'match_basis':'native_resetti_dictionary_and_complete_legacy_agreement'}}
    verify_values(values,info)
    return result


def permits(rom, edits, info):
    originals = source_entries(rom)
    selected = [edit for edit in edits if edit.get('id') in IDS]
    if len(selected) != len(IDS) or {e['id'] for e in selected} != set(IDS):
        raise ValueError('English Resetti replies require the complete unique dictionary')
    by_id = {e['id']:e for e in selected}
    values = [encode(by_id[id]['translation'],info) for id in IDS]
    verify_values(values,info)
    result = {}
    for id,value in zip(IDS,values):
        digest = sha256(originals[int(id[7:],16)])
        if by_id[id].get('source_sha256') != digest or by_id[id].get('control_policy','exact') != 'exact':
            raise ValueError('Changed Resetti reply source or control policy')
        result[id] = ResettiReplyPermit(digest,sha256(value))
    return result


def patch(data, reloc):
    if sha256(data) != SOURCE_SHA256 or sha256(reloc) != RELOC_SHA256:
        raise ValueError('Changed native Resetti overlay or relocation')
    at = TABLE_RAM-RAM
    if struct.unpack_from('>6i',data,at) != (6,16,25,30,31,-1):
        raise ValueError('Native reply length transitions changed')
    count = struct.unpack_from('>I',reloc,16)[0]
    rows = struct.unpack_from('>'+str(count)+'I',reloc,20)
    output = bytearray(data)
    for address,before,after in CHANGES:
        offset = address-RAM
        if struct.unpack_from('>I',data,offset)[0] != before or any(r&0xFFFFFF == offset for r in rows):
            raise ValueError('Unexpected Resetti matcher instruction or relocation')
        struct.pack_into('>I',output,offset,after)
    # Writable-section relocations use section-relative offsets.
    text_size = struct.unpack_from('>I',reloc)[0]
    if any(r>>30 == 2 and at <= text_size+(r&0xFFFFFF) < at+len(TABLE) for r in rows):
        raise ValueError('Reply length table unexpectedly contains a relocated value')
    output[at:at+len(TABLE)] = TABLE
    return bytes(output)


def install(rom, replacements):
    files = by_vrom(rom)
    data,reloc = files[VROM].extract(rom),files[RELOC_VROM].extract(rom)
    output = patch(data,reloc)
    if replacements.get(VROM,data) != data or replacements.get(RELOC_VROM,reloc) != reloc:
        raise ValueError('English Resetti replies overlap another actor patch')
    replacements[VROM] = output
