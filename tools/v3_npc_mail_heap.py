"""Connect the English NPC creator to the existing guarded scene allocator."""
import copy
import struct
import zlib

from aflib import by_vrom,sha256
from apply_translation import write_new
from runtime_layout import MODULE_RAM,MODULE_VROM
from v3_asset_loader import ROOT,compile_part
from v3_private_save_bank import refresh_aliases

RAM=0x804F3820
START,END,FAIL=0x80197DBC,0x80197DF0,0x80197F30
BEFORE=bytes.fromhex('3c027fe6244237203c0300260262102124633721'
    '0043102b104000563c0280093c028040005310230050102b144000513c028009')
SOURCES=('tools/v3_npc_mail_heap.py','overlays/v3/npc_mail_heap.c',
         'overlays/v3/npc_mail_heap.ld')


def patch():
    # Preserve s0=size, s3=allocation, and the loader's existing failure/cleanup.
    words=(0x02602025,0x0C000000|((RAM>>2)&0x3FFFFFF),0x02002825,
        0x10400000|((FAIL-(START+12+4))//4)&65535,0x3C028009,
        0x10000000|((END-(START+20+4))//4)&65535,0)
    return struct.pack('>7I',*words).ljust(END-START,b'\0')


def install(base,prior,module,output):
    e=copy.deepcopy(prior['equipment_resources']);scene=e['scene_arena']
    if (scene.get('npc_mail_heap') or not scene.get('installed') or
            module[START-MODULE_RAM:END-MODULE_RAM]!=BEFORE):
        raise ValueError('Changed complete NPC creator heap guard or scene allocation')
    old=copy.deepcopy(e['console_storage']['packet'])
    data=bytearray(base[old['physical']:old['physical']+old['bytes']])
    if sha256(data)!=old['sha256'] or old['ram']!=0x804DE200:
        raise ValueError('Changed complete scene startup packet')
    code,compiled=compile_part('npc_mail_heap',output/'npc_mail_heap')
    at=RAM-old['ram']
    if not code or len(code)>0x1E0 or any(data[at:at+0x1E0]):
        raise ValueError('Mail heap guard overlaps retained startup code or data')
    data[at:at+len(code)]=code
    replacement=dict(old,sha256=sha256(data),crc32=zlib.crc32(data))
    refresh_aliases(e,old,replacement)
    records=copy.deepcopy(prior['physical_resources'])
    record=next(r for r in records if r['id']==old['id']);record.update(replacement)
    module[START-MODULE_RAM:END-MODULE_RAM]=patch()
    scene['npc_mail_heap']=dict(installed=True,code=dict(compiled,ram=RAM),
        patch=dict(ram=START,before=BEFORE.hex(),after=patch().hex()),
        lower_end=0x80400000,upper_start=0x80400040,upper_end=0x8044FFF0,
        exclusive_borrow_required=True,complete_workspace_guards_required=True,
        mail_rules_changed=False,saved_format_changed=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'npc_mail_heap/installed.bin',code)
    return e,records,[(dict(record,previous_sha256=old['sha256']),bytes(data))]


def checked(image,report):
    e=report['equipment_resources'];scene=e['scene_arena']
    receipt=scene.get('npc_mail_heap')
    if not receipt or not receipt.get('installed'):
        raise ValueError('NPC creator does not accept checked scene allocations')
    files=by_vrom(image);module=files[MODULE_VROM].extract(image)
    packet=e['console_storage']['packet'];first=packet['physical']
    data=image[first:first+packet['bytes']];code=receipt['code'];at=RAM-packet['ram']
    if (sha256(data)!=packet['sha256'] or code['ram']!=RAM or
            not 0<code['bytes']<=0x1E0 or
            sha256(data[at:at+code['bytes']])!=code['sha256'] or
            module[START-MODULE_RAM:END-MODULE_RAM]!=patch() or
            receipt['patch']!=dict(ram=START,before=BEFORE.hex(),after=patch().hex()) or
            not receipt['exclusive_borrow_required'] or
            not receipt['complete_workspace_guards_required'] or
            receipt['mail_rules_changed'] or receipt['saved_format_changed']):
        raise ValueError('Changed installed NPC creator scene-allocation guard')
    return receipt
