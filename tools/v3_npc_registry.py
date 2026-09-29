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
    return append_banks(base,prior,blob,[dict(identity='GAFE01-r0/npc/ev-soncho2',
        directory=art_directory,model_bank=448,texture_bank=449)])


def append_banks(base,prior,blob,entries):
    """Append a complete batch using its fixed, independently reserved banks.

    The existing helper contains later voice/audio edits. Retain those bytes;
    change only its verified object-status bound and the matching blob header.
    The shared builder compiles the corresponding startup capacity together.
    """
    capacity=prior['object_capacity'];end=capacity+len(entries)*2
    wanted=sorted(e[k] for e in entries for k in ('model_bank','texture_bank'))
    if (not entries or not 448<=capacity<end<=460 or wanted!=list(range(capacity,end)) or
            struct.unpack_from('>I',blob,12)[0]!=capacity):
        raise ValueError('Changed additional NPC object-table capacity')
    start=prior['asset']['symbols']['af_v3_object_status']-BLOB_RAM
    expected=struct.pack('>4I',0x00063C00,0x00073C03,0x2CE30000|capacity,0x1060002B)
    if blob[start:start+16]!=expected:
        raise ValueError('Changed complete native object-status bounds prefix')
    if any(blob[0x1000+capacity*8:0x1000+end*8]):raise ValueError('New NPC banks overwrite existing table data')
    files=by_vrom(base);boot=files[0x1060].extract(base)
    contracts=((0x80026500,0x800266C4,PI_SHA),
        (0x800269E4,0x80026A64,'62a632b542b21e2894e796994d446f63a77723f7c97f3ded2d9fbfd6c0d0cdb9'),
        (0x80026828,0x800269E4,'d942b1364e90687253721fdca5f2c6398025f3a760cbbfd7649b66e0740a4da8'))
    for a,b,digest in contracts:
        if sha256(boot[a-0x80025C60:b-0x80025C60])!=digest:
            raise ValueError('Changed complete native NPC transfer consumer')
    records=[];resources=[]
    for entry in entries:
        directory=entry['directory'];art=json.loads((directory/'art.json').read_bytes())
        for kind,limit in (('model',0x2800),('texture',0x1620)):
            resources.append((kind,entry[kind+'_bank'],limit,directory,art,entry['identity']))
    staging=bytearray(base);physical_rows=copy.deepcopy(prior.get('physical_resources',[]));writes=[]
    old_banks=prior.get('equipment_resources',{}).get('npc_extra',{}).get('banks',[])
    for kind,bank,limit,directory,art,identity in sorted(resources,key=lambda row:row[1]):
        data=(directory/(kind+'.bin')).read_bytes()
        if (len(data)!=art[kind+'_bytes'] or sha256(data)!=art[kind+'_sha256'] or
                len(data)>limit or len(data)&15):raise ValueError('Invalid complete additional NPC '+kind)
        # The original eight additional banks end before the extended audio
        # archive at 04000000..04800000. Keep those published identities and
        # reserve subsequent banks beyond the complete audio reservation.
        vrom=(0x03FE0000+(bank-448)*0x4000 if bank<456 else
              0x04800000+(bank-456)*0x4000)
        if any(e.vstart<vrom+len(data) and vrom<e.vend for e in files.values()):
            raise ValueError('New NPC bank overlaps existing virtual resource')
        if any(e['vrom']<vrom+len(data) and vrom<e['vrom']+e['bytes'] for e in old_banks):
            raise ValueError('New NPC bank overlaps a retained additional bank')
        suffix='GAFE01-r0' if bank<450 else identity.replace('/','-')
        row=physical.allocate(staging,physical_rows,data,'npc-'+kind+'-'+suffix,best_fit=True);physical_rows.append(row)
        staging[row['physical']:row['physical']+len(data)]=data;writes.append((row,data))
        struct.pack_into('>2I',blob,0x1000+bank*8,vrom,vrom+len(data))
        records.append(dict(row,bank=bank,kind=kind,vrom=vrom,native_buffer_bytes=limit,identity=identity))
    struct.pack_into('>I',blob,12,end);struct.pack_into('>I',blob,start+8,0x2CE30000|end)
    asset=copy.deepcopy(prior['asset'])
    asset['sha256']=sha256(blob[0x100:0x100+asset['bytes']])
    asset['flags']=[f.replace(f'AF_V3_OBJECT_CAPACITY={capacity}',f'AF_V3_OBJECT_CAPACITY={end}') for f in asset['flags']]
    asset['npc_capacity_patch']=dict(address=BLOB_RAM+start+8,before=f'{0x2CE30000|capacity:08x}',after=f'{0x2CE30000|end:08x}',
        previous_sha256=prior['asset']['sha256'],retained_existing_hooks=True)
    return records,asset,physical_rows,writes,staging


