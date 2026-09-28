"""Install the complete prepared clothing category through shared consumers."""
import copy
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32, verified_rom
from apply_translation import write_new
from v3_asset_loader import ROOT, BLOB, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, ROWS, ROWS_RAM, ITEMS, slot
from v3_registry import CLOTHING, CLOTHING_DISPLAYS, CLOTHING_REGISTRY_VERSION

RAM, SIZE = 0x8066E000, 0x1000
SOURCES = ('tools/v3_clothing_install.py','tools/v3_clothing_batch.py','tools/v3_clothing.py',
    'tools/v3_registry.py','tools/v3_furniture_install.py','tools/v3_furniture_pipeline.py',
    'tools/v3_optional_composition.py','tools/v3_browser_composition.py','tools/v3_catalogue.py',
    'tools/v3_garden_runtime.py','tools/v3_display_aliases.py','tools/v3_room_goods.py',
    'tools/v3_save_runtime.py','tools/v3_asset_loader.py','overlays/v3/clothing_batch.h',
    'overlays/v3/clothing_batch.ld','overlays/v3/clothing_roster.c','overlays/v3/clothing_stock.c',
    'overlays/v3/furniture.c','overlays/v3/catalogue.c','overlays/v3/catalogue.ld','overlays/v3/surface_bootstrap.c')


def metadata_offset(blob, report, row):
    address=int(row['metadata_ram'],16)
    batch=report['clothing'].get('batch')
    if not batch:
        at=address-0x80460000
        if not 0x2820<=at<=0x2900-32:raise ValueError('Unbound legacy clothing record')
        return at
    p=batch['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    if (p['ram']!=RAM or p['bytes']!=SIZE or sha256(raw)!=p['sha256'] or
            not RAM+0x800<=address<=RAM+0x900-32 or (address-RAM-0x800)%32):
        raise ValueError('Unbound complete clothing category record')
    return p['blob_offset']+address-RAM


def checksum_fields(image,report):
    batch=report['clothing'].get('batch')
    if not batch:return []
    e=report['equipment_resources'];p=batch['packet'];f=by_vrom(image)[BLOB]
    ram=e['surface_bootstrap']['code']['symbols']['af_v3_clothing_crc_expected']
    at=f.pstart+e['blob_offset']+ram-e['ram'];start=f.pstart+p['blob_offset']
    if (u32(image,at)!=p['crc32'] or zlib.crc32(image[start:start+SIZE])!=p['crc32']):
        raise ValueError('Changed complete clothing checksum binding')
    return [dict(offset=at,before=image[at:at+4].hex(),start=start,length=SIZE)]


def update_report(blob,report):
    batch=report['clothing'].get('batch')
    if not batch:return
    p=batch['packet'];raw=blob[p['blob_offset']:p['blob_offset']+SIZE]
    p.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    batch['compiled']['sha256']=sha256(raw[:batch['compiled']['bytes']])
    report['equipment_resources']['clothing_batch']=copy.deepcopy(batch)


def stock_data(base,prior,original,rows,prepared):
    from v3_clothing_stock import VROM, TABLE, SIZE as OLD_SIZE, SOURCE_SHA
    files=by_vrom(base);before=files[VROM].extract(base)
    native=by_vrom(original)[VROM].extract(original)
    if sha256(native)!=SOURCE_SHA or sha256(before)!=prior['clothing']['stock']['output_sha256']:
        raise ValueError('Changed complete clothing stock resource')
    originals=[struct.unpack_from('>71H',native,i*0x90) for i in range(3)]
    counts=prepared['source_season_counts'];prefix=len(before);data=bytearray(before+native);records=[]
    names=('cloth_listA','cloth_listB','cloth_listC')
    sources={r['donor_item_id']:r for r in prepared['rows']}
    for group,name in enumerate(names):
        values=[];expanded=[];cursor=0
        for season,count in zip(('all','spring','summer','autumn','winter'),counts,strict=True):
            values.extend(originals[group][cursor:cursor+count]);cursor+=count
            additions=[int(r['item_id'],16) for r in rows for route in sources[r['donor_item_id']]['stock']
                       if route['symbol']==name and route['season']==season]
            values.extend(additions);expanded.append(count+len(additions))
        at=len(data);data+=struct.pack('>'+str(len(values)+1)+'H',*values,0)
        data+=bytes(-len(data)%16)
        struct.pack_into('>I',data,prefix+TABLE+group*4,0x06000000+at)
        records.append(dict(segment=0x06000000+at,counts=expanded,items=values))
    if data[prefix+0x21C:prefix+0x221]!=bytes(counts) or data[prefix:prefix+TABLE]!=native[:TABLE]:
        raise ValueError('Expanded clothing stock changes native lists/counts')
    return bytes(data),records,dict(previous_sha256=sha256(before),native_sha256=sha256(native),
        bytes=len(data),native_bytes=OLD_SIZE,output_sha256=sha256(data),groups=records,
        resource_prefix_bytes=prefix,pointer_table=prefix+TABLE,
        original_lists_and_seasons_retained=True)


