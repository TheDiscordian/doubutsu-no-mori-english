"""Install the connected global stationery policy without enabling imports."""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,by_vrom,sha256,u32
from v3_asset_loader import ROOT
from v3_import_storage import jump
from v3_submenu_tables import resize


def install(base,prior,core,output,directory):
    from v3_console_disk_install import reservations
    from v3_furniture_install import relocate_resource_plan
    from v3_holiday_selection import refresh_receipts
    from v3_catalogue import PARENT
    import v3_physical_resources as physical
    directory=directory.resolve()
    if not directory.is_relative_to(ROOT/'build'):raise ValueError('Use ignored prepared stationery')
    prepared=json.loads((directory/'prepared.json').read_bytes())
    if (prepared['format']!='AFV3-PAPER-QUANTITIES-1' or prepared['installed'] or
            prepared['base_sha256']!=sha256(base) or prepared['base_abi']!=prior['runtime_abi']):
        raise ValueError('Changed stationery preparation or complete base')
    for name,digest in prepared['sources'].items():
        if sha256((ROOT/name).read_bytes())!=digest:raise ValueError('Stale stationery source: '+name)
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items'];q=d['quest'];old=q['packet']
    lo,end=prepared['ram'],prepared['end'];files=by_vrom(base)
    if (d['paper'].get('quantities') or not q.get('manager') or old!=d['spawning']['packet'] or
            old['ram']+old['bytes']!=lo or any(a<end and lo<b for a,b in reservations(prior))):
        raise ValueError('Stationery extension overlaps or replaces an unexpected owner')
    raw=bytearray(base[old['physical']:old['physical']+old['bytes']])
    if sha256(raw)!=old['sha256'] or raw[-16:]!=b'AFCQ'*4:raise ValueError('Changed current quest packet')
    raw.extend(bytes(end-old['ram']-len(raw)));raw[-16:]=b'AFPQ'*4
    code=prepared['code'];storage=prepared['storage'];save_ram=0x807B7000
    for filename,address,size,digest in (
        ('readers/code.bin',lo,code['bytes'],code['sha256']),
        ('storage/code.bin',save_ram,storage['bytes'],storage['sha256']),
        ('supply-bridges.bin',prepared['supply']['ram'],prepared['supply']['bytes'],prepared['supply']['sha256'])):
        value=(directory/filename).read_bytes();at=address-old['ram']
        if len(value)!=size or sha256(value)!=digest or not lo<=address<address+size<=end-16:
            raise ValueError('Changed or oversized complete stationery module')
        if any(raw[at:at+size]):raise ValueError('Stationery modules overlap')
        raw[at:at+size]=value
    for patch in prepared['supply']['core_patches']:
        at=patch['address']-CODE_RAM;before=bytes.fromhex(patch['before']);after=bytes.fromhex(patch['after'])
        if core[at:at+len(before)]!=before:raise ValueError('Changed shared stationery caller')
        core[at:at+len(after)]=after
    prefix_packet=d['packet'];prefix=bytearray(base[prefix_packet['physical']:prefix_packet['physical']+prefix_packet['bytes']])
    if sha256(prefix)!=prefix_packet['sha256']:raise ValueError('Changed retained carried module packet')
    redirects=[]
    def redirect(previous,start,target,target_start,payload,packet_ram,prefixes):
        stop=start+previous['bytes'];symbols=previous['symbols']
        bounds=sorted(set(v for v in symbols.values() if start<=v<stop))
        for name,address in sorted(symbols.items()):
            if not name.startswith(prefixes) or not start<=address<stop:continue
            dest=target['symbols'].get(name);next_entry=next((v for v in bounds if v>address),stop)
            if dest is None or not target_start<=dest<target_start+target['bytes'] or next_entry-address<8:
                raise ValueError('Missing or short stationery public entry: '+name)
            at=address-packet_ram;before=bytes(payload[at:at+8]);after=struct.pack('>2I',jump(dest),0)
            payload[at:at+8]=after
            redirects.append(dict(name=name,address=address,target=dest,before=before.hex(),after=after.hex()))
        previous['sha256']=sha256(payload[start-packet_ram:stop-packet_ram])
    reader=d['code'];redirect(reader,d['ram'],code,lo,prefix,prefix_packet['ram'],('af_carried_','af_v3_ground_'))
    cat_code=d['paper']['catalogue']['code']
    cat_start=min(v for k,v in cat_code['symbols'].items() if k.startswith('af_carried_') and RAM<=v<TABLE)
    redirect(cat_code,cat_start,code,lo,prefix,prefix_packet['ram'],('af_carried_',))
    redirect(q['storage'],q['storage_ram'],storage,save_ram,raw,old['ram'],('af_v3_','af_holiday_cards_','af_carried_'))
    # Allocate before changing checksums of retained physical resources, so the
    # allocator can still verify every predecessor against the source image.
    records=copy.deepcopy(prior['physical_resources']);retired=[];allocation_base=base
    try:replacement=physical.grow_backwards(base,records,old['id'],bytes(raw))
    except ValueError as error:
        if str(error)!='No checked adjacent space for complete physical resource growth':raise
        # A complete superseded furniture/audio resource still occupies its old
        # cartridge space. Its replacement prefix remains exact in the current
        # expanded DMA owner; reclaim only that recorded copy in the new build.
        retired=[copy.deepcopy(e['furniture_audio']['batches'][0]['resource_growth'])]
        allocation_base=physical.retire_dma_copies(base,records,retired)
        replacement=physical.allocate(allocation_base,records,bytes(raw),'global-stationery-GAFE01-r0',best_fit=True)
    resource={k:replacement[k] for k in ('id','physical','bytes','sha256')}
    if resource['id']==old['id']:records[records.index(next(r for r in records if r['id']==old['id']))]=resource
    else:records.append(resource)
    packet=dict(resource,ram=old['ram'],crc32=zlib.crc32(raw),storage='physical-ROM')
    q['packet']=copy.deepcopy(packet);d['spawning']['packet']=copy.deepcopy(packet)
    q['storage_previous']=q['storage'];q.update(storage=copy.deepcopy(storage),storage_ram=save_ram,save_format=18,wire_version=5)
    refresh_receipts(e,records,{prefix_packet['id']:prefix})
    d['sha256']=sha256(prefix[RAM-prefix_packet['ram']:])
    for saved in (d['storage'],e['holiday_items']['controls']['storage']):
        saved.update(active_code=copy.deepcopy(storage),save_format=18,wire_version=5)
    e['console_storage'].update(save_format=18,card_runtime=copy.deepcopy(storage))
    changes={};allocations=[];targets={};menu=bytearray(files[PARENT].extract(base))
    updates={k:copy.deepcopy(prior[k]) for k in ('save_codec','clothing','room_surfaces','catalogue','shop_actors','shop_floor')}
    def prepared_owner(name,vrom,reloc,receipt):
        data=(directory/(name+'.bin')).read_bytes();rel=(directory/(name+'-reloc.bin')).read_bytes()
        if len(data)!=receipt['bytes'] or sha256(data)!=receipt['owner_sha256'] or sha256(rel)!=receipt['relocation_sha256']:
            raise ValueError('Changed prepared native stationery owner: '+name)
        changes.update({vrom:data,reloc:rel})
        return data,rel
    for name,vrom,reloc,ram,offset in (
        ('letter',0x3B60000,0x3B70000,0x80888E90,0x2B90),
        ('catalogue',0x3970000,0x3980000,0x808A6100,0x2C90)):
        data,rel=prepared_owner(name,vrom,reloc,prepared[name]['owner'])
        allocation=resize(menu,core,vrom=vrom,ram=ram,offset=offset,before=files[vrom].size,after=len(data))
        allocations.append(allocation);d['menu_allocations'].append(allocation)
        if name=='letter':d['actions']['letter'].update(prepared[name]['owner'])
        else:
            c=updates['catalogue'];c.update(bytes=len(data),output_sha256=sha256(data),relocation_bytes=len(rel),relocation_sha256=sha256(rel))
            d['paper']['catalogue'].update(prepared[name]['owner'])
    changes[PARENT]=bytes(menu);e['pocket_icons']['owner_sha256']=sha256(menu)
    native_consumers=copy.deepcopy(prepared['native_consumers'])
    for index,row in enumerate(native_consumers):
        vrom,reloc,ram=row['vrom'],row['reloc'],row['ram'];source=row['source']
        if sha256(files[vrom].extract(base))!=source['sha256'] or sha256(files[reloc].extract(base))!=source['relocation_sha256']:
            raise ValueError('Changed complete native stationery input: '+row['name'])
        data,rel=prepared_owner(row['name'],vrom,reloc,row['owner']);at=row['descriptor']-CODE_RAM
        before=(vrom,vrom+source['bytes'],ram,ram+source['resident_bytes'])
        if struct.unpack_from('>4I',core,at)!=before:raise ValueError('Changed stationery owner allocation: '+row['name'])
        target=vrom;target_rel=reloc
        if row['name'].startswith('shop-'):
            # Native shop owners end exactly where their relocation files
            # begin. Retain both DMA-directory indices, but move their virtual
            # extents together so appended adapters never overlap a neighbour.
            target=0x04640000+index*0x20000;target_rel=target+0x10000
            targets.update({vrom:target,reloc:target_rel})
        row.update(installed_vrom=target,installed_reloc=target_rel)
        struct.pack_into('>4I',core,at,target,target+len(data),ram,ram+len(data))
        if row['name']=='shop-floor':updates['shop_floor'].update(output_sha256=sha256(data),relocation_sha256=sha256(rel),vrom=target,reloc=target_rel)
        elif row['name'].startswith('shop-'):
            updates['shop_actors']['owners'][row['name'][5:]].update(output_sha256=sha256(data),relocation_sha256=sha256(rel),allocation_bytes=len(data),vrom=target,reloc=target_rel)
        elif row['name']=='room-goods':
            # All model offsets/fixups/table rows are unchanged. Only the loaded
            # owner's complete length grows to include the classifier adapters.
            diary=e['diary_items'];p=diary['packet'];payload=bytearray(base[p['physical']:p['physical']+p['bytes']])
            if sha256(payload)!=p['sha256'] or u32(payload,0x300C)!=source['resident_bytes']:
                raise ValueError('Changed complete diary model configuration')
            previous=p['sha256'];struct.pack_into('>I',payload,0x300C,len(data))
            p.update(sha256=sha256(payload),crc32=zlib.crc32(payload))
            next(r for r in records if r['id']==p['id'])['sha256']=p['sha256']
            diary['room_art'].update(bytes=len(data),sha256=sha256(data),relocation_sha256=sha256(rel))
            e['room_goods']['diary_room_art']['bytes']=len(data)
            diary_write=(dict(next(r for r in records if r['id']==p['id']),previous_sha256=previous),bytes(payload))
    resizes=[dict(vrom=v,previous_bytes=files[v].size,previous_sha256=sha256(files[v].extract(base)),
        bytes=len(data),sha256=sha256(data)) for v,data in changes.items() if len(data)!=files[v].size]
    growth=[]
    for row in resizes:
        v=row['vrom'];_,record=relocate_resource_plan(allocation_base,files,v,changes[v],minimum_physical=0x100000,
            reservations=records+growth,append_only=False,allow_compressed=True,target_vrom=targets.get(v))
        growth.append(record)
    warning=('Format-18 experimental saves require this or a newer compatible build. Compatible older saves migrate forward. '
        'Four-sheet-mode saves require four-sheet mode when reloading; switching to single sheets rejects them without changing the save. '
        'V2 and format-17-or-earlier V3 cannot load new saves. Keep backups.')
    updates['save_codec'].update(format_version=18,active_storage_code=copy.deepcopy(storage),card_storage_code=copy.deepcopy(storage))
    ext=updates['clothing']['save_extension'];ext.update(format_version=18,active_storage_code=copy.deepcopy(storage))
    ext['legacy_formats_read']=list(dict.fromkeys([*ext['legacy_formats_read'],'AFS3-v17']))
    updates['room_surfaces']['save']['disk_format_version']=18
    updates.update(physical_resources=records,runtime_owner_resizes=resizes,resource_growth=growth,
        retired_dma_copies=retired,save_warning=warning)
    d['paper']['quantities']=dict(prepared,prepared=str(directory.relative_to(ROOT)),installed=True,
        packet=copy.deepcopy(packet),redirects=redirects,native_consumers=native_consumers,additional_resident_bytes=end-lo,
        additional_menu_bytes=sum(r['additional_pool_bytes'] for r in allocations),
        save_warning=warning,native_gameplay_verified=False,native_save_reload_verified=False,
        pending=['ordinary native gameplay and save/reload'])
    d['sources'].update(prepared['sources'])
    d['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in (
        'tools/v3_paper_install.py','tools/v3_room_goods.py','tools/v3_furniture_install.py')})
    prefix_resource=next(r for r in records if r['id']==prefix_packet['id'])
    return e,changes,updates,[(replacement,bytes(raw)),
        (dict(prefix_resource,previous_sha256=prefix_packet['sha256']),bytes(prefix)),diary_write]


# Retained reader addresses belong to the original carried packet.
RAM,TABLE=0x80771000,0x80773800
