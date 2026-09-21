"""Shared selected-surface reservation/application and full room identity."""
import copy
import struct
import zlib

from aflib import CODE_RAM, by_vrom, sha256
from v3_asset_loader import ROOT, MODULE_RAM, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, jump
from v3_npc_clothing import guard_incoming
from v3_npc_draw import relocation_offsets
from v3_surface_items import RAM, SIZE, TABLE, BOOT, BOOT_END, SOURCES as ITEM_SOURCES

SOURCES=ITEM_SOURCES+('tools/v3_surface_application.py','overlays/v3/save_runtime.c',
    'overlays/v3/save_runtime.h','overlays/v3/save_codec.h','overlays/v3/campsite_environment.S')
OWNER,RELOC,OWNER_RAM=0x846860,0x8476A0,0x80951A70
FUNCTIONS=(
    (0x80952444,0xF8,'07a00a2007df8fb6c887e47d915cf7c6d57443d64ff5b1470c10102fcae46104'),
    (0x8095253C,0x108,'376af96740c109b2f218fd80a2c479ca67a8721417d00d88e7ba87a626d1e3e0'),
    (0x8095267C,0x58,'2abfe3fddc2ed21722d2fe4d8890f836c555c9a44bcd2805479b009dc325c14c'),
    (0x809526D4,0x58,'348a568e0b5f4ef55b379e87101d543bee28b041fcb12b1cf535d1ca66043032'),
    (0x80951F14,0xD4,'e8f30d47c4374ac7124c3e2464b3a49fc48fd319c9c89a4d15a17592208ddd66'))


def words(*values):return struct.pack('>'+str(len(values))+'I',*values)


