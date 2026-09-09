"""Source-bound English omission of the Japanese town-name suffix."""
from dataclasses import replace
from pathlib import Path
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from textbanks import Bank, banks

ROOT=Path(__file__).resolve().parents[1]
ID='string:01E4'
SOURCE_SHA='7580e814a6292c374299a1b0e9b3f08b6a494dd51561a554c01514d759495b55'
EMPTY_SHA=sha256(b'')
START,END=0x80094F24,0x800950D8
CODE_SHA='0655770ae61d611fd8400f80bdc16319c3e782c00acb4136688c859891da8275'


def references(native):
    from gc_names import symbol_data
    verified_rom(native)
    bank=next(b for b in banks(native) if b.name=='string')
    if sha256(bank.entries()[0x1E4])!=SOURCE_SHA: raise ValueError('Changed native town suffix')
    code=by_vrom(native)[CODE_VROM].extract(native)
    if sha256(code[START-CODE_RAM:END-CODE_RAM])!=CODE_SHA:
        raise ValueError('Changed native town-suffix consumers')
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel)!='29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed English town-name executable')
    functions={'mLd_AddMuraString':'809ca46e4fe9a45e1e41dfd7486ed3c552753b3c918c41cd210536fe0a20c95e',
               'mLd_GetLandNameStringAddMura':'e1bc973b3be1906038295be5efd676113b37bbe9d893feef7341e8651d8372ed',
               'mLd_SetFreeStrLandMuraName':'e4f0af85c93f99590a1e99fa8e682ab3c94a811c4c769348c30eb751b702b057'}
    for name,digest in functions.items():
        if sha256(symbol_data(rel,symbols,name))!=digest: raise ValueError('Changed English suffix consumer')
    directory=ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    data,table=[(directory/('string'+s)).read_bytes() for s in ('_data.bin','_data_table.bin')]
    if (sha256(data)!='1ca41141a2265ddd0b3bee22868f27fe3cd980f2caeb948e1d00e7910e0533cf'
            or sha256(table)!='1b61ef035cd276a575169a7473f62a8cd9b1b788abd713bbd972c016487079df'
            or Bank('string',0,0,data,table).entries()[0x1E4]!=b''):
        raise ValueError('English town suffix is not the complete empty reference')
    return {'id':ID,'source_sha256':SOURCE_SHA,'encoded_sha256':EMPTY_SHA,
            'native_consumers_sha256':CODE_SHA,'reference_functions':functions,
            'meaning':'English town names omit the Japanese village suffix',
            'saved_name_bytes':6,'code_changes':0}


def with_candidate(native,edits):
    references(native)
    for row in edits:
        if row['id']==ID:
            if row['source_sha256']!=SOURCE_SHA or row['translation']!='':
                raise ValueError('Conflicting town-suffix translation')
            return list(edits)
    return [*edits,{'id':ID,'source_sha256':SOURCE_SHA,'translation':'','control_policy':'exact',
                   'status':'source_verified_english_omission',
                   'provenance':{'source':'user-supplied GAFE01 revision 0 disc',
                                 'reference_id':ID,'reference_sha256':EMPTY_SHA}}]


def planned(native,replacements):
    evidence=references(native)
    code=replacements.get(CODE_VROM,by_vrom(native)[CODE_VROM].extract(native))
    if sha256(code[START-CODE_RAM:END-CODE_RAM])!=CODE_SHA:
        raise ValueError('English suffix consumer was modified')
    bank=next(b for b in banks(native) if b.name=='string')
    current=replace(bank,data=replacements.get(bank.data_vrom,bank.data),
                    table=replacements.get(bank.table_vrom,bank.table))
    if current.entries()[0x1E4]!=b'': raise ValueError('Complete English suffix omission is not installed')
    return evidence


def verify_installation(built,native,report):
    files=by_vrom(built)
    moved={int(k,16):int(v,16) for k,v in report.get('vrom_relocations',{}).items()}
    bank=next(b for b in banks(native) if b.name=='string')
    replacements={v:files[moved.get(v,v)].extract(built) for v in (CODE_VROM,bank.data_vrom,bank.table_vrom)}
    evidence=planned(native,replacements)
    if report.get('town_suffix')!=evidence: raise ValueError('Missing or changed town-suffix approval')
    return evidence