def install_art_batch(base,prior,blob,output,directory,*,core=None,module=None):
    """Install every prepared character's banks without claiming actor readiness."""
    raw=(directory/'batch.json').read_bytes();batch=json.loads(raw)
    if batch.get('format')=='AFV3-NPC-NATIVE-BATCH-1':
        from v3_npc_native import install_batch
        return install_batch(base,prior,output,batch,raw,core=core,module=module)
    if batch.get('format')=='AFV3-NPC-VARIANT-BATCH-1':
        return install_variant_batch(base,prior,output,batch,raw)
    if batch.get('format')!='AFV3-NPC-ART-BATCH-1' or not batch.get('records'):
        raise ValueError('Expected a complete additional character art batch')
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra']
    if not npc.get('renderer_capabilities',{}).get('absent_expressions'):
        raise ValueError('Additional art needs the complete shared character renderer')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    prepared=npc.setdefault('prepared_characters',{});entries=[];receipts=[]
    for row in batch['records']:
        identity=row['identity']
        if identity not in SPECIAL_NPCS or identity in prepared:
            raise ValueError('Unknown or already prepared additional character')
        reservation=SPECIAL_NPCS[identity];art_directory=(ROOT/row['art']).resolve()
        if not art_directory.is_relative_to(ROOT/'build'):raise ValueError('Character artwork must stay local')
        art_raw=(art_directory/'art.json').read_bytes();art=json.loads(art_raw)
        if art['draw_index']!=reservation['draw_index']:raise ValueError('Character artwork identity mismatch')
        draw,stream,voice=native_records(source,art,reservation['name'],reservation['model_bank'],reservation['texture_bank'])
        prepared[identity]=dict(identity=reservation,registry_version=SPECIAL_NPC_REGISTRY_VERSION,
            art=str(art_directory.relative_to(ROOT)),art_sha256=sha256(art_raw),draw_hex=draw.hex(),
            stream_hex=stream.hex(),voice=voice,model_bytes=art['model_bytes'],texture_bytes=art['texture_bytes'],
            banks_installed=True,actor_installed=False,selectable=False,native_execution_verified=False)
        entries.append(dict(identity=identity,directory=art_directory,**reservation));receipts.append(identity)
    banks,asset,records,writes,staging=append_banks(base,prior,blob,entries)
    old=copy.deepcopy(npc['packet']);data=bytearray(base[old['physical']:old['physical']+old['bytes']])
    old_banks=npc['banks'];all_banks=old_banks+banks
    expected=struct.pack('>4I',0x41464E44,1,len(old_banks),12)+b''.join(
        struct.pack('>3I',b['vrom'],b['vrom']+b['bytes'],b['physical']) for b in old_banks)
    if (sha256(data)!=old['sha256'] or data[DMA:DMA+len(expected)]!=expected or
            any(data[DMA+len(expected):DMA+16+len(all_banks)*12])):
        raise ValueError('Changed complete shared character transfer directory')
    struct.pack_into('>I',data,DMA+8,len(all_banks))
    for i,b in enumerate(banks,len(old_banks)):
        struct.pack_into('>3I',data,DMA+16+i*12,b['vrom'],b['vrom']+b['bytes'],b['physical'])
    npc['banks']=all_banks;npc['packet'].update(sha256=sha256(data),crc32=zlib.crc32(data))
    record=next(r for r in records if r['id']==old['id']);record['sha256']=sha256(data)
    writes.append((dict(record,previous_sha256=old['sha256']),bytes(data)))
    receipt=dict(format=batch['format'],manifest_sha256=sha256(raw),characters=receipts,
        banks=banks,additional_resident_bytes=0,actor_admission_changed=False,saved_format_changed=False)
    npc.setdefault('art_batches',[]).append(receipt)
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    work=output/'npc-art-batch';work.mkdir()
    write_new(work/'installed.json',(json.dumps(receipt,indent=2)+'\n').encode())
    write_new(work/'packet.bin',data)
    return equipment,{},dict(physical_resources=records,object_capacity=prior['object_capacity']+len(banks),asset=asset),writes


