"""Atomic experimental installation of the complete cartridge NPC reply creator."""

import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256
from mail_catalog import VROM as CATALOG_VROM,verify_registered
from mail_view_patch import install as install_reader
from npc_mail_capture import validate,call_patches
from npc_mail_delivery import START,END,patch as delivery_patch
from runtime_layout import MODULE_RAM,MODULE_VROM,RESERVATION,LINKED_LIMIT

VROM,CONFIG_OFFSET,CONFIG_BYTES,ABI,WORK_BYTES = 0x03200000,0x48,32,0x41464E01,5344


def configuration(data,reloc,report,module):
    validate(data,reloc,report,module)
    if len(reloc) < 32 or len(reloc)&15:
        raise ValueError('NPC creator relocation blob must be DMA aligned')
    entry = 'af_system_mail_create' if report.get('mother_letters') else 'af_npc_mail_create'
    if report.get('departed_letters'): entry = 'af_departed_mail_create'
    if report.get('villager_events'): entry = 'af_villager_event_mail_create'
    if report.get('academy_letters'): entry = 'af_academy_mail_create'
    if report.get('academy_scores'): entry = 'af_academy_score_mail_create'
    if report.get('post_office'): entry = 'af_post_office_mail_create'
    if report.get('museum'): entry = 'af_museum_mail_create'
    if report.get('shop_notices'): entry = 'af_shop_notice_mail_create'
    if report.get('quest_replies'): entry = 'af_quest_reply_mail_create'
    if report.get('notice_treasure'): entry = 'af_notice_treasure_create'
    return [VROM,len(data)+len(reloc),len(data),len(reloc),report['symbols'][entry],
            struct.unpack_from('>I',reloc)[0],zlib.crc32(data+reloc),ABI]


def verify_configuration(module_data,blob,module):
    """Native symbol checks need the build's external approval, not a self-CRC.

    The ordinary compiler report has no approval. Configured test ROMs use the
    enriched runtime-module.json written by the final ROM builder instead.
    """
    approval = module.get('npc_mail_loader')
    if not isinstance(approval,dict) or not isinstance(approval.get('configuration'),list):
        raise ValueError('NPC creator configuration requires the configured build report')
    expected = approval['configuration']
    if (len(expected) != 8 or any(type(value) is not int or not 0 <= value <= 0xFFFFFFFF for value in expected)
            or len(blob) != expected[1] or not 0 < expected[2] <= len(blob)
            or sha256(blob) != approval.get('blob_sha256')):
        raise ValueError('Changed approved NPC creator configuration or blob')
    actual = configuration(blob[:expected[2]],blob[expected[2]:],approval['overlay'],module)
    if actual != expected or module_data[CONFIG_OFFSET:CONFIG_OFFSET+CONFIG_BYTES] != struct.pack('>8I',*actual):
        raise ValueError('NPC creator configuration does not match its verified image')


def install(rom,replacements,additions,module,directory,*,glyph_font=None):
    from runtime_module import runtime_source_hashes
    if (not module or MODULE_VROM not in additions or module.get('source_sha256') != sha256(rom)
            or module.get('runtime_sources') != runtime_source_hashes(Path(__file__).resolve().parents[1]/'runtime')):
        raise ValueError('NPC cartridge creation requires the current verified resident module')
    binary = bytearray(additions[MODULE_VROM])
    if len(binary) != RESERVATION:
        raise ValueError('NPC cartridge creation requires the unchanged module reservation')
    baseline = bytearray(binary)
    for offset,vrom in ((56,0x02A00000),(60,0x02C00000),(64,0x02E00000),(68,CATALOG_VROM)):
        value = struct.unpack_from('>I',baseline,offset)[0]
        if value and (value != vrom or value not in additions):
            raise ValueError('Unverified preceding NPC creator resource configuration')
        baseline[offset:offset+4] = bytes(4)
    if sha256(baseline) != module['module_sha256'] or module.get('npc_mail_loader') or VROM in additions:
        raise ValueError('Changed or duplicate NPC creator module configuration')
    if struct.unpack_from('>I',binary,68)[0] != CATALOG_VROM or CATALOG_VROM not in additions:
        raise ValueError('NPC cartridge creation requires the complete English catalog')
    verify_registered(additions[CATALOG_VROM])
    expected_reader = {}
    install_reader(rom,expected_reader,{MODULE_VROM:bytes(baseline)},module,snapshots=True)
    if any(replacements.get(vrom) != data for vrom,data in expected_reader.items()):
        raise ValueError('NPC cartridge creation requires the complete installed snapshot reader')
    report = json.loads((directory/'overlay.json').read_text())
    data,reloc = (directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes()
    approved = configuration(data,reloc,report,module)
    if report.get('notice_treasure'):
        from item_articles import verify_names
        verify_names(additions.get(0x02A00000, b''), struct.unpack_from('>I', binary, 56)[0])
    if report.get('mail_glyphs'):
        from extended_font_cartridge import mail_capability
        from mail_creator_catalog import identity,vrom
        if glyph_font is None or identity(additions.get(vrom(4),b'')) != 4:
            raise ValueError('Glyph creator requires catalogue four and its complete cartridge font')
        glyph_font_hash = mail_capability(glyph_font)
    blob = data+reloc
    files = by_vrom(rom)
    intervals = [(entry.vstart,entry.vend) for entry in files.values()]
    intervals += [(start,start+len(value)) for start,value in additions.items()]
    if any(start < VROM+len(blob) and VROM < end for start,end in intervals):
        raise ValueError('NPC creator cartridge range overlaps an existing resource')
    first = DMA_START+len(files)*16
    end = first+(len(additions)+2)*16  # Existing additions, creator, and terminator.
    if end > DMA_END or rom[first:end] != bytes(end-first):
        raise ValueError('NPC creator requires unused DMA rows and a retained terminator')
    code = bytearray(replacements.get(CODE_VROM,files[CODE_VROM].extract(rom)))
    hooks = call_patches(code,module)  # Complete seven-function and table guards.
    target = int(module['symbols'].get('af_npc_mail_load','0'),16)
    if target&3 or not MODULE_RAM+0x300 <= target < MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT):
        raise ValueError('NPC cartridge loader target is outside resident code')
    delivery = delivery_patch(bytes(code[START-CODE_RAM:END-CODE_RAM]),target)
    for at,before,after in hooks:
        if code[at-CODE_RAM:at-CODE_RAM+4] != before: raise ValueError('Overlapping NPC capture installation')
        code[at-CODE_RAM:at-CODE_RAM+4] = after
    code[START-CODE_RAM:END-CODE_RAM] = delivery
    struct.pack_into('>8I',binary,CONFIG_OFFSET,*approved)
    approval = {'configuration':approved,'blob_sha256':sha256(blob),'overlay':report}
    if report.get('mail_glyphs'): approval['glyph_font_sha256'] = glyph_font_hash
    # Publish only after all resource, dependency, native-code, and target checks.
    replacements[CODE_VROM] = bytes(code)
    additions[MODULE_VROM],additions[VROM] = bytes(binary),blob
    module['npc_mail_loader'] = approval
    return {**approval,'vrom':f'{VROM:08X}','loader_ram':f'{target:08X}',
            'configuration_ram':f'{MODULE_RAM+CONFIG_OFFSET:08X}',
            'temporary_allocation_bytes':len(blob)+WORK_BYTES+15,
            'capture_calls':[f'{at:08X}' for at,_,_ in hooks],
            'delivery_sha256':sha256(delivery),'configured_module_sha256':sha256(binary),
            'status':'Experimental NPC reply generation; normal gameplay, source review, and hardware acceptance remain'}
