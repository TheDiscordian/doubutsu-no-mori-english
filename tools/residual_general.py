"""Complete residual general strings while retaining installed full-text consumers."""
import argparse
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from textbanks import Bank, banks
from textcodec import command_info, encode, tokenize
from mail_reference import BANK_HASHES, DECODER_SHA256
from gc_text import decoder_tables, decode_gc
from fortune_strings import source_entries, STRING_RELOCATION
from reserve_strings import verify_source as verify_loader_source, START, END as LOADER_END, LOADER_SHA
from unused_names import assemble, DATA_VROM, TABLE_VROM
import fortune_slips

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/unused-names-pilot'
BASE_SHA = 'e02d3387c61913dad85aece9ff69f3d9de30a7951373755a89620f7849916ccf'
MANIFEST = ROOT/'translations/n64-residual-general.json'
MANIFEST_SHA = '57e1548db94eb4f41f544aaea78b4ac0e83b465b8f4d13810cb4ab2e7dc4369f'
CATCHPHRASES = (0x11,0x12,0x13,0x14,0x19,0x21,0x2F,0x37,0x3A,0x40,0x4F,
               0x50,0x53,0x5A,0x5D,0x60,0x63,0x65,0x6D,0x78,0x80,0x83,0x262,0x269,0x298)
ORIGINAL_IDS = tuple(sorted((*range(3,16),*(i for i in CATCHPHRASES if i not in (0x78,0x298)))))
FORTUNES = tuple(int(i[7:],16) for i in fortune_slips.IDS)
REFERENCE_IDS = tuple(sorted((0,1,2,0x78,0x298,*FORTUNES,*range(0x2EA,0x2ED),
                             *range(0x458,0x464),*range(0x494,0x4A0),*range(0x558,0x55C))))
IDS = tuple(f'string:{n:04X}' for n in sorted((*ORIGINAL_IDS,*REFERENCE_IDS)))
EMPTY_IDS = tuple(f'string:{n:04X}' for start in (0x593,0x5B1) for n in range(start,start+15))
EMPTY_FORMS = (0,1,2,1,1,0,1,0,1,0,0,1,2,1,1)
EMPTY_SOURCE_HASHES = {
    f'string:{start+i:04X}': sha256(bytes.fromhex(forms[kind]))
    for start,forms in ((0x593,('ffc3','1dc3','fac3')),(0x5B1,('fc06','1a06','f706')))
    for i,kind in enumerate(EMPTY_FORMS)
}


def reference(native):
    directory = ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    data,table = ((directory/n).read_bytes() for n in ('string_data.bin','string_data_table.bin'))
    decoder = ROOT/'local/ac-decomp/tools/msg_tool.py'
    if ((sha256(data),sha256(table)) != BANK_HASHES['string']
            or sha256(decoder.read_bytes()) != DECODER_SHA256):
        raise ValueError('Changed supplied general-string reference or decoder')
    entries = Bank('string',0,0,data,table).entries()
    native = verified_rom(native)
    info = command_info(by_vrom(native)[CODE_VROM].extract(native))
    tables = decoder_tables(decoder)
    values = {n:encode(decode_gc(entries[n],tables),info) for n in REFERENCE_IDS}
    if any(not v or any(t.kind!='text' or not 32<=t.data[0]<127 for t in tokenize(v,info))
           for v in values.values()):
        raise ValueError('General reference requires complete plain English')
    return values


def originals(native, data=None):
    native = verified_rom(native)
    info = command_info(by_vrom(native)[CODE_VROM].extract(native))
    entries = source_entries(native)
    data = MANIFEST.read_bytes() if data is None else data
    if sha256(data) != MANIFEST_SHA:
        raise ValueError('Changed approved residual-general translation manifest')
    rows = json.loads(data)
    if tuple(int(r['id'][7:],16) for r in rows) != ORIGINAL_IDS:
        raise ValueError('Residual general translations require all exact ordered IDs')
    result = {}
    for row in rows:
        n = int(row['id'][7:],16)
        value = encode(row['translation'],info)
        if (row['id'] != f'string:{n:04X}' or row['source_sha256'] != sha256(entries[n])
                or row['control_policy'] != 'exact' or not 1<=len(value)<=6
                or any(t.kind!='text' or not 32<=t.data[0]<127 for t in tokenize(value,info))):
            raise ValueError('Changed residual-general source, complete wording, or plain encoding')
        result[n] = value
    # Original helpers append these after at most four year or two other digits.
    suffix_limits = {3:2,4:2,5:2,6:1,7:2,8:3}
    if any(len(result[n])>limit for n,limit in suffix_limits.items()):
        raise ValueError('Compact date unit exceeds its unchanged native formatter')
    if any(len(result[n])!=3 for n in range(9,16)):
        raise ValueError('Compatibility weekdays must fit the four-byte length scan')
    return result


