"""Native contributor identities and owned twenty-five-byte credit rows."""

from dataclasses import dataclass, replace
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from fortune_strings import source_entries
from gc_names import symbol_data
from npc_mail_show import relocate_verified_data
from textcodec import encode, tokenize

FIRST, END = 0x4EA, 0x558
IDS = tuple(f'string:{i:04X}' for i in range(FIRST, END))
VROM, RAM, RELOCATION = 0x963DF0, 0x80AA3BA0, 0x965040
FILE_BYTES, OLD_BSS, EXTRA_BSS = 4688, 224, 256
BUFFER = RAM + FILE_BYTES + OLD_BSS
RESIDENT_BYTES = FILE_BYTES + OLD_BSS + EXTRA_BSS
METADATA = 0x80102210
METADATA_BYTES = bytes.fromhex('00963DF00096504080AA3BA080AA4ED00000000080AA4D300000000000000000')
SECTIONS = (4496, 176, 16, OLD_BSS, 98)
ACTOR_HASH = 'e34789965dda5548c380a87e7384b635931fe6d6826356332f3ba6aa8878757c'
RELOCATION_HASH = '4eed1aaf28aacc093e4b6bf8c6d1fb773bdaeaba8b0228a05624b758ef6f8e31'
PAGES = (0,3,9,18,27,36,44,52,56,64,69,77,85,91,98,105,107)
ROLE_LINES = (6,12,16,21,25,34,39,42,47,50,59,62,67,88,89,95,102)
VALUES_HASH = '1ab4a9d3d2d0c854cd2ae3d48fc3c40e6114e8867cd50446ee85710203ed5020'
REFERENCE_HASH = 'a1e5e6183398737fa0fdd62854f845a6de1da63bea8c52589142c233c4aa7f09'

# Explicit identity mapping, not matching numeric IDs or the legacy order.
# These are the active English credits at 077B..07FE, not the older unused
# credit strings also present in the supplied disc.
REFERENCES = {
    0x4ED:0x77E, 0x4EE:0x77F, 0x4F0:0x781, 0x4F1:0x782, 0x4F2:0x783,
    0x4F3:0x784, 0x4F4:0x785, 0x4F6:0x787, 0x4F7:0x788, 0x4F8:0x789,
    0x4FA:0x78B, 0x4FB:0x78C, 0x4FC:0x78D, 0x4FD:0x78E,
    0x4FF:0x790, 0x500:0x791, 0x501:0x792, 0x503:0x794, 0x504:0x795,
    0x505:0x799, 0x506:0x79A, 0x507:0x79B, 0x508:0x79C, 0x509:0x79D,
    0x50A:0x79E, 0x50C:0x796, 0x50D:0x797, 0x50E:0x7A0, 0x50F:0x7A1,
    0x511:0x7A3, 0x512:0x7A4, 0x514:0x7A6, 0x515:0x7A7,
    0x516:0x7A8, 0x517:0x7A9, 0x519:0x7AB, 0x51A:0x7AC,
    0x51C:0x7AE, 0x51D:0x7AF, 0x51E:0x7B0, 0x51F:0x7B1,
    0x520:0x7B3, 0x521:0x7B2, 0x522:0x7B4, 0x523:0x7B5,
    0x526:0x7B8, 0x529:0x7B9, 0x52B:0x7BA, 0x52E:0x7BB,
    0x52F:0x7B7, 0x530:0x7CA, 0x531:0x7C3, 0x532:0x7BF,
    0x533:0x7C6, 0x534:0x7C4, 0x535:0x7C7, 0x536:0x7C8,
    0x537:0x7C5, 0x538:0x7C9, 0x539:0x7C1, 0x53A:0x7C2,
    0x53B:0x7BC, 0x53C:0x7C0, 0x53D:0x7CC, 0x53E:0x7CB,
    0x540:0x7CE, 0x544:0x7CF, 0x547:0x7F3,
    0x54C:0x7EB, 0x54D:0x7EC, 0x54E:0x7ED,
    0x550:0x7EF, 0x551:0x7F0, 0x553:0x7F5,
}
# Original translations/transliterations for native-only rows. Keep native
# responsibilities instead of replacing them with the English release's roles.
DRAFTS = {
    0x4EA:'Animal Forest', 0x4EC:'Staff Credits',
    0x525:'Character Programming', 0x528:'Player Programming',
    0x52A:'Data Processing Program', 0x52D:'Field Programming',
    0x53F:'Famicom Emulator Program', 0x542:'Famicom Emulator',
    0x543:'   Sound Programming', 0x545:'Supervisor',
    0x546:'   Shigeru Miyamoto', 0x549:'Project Management',
    0x54A:'   Keizo Kato', 0x54B:'   Minoru Narita',
    0x552:'   Sarugakucho', 0x554:'   Hiroshi Yamauchi',
    0x555:'Reserved', 0x556:'Reserved', 0x557:'Reserved',
}

