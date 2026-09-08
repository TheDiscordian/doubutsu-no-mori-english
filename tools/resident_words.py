"""Complete ordinary-resident words with scoped native sixteen-byte callers."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import struct

from aflib import sha256, verified_rom
from audit_string_callers import audit
from npc_mail_show import OVERLAYS, source, verify, relocated as original_relocated
from fortune_strings import source_entries
from textcodec import encode, tokenize

SPEC = OVERLAYS['ordinary']
HELPER, SCRATCH, SCRATCH_END = 0x80920FFC, 0x80921E08, 0x80921E18
GROUPS = ((0x414,64),(0x454,4),(0x464,32),(0x4A0,32),(0x55D,4))
IDS = tuple(f'string:{base+i:04X}' for base,count in GROUPS for i in range(count))
VALUES_SHA256 = '383be6afb5a066b941ecce12bf9ea5b5889966327642257b8a5c14aae83d511f'
SYMBOLS_SHA256 = 'dd213741db4b789fe0d3eb559acad92289dc636dc44866d67f35070d851f025b'
CALLS = (0x809210B4,0x80921290,0x809212F0,0x80921380)
TABLES = ((0x80921D2C,(0x219,0x1E5,0x334,0x314,0x414)),
          (0x80921D4C,(0x464,0x2F4,0x4A0)),(0x80921D70,(0x458,0x494)))
CHANGES = ((0x8092102C,0x2405000A,0x24050010),
           (0x80921058,0x2407000A,0x24070010),
           (0x809211D8,0x27BDFFD0,0x27BDFFC8),
           (0x80921254,0x27A4002A,0x27A40024),
           (0x80921258,0x24050004,0x24050010),
           (0x8092127C,0x2407000A,0x24070010),
           (0x8092129C,0x27BD0030,0x27BD0038))


@dataclass(frozen=True)
class ResidentWordPermit:
    source_sha256: str
    encoded_sha256: str
    capacity: int


def capacity(id):
    if id not in IDS:
        raise ValueError('Not a scoped resident word')
    return 10 if int(id[7:],16)>=0x55D else 16


def verify_values(values,info):
    if (len(values)!=len(IDS)
            or sha256(b''.join(struct.pack('>H',len(value))+value for value in values))!=VALUES_SHA256
            or any(not 1<=len(value)<=capacity(id)
                   or any(t.kind!='text' for t in tokenize(value,info)) for id,value in zip(IDS,values))):
        raise ValueError('Resident words require all 136 complete English values')


def verify_source(data,reloc):
    verify(SPEC,data,reloc)
    for address,values in TABLES:
        if struct.unpack_from('>'+str(len(values))+'I',data,address-SPEC.ram)!=values:
            raise ValueError('Changed native resident random-word family')
    if data[0x80921D40-SPEC.ram:0x80921D4A-SPEC.ram]!=bytes.fromhex('7F5046A0000400000000'):
        raise ValueError('Changed native four-character shop-name construction')
    rows=struct.unpack_from('>'+str(SPEC.sections[4])+'I',reloc,20)
    for address,before,_ in CHANGES:
        at=address-SPEC.ram
        if struct.unpack_from('>I',data,at)[0]!=before or any(row&0xFFFFFF==at for row in rows):
            raise ValueError('Changed resident word instruction or relocation overlap')


@lru_cache(maxsize=1)
def caller_evidence(rom):
    rom=verified_rom(rom);data,reloc=source(rom,'ordinary');verify_source(data,reloc)
    report=audit(rom,HELPER)
    if [(int(row['vrom'],16),int(row['call_ram'],16)) for row in report['callers']]!=[(SPEC.vrom,pc) for pc in CALLS]:
        raise ValueError('Unexpected native random-word helper caller')
    symbols=Path(__file__).resolve().parents[1]/'upstream/af/linker_scripts/jp/symbol_addrs_overlays.txt'
    if sha256(symbols.read_bytes())!=SYMBOLS_SHA256 or SCRATCH_END-SCRATCH!=16:
        raise ValueError('Changed native resident temporary ownership evidence')
    return {'helper_calls':[f'{pc:08X}' for pc in CALLS],
            'scratch':[f'{SCRATCH:08X}',f'{SCRATCH_END:08X}'],
            'definition_sha256':report['definition_sha256'],'symbols_sha256':SYMBOLS_SHA256}


def candidates(rom,references,inventory,info):
    caller_evidence(rom);originals=source_entries(rom);result={};values=[]
    for id in IDS:
        native=originals[int(id[7:],16)];row,reference=inventory.get(id),references.get(id)
        if not row or not reference:
            raise ValueError('Missing complete resident-word source')
        value=encode(reference['text'],info)
        if (row['id']!=id or reference['id']!=id or row['source_sha256']!=sha256(native)
                or reference['sha256']!=sha256(value) or encode(row['legacy'],info)!=value):
            raise ValueError('Changed complete resident-word reference or native/legacy agreement')
        values.append(value)
        result[id]={'id':id,'source_sha256':sha256(native),'translation':reference['text'],
                    'control_policy':'exact','status':'mechanically_validated_candidate_not_reviewed',
                    'provenance':{'source':'user-supplied GAFE01 revision 0 disc','reference_id':id,
                        'reference_sha256':reference['sha256'],
                        'match_basis':'native_resident_word_family_and_complete_legacy_agreement'}}
    verify_values(values,info)
    return result


def permits(rom,edits,info):
    caller_evidence(rom);originals=source_entries(rom)
    selected=[e for e in edits if e.get('id') in IDS]
    if len(selected)!=len(IDS) or {e['id'] for e in selected}!=set(IDS):
        raise ValueError('Resident words require the complete unique 136-record group')
    by_id={e['id']:e for e in selected};values=[encode(by_id[id]['translation'],info) for id in IDS]
    verify_values(values,info);result={}
    for id,value in zip(IDS,values):
        digest=sha256(originals[int(id[7:],16)])
        if by_id[id].get('source_sha256')!=digest or by_id[id].get('control_policy','exact')!='exact':
            raise ValueError('Changed resident-word source or control policy')
        result[id]=ResidentWordPermit(digest,sha256(value),capacity(id))
    return result


def patch(data,reloc,*,module=None,dates=False):
    """Only original input or the exact existing date/birthday patch may precede us."""
    verify_source(data,reloc)
    if dates:
        from dialogue_dates import patch as date_patch
        before,new_reloc=date_patch(data,reloc,module)
    else:
        before,new_reloc=data,reloc
    result=bytearray(before)
    for address,old,new in CHANGES:
        at=address-SPEC.ram
        if struct.unpack_from('>I',result,at)[0]!=old:
            raise ValueError('Resident word patch overlaps date/birthday preparation')
        struct.pack_into('>I',result,at,new)
    return bytes(result),new_reloc


def install(rom,replacements,module):
    if not module:
        raise ValueError('Resident words require the complete resident item-field runtime')
    caller_evidence(rom);data,reloc=source(rom,'ordinary')
    current=(replacements.get(SPEC.vrom,data),replacements.get(SPEC.relocation,reloc))
    dates=current!=(data,reloc)
    if dates:
        from dialogue_dates import patch as date_patch
        if current!=date_patch(data,reloc,module):
            raise ValueError('Resident words overlap an unknown overlay patch')
    replacements[SPEC.vrom],new_reloc=patch(data,reloc,module=module,dates=dates)
    if dates:replacements[SPEC.relocation]=new_reloc


def relocated(data,reloc,base,*,module=None,dates=False):
    """Independent expectation: relocate the original, then change immediate words."""
    patch(data,reloc,module=module,dates=dates)
    if dates:
        from dialogue_dates import relocated as date_relocated
        result=bytearray(date_relocated(data,reloc,module,base))
    else:
        result=bytearray(original_relocated(SPEC,data,reloc,base))
    for address,_,new in CHANGES:struct.pack_into('>I',result,address-SPEC.ram,new)
    return bytes(result)