def consumers(native,base,previous,values):
    verify_loader_source(native)
    from catchphrases import native_table
    if set(CATCHPHRASES) & {row[1] for row in native_table(native)}:
        raise ValueError('Unused catchphrase group overlaps a saved default selector')
    files = by_vrom(base)
    code = bytearray(files[CODE_VROM].extract(base))
    _,at,before,after = STRING_RELOCATION
    if code[at-CODE_RAM:at-CODE_RAM+8]!=bytes.fromhex(after):
        raise ValueError('General strings require the existing data relocation')
    code[at-CODE_RAM:at-CODE_RAM+8]=bytes.fromhex(before)
    if sha256(code[START-CODE_RAM:LOADER_END-CODE_RAM])!=LOADER_SHA:
        raise ValueError('Changed bounded general-string loader')
    # Live fortune selection uses its complete owned 16-byte phrases, not the
    # retained ten-byte calls in the old prefix.
    from fortune_actor import verify_installation as verify_fortune, NEW_VROM
    verify_fortune(base,native,previous['fortune_actor']['overlay'],previous['runtime_module'])
    wordbytes = b''.join(values[n].ljust(16,b' ') for n in FORTUNES)
    if sha256(wordbytes)!=fortune_slips.WORDS_HASH:
        raise ValueError('General fortune words differ from complete native-order reference')
    offset=previous['fortune_actor']['overlay']['symbols']['af_fortune_words']
    if files[NEW_VROM].extract(base)[offset:offset+len(wordbytes)]!=wordbytes:
        raise ValueError('Installed fortune consumer differs from complete bank wording')
    # Birthday preparation jumps to the existing complete resident owner.
    from birthday_fields import changes, SPEC
    moved={int(k,16):int(v,16) for k,v in previous['vrom_relocations'].items()}
    actor=files[moved.get(SPEC.vrom,SPEC.vrom)].extract(base)
    for address,_,word in changes(previous['runtime_module']):
        if struct.unpack_from('>I',actor,address-SPEC.ram)[0]!=word:
            raise ValueError('Birthday strings lack their complete installed consumer')
    from runtime_layout import MODULE_VROM
    module=files[MODULE_VROM].extract(base)
    for first,end,width in ((0x458,0x464,8),(0x494,0x4A0,12)):
        packed=b''.join(values[n].ljust(width,b'\0') for n in range(first,end))
        if any(len(values[n])>=width for n in range(first,end)) or packed not in module:
            raise ValueError('Birthday bank wording differs from complete resident names')
    # The original narrow shop/date helpers are reclaimed by the seasonal owner.
    from notice_seasonal_owner import START as SHOP_START, END as SHOP_END, expected, call
    actual=files[CODE_VROM].extract(base)
    loader=int(previous['runtime_module']['symbols']['af_npc_mail_load'],16)
    if (actual[SHOP_START-CODE_RAM:SHOP_END-CODE_RAM]!=expected(loader)
            or any(struct.unpack_from('>I',actual,a-CODE_RAM)[0]!=w for a,w in
                   ((0x800A66C8,0),(0x800A671C,0),(0x800A6778,call(SHOP_START))))):
        raise ValueError('Complete seasonal owner must replace the narrow shop-name helpers')
    from notice_seasonal import shop_names
    if tuple(values[n].ljust(16,b' ') for n in range(0x558,0x55C))!=shop_names(native):
        raise ValueError('General shop names differ from complete seasonal names')


def verify_empty_units(native,base,previous,entries):
    from shop_units import (SHOPS, verify_callers, group_hash, VALUES_SHA256,
                            FIRST, END)
    verify_callers(native)
    source=source_entries(native)
    if any(sha256(source[int(identity[7:],16)])!=digest for identity,digest in EMPTY_SOURCE_HASHES.items()):
        raise ValueError('Changed native source for an intentional English counter omission')
    if group_hash(entries[FIRST:END])!=VALUES_SHA256:
        raise ValueError('English omissions require the complete approved counter group')
    if any(entries[int(identity[7:],16)] for identity in EMPTY_IDS):
        raise ValueError('Intentional English counter must be empty')
    native_files,files=by_vrom(native),by_vrom(base)
    moved={int(k,16):int(v,16) for k,v in previous['vrom_relocations'].items()}
    for shop in SHOPS.values():
        old=native_files[shop.vrom].extract(native)
        actual=files[moved.get(shop.vrom,shop.vrom)].extract(base)
        for lo,hi in ((shop.handler-shop.ram,shop.handler-shop.ram+0xCC),
                      (shop.pointers-shop.ram-0x300,shop.pointers-shop.ram+0xC0)):
            if actual[lo:hi]!=old[lo:hi]:
                raise ValueError('Changed installed quantity selection, capacity, or native family table')
    return EMPTY_IDS