CHANGES = (
    (0x80AA3D2C,0x26314E20,0x26314ED0),
    (0x80AA3D50,0x2405000F,0x24050019),
    (0x80AA3D74,0x2631000F,0x26310019),
    (0x80AA3DE8,0x26314E20,0x26314ED0),
    (0x80AA3FD4,0x2406000F,0x24060019),
    # The English direct-font caller requests variable-width glyph drawing.
    # t6 is already one here; no new instruction or relocation is needed.
    (0x80AA3FE8,0xAFA00028,0xAFAE0028),
    (0x80AA4030,0x2631000F,0x26310019),
)
DEPENDENCIES = (
    (0x8CB690,'47d03c6fd4526d45a8685747a90253fb0daa102f0a4831a59a9fe472fab62987'),
    (0x949BE0,'d99c2106beef460f2174528941d889edb19be315e6fd1bd5b1f59f5d533dc5ca'),
)
GC_SYMBOLS = {
    'aMKBC_clip_set_string':(148,'c0377b8197cb1b6fb67b34073c3983ef89bea82d8ba44e7747fa3c2e7eb5b841'),
    'aMKBC_clip_roll_draw':(724,'bfb3f65b7ad6307b120cecc5b7daa1500a60df0edbe2e9659e0fa5e421550db9'),
    'page_table':(17,'46b6d9ab337cae3a002e2105b57d61f6f1f564958ef8897e6c38a1be0fc7f587'),
    'index_line_table':(32,'7b946f55f42d2a6a5c4faef178287bc66b0588abc570135f9f9a10835a0377aa'),
}


@dataclass(frozen=True)
class CreditsPermit:
    source_sha256: str
    encoded_sha256: str


@dataclass(frozen=True)
class CreditsOverlay:
    ram: int = RAM
    file_bytes: int = FILE_BYTES
    sections: tuple = SECTIONS

    @property
    def resident_bytes(self):
        return self.file_bytes + self.sections[3]


def group_hash(values):
    return sha256(b''.join(struct.pack('>H',len(value))+value for value in values))


def reference_evidence():
    root = Path(__file__).resolve().parents[1]
    data = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(data) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied English credits executable')
    for name,expected in GC_SYMBOLS.items():
        block = symbol_data(data,symbols,name)
        if (len(block),sha256(block)) != expected:
            raise ValueError('Changed English credits function or row table')