def install(base,prior,blob,core,output,directory):
    from v3_furniture_pipeline import Source
    from v3_clothing_batch import checked
    from v3_villager_text import read_text_donor
    from v3_console_disk_install import reservations
    from v3_furniture_install import scoring,relocate_resource_plan,STABLE,STABLE_SHA
    from v3_garden_runtime import install_catalogue
    from v3_hra_birth import checked_categories
    import v3_hra as hra
    import v3_feng_shui as feng
    import v3_display_aliases as aliases
    import v3_catalogue as catalogue
    from v3_clothing_stock import VROM as STOCK_VROM,DESCRIPTOR
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    first=read_text_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    prepared,data=checked(source,original,first,ROOT/'build/item-identity-megasheet.xlsx',directory,
        installed=(base,prior))
    if (prior['clothing'].get('batch') or any(a<RAM+SIZE and RAM<b for a,b in reservations(prior))):
        raise ValueError('Clothing category already installed or resident reservation occupied')
    files=by_vrom(base);old_blob=files[BLOB].extract(base)
    garment=copy.deepcopy(prior['clothing']);equipment=copy.deepcopy(prior['equipment_resources'])
    rows=garment['imports'];added=[]
    new=[r for r in prepared['rows'] if not r['native_candidates'] and not r['installed_resource']]
    if len(rows)+len(new)!=8 or {int(r['donor_item_id'],16) for r in rows+new}!=set(CLOTHING):
        raise ValueError('Incomplete clothing category or registry')
    prototype=old_blob[0x6608:0x664C]
    if sha256(prototype)!=garment['display']['profile_sha256']:
        raise ValueError('Changed complete native mannequin profile')
    profile=bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if blob[0x20:0xE0]!=profile:raise ValueError('Changed saved clothing selection profile')
    displays=copy.deepcopy(prior['aloha_display']);display_rows=displays['rows']
    for row in new:
        donor=int(row['donor_item_id'],16);item,index,reserved=CLOTHING[donor]
        if reserved is not None:raise ValueError('New garment overlaps a retained resource reservation')
        at=row['resource_offset'];resource=data[at:at+544]
        if sha256(resource)!=row['resource_sha256']:raise ValueError('Incomplete prepared garment')
        blob.extend(bytes(-len(blob)%16));vrom=BLOB+len(blob);blob.extend(resource)
        created=dict(row,item_id=f'{item:04X}',resource_index=index,vrom=f'{vrom:08X}',
            registry_version=CLOTHING_REGISTRY_VERSION,save_profile_installed=True,
            ordinary_shop_stock_added=True,runtime_installed=True,installed_resource=True,
            selectable=True,remaining=['native gameplay/save verification'])
        rows.append(created);added.append(created)
        display_index,display=CLOTHING_DISPLAYS[donor];at=ROWS+slot(display)*80
        if any(blob[at:at+80]) or any(blob[ITEMS+slot(display)*32:ITEMS+(slot(display)+1)*32]):
            raise ValueError('New garment replaces an occupied display identity')
        blob[at:at+80]=struct.pack('>HHI',display_index,display,1)+prototype+bytes(4)
        display_rows.append(dict(donor_item_id=row['donor_item_id'],item_id=f'{display:04X}',
            pocket_item_id=f'{item:04X}',runtime_index=display_index,resource_index=index,
            catalogue_index=(display-0x1000)//4,donor_runtime_index=(int(row['display_item_id'],16)-0x1000)//4,
            donor_position=row['catalogue_position'],independently_selectable=False,
            profile_ram=f'{ROWS_RAM+slot(display)*80+8:08X}'))
        for byte,bit in ((160,(item&255)),(32,slot(display))):
            profile[byte+bit//8]|=1<<(bit&7)
    blob[0x20:0xE0]=profile
    garment['display']['imports']=copy.deepcopy(display_rows)
    stocks,stock_records,stock=stock_data(base,prior,original,rows,prepared)
    # Metadata and independent immutable identity tuples occupy the same checked
    # startup packet. Existing callers retain their register-preserving bridges.
    metadata=bytearray();identities=bytearray()
    for i,row in enumerate(rows):
        item,index,vrom=int(row['item_id'],16),row['resource_index'],int(row['vrom'],16)
        record=struct.pack('>HHIHBB16sI',item,index,vrom,row['price'],1,0,row['name'].encode().ljust(16,b' '),0)
        metadata+=record;identities+=struct.pack('>HHI',item,index,vrom)
        row.update(metadata_ram=f'{RAM+0x800+i*32:08X}',metadata_sha256=sha256(record))
    stock_raw=b''.join(struct.pack('>I5B3x',r['segment'],*r['counts']) for r in stock_records)
    assembly='.section .rodata.clothing_records\n.balign 16\n'
    for name,raw in (('af_v3_batch_clothing',metadata),('af_v3_batch_identities',identities),('af_v3_batch_stock',stock_raw)):
        assembly+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,raw))+'\n'
    write_new(output/'clothing_records.S',assembly.encode())
    compiled_code,compiled=compile_part('clothing_batch',output/'clothing_batch',
        primary_source='overlays/v3/clothing_roster.c',defines=('AF_V3_CLOTHING_BATCH=1',),
        extra_sources=('overlays/v3/clothing_stock.c',str((output/'clothing_records.S').relative_to(ROOT))))
    if compiled['symbols']['af_v3_batch_clothing']!=RAM+0x800 or len(compiled_code)>SIZE-16:
        raise ValueError('Clothing code/records escape reserved packet')
    packet=compiled_code.ljust(SIZE-16,b'\0')+bytes.fromhex('41464342')*4
    blob.extend(bytes(-len(blob)%16));packet_at=len(blob);blob.extend(packet)
    p=dict(ram=RAM,bytes=SIZE,vrom=BLOB+packet_at,blob_offset=packet_at,
        sha256=sha256(packet),crc32=zlib.crc32(packet))
    hooks=[];old=prior['aloha_outfits']['code'];at=PACKAGE+0x80473A00-PACKAGE_RAM
    if sha256(old_blob[at:at+old['bytes']])!=old['sha256']:
        raise ValueError('Changed complete prior clothing roster')
    for name in ('af_v3_roster_clothing_record','af_v3_roster_clothing_source',
                 'af_v3_roster_clothing_index','af_v3_roster_outfit_ready'):
        entry=old['symbols'][name];pos=PACKAGE+entry-PACKAGE_RAM
        before=bytes(blob[pos:pos+8]);after=struct.pack('>II',0x08000000|(compiled['symbols'][name]>>2&0x3FFFFFF),0)
        if not at<=pos<=at+old['bytes']-8 or before!=old_blob[pos:pos+8]:raise ValueError('Changed roster entry')
        blob[pos:pos+8]=after;hooks.append(dict(entry=entry,blob_offset=pos,before=before.hex(),after=after.hex()))
    stock_entry=int(prior['clothing']['stock']['helper_entry'],16);pos=stock_entry-0x80460000
    if stock_entry!=0x80460DE4 or blob[pos:pos+8]!=old_blob[pos:pos+8]:raise ValueError('Changed stock helper entry')
    before=bytes(blob[pos:pos+8]);after=struct.pack('>II',0x08000000|(compiled['symbols']['af_v3_clothing_stock_index']>>2&0x3FFFFFF),0)
    blob[pos:pos+8]=after;hooks.append(dict(entry=stock_entry,blob_offset=pos,before=before.hex(),after=after.hex()))
    outfit=copy.deepcopy(prior['aloha_outfits']);outfit['code']['sha256']=sha256(blob[at:at+old['bytes']])
    outfit['installed_items']=[r['item_id'] for r in rows]
    expanded=copy.deepcopy(prior['furniture']['expanded_tables']);old_ftr=expanded['expanded_code']
    flags=tuple(f[2:] for f in old_ftr['flags'] if f.startswith('-D'))+('AF_V3_BATCH_CLOTHING_DISPLAY=1',)
    code,ftr=compile_part('furniture_expanded',output/'furniture_expanded',defines=flags,
        primary_source='overlays/v3/furniture.c',extra_sources=('overlays/v3/furniture_entry.S',))
    if (sha256(blob[0x5800:0x5800+old_ftr['bytes']])!=old_ftr['sha256'] or
            any(blob[0x5800+old_ftr['bytes']:0x6000]) or len(code)>0x800):
        raise ValueError('Changed complete furniture loader or occupied padding')
    blob[0x5800:0x6000]=code.ljust(0x800,b'\0')
    for hook in expanded['public_entries']:
        pos=hook['entry']-0x80460000;before=bytes.fromhex(hook['after'])
        if blob[pos:pos+8]!=before:raise ValueError('Changed public furniture entry')
        target=ftr['symbols'][hook['name']];after=struct.pack('>II',0x08000000|(target>>2&0x3FFFFFF),0)
        blob[pos:pos+8]=after;hook.update(before=before.hex(),after=after.hex(),target=target)
    expanded['expanded_code']=ftr;furniture=copy.deepcopy(prior['furniture']);furniture['expanded_tables']=expanded
    from v3_furniture_room import VROM as ROOM_VROM,RAM as ROOM_RAM
    bank=furniture['bank_pool'];hook=bank['hook'];room=bytearray(files[ROOM_VROM].extract(base))
    pos=hook['address']-ROOM_RAM;before=bytes.fromhex(hook['after'])
    if (room[pos:pos+len(before)]!=before or
            u32(before,4)!=(0x0C000000|(old_ftr['symbols']['af_v3_furniture_secure_banks']>>2&0x3FFFFFF))):
        raise ValueError('Changed complete furniture bank constructor binding')
    after=before[:4]+struct.pack('>I',0x0C000000|(ftr['symbols']['af_v3_furniture_secure_banks']>>2&0x3FFFFFF))+before[8:]
    room[pos:pos+len(after)]=after;hook.update(before=before.hex(),after=after.hex())
    bank.update(source_owner_sha256=sha256(files[ROOM_VROM].extract(base)),output_owner_sha256=sha256(room))
    # The common inverse metadata and forward alias index serve every garment.
    context={**prior,'clothing':garment};alias=copy.deepcopy(prior['display_aliases'])
    new_aliases=aliases.records(context,blob);table,alias_metadata=aliases.encode(new_aliases)
    old_table,_=aliases.encode(alias['rows'])
    if blob[aliases.OFFSET:aliases.OFFSET+len(old_table)]!=old_table:raise ValueError('Changed prior alias index')
    for item,payload in alias_metadata.items():
        pos=ITEMS+slot(item)*32;parent,footprint=struct.unpack('>HH',payload)
        if item in {int(r['item_id'],16) for r in display_rows[-len(added):]}:
            if any(blob[pos:pos+32]):raise ValueError('Occupied clothing parent metadata')
            blob[pos:pos+32]=aliases.metadata_record(1024+slot(item),item,parent,footprint)
    blob[aliases.OFFSET:aliases.OFFSET+len(table)]=table
    alias.update(rows=new_aliases,table_sha256=sha256(table))
    # Exact original rows remain, followed by the complete added category.
    clothes=copy.deepcopy(prior['catalogue']['clothing']);old_cat=files[catalogue.VROM].extract(base)
    pos=clothes['table_address']-catalogue.RAM;ordering=old_cat[pos:pos+clothes['total_rows']*2]
    new_displays=display_rows[-len(added):]
    ordering+=b''.join(struct.pack('>H',r['catalogue_index']) for r in new_displays)
    clothes['imports']+=copy.deepcopy(new_displays);clothes['total_rows']+=len(added)
    stable=STABLE.read_bytes()
    if sha256(stable)!=STABLE_SHA:raise ValueError('Changed common catalogue source baseline')
    changes,cat=install_catalogue(base,stable,prior,prior['catalogue']['imports'],output,
        source.rel,source.symbols.encode(),reviewed_rows=prior['catalogue']['imports'],clothing=(ordering,clothes))
    changes[ROOM_VROM]=bytes(room)
    # The common builder already returns only the changed catalogue core words.
    changed_core=changes.pop(CODE_VROM,None)
    if changed_core is not None:
        old_core=files[CODE_VROM].extract(base)
        for i,(a,b) in enumerate(zip(old_core,changed_core,strict=True)):
            if a!=b:
                if core[i]!=a:raise ValueError('Conflicting clothing catalogue core change')
                core[i]=b
    mapping,_=checked_categories(files[hra.NEW_VROM].extract(base),prior['hra'],source)
    if (sha256(source.data[0x4FAFC:0x4FAFC+1266*4])!=hra.DONOR_SHA or
            sha256(source.data[0x4EBF0:0x4EBF0+1266*2])!=feng.DONOR_SHA):
        raise ValueError('Changed complete donor clothing scoring tables')
    score_rows=[]
    for row in new_displays:
        index=row['donor_runtime_index'];value=u32(source.data,0x4FAFC+index*4)
        donor=value>>8&63;birth=mapping[donor];surface=value>>6&3;series=value>>26
        score_rows.append(dict(item_id=row['item_id'],runtime_index=row['runtime_index'],
            donor_birth_category=donor,birth_category=birth,surface=surface,series=series,
            donor_hra_hex=f'{value:08x}',native_hra_hex=f'{(value&0xFFFFC000)|(birth<<9)|(surface<<7):08x}',
            donor_series_hex=source.raw('mMkRm_series_info')[series*3:series*3+3].hex(),
            feng_hex=source.data[0x4EBF0+index*2:0x4EBF0+index*2+2].hex()))
    scored,score_reports=scoring(base,prior,score_rows,source);changes.update(scored)
    _,growth=relocate_resource_plan(base,files,STOCK_VROM,stocks,
        minimum_physical=0x3C00000,reservations=prior.get('physical_resources',[]))
    # Keep the old complete resource as an unused prefix. The descriptor and
    # segment-six pointers select the appended lists without rebasing the segment.
    prefix=len(files[STOCK_VROM].extract(base));changes[STOCK_VROM]=stocks
    descriptor=DESCRIPTOR-CODE_RAM
    if tuple(struct.unpack_from('>3I',core,descriptor))!=(STOCK_VROM,STOCK_VROM+prefix,0x060001F0):
        raise ValueError('Changed native clothing stock descriptor')
    struct.pack_into('>3I',core,descriptor,STOCK_VROM,STOCK_VROM+len(stocks),0x06000000+stock['pointer_table'])
    garment['stock']={**{key:prior['clothing']['stock'][key] for key in
        ('call','caller_bridge','helper_entry','descriptor','allocation')},**stock,
        'ordinary_stock_and_purchase_tested':False}
    batch=dict(format='AFV3-CLOTHING-CATEGORY-1',packet=p,compiled=compiled,hooks=hooks,
        prepared_directory=str(directory.relative_to(ROOT)),prepared_sha256=sha256((directory/'art.json').read_bytes()),
        imports=[r['donor_item_id'] for r in rows],added=[r['donor_item_id'] for r in added],
        source_stock=stock_records,installed=True,selectable=True,native_execution_tested=False,
        additional_resident_bytes=SIZE,additional_scene_bytes=0,saved_format_changed=False,
        sources={path:sha256((ROOT/path).read_bytes()) for path in SOURCES})
    garment['batch']=batch;equipment['clothing_batch']=copy.deepcopy(batch)
    save=copy.deepcopy(prior['save_runtime']);save.update(profile_hex=bytes(profile).hex(),profile_sha256=sha256(profile))
    updates=dict(clothing=garment,aloha_display=displays,aloha_outfits=outfit,furniture=furniture,
        catalogue=cat,display_aliases=alias,save_runtime=save,resource_growth=[growth],**score_reports)
    updates['save_warning']=prior['save_warning']+' Clothing uses the same format-9 layout. Saves made with the added garments require those garment/display selections; builds or profiles missing them reject the save. Preserve backups before changing profiles.'
    return equipment,changes,updates
