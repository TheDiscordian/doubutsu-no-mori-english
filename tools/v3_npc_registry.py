"""Prepare additive NPC allocation/cleanup and complete drawing/voice dispatch.

The packet has inactive records and explicit actor callback fixups. Installation
must bind the complete actors, artwork banks, startup, and selections together.
No ROM or deployed patcher is modified by this preparation.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,BLOB,BLOB_RAM,compile_part
from v3_console_disk_install import reservations
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_import_storage import jump
from v3_npc_draw import OWNERS,relocation_offsets
from v3_npc_stream_runtime import native_records,patch_owners as stream_owners
from v3_registry import SPECIAL_NPCS,SPECIAL_NPC_REGISTRY_VERSION
import v3_physical_resources as physical
from v3_console_image_native import PI_SHA
from v3_keyframes import npc_motion,compile_animations

RAM,SIZE,TABLE,DESCRIPTOR,PROFILE,DRAW,STREAM,POOL=0x806E4000,0x10000,0xA000,0xA200,0xA220,0xA250,0xA2C0,0xC000
ACTOR_BYTES,SLOTS=0xA34,2
DMA=0xA300
CANE=0xB000
SOURCES=('tools/v3_npc_registry.py','tools/v3_registry.py','tools/v3_npc_stream_runtime.py',
    'tools/v3_asset_loader.py','overlays/v3/npc_registry.c','overlays/v3/npc_registry.h',
    'overlays/v3/npc_registry.ld','overlays/v3/npc_stream_draw.h','overlays/v3/npc_stream_draw.c',
    'tools/v3_furniture_install.py','tools/v3_room_goods.py','overlays/v3/surface_bootstrap.c',
    'overlays/v3/npc_dma.c','overlays/v3/npc_dma.h','tools/v3_keyframes.py')


def checked_memory(prior):
    if (RAM+SIZE>0x807DA800 or any(a<RAM+SIZE and RAM<b for a,b in reservations(prior))):
        raise ValueError('Additional NPC packet overlaps a retained allocation')
    return dict(ram=RAM,bytes=SIZE,installed=False,
        registry_code=dict(ram=RAM,bytes=0x2000),actor_code=dict(ram=RAM+0x2000,bytes=0x8000),
        records=dict(ram=RAM+TABLE,bytes=0x1000),
        pool=dict(ram=RAM+POOL,bytes=SLOTS*((ACTOR_BYTES+15&~15)+32)))


def packet(source,art):
    r=SPECIAL_NPCS['GAFE01-r0/npc/ev-soncho2']
    profile=source.raw('Ev_Soncho2_Profile')
    if (struct.unpack_from('>HHIHHI',profile)!=(r['donor_profile'],4<<8,0,r['donor_name'],3,0x9B0)
            or len(profile)!=36):raise ValueError('Changed complete donor holiday NPC profile')
    draw,stream,voice=native_records(source,art,r['name'],r['model_bank'],r['texture_bank'])
    if voice!=281:raise ValueError('Changed full Tortimer voice identity')
    stride=(ACTOR_BYTES+15&~15)+32
    data=bytearray(SIZE)
    struct.pack_into('>4I',data,TABLE,0x41464E58,1,1,44)
    struct.pack_into('>HH9I2H',data,TABLE+16,r['name'],r['profile'],0,ACTOR_BYTES,SLOTS,stride,
        RAM+POOL,RAM+DESCRIPTOR,RAM+DRAW,RAM+STREAM,voice,r['model_bank'],r['texture_bank'])
    # Resident descriptor: original actor deletion skips an overlay free. The
    # registry releases the new pool slot and its loaded count together.
    struct.pack_into('>8I',data,DESCRIPTOR,0,0,0,0,0,RAM+PROFILE,0,0)
    struct.pack_into('>HHIHH6I',data,PROFILE,r['profile'],3<<8,0,r['name'],3,ACTOR_BYTES,0,0,0,0,0)
    data[DRAW:DRAW+100]=draw;data[STREAM:STREAM+36]=stream
    motions=source.names.get('cKF_ba_r_npc_1_tue1',[])
    if len(motions)!=1:raise ValueError('Ambiguous complete cane motion')
    motion=npc_motion(source,motions[0][0],joints=26)
    cane,cane_report=compile_animations(source,[motion],start=CANE,address_base=RAM)
    if CANE+len(cane)>POOL:raise ValueError('Complete cane motion overlaps NPC slots')
    data[CANE:CANE+len(cane)]=cane
    for i in range(SLOTS):
        at=POOL+i*stride
        struct.pack_into('>4I',data,at,0x41464E53,0,r['name'],r['profile'])
        struct.pack_into('>4I',data,at+stride-16,*([0x4E504347]*4))
    data[-16:]=b'AFNX'*4
    return bytes(data),dict(identity=r,registry_version=SPECIAL_NPC_REGISTRY_VERSION,
        actor_bytes=ACTOR_BYTES,slots=SLOTS,slot_stride=stride,voice=voice,
        cane=dict(description=motion,conversion=cane_report,offset=CANE,bytes=len(cane),
            sha256=sha256(cane),header=RAM+cane_report['headers'][0]['native_offset'],runtime_bound=False),
        native_pool_bytes=2400,uses_native_pool=False,heap_fallback=False,
        # Drawing remains off until the native NPC init installs ctor_data.draw.
        profile_fixups=[dict(offset=PROFILE+offset,symbol='af_holiday_npc_'+name)
            for offset,name in ((16,'ctor'),(20,'dtor'),(24,'init'),(32,'save'))],
        flags_offset=TABLE+20,implemented=False,selected=False,
        model_bytes=art['model_bytes'],texture_bytes=art['texture_bytes'],
        draw_sha256=sha256(draw),stream_sha256=sha256(stream))


def patch_owners(base,prior,symbols=None):
    files=by_vrom(base);changes={};patches=[]
    def patch(vrom,ram,at,before,helper):
        data=changes.setdefault(vrom,bytearray(files[vrom].extract(base)));off=at-ram
        if data[off:off+len(before)]!=before:raise ValueError(f'Changed additional NPC hook {at:08X}')
        after=None
        if symbols is not None:
            target=symbols[helper]
            if target&3 or not RAM<=target<RAM+0x2000:raise ValueError('NPC dispatcher exceeds its linked reservation')
            after=struct.pack('>I',jump(target,link=True))
            # Native draw exports are entry jumps, not calls.
            if helper=='af_v3_npc_extra_draw':after=struct.pack('>I',jump(target))
            data[off:off+4]=after
        patches.append(dict(vrom=vrom,ram=ram,address=at,before=before.hex(),
            after=after.hex() if after else None,helper=helper,delay_slot_preserved=True))
    old=prior['asset']['symbols']
    balloon=prior['equipment_resources']['player_actions']['balloon_actor']['code']['symbols']['af_v3_balloon_descriptor']
    patch(CODE_VROM,CODE_RAM,0x80057E4C,struct.pack('>2I',jump(balloon,link=True),0x00C02025),'af_v3_npc_extra_descriptor')
    patch(CODE_VROM,CODE_RAM,0x80057EE4,bytes.fromhex('0c015f12afac0010'),'af_v3_npc_extra_allocate')
    patch(CODE_VROM,CODE_RAM,0x800583B8,bytes.fromhex('0320f80900000000'),'af_v3_npc_extra_free')
    for vrom,reloc,ram,draw,tail,frame,helper in OWNERS:
        rel=files[reloc].extract(base)
        if draw-ram in relocation_offsets(rel,files[vrom].size):
            raise ValueError('Additional draw dispatch overlaps a native relocation')
        patch(vrom,ram,draw,struct.pack('>2I',jump(old['af_v3_npc_draw']),0),'af_v3_npc_extra_draw')
        arg=0x58 if frame==0xC0 else 0x50
        patch(BLOB,BLOB_RAM,old[helper],struct.pack('>2I',jump(old['af_v3_npc_voice'],link=True),0x27A40000|arg),
            'af_v3_npc_extra_voice')
    return {k:bytes(v) for k,v in changes.items()},patches,dict(
        af_v3_npc_extras=RAM+TABLE,af_npc_previous_descriptor=balloon,
        af_npc_previous_allocate=0x80057C48,af_npc_allocation_failed=0x80057848,
        af_npc_previous_draw=old['af_v3_npc_draw'],af_npc_previous_voice=old['af_v3_npc_voice'],
        af_v3_npc_dma=RAM+DMA,af_npc_dma_previous=0x80026828,af_npc_dma_pi=0x80026500,
        af_npc_dma_error=0x800263F0,af_npc_dma_writeback=0x8002FE00,af_npc_dma_invalidate=0x80034CE0)


def prepare(lock,art_directory,output):
    base,prior=inputs(lock);layout=checked_memory(prior)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    art=json.loads((art_directory/'art.json').read_bytes())
    # Keep the finished model/texture files; this does not reconvert the artwork.
    for kind in ('model','texture'):
        raw=(art_directory/(kind+'.bin')).read_bytes()
        if len(raw)!=art[kind+'_bytes'] or sha256(raw)!=art[kind+'_sha256']:
            raise ValueError('Changed prepared complete NPC artwork: '+kind)
    data,record=packet(source,art);_,_,bindings=patch_owners(base,prior)
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored NPC output')
    output.mkdir(parents=True)
    code,compiled=compile_part('npc_registry',output/'code',link_symbols=bindings,
        extra_sources=('overlays/v3/npc_stream_draw.c','overlays/v3/npc_dma.c'))
    result=bytearray(data);result[:len(code)]=code
    changed,patches,_=patch_owners(base,prior,compiled['symbols'])
    rendered,render_hooks=stream_owners(base,compiled['symbols']['af_v3_npc_stream_draw'])
    for h in render_hooks:
        vrom=h['vrom'];at=h['call']-h['ram'];raw=bytearray(changed[vrom])
        raw[at:at+4]=rendered[vrom][at:at+4];changed[vrom]=bytes(raw)
    # Proposed changed owner files stay local and cannot alone enable the actor.
    for vrom,raw in changed.items():write_new(output/f'owner-{vrom:08x}.bin',raw)
    write_new(output/'packet.bin',result)
    report=dict(format='AFV3-NPC-REGISTRY-1',base_abi=prior['runtime_abi'],base_sha256=sha256(base),
        memory=layout,record=record,code=compiled,bindings=bindings,hooks=patches,
        render_hooks=render_hooks,packet_sha256=sha256(result),runtime_installed=False,
        object_banks_installed=False,actor_callbacks_bound=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'registry.json',(json.dumps(report,indent=2)+'\n').encode());return report


def install_banks(base,prior,blob,art_directory):
    """Append complete art and extend only the two reserved table entries.

    The existing helper contains later voice/audio edits. Retain those bytes;
    change only its verified object-status bound and the matching blob header.
    The shared builder compiles the corresponding startup capacity together.
    """
    if prior['object_capacity']!=448 or struct.unpack_from('>I',blob,12)[0]!=448:
        raise ValueError('Changed additional NPC object-table capacity')
    start=prior['asset']['symbols']['af_v3_object_status']-BLOB_RAM
    if blob[start:start+16]!=bytes.fromhex('00063c0000073c032ce301c01060002b'):
        raise ValueError('Changed complete native object-status bounds prefix')
    if any(blob[0x1E00:0x1E10]):raise ValueError('New NPC banks overwrite existing table data')
    files=by_vrom(base);boot=files[0x1060].extract(base)
    contracts=((0x80026500,0x800266C4,PI_SHA),
        (0x800269E4,0x80026A64,'62a632b542b21e2894e796994d446f63a77723f7c97f3ded2d9fbfd6c0d0cdb9'),
        (0x80026828,0x800269E4,'d942b1364e90687253721fdca5f2c6398025f3a760cbbfd7649b66e0740a4da8'))
    for a,b,digest in contracts:
        if sha256(boot[a-0x80025C60:b-0x80025C60])!=digest:
            raise ValueError('Changed complete native NPC transfer consumer')
    art=json.loads((art_directory/'art.json').read_bytes());records=[]
    staging=bytearray(base);physical_rows=copy.deepcopy(prior.get('physical_resources',[]));writes=[]
    for kind,bank,limit in (('model',448,0x2800),('texture',449,0x1620)):
        data=(art_directory/(kind+'.bin')).read_bytes()
        if (len(data)!=art[kind+'_bytes'] or sha256(data)!=art[kind+'_sha256'] or
                len(data)>limit or len(data)&15):raise ValueError('Invalid complete additional NPC '+kind)
        vrom=0x03FE0000+(bank-448)*0x4000
        if any(e.vstart<vrom+len(data) and vrom<e.vend for e in files.values()):
            raise ValueError('New NPC bank overlaps existing virtual resource')
        row=physical.allocate(staging,physical_rows,data,'npc-'+kind+'-GAFE01-r0');physical_rows.append(row)
        staging[row['physical']:row['physical']+len(data)]=data;writes.append((row,data))
        struct.pack_into('>2I',blob,0x1000+bank*8,vrom,vrom+len(data))
        records.append(dict(row,bank=bank,kind=kind,vrom=vrom,native_buffer_bytes=limit))
    struct.pack_into('>I',blob,12,450);struct.pack_into('>I',blob,start+8,0x2CE301C2)
    asset=copy.deepcopy(prior['asset'])
    asset['sha256']=sha256(blob[0x100:0x100+asset['bytes']])
    asset['flags']=[f.replace('AF_V3_OBJECT_CAPACITY=448','AF_V3_OBJECT_CAPACITY=450') for f in asset['flags']]
    asset['npc_capacity_patch']=dict(address=BLOB_RAM+start+8,before='2ce301c0',after='2ce301c2',
        previous_sha256=prior['asset']['sha256'],retained_existing_hooks=True)
    return records,asset,physical_rows,writes,staging


def install(base,prior,blob,core,output,art_directory,lock):
    """Connect guarded memory, banks, renderers, and cleanup in the shared build.

    The record remains inactive until event/conversation services bind its actor
    callbacks. Merely installing its resources cannot enable unfinished gameplay.
    """
    prepared=prepare(lock,art_directory,output/'npc-registry')
    equipment=copy.deepcopy(prior['equipment_resources'])
    if equipment.get('npc_extra'):raise ValueError('Additional NPC registry already installed')
    files=by_vrom(base);changed={}
    # Apply only declared instructions to current shared buffers. Never replace
    # a buffer with an old full copy after another builder has changed it.
    for h in prepared['hooks']:
        vrom=h['vrom'];at=h['address']-h['ram']
        target=blob if vrom==BLOB else core if vrom==CODE_VROM else changed.setdefault(vrom,bytearray(files[vrom].extract(base)))
        before=bytes.fromhex(h['before'])
        if target[at:at+len(before)]!=before:raise ValueError('Changed NPC hook while installing')
        target[at:at+4]=bytes.fromhex(h['after'])
    render_target=prepared['code']['symbols']['af_v3_npc_stream_draw']
    for h in prepared['render_hooks']:
        at=h['call']-h['ram'];target=changed[h['vrom']]
        if target[at:at+8]!=bytes.fromhex('0c11cc40afa80014'):raise ValueError('Changed complete NPC rendering call')
        struct.pack_into('>I',target,at,jump(render_target,link=True))
    banks,asset,records,writes,staging=install_banks(base,prior,blob,art_directory)
    data=bytearray((output/'npc-registry/packet.bin').read_bytes())
    if sha256(data)!=prepared['packet_sha256']:raise ValueError('Changed complete NPC registry packet')
    struct.pack_into('>4I',data,DMA,0x41464E44,1,len(banks),12)
    for i,b in enumerate(banks):struct.pack_into('>3I',data,DMA+16+i*12,b['vrom'],b['vrom']+b['bytes'],b['physical'])
    data=bytes(data);record=physical.allocate(staging,records,data,'npc-extra-GAFE01-r0');records.append(record)
    write_new(output/'npc-registry/installed-packet.bin',data)
    equipment['npc_extra']=dict(format='AFV3-NPC-INSTALLED-1',
        packet=dict(record,ram=RAM,crc32=zlib.crc32(data),storage='physical-ROM'),
        memory=prepared['memory'],record=prepared['record'],code=prepared['code'],
        hooks=prepared['hooks'],render_hooks=prepared['render_hooks'],banks=banks,
        installed=True,actor_callbacks_bound=False,selectable=False,native_execution_tested=False,
        pending=['Event owner and actor providers','Cane motion and walking-only schedule',
                 'English messages and demo transport','Separate exercise/card route'],
        sources=prepared['sources'])
    equipment['npc_extra']['memory']['installed']=True
    updates=dict(physical_resources=records,object_capacity=450,asset=asset)
    return equipment,{k:bytes(v) for k,v in changed.items()},updates,[*writes,(record,data)]


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lock',type=Path,required=True);p.add_argument('--art',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=prepare(a.lock,a.art,a.output)
    print(json.dumps(dict(bytes=r['code']['bytes'],sha256=r['code']['sha256'],
        record=r['record'],runtime_installed=False),indent=2))