def baseline():
    base=(BASE/'animal-forest-halfwidth.z64').read_bytes()
    previous=json.loads((BASE/'build.json').read_text())
    if sha256(base)!=BASE_SHA or previous['output_sha256']!=BASE_SHA:
        raise ValueError('Residual general strings require the complete retained-name predecessor')
    return base,previous


def plan(native,base,previous):
    values={**originals(native),**reference(native)}
    if tuple(f'string:{n:04X}' for n in sorted(values))!=IDS:
        raise ValueError('Overlapping or incomplete general-string groups')
    consumers(native,base,previous,values)
    files=by_vrom(base)
    bank=next(b for b in banks(native) if b.name=='string')
    current=replace(bank,data=files[DATA_VROM].extract(base),table=files[TABLE_VROM].extract(base))
    before=current.entries()
    empty_ids=verify_empty_units(native,base,previous,before)
    after=list(before)
    for n,value in values.items():
        if len(value)>64:
            raise ValueError('Residual general string exceeds native staging capacity')
        after[n]=value
    data,table=current.rebuild(after,allow_expand=True)
    if replace(current,data=data,table=table).entries()!=after:
        raise ValueError('Residual general-string bank round trip failed')
    evidence={'version':1,'baseline_rom_sha256':BASE_SHA,'manifest_sha256':MANIFEST_SHA,
        'ids':list(IDS),'records':len(IDS),'changed_records':sum(a!=b for a,b in zip(before,after)),
        'intentional_empty_ids':list(empty_ids),'data_sha256':sha256(data),'table_sha256':sha256(table),
        'complete_reference_ids':[f'string:{n:04X}' for n in REFERENCE_IDS],
        'compatibility_date_ids':[f'string:{n:04X}' for n in range(3,16)],
        'runtime_changes':0,'saved_layout_changes':0}
    return {DATA_VROM:data,TABLE_VROM:table},evidence


def expected_report(previous,built,evidence):
    report=deepcopy(previous)
    report.update(residual_general=evidence,output_sha256=sha256(built),size=len(built),
                  translation_edits=previous['translation_edits']+evidence['changed_records'])
    report.pop('patch_sha256',None)
    return report


def verify_installation(built,native,report):
    verified_rom(native)
    base,previous=baseline()
    updates,evidence=plan(native,base,previous)
    expected=assemble(native,base,previous,updates)
    if built!=expected:
        raise ValueError('Residual-general cartridge differs from its exact two-file update')
    actual=deepcopy(report);actual.pop('patch_sha256',None)
    if actual!=expected_report(previous,built,evidence):
        raise ValueError('Changed residual-general installation report')
    return base,previous,tuple(evidence['intentional_empty_ids'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/residual-general-pilot')
    a=p.parse_args()
    native=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    base,previous=baseline()
    from unused_names import verify_installation as verify_previous
    accent,accent_report=verify_previous(base,native,previous)
    from accent_items_install import verify_installation as verify_accents
    verify_accents(accent,native,accent_report)
    updates,evidence=plan(native,base,previous)
    output=assemble(native,base,previous,updates)
    report=expected_report(previous,output,evidence)
    verify_installation(output,native,report)
    patch=make_ups(native,output)
    if apply_ups(native,patch)!=output:
        raise ValueError('Residual-general patch reconstruction failed')
    report['patch_sha256']=sha256(patch)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'animal-forest-halfwidth.z64').write_bytes(output)
    (a.output/'animal-forest-halfwidth.ups').write_bytes(patch)
    (a.output/'runtime-module.json').write_text(json.dumps(report['runtime_module'],indent=2)+'\n')
    (a.output/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output_sha256':sha256(output),'patch_sha256':sha256(patch),
                      'changed_records':evidence['changed_records'],'runtime_changes':0}))


if __name__=='__main__':main()