def verify_native(rom,replacements=None):
    files = by_vrom(rom); replacements = replacements or {}
    for vrom,digest in ((VROM,ACTOR_HASH),(RELOCATION,RELOCATION_HASH),*DEPENDENCIES):
        if sha256(replacements.get(vrom,files[vrom].extract(rom))) != digest:
            raise ValueError('Changed credits actor, relocation, controller, or structure allocator')
    code = replacements.get(CODE_VROM,files[CODE_VROM].extract(rom))
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES:
        raise ValueError('Changed credits overlay ownership metadata')
    native_code = files[CODE_VROM].extract(rom)
    for start,end in ((0x800578E0,0x80057A8C),(0x80057E24,0x80057EFC),
                      (0x80090CC0,0x80090E98)):
        if code[start-CODE_RAM:end-CODE_RAM] != native_code[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed credits allocation or direct-font helper')


def verify_values(values,info):
    if (len(values)!=110 or group_hash(values)!=VALUES_HASH
            or any(len(v)>25 or any(t.kind!='text' for t in tokenize(v,info)) for v in values)):
        raise ValueError('Credits require all complete native-identity English rows')


def candidates(rom,references,inventory,info):
    verify_native(rom); reference_evidence()
    originals = source_entries(rom); result = {}; values = []; donor_values = []
    for n in range(FIRST,END):
        id = f'string:{n:04X}'; row = inventory.get(id); original = originals[n]
        if not row or row['id']!=id or row['source_sha256']!=sha256(original):
            raise ValueError('Stale native credits inventory')
        if n in REFERENCES:
            reference_id = f'string:{REFERENCES[n]:04X}'
            reference = references.get(reference_id)
            if not reference or reference['id']!=reference_id:
                raise ValueError('Missing identity-matched English credit')
            text = reference['text']; value = encode(text,info)
            if reference['sha256']!=sha256(value):
                raise ValueError('Changed complete English credit reference')
            donor_values.append(value)
            extra = {'status':'mechanically_validated_candidate_not_reviewed',
                     'provenance':{'source':'user-supplied GAFE01 revision 0 disc',
                         'reference_id':reference_id,'reference_sha256':reference['sha256'],
                         'match_basis':'explicit_native_contributor_or_role_identity_in_active_English_credits'}}
        else:
            text = DRAFTS.get(n,'')
            if n not in DRAFTS and original.strip(b' '):
                raise ValueError('Native nonblank credit has no identity mapping')
            value = encode(text,info)
            extra = {'status':'draft' if n in DRAFTS else 'intentional_blank',
                     'provenance':'Original English translation/transliteration of native credit, or preserved native blank row'}
        values.append(value)
        result[id] = {'id':id,'source_sha256':sha256(original),'translation':text,
                      'control_policy':'exact',**extra}
    if group_hash(donor_values)!=REFERENCE_HASH:
        raise ValueError('Changed native-identity complete English reference group')
    verify_values(values,info)
    return result


def permits(rom,edits,info):
    verify_native(rom); originals = source_entries(rom)
    selected = [e for e in edits if e.get('id') in IDS]
    if len(selected)!=110 or {e['id'] for e in selected}!=set(IDS):
        raise ValueError('English credits require the complete unique 110-row group')
    by_id = {e['id']:e for e in selected}
    values = [encode(by_id[id]['translation'],info) for id in IDS]
    verify_values(values,info); result = {}
    for id,value in zip(IDS,values):
        digest = sha256(originals[int(id[7:],16)])
        if by_id[id].get('source_sha256')!=digest or by_id[id].get('control_policy','exact')!='exact':
            raise ValueError('Changed credits source identity or control policy')
        result[id] = CreditsPermit(digest,sha256(value))
    return result


def patch(data,reloc):
    if (sha256(data)!=ACTOR_HASH or sha256(reloc)!=RELOCATION_HASH
            or len(data)!=FILE_BYTES or struct.unpack_from('>5I',reloc)!=SECTIONS):
        raise ValueError('Changed native credits overlay or relocation')
    if (data[0x11B4:0x11C5]!=bytes(PAGES) or data[0x11C8:0x11D9]!=bytes(ROLE_LINES)):
        raise ValueError('Changed native credits page or role tables')
    rows = struct.unpack_from('>98I',reloc,20); output = bytearray(data)
    for address,before,after in CHANGES:
        at = address-RAM
        expected_reloc = [0x46000000|at] if address in (0x80AA3D2C,0x80AA3DE8) else []
        if (struct.unpack_from('>I',data,at)[0]!=before
                or [r for r in rows if r&0xFFFFFF==at]!=expected_reloc):
            raise ValueError('Changed credits instruction or buffer-pointer relocation')
        struct.pack_into('>I',output,at,after)
    relocation = bytearray(reloc)
    struct.pack_into('>I',relocation,12,OLD_BSS+EXTRA_BSS)
    return bytes(output),bytes(relocation)


def relocated(data,reloc,base):
    output,new_reloc = patch(data,reloc)
    spec = replace(CreditsOverlay(),sections=(*SECTIONS[:3],OLD_BSS+EXTRA_BSS,SECTIONS[4]))
    return relocate_verified_data(spec,output,new_reloc,base)


def install(rom,replacements):
    verify_native(rom,replacements); files = by_vrom(rom)
    output,reloc = patch(files[VROM].extract(rom),files[RELOCATION].extract(rom))
    code = bytearray(replacements.get(CODE_VROM,files[CODE_VROM].extract(rom)))
    struct.pack_into('>I',code,METADATA-CODE_RAM+12,RAM+RESIDENT_BYTES)
    replacements.update({VROM:output,RELOCATION:reloc,CODE_VROM:bytes(code)})
