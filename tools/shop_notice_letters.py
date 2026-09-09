"""Source-bound shop notice owners and complete letter installation."""

import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_shop_notice_letters import ROOT,TEMPLATES,RARE_TABLE,REOPENING_TABLE,GUARDS,audit
from npc_mail_loader import VROM as CREATOR_VROM,verify_configuration
from post_office_letters import verify_items
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT
import mail_creator_catalog as creator_catalog

START,END = 0x800C0E98,0x800C1428
REGIONS = ((START,0x800C1070),(0x800C1230,END))
NATIVE_CALLS = {0x8009C534,0x80094C10,0x800816C0,0x800B6A3C,0x8009C67C,
                0x8007D318,0x800C16F0,0x800B79E0}


def sources():
    names = ('overlays/mail_generation/shop_notice_entry.s','tools/build_shop_notice_owners.py',
             'tools/shop_notice_letters.py','tools/audit_shop_notice_letters.py')
    return {name:sha256((ROOT/name).read_bytes()) for name in names}


def verify_code(code):
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM])!=digest:
            raise ValueError('Changed native shop notice owner or selector')
    for at,values in ((0x8010DC3C,RARE_TABLE),(0x8010DC5C,REOPENING_TABLE)):
        if struct.unpack_from('>'+str(len(values))+'I',code,at-CODE_RAM)!=values:
            raise ValueError('Changed native shop notice template table')


def validate(data,report,module):
    loader = int(module['symbols']['af_npc_mail_load'],16)
    if (loader&3 or not MODULE_RAM+0x300<=loader<MODULE_RAM+LINKED_LIMIT
            or report.get('version')!=1 or report.get('sources')!=sources()
            or report.get('module_sha256')!=module['module_sha256']
            or report.get('loader_ram')!=loader or report.get('sha256')!=sha256(data)
            or len(data)!=END-START):
        raise ValueError('Stale or changed shop notice owners')
    symbols = report.get('symbols',{})
    if set(symbols)!={'shop_spotlight_entry','shop_spotlight_end','shop_reopening_entry','shop_reopening_end'}:
        raise ValueError('Invalid shop notice owner exports')
    result = {}
    calls = set()
    for (start,end),name in zip(REGIONS,('shop_spotlight','shop_reopening')):
        used = symbols[name+'_end']
        if symbols[name+'_entry']!=start or used&3 or not start<used<=end:
            raise ValueError('Shop notice owner exceeds original function space')
        value = data[start-START:end-START]
        if any(value[used-start:]): raise ValueError('Unexpected shop notice owner padding')
        for offset in range(0,used-start,4):
            word = struct.unpack_from('>I',value,offset)[0];op = word>>26;at = start+offset
            if op in (2,3):
                target = 0x80000000|((word&0x3FFFFFF)<<2)
                if op!=3 or target not in NATIVE_CALLS|{loader}: raise ValueError('Unapproved shop notice call')
                calls.add(target)
            elif op in (1,4,5,6,7,20,21,22,23):
                displacement = (word&0xFFFF)-(0x10000 if word&0x8000 else 0)
                if not start<=at+4+4*displacement<used: raise ValueError('Shop notice branch leaves its owner')
        result[start] = value
    if calls!=NATIVE_CALLS|{loader}: raise ValueError('Incomplete shop notice helper inventory')
    if any(data[REGIONS[0][1]-START:REGIONS[1][0]-START]):
        raise ValueError('Shop notice build includes an unrelated selector replacement')
    return result


def install(native,replacements,additions,module,directory):
    native = verified_rom(native)
    if not module or module.get('npc_mail_loader',{}).get('overlay',{}).get('shop_notices') is not True:
        raise ValueError('Shop notices require the complete shop dispatcher')
    if any(v not in additions for v in (MODULE_VROM,CREATOR_VROM,0x02A00000)):
        raise ValueError('Missing shop notice module, creator, or complete item names')
    verify_configuration(additions[MODULE_VROM],additions[CREATOR_VROM],module)
    verify_items(additions[MODULE_VROM],additions[0x02A00000])
    report = json.loads((directory/'owners.json').read_text());data = (directory/'owners.bin').read_bytes()
    changes = validate(data,report,module)
    original = by_vrom(native)[CODE_VROM].extract(native)
    code = bytearray(replacements.get(CODE_VROM,original));verify_code(code)
    evidence = audit(native,creator_catalog.resource(additions,module))
    for at,value in changes.items(): code[at-CODE_RAM:at-CODE_RAM+len(value)] = value
    replacements[CODE_VROM] = bytes(code)
    return {**evidence,'installed':True,'complete_templates':list(TEMPLATES),'owners':report,
            'patches':[{'ram':f'{at:08X}','bytes':len(v),'sha256':sha256(v)} for at,v in changes.items()],
            'item_resource_sha256':sha256(additions[0x02A00000]),'new_resident_bytes':0,
            'owner_stack_bytes':{'spotlight':304,'reopening':288},
            'status':'Complete shop notices installed; native and gameplay acceptance remain'}


def verify_installation(built,native,module,report):
    files = by_vrom(built)
    verify_configuration(files[MODULE_VROM].extract(built),files[CREATOR_VROM].extract(built),module)
    creator_catalog.verify_installation(built,module,report)
    if module['npc_mail_loader']['overlay'].get('shop_notices') is not True:
        raise ValueError('Shop notice dispatcher is not installed')
    if not isinstance(report.get('item_resource_sha256'),str): raise ValueError('Missing shop item approval')
    verify_items(files[MODULE_VROM].extract(built),files[0x02A00000].extract(built),report['item_resource_sha256'])
    actual = bytearray(files[CODE_VROM].extract(built));original = by_vrom(native)[CODE_VROM].extract(native)
    data = bytearray(END-START)
    for start,end in REGIONS:
        data[start-START:end-START] = actual[start-CODE_RAM:end-CODE_RAM]
        actual[start-CODE_RAM:end-CODE_RAM] = original[start-CODE_RAM:end-CODE_RAM]
    changes = validate(bytes(data),report['owners'],module);verify_code(actual)
    expected = [{'ram':f'{at:08X}','bytes':len(v),'sha256':sha256(v)} for at,v in changes.items()]
    if (report.get('patches')!=expected or report.get('complete_templates')!=list(TEMPLATES)
            or report.get('native_rare_table')!=list(RARE_TABLE)
            or report.get('native_reopening_table')!=list(REOPENING_TABLE)):
        raise ValueError('Changed shop notice installation report')
