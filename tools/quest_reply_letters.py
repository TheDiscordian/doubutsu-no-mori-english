"""Install complete quest replies while retaining native rewards and eligibility."""
import json
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_quest_reply_letters import ROOT,TEMPLATES,GUARDS,CALLER_VROM,CALLER_RAM,CALLER_START,CALLER_END,CALLER_HASH,audit
from npc_mail_loader import VROM as CREATOR_VROM,verify_configuration
from post_office_letters import verify_items
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT
import mail_creator_catalog as creator_catalog

START,END,BLOB_BYTES = 0x800BB86C,0x800BBA98,556
REGIONS = ((START,0x800BB990),(0x800BBA64,END))


def sources():
    return {name:sha256((ROOT/name).read_bytes()) for name in (
        'overlays/mail_generation/quest_reply_entry.s','tools/build_quest_reply_owners.py',
        'tools/quest_reply_letters.py','tools/audit_quest_reply_letters.py')}


def expected_image(loader):
    if loader&3 or not MODULE_RAM+0x300<=loader<MODULE_RAM+LINKED_LIMIT:
        raise ValueError('Invalid quest reply resident loader')
    entry = (0x2CE8000C,0x11000016,0x00001025,0x27BDFFC0,0xAFBF003C,0x3C084146,
             0x35085152,0xAFA80020,0xA3A70024,0xA3A00025,0x97A80052,0xA7A80026,
             0xAFA00028,0xAFA0002C,0x240800F6,0xA3A80030,0xA3A00031,0x24080001,
             0xAFA00010,0xAFA80014,0x0C000000|((loader>>2)&0x3FFFFFF),0x27A70020,
             0x8FBF003C,0x27BD0040,0x03E00008,0)
    gate = (0x1040000C,0x8FA3003C,0x8FA80040,0x240900A4,0x00690019,0x00004812,
            0x01092021,0x24840478,0x0C02719F,0x27A5004C,0x240A0001,0xAFAA0038,0)
    data = bytearray(BLOB_BYTES)
    struct.pack_into('>'+str(len(entry))+'I',data,0,*entry)
    struct.pack_into('>'+str(len(gate))+'I',data,REGIONS[1][0]-START,*gate)
    return bytes(data)


def verify_code(code):
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM])!=digest:
            raise ValueError('Changed original quest reply, reward, grading, or delivery code')


def verify_caller(files,rom):
    caller = files[CALLER_VROM].extract(rom)
    if sha256(caller[CALLER_START-CALLER_RAM:CALLER_END-CALLER_RAM])!=CALLER_HASH:
        raise ValueError('Changed quest reply conversation result branch')


def validate(data,report,module):
    loader = int(module['symbols']['af_npc_mail_load'],16)
    if (data!=expected_image(loader) or report.get('version')!=1 or report.get('sources')!=sources()
            or report.get('sha256')!=sha256(data) or report.get('module_sha256')!=module['module_sha256']
            or report.get('loader_ram')!=loader or report.get('symbols')!={
                'quest_reply_entry':START,'quest_reply_end':START+104,
                'quest_reply_gate':REGIONS[1][0],'quest_reply_gate_end':END}):
        raise ValueError('Changed or stale complete quest reply wrapper or copy gate')
    return {start:data[start-START:end-START] for start,end in REGIONS}


def install(native,replacements,additions,module,directory):
    native = verified_rom(native)
    if not module or module.get('npc_mail_loader',{}).get('overlay',{}).get('quest_replies') is not True:
        raise ValueError('Quest replies require their complete creator dispatcher')
    if any(v not in additions for v in (MODULE_VROM,CREATOR_VROM,0x02A00000)):
        raise ValueError('Missing quest reply runtime, creator, or complete item names')
    verify_configuration(additions[MODULE_VROM],additions[CREATOR_VROM],module)
    verify_items(additions[MODULE_VROM],additions[0x02A00000])
    report = json.loads((directory/'owners.json').read_text());data = (directory/'owners.bin').read_bytes()
    changes = validate(data,report,module);files = by_vrom(native);verify_caller(files,native)
    caller = replacements.get(CALLER_VROM,files[CALLER_VROM].extract(native))
    if sha256(caller[CALLER_START-CALLER_RAM:CALLER_END-CALLER_RAM])!=CALLER_HASH:
        raise ValueError('Overlapping quest reply conversation patch')
    code = bytearray(replacements.get(CODE_VROM,files[CODE_VROM].extract(native)));verify_code(code)
    evidence = audit(native,creator_catalog.resource(additions,module))
    for at,value in changes.items(): code[at-CODE_RAM:at-CODE_RAM+len(value)] = value
    replacements[CODE_VROM] = bytes(code)
    return {**evidence,'installed':True,'complete_templates':list(TEMPLATES),'owners':report,
            'patches':[{'ram':f'{at:08X}','bytes':len(v),'sha256':sha256(v)} for at,v in changes.items()],
            'item_resource_sha256':sha256(additions[0x02A00000]),'new_resident_bytes':0,'creator_stack_bytes':64,
            'status':'Complete quest replies installed; native delivery and gameplay acceptance remain'}


def verify_installation(built,native,module,report):
    files = by_vrom(built)
    verify_configuration(files[MODULE_VROM].extract(built),files[CREATOR_VROM].extract(built),module)
    creator_catalog.verify_installation(built,module,report)
    if module['npc_mail_loader']['overlay'].get('quest_replies') is not True:
        raise ValueError('Quest reply dispatcher is not installed')
    verify_items(files[MODULE_VROM].extract(built),files[0x02A00000].extract(built),report['item_resource_sha256'])
    verify_caller(files,built)
    actual = bytearray(files[CODE_VROM].extract(built));original = by_vrom(native)[CODE_VROM].extract(native)
    data = bytearray(BLOB_BYTES)
    for start,end in REGIONS:
        data[start-START:end-START] = actual[start-CODE_RAM:end-CODE_RAM]
        actual[start-CODE_RAM:end-CODE_RAM] = original[start-CODE_RAM:end-CODE_RAM]
    changes = validate(bytes(data),report['owners'],module);verify_code(actual)
    expected = [{'ram':f'{at:08X}','bytes':len(v),'sha256':sha256(v)} for at,v in changes.items()]
    if (report.get('patches')!=expected or report.get('complete_templates')!=list(TEMPLATES)
            or report.get('caller_sha256')!=CALLER_HASH or report.get('paper')!=22):
        raise ValueError('Changed complete quest reply installation report')