def install_variant_batch(base,prior,output,batch,manifest):
    """Share complete actor implementations across source-equivalent appearances.

    Append code/data to the existing startup packet and redirect old public
    entries. No caller, saved layout, native pool, or accepted artwork is replaced.
    """
    from v3_console_disk_install import reservations
    from v3_holiday_placement import NAMES
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra']
    if npc.get('variants') or not batch.get('records'):raise ValueError('Expected a new complete variant batch')
    events=npc['events'];sky=events['sky'];participants=events['participants']
    old_packet=copy.deepcopy(sky['packet']);prefix=base[old_packet['physical']:old_packet['physical']+old_packet['bytes']]
    start=old_packet['ram']+old_packet['bytes']
    if sha256(prefix)!=old_packet['sha256'] or participants['packet']!=old_packet:
        raise ValueError('Changed complete participant packet before variant append')
    packet=npc['packet'];original=base[packet['physical']:packet['physical']+packet['bytes']];data=bytearray(original)
    if sha256(data)!=packet['sha256'] or struct.unpack_from('>4I',data,TABLE)!=(0x41464E58,1,1,44):
        raise ValueError('Changed complete additional character registry')
    if u32_local(data,TABLE+20):raise ValueError('Cannot extend an active unfinished holiday category')
    work=output/'npc-variants';work.mkdir();members=[];names={npc['record']['identity']['name']:npc['record']['identity']['profile']}
    for row in batch['records']:
        identity=row['identity'];member=npc['prepared_characters'].get(identity)
        if (not member or member['actor_installed'] or row['base']!='GAFE01-r0/npc/ev-soncho2' or
                type(row['slots']) is not int or not 1<=row['slots']<=16 or
                member['identity']!=SPECIAL_NPCS[identity] or
                member['identity']['donor_profile']!=npc['record']['identity']['donor_profile']):
            raise ValueError('Variant lacks prepared art or the complete shared actor implementation')
        r=member['identity']
        if r['name'] in names or r['profile'] in names.values():raise ValueError('Duplicate variant identity')
        names[r['name']]=r['profile'];members.append((identity,member,row['slots']))
    if 1+len(members)>8:raise ValueError('Variant batch exceeds shared actor registry')
    # Preserve the native controllers' narrow at/t1 scratch-register ABI and
    # profile result at sp+56. Unmatched names retain their original row pointer.
    assembly=['.set noreorder','.set noat','.set nomacro','.text',
        '.globl af_npc_variant_spawn','af_npc_variant_spawn:']
    for i,(name,profile) in enumerate(sorted(names.items())):
        assembly.extend((f'ori $at,$zero,{name}',f'bne $at,$v1,.Lnext{i}',' nop',
            f'addiu $t1,$zero,{profile}','jr $ra',' sh $t1,0x56($sp)',f'.Lnext{i}:'))
    previous=participants['code']['symbols']['af_hp_spawn_profile']
    assembly.extend(('j af_npc_variant_previous_spawn',' nop'))
    spawn=work/'spawn.S';write_new(spawn,('\n'.join(assembly)+'\n').encode())
    appended=bytearray(0x5000);refreshed={}
    for kind,at,old_at,limit,extra in (
        ('motion',0,0x2000,0x1000,('overlays/v3/holiday_motion_native.c',
            'overlays/v3/holiday_motion_original.S',str(spawn.relative_to(ROOT)))),
        ('world',0x1000,0x4000,0x4000,('overlays/v3/holiday_rewards.c','overlays/v3/holiday_talk.c',
            'overlays/v3/holiday_actor.c','overlays/v3/diary_calendar.c'))):
        old=npc[kind]['code'];links=dict(old['link_symbols'])
        links['HOLIDAY_'+kind.upper()+'_BASE']=start+at
        if kind=='motion':links['af_npc_variant_previous_spawn']=previous
        code,compiled=compile_part('holiday_'+kind,work/kind,link_symbols=links,extra_sources=extra)
        if len(code)>limit or sha256(data[old_at:old_at+old['bytes']])!=old['sha256']:
            raise ValueError('Changed or overflowing complete shared actor module')
        appended[at:at+len(code)]=code;redirects=[]
        symbols=old['symbols'];addresses=sorted(set(v for v in symbols.values() if RAM+old_at<=v<RAM+old_at+old['bytes']))
        for name,address in symbols.items():
            if not name.startswith('af_') or not RAM+old_at<=address<RAM+old_at+old['bytes']:continue
            target=compiled['symbols'].get(name)
            following=next((v for v in addresses if v>address),RAM+old_at+old['bytes'])
            if target is None or not start+at<=target<start+at+len(code) or following-address<8:
                raise ValueError('Cannot preserve complete actor public entry: '+name)
            pos=address-RAM;before=bytes(data[pos:pos+8]);after=struct.pack('>2I',jump(target),0)
            data[pos:pos+8]=after;redirects.append(dict(name=name,address=address,target=target,before=before.hex(),after=after.hex()))
        old.update(sha256=sha256(data[old_at:old_at+old['bytes']]),variant_redirects=redirects)
        refreshed[kind]=dict(ram=start+at,bytes=len(code),sha256=sha256(code),code=compiled,redirects=redirects)
    installed=[];callbacks=npc['lifecycle']['code']['symbols']
    for index,(identity,member,slots) in enumerate(members,1):
        r=member['identity'];offset=len(appended);descriptor=start+offset;profile=descriptor+32
        draw=profile+48;stream=draw+112;area=stream+48;stride=npc['record']['slot_stride']
        chunk=bytearray(240+slots*stride)
        struct.pack_into('>8I',chunk,0,0,0,0,0,0,profile,0,0)
        struct.pack_into('>HHIHH6I',chunk,32,r['profile'],3<<8,0,r['name'],3,ACTOR_BYTES,
            callbacks['af_holiday_npc_ctor'],callbacks['af_holiday_npc_dtor'],callbacks['af_holiday_npc_init'],0,
            callbacks['af_holiday_npc_save'])
        chunk[80:180]=bytes.fromhex(member['draw_hex']);chunk[192:228]=bytes.fromhex(member['stream_hex'])
        for i in range(slots):
            pos=240+i*stride
            struct.pack_into('>4I',chunk,pos,0x41464E53,0,r['name'],r['profile'])
            struct.pack_into('>4I',chunk,pos+stride-16,*([0x4E504347]*4))
        at=TABLE+16+index*44
        if any(data[at:at+44]):raise ValueError('Variant record overwrites retained registry data')
        struct.pack_into('>HH9I2H',data,at,r['name'],r['profile'],0,ACTOR_BYTES,slots,stride,
            area,descriptor,draw,stream,member['voice'],r['model_bank'],r['texture_bank'])
        appended.extend(chunk)
        member.update(actor_installed=True,active=False,descriptor=descriptor,profile=profile,
            slots=slots,slot_stride=stride,pool_ram=area,flags_offset=at+4,
            callback_family='Ev_Soncho2',actor_bytes=ACTOR_BYTES)
        installed.append(identity)
    struct.pack_into('>I',data,TABLE+8,1+len(members))
    # This shared owner table explicitly distinguishes normal/costume placement.
    for _,member,_ in members:
        if member['identity']['donor_name']==0xD079:
            at=NAMES-RAM+2
            if data[at:at+2]!=bytes(2):raise ValueError('Changed costume owner identity')
            struct.pack_into('>H',data,at,member['identity']['name'])
    appended.extend(b'AFNV'*4);end=start+len(appended)
    if end>0x807DA800 or any(a<end and start<b for a,b in reservations(prior)):
        raise ValueError('Shared actor variants overlap retained native memory')
    files=by_vrom(base);changes={};hooks=[];target=refreshed['motion']['code']['symbols']['af_npc_variant_spawn']
    for hook in participants['installed_hooks']:
        if hook['replacement']!='af_hp_spawn_profile':continue
        vrom=hook['vrom'];owner=bytearray(files[vrom].extract(base));at=hook['address']-hook['ram']
        before=bytes.fromhex(hook['after']);after=struct.pack('>I',jump(target,link=True))
        if len(before)!=4 or owner[at:at+4]!=before:raise ValueError('Changed shared NPC spawn hook')
        owner[at:at+4]=after;changes[vrom]=bytes(owner)
        hooks.append(dict(hook,before=before.hex(),after=after.hex(),replacement='af_npc_variant_spawn'))
    if len(hooks)!=2:raise ValueError('Incomplete shared NPC spawn binding')
    combined=prefix+appended;records=copy.deepcopy(prior['physical_resources'])
    write=physical.grow_backwards(base,records,old_packet['id'],combined)
    fresh={k:write[k] for k in ('id','physical','bytes','sha256')}
    records=[fresh if r['id']==old_packet['id'] else r for r in records]
    new=dict(fresh,ram=old_packet['ram'],crc32=zlib.crc32(combined),storage='physical-ROM')
    sky['packet']=copy.deepcopy(new);participants['packet']=copy.deepcopy(new)
    previous_npc=packet['sha256'];packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    record=next(r for r in records if r['id']==packet['id']);record['sha256']=sha256(data)
    sources=(*SOURCES,'tools/v3_holiday_placement.py','tools/v3_asset_loader.py',
        'overlays/v3/holiday_motion.c','overlays/v3/holiday_motion.ld',
        'overlays/v3/holiday_world.c','overlays/v3/holiday_world.ld','tools/v3_physical_resources.py')
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in sources})
    npc['variants']=dict(format=batch['format'],manifest_sha256=sha256(manifest),installed=True,
        ram=start,bytes=len(appended),sha256=sha256(appended),guard='AFNV',modules=refreshed,
        characters=installed,spawn_hooks=hooks,preserved_packet=old_packet,
        additional_resident_bytes=len(appended),actor_admission_changed=False,
        saved_format_changed=False,native_execution_verified=False)
    write_new(work/'installed.json',(json.dumps(npc['variants'],indent=2)+'\n').encode())
    write_new(work/'packet.bin',combined);write_new(work/'registry.bin',data)
    return equipment,changes,dict(physical_resources=records),[(write,combined),
        (dict(record,previous_sha256=previous_npc),bytes(data))]