def patch_owner(data,reloc,symbols):
    for address,n,digest in FUNCTIONS:
        at=address-OWNER_RAM
        if sha256(data[at:at+n])!=digest:raise ValueError('Changed complete native surface action or home initializer')
    changes=[]
    for kind,at,end,base,queued,bank,identity,reg in (
            ('wall',0x809524A8,0x80952528,0x2700,0x1AC,0x17A,0x176,9),
            ('floor',0x809525A0,0x80952630,0x2600,0x1B4,0x178,0x174,10)):
        # Keep the native bank swap, complete DMA, saved-byte writes, and sounds.
        # s0 is callee-saved; all changed temporary registers are reloaded here.
        after=words(0x00602025,jump(symbols['af_v3_surface_allowed'])|0x04000000,
            0x24050000|base,0x10400000|((end-(at+16))//4),
            0x96000000|(reg<<16)|queued,0x24000000|(reg<<21)|(reg<<16)|((-base)&65535),
            0x86030000|bank,0xA6000000|(reg<<16)|identity)
        changes.append((at,after,'apply_'+kind))
    for kind,address in (('floor',0x8095267C),('wall',0x809526D4)):
        changes.append((address,words(jump(symbols['af_v3_surface_reserve_'+kind]),0),'reserve_'+kind))
    windows=[(a-OWNER_RAM,len(b)) for a,b,_ in changes]
    guard_incoming(data,struct.unpack_from('>I',reloc)[0],OWNER_RAM,windows)
    slots=relocation_offsets(reloc,len(data))
    if any(slots&set(range(a,a+n,4)) for a,n in windows):
        raise ValueError('Surface action patch overlaps native relocation')
    result=bytearray(data);records=[]
    for address,after,kind in changes:
        at=address-OWNER_RAM;before=data[at:at+len(after)];result[at:at+len(after)]=after
        records.append(dict(kind=kind,address=address,before=before.hex(),after=after.hex()))
    return bytes(result),records


def install(base,prior,blob,core,module,output):
    surface=copy.deepcopy(prior['room_surfaces']);items=surface['items']
    if surface.get('application'):raise ValueError('Surface application already installed')
    files=by_vrom(base);owner=files[OWNER].extract(base);reloc=files[RELOC].extract(base)
    existing=surface['owners'][0]
    if (existing['vrom']!=OWNER or sha256(owner)!=existing['sha256'] or
            sha256(reloc)!=existing['relocation_sha256']):
        raise ValueError('Changed complete current surface owner')
    at=items['blob_offset'];packet=bytearray(blob[at:at+SIZE])
    old=items['code'];table=packet[TABLE:TABLE+items['table_bytes']]
    if (items['ram']!=RAM or items['bytes']!=SIZE or sha256(packet)!=items['sha256'] or
            zlib.crc32(packet)!=items['crc32'] or sha256(packet[:old['bytes']])!=old['sha256'] or
            any(packet[old['bytes']:TABLE]) or sha256(table)!=items['table_sha256']):
        raise ValueError('Changed complete surface packet/code/metadata')
    code,compiled=compile_part('surface_items',output/'surface_items',defines=('AF_SURFACE_ROOM=1',))
    symbols=compiled['symbols']
    if (len(code)>TABLE or any(symbols.get(n)!=a for n,a in
            dict(af_surface_prior_floor=0x804A2F54,af_surface_field=0x80087C88,
                 af_surface_npc_floor=0x800AE558).items())):
        raise ValueError('Changed shared surface room bindings')
    packet[:TABLE]=code+bytes(TABLE-len(code));blob[at:at+SIZE]=packet
    for hook in items['hooks']:
        address=hook['address'];target=symbols['af_v3_surface_item_'+hook['kind']]
        data,ram=(module,MODULE_RAM) if address>=MODULE_RAM else (core,CODE_RAM)
        a=address-ram
        if (data[a:a+8].hex()!=hook['after'] or
                symbols['af_surface_prior_'+hook['kind']]!=hook['prior']):
            raise ValueError('Changed outer surface item dispatch')
        hook['before']=hook['after'];hook['after']=words(jump(target),0).hex();hook['target']=target
        data[a:a+8]=bytes.fromhex(hook['after'])
    changed,patches=patch_owner(owner,reloc,symbols)
    # Preserve the entire campsite floor/light wrapper, not merely its entry.
    environment=prior['campsite_environment']['code'];env_at=PACKAGE+0x804A2F54-PACKAGE_RAM
    if sha256(blob[env_at:env_at+environment['bytes']])!=environment['sha256']:
        raise ValueError('Changed complete campsite environment wrapper')
    floor=0x800BEEC4-CODE_RAM;before=bytes(core[floor:floor+8])
    if sha256(core[floor:floor+0x108])!='9ecf19205998ba63c613f17f4d91d851dffcfbb7974c6f3d47ab9e1705e7b308':
        raise ValueError('Changed complete native floor getter')
    after=words(jump(symbols['af_v3_surface_floor_index']),0);core[floor:floor+8]=after
    # Full-byte home fields live inside the native payload. No saved bit-field
    # is repurposed. Check current initialization and guarded payload-copy code.
    init=0x80094744-CODE_RAM
    if sha256(core[init:init+0x7C])!='82b7d2e308804f16ed877b60a8db56efe68f5d0f210f3b494a0f9ccd30f50368':
        raise ValueError('Changed complete native home defaults')
    saved=prior['save_runtime'];sc=saved['code'];save_at=sc['symbols']['af_v3_save_reset']-0x80460000
    if (saved['native_live_payload_bytes']!=0xF980 or
            sha256(blob[save_at:save_at+sc['bytes']])!=sc['sha256']):
        raise ValueError('Changed complete native saved-payload runtime')
    for patch in saved['patches']:
        a=patch['address']-CODE_RAM;value=bytes.fromhex(patch['after'])
        if core[a:a+len(value)]!=value:raise ValueError('Changed native saved-payload hook')
    copies=[]
    for address in (0x8008F9F0,0x8008FB84,0x80095820,0x800961F8):
        value=bytes(core[address-CODE_RAM:address-CODE_RAM+4])
        if value!=words(0x3406F980):raise ValueError('Changed complete native payload-copy size')
        copies.append(dict(address=address,word=value.hex()))
    equipment=copy.deepcopy(prior['equipment_resources']);ea=equipment['blob_offset']
    ep=bytearray(blob[ea:ea+equipment['bytes']]);ba=BOOT-equipment['ram'];be=BOOT_END-equipment['ram']
    boot_old=items['bootstrap']['code']
    if (sha256(ep)!=equipment['sha256'] or zlib.crc32(ep)!=equipment['crc32'] or
            sha256(ep[ba:ba+boot_old['bytes']])!=boot_old['sha256'] or
            any(ep[ba+boot_old['bytes']:be]) or ep[be:be+16]!=bytes.fromhex('AF48C0DE')*4):
        raise ValueError('Changed surface bootstrap or equipment packet')
    crc=zlib.crc32(packet)
    boot,boot_code=compile_part('surface_bootstrap',output/'surface_bootstrap',defines=(
        f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',f'AF_SURFACE_ITEMS_CRC=0x{crc:X}u'))
    if len(boot)>be-ba:raise ValueError('Surface bootstrap exceeds checked reservation')
    ep[ba:be]=boot+bytes(be-ba-len(boot));blob[ea:ea+len(ep)]=ep
    items.update(code=compiled,crc32=crc,sha256=sha256(packet),additional_resident_bytes=0,
        native_execution_tested=False)
    items['bootstrap']['code']=boot_code
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=items['bootstrap'])
    existing['sha256']=sha256(changed)
    surface['application']=dict(format='AFV3-SURFACE-APPLICATION-1',owner_vrom=OWNER,
        owner_ram=OWNER_RAM,relocation_vrom=RELOC,relocation_sha256=sha256(reloc),
        functions=[dict(address=a,bytes=n,sha256=h) for a,n,h in FUNCTIONS],patches=patches,
        floor_hook=dict(address=0x800BEEC4,before=before.hex(),after=after.hex()),
        campsite_code_sha256=environment['sha256'],saved_payload_bytes=0xF980,
        saved_home_offset=0x3588,home_stride=0xB48,home_count=4,floor_byte=0x14,wall_byte=0x15,
        saved_runtime_sha256=sc['sha256'],payload_copy_sizes=copies,
        application_installed=True,saved_format_changed=False,saved_profile_changed=False,
        profile_and_catalogue_pending=True,ordinary_save_reload_tested=False,native_execution_tested=False)
    surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return {OWNER:changed},dict(room_surfaces=surface,equipment_resources=equipment)
