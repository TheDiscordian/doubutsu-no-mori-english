"""Two exact GC apology targets, gated by installed input/font/matcher support."""
from dataclasses import dataclass, replace

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from fortune_strings import source_entries, STRING_RELOCATION
from textbanks import banks

TARGETS={
    'string:048E':('c627a0bfbf57c068b25ee907a57998bc7a434c3b122d0716ad737fbacf0e4746',
                  'U R my {glyph:80A7}!',b'U R my \x80\xa7!',
                  '9b76c706cb2d9cac4250d05c9bb9168532b6975f3cd5ec748c73d9f3619bf6e5'),
    'string:0491':('eb7b5123ef0b9ae3c3d1e2f1c57cc5d767f98ca40060e0cbc61ca6f679cec8f0',
                  'Reset = {glyph:80BA}',b'Reset = \x80\xba',
                  '8aa1171fc62ce23690e758e985e6708f8f9c88f81d1491d4ae4c5832f453d514'),
}


@dataclass(frozen=True)
class ApologyPermit:
    id: str
    source_sha256: str
    encoded_sha256: str


def approved(id):
    source,_,value,_=TARGETS[id]
    return ApologyPermit(id,source,sha256(value))


def with_candidates(native,edits):
    originals=source_entries(native);seen=set();result=list(edits)
    for id,(source,text,value,gc_hash) in TARGETS.items():
        if (sha256(originals[int(id[7:],16)])!=source or len(value)!=10
                or sha256(value.replace(b'\x80',b''))!=gc_hash):
            raise ValueError('Changed apology source or exact GC encoding')
    for row in edits:
        if row['id'] not in TARGETS:continue
        source,text,_,_=TARGETS[row['id']]
        if (row['id'] in seen or row.get('source_sha256')!=source
                or row.get('translation')!=text or row.get('control_policy','exact')!='exact'):
            raise ValueError('Conflicting exact apology target')
        seen.add(row['id'])
    result.extend({'id':id,'source_sha256':source,'translation':text,'control_policy':'exact',
                   'status':'source_verified_reference','provenance':{
                       'source':'user-supplied GAFE01 revision 0 disc','reference_id':id,
                       'reference_sha256':gc_hash,'contract':'specs/APOLOGY_INPUT.md'}}
                  for id,(source,text,_,gc_hash) in TARGETS.items() if id not in seen)
    return result


def validate_permit(permit,source,value):
    if (not isinstance(permit,ApologyPermit) or permit.id not in TARGETS
            or permit!=approved(permit.id) or sha256(source)!=permit.source_sha256
            or value!=TARGETS[permit.id][2]):
        raise ValueError('Symbol input requires its exact complete apology target permit')


def planned(native,replacements,module):
    from resetti_replies import VROM,RELOC_VROM,patch,FIRST,END,verify_values
    from runtime_module import module_command_info
    from reserve_strings import START,END as LOADER_END,LOADER_SHA
    originals=by_vrom(native)
    if (replacements.get(VROM)!=patch(originals[VROM].extract(native),originals[RELOC_VROM].extract(native))
            or replacements.get(RELOC_VROM,originals[RELOC_VROM].extract(native))!=originals[RELOC_VROM].extract(native)
            or not module.get('extended_font',{}).get('font',{}).get('mail_glyphs')):
        raise ValueError('Apology targets require the complete matcher and symbol font')
    with_candidates(native,[])
    code=bytearray(replacements[CODE_VROM]);_,at,before,after=STRING_RELOCATION
    if code[at-CODE_RAM:at-CODE_RAM+8]!=bytes.fromhex(after):
        raise ValueError('Apology target bank is not relocated')
    code[at-CODE_RAM:at-CODE_RAM+8]=bytes.fromhex(before)
    if sha256(code[START-CODE_RAM:LOADER_END-CODE_RAM])!=LOADER_SHA:
        raise ValueError('Changed bounded apology string loader')
    bank=next(b for b in banks(native) if b.name=='string')
    entries=replace(bank,data=replacements[bank.data_vrom],table=replacements[bank.table_vrom]).entries()
    verify_values(entries[FIRST:END],module_command_info(native))
    if any(entries[int(id[7:],16)]!=value for id,(_,_,value,_) in TARGETS.items()):
        raise ValueError('Incomplete installed sun/skull apology targets')
    return {id:{'source_sha256':source,'encoded_sha256':sha256(value),'reference_sha256':gc_hash}
            for id,(source,_,value,gc_hash) in TARGETS.items()}


def verify_installation(built,native,report):
    from resetti_replies import VROM,RELOC_VROM
    from runtime_module import verify_test_module
    verify_test_module(built,report['runtime_module'])
    files=by_vrom(built);moved={int(k,16):int(v,16) for k,v in report['vrom_relocations'].items()}
    bank=next(b for b in banks(native) if b.name=='string')
    replacements={v:files[moved.get(v,v)].extract(built)
                  for v in (VROM,RELOC_VROM,CODE_VROM,bank.data_vrom,bank.table_vrom)}
    result=planned(native,replacements,report['runtime_module'])
    if report['apology_input'].get('targets')!=result:
        raise ValueError('Missing installed apology target evidence')
    return result