def u32_local(data,at):
    return struct.unpack_from('>I',data,at)[0]


def refresh_renderer(npc,data,output,base,changes,*,extra_sources=(),link_symbols=None):
    """Refresh the common character renderer in its existing code reservation.

    Registry/actor callers retain their public entries. The two native drawing
    callers are rebound together. The shared startup publisher reads the
    refreshed DMA initializer from this same code report.
    """
    old=npc['code'];data=bytearray(data)
    if (len(data)!=SIZE or sha256(data)!=npc['packet']['sha256'] or
            sha256(data[:old['bytes']])!=old['sha256'] or any(data[old['bytes']:0x2000])):
        raise ValueError('Changed shared NPC code reservation')
    code,compiled=compile_part('npc_registry',output,link_symbols=link_symbols or old['link_symbols'],
        extra_sources=('overlays/v3/npc_stream_draw.c','overlays/v3/npc_dma.c',*extra_sources))
    for name,address in old['symbols'].items():
        if name.startswith('af_') and RAM<=address<RAM+0x2000 and name not in (
                'af_v3_npc_dma_request','af_v3_npc_dma_init','af_v3_npc_stream_draw'):
            if compiled['symbols'].get(name)!=address:
                raise ValueError('Moved shared NPC reader without rebinding: '+name)
    files=by_vrom(base)
    before=struct.pack('>I',jump(old['symbols']['af_v3_npc_stream_draw'],link=True))
    after=struct.pack('>I',jump(compiled['symbols']['af_v3_npc_stream_draw'],link=True))
    for hook in npc['render_hooks']:
        vrom=hook['vrom'];owner=bytearray(changes.get(vrom,files[vrom].extract(base)))
        at=hook['call']-hook['ram']
        if owner[at:at+8]!=before+bytes.fromhex(hook['delay_slot']):
            raise ValueError('Changed installed complete NPC drawing call')
        owner[at:at+4]=after;changes[vrom]=bytes(owner)
        hook.update(previous_call=before.hex(),installed_call=after.hex())
    data[:0x2000]=code+bytes(0x2000-len(code))
    npc['code']=compiled;npc['packet'].update(sha256=sha256(data),crc32=zlib.crc32(data))
    npc['renderer_capabilities']=dict(absent_expressions=True,clamped_non_power_of_two_tiles=True,
        shared_model_commands=True,installed=True,native_execution_verified=False)
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return bytes(data)


def install(base,prior,blob,core,output,art_directory,lock,*,module=None):
    """Connect guarded memory, banks, renderers, and cleanup in the shared build.

    The record remains inactive until event/conversation services bind its actor
    callbacks. Merely installing its resources cannot enable unfinished gameplay.
    """
    if prior['equipment_resources'].get('npc_extra'):
        return install_art_batch(base,prior,blob,output,art_directory,core=core,module=module)
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
