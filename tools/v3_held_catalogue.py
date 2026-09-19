"""Install prepared parent representations into their actual catalogue category."""
import copy
import json
import struct

from aflib import by_vrom,sha256,u32
from v3_asset_loader import BLOB,ROOT,compile_part
from v3_furniture_pipeline import Source,prepare
from v3_import_storage import ROWS,ROWS_RAM,ITEMS,slot,jump,replace_checked
from v3_held_collection import source_records
import v3_catalogue as catalogue
import v3_garden_runtime as shared_catalogue
import v3_furniture_runtime as room

SOURCES=('tools/v3_held_catalogue.py','tools/v3_held_collection.py',
    'tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py',
    'tools/v3_garden_runtime.py','tools/v3_catalogue.py','tools/v3_catalogue_capacity.py',
    'overlays/v3/furniture.c','overlays/v3/furniture_expanded.ld',
    'overlays/v3/furniture_tables.c','overlays/v3/catalogue.c',
    'overlays/v3/catalogue.ld','overlays/v3/catalogue_bridge.S')


def select_installed(prior,blob):
    """Prepare the full experimental reference; selectors remove parent choices."""
    equipment=copy.deepcopy(prior['equipment_resources'])
    required=('catalogue','collection','parent_readers','event_acquisition',
              'ground_categories','inventory_preview','player_actions','item_categories')
    if (any(not equipment.get(k) for k in required) or equipment.get('optional_selection') or
            equipment['catalogue']['imports']!=prior['catalogue']['handheld']['imports']):
        raise ValueError('Parent selection requires the complete installed shared adapters')
    start=equipment['blob_offset']
    if sha256(blob[start:start+equipment['bytes']])!=equipment['sha256']:
        raise ValueError('Changed complete installed equipment module')
    saved=copy.deepcopy(prior['save_runtime']);profile=bytearray.fromhex(saved['profile_hex'])
    if len(profile)!=192 or blob[0x20:0xE0]!=profile or sha256(profile)!=saved['profile_sha256']:
        raise ValueError('Changed complete saved profile')
    parents={r['item_id']:r for r in equipment['parent_readers']['rows']}
    collections={r['item_id']:r for r in equipment['collection']['rows']}
    seen=set();identities=[]
    for row in equipment['catalogue']['imports']:
        parent=parents[row['parent_item_id']];collected=collections[row['parent_item_id']]
        item=int(row['item_id'],16);index=slot(item);at=ROWS+index*80
        art=int(row['object_vrom'],16)-BLOB
        if (parent['item_id'] in seen or row['runtime_index']!=1024+index or
                parent['display_item_id']!=row['item_id'] or collected['display_item_id']!=row['item_id'] or
                (parent['profile_byte'],parent['profile_mask'])!=(32+index//8,1<<(index&7)) or
                struct.unpack_from('>HHI',blob,at)!=(row['runtime_index'],item,1) or
                u32(blob,at+76)!=1 or sha256(blob[at+8:at+76])!=row['profile_sha256'] or
                sha256(blob[ITEMS+index*32:ITEMS+(index+1)*32])!=row['metadata_sha256'] or
                sha256(blob[art:art+row['object_bytes']])!=row['object_sha256'] or
                profile[parent['profile_byte']]&parent['profile_mask']):
            raise ValueError('Changed parent selection identity, installed model, or profile binding')
        seen.add(parent['item_id']);identities.append(parent['id'])
        profile[parent['profile_byte']]|=parent['profile_mask']
    if not seen or seen!=set(parents) or seen!=set(collections):
        raise ValueError('Incomplete installed parent selection inventory')
    blob[0x20:0xE0]=profile
    saved.update(profile_hex=profile.hex(),profile_sha256=sha256(profile))
    equipment['optional_selection']=dict(format='AFV3-HELD-SELECTION-1',
        identities=sorted(identities),profile_bits_enabled=len(identities),
        experimental=True,playable_handoff=False,web_patcher_enabled=False,
        save_compatibility='Older profiles lacking these imports reject saves using them; retain separate test saves.')
    return equipment,{},dict(save_runtime=saved)


def assets(source,equipment,directory):
    """Check the prepared complete assets; never run another graphics compiler."""
    directory=directory.resolve();raw=(directory/'art.json').read_bytes();art=json.loads(raw)
    if (art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1' or
            art['source_rel_sha256']!=sha256(source.rel) or
            art['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed prepared representation format or source')
    _,discovered=source_records(source,equipment)
    if discovered['rows']!=equipment['collection']['rows']:
        raise ValueError('Changed installed collection contexts')
    by_id={r['item_id']:r for r in art['objects']}
    if len(by_id)!=len(art['objects']):raise ValueError('Duplicate prepared representation')
    prepared=[]
    for parent in discovered['rows']:
        if parent['catalogue']['category']!='umbrella':
            raise ValueError('Unimplemented parent catalogue category')
        row=by_id[parent['display_item_id']]
        descriptor,body,resources,_,models,commands,sections=prepare(source,int(row['item_id'],16))
        path=(directory/row['object_file']).resolve()
        if path.parent!=directory:raise ValueError('Prepared representation escapes its directory')
        data=path.read_bytes()
        if (json.loads(json.dumps(descriptor))!=row['profile'] or row['resources']!=resources or
                set(row['model_offsets'])!=set(models) or len(data)!=row['object_bytes'] or
                sha256(data)!=row['object_sha256'] or data[:len(body)]!=body or
                (directory/row['item_id']/'commands.c').read_text()!=commands or
                len(data)!=(len(body)+sum(n for _,n in sections)+15)&~15 or
                row['native_profile_scalar_hex']!=descriptor['scalar_hex'] or
                descriptor['callback_adapter']['category']!='indexed-model-sequence'):
            raise ValueError('Changed complete prepared model or source-derived profile')
        if len(row['models'])!=len(models):raise ValueError('Incomplete compiled model list')
        cursor=len(body)
        for model,(layer,size) in zip(row['models'],sections):
            offset=row['model_offsets'][layer]
            if (model['layer']!=layer or offset!=cursor or model['bytes']!=size or
                    model['source_sha256']!=models[layer]['source_sha256'] or
                    model.get('source_parts')!=models[layer].get('source_parts') or
                    sha256(data[offset:offset+size])!=model['output_sha256']):
                raise ValueError('Changed prepared model sequence or complete commands')
            cursor+=size
        if any(data[cursor:]):raise ValueError('Unexpected prepared model padding')
        prepared.append((parent,row,data))
    # Complete source init and the real handheld-branch constant relocations.
    _,init=source.function(0x259014)
    if init['sha256']!='6bfe84fd17e661290e19a263a63a0299614f9ea7b7f091598434328245957e73':
        raise ValueError('Changed donor catalogue presentation')
    constants=[]
    for hi,lo,address,number in ((966,974,40272,36.0),(970,986,40260,1.0),(978,990,40240,0.0)):
        if (init['relocations'][hi]!=(6,1,4,address) or init['relocations'][lo]!=(4,1,4,address) or
                source.rel[source.sections[4][0]+address:source.sections[4][0]+address+4]!=struct.pack('>f',number)):
            raise ValueError('Changed shared handheld preview framing')
        constants.append(dict(high_offset=hi,low_offset=lo,rodata_offset=address,value=number))
    return prepared,dict(prepared_directory=str(directory.relative_to(ROOT)),prepared_sha256=sha256(raw),
        source_initializer=init,framing_constants=constants)


def install(base,prior,blob,core,original,output,directory):
    from v3_furniture_install import profile,STABLE,STABLE_SHA
    equipment=prior['equipment_resources'];files=by_vrom(base)
    if not equipment.get('collection') or equipment.get('catalogue'):
        raise ValueError('Held previews require installed collection and no previous preview adapter')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    prepared,evidence=assets(source,equipment,directory)
    stable=STABLE.read_bytes()
    if sha256(stable)!=STABLE_SHA:raise ValueError('Changed import-free baseline')
    installed=[]
    for parent,row,asset in prepared:
        item=int(row['item_id'],16);index=parent['runtime_index'];i=slot(item)
        if (index!=1024+i or any(blob[ROWS+i*80:ROWS+(i+1)*80]) or
                any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or blob[32+i//8]&(1<<(i&7))):
            raise ValueError('Parent representation collides with an installed identity')
        blob.extend(bytes(-len(blob)%16));vrom=BLOB+len(blob);blob.extend(asset)
        native=profile(row,vrom)
        # Tag one checks the parent's selection; it is never standalone furniture.
        blob[ROWS+i*80:ROWS+(i+1)*80]=struct.pack('>HHI',index,item,1)+native+struct.pack('>I',1)
        # Inverse alias only: no forward room-drop conversion is registered.
        metadata=struct.pack('>HH',index,item)+bytes(24)+struct.pack('>HH',int(parent['item_id'],16),0)
        blob[ITEMS+i*32:ITEMS+(i+1)*32]=metadata
        installed.append(dict(parent_item_id=parent['item_id'],item_id=row['item_id'],runtime_index=index,
            catalogue_index=(item-0x1000)//4,donor_position=parent['catalogue']['position'],
            object_vrom=f'{vrom:08X}',object_bytes=len(asset),object_sha256=sha256(asset),
            profile_ram=f'{ROWS_RAM+i*80+8:08X}',profile_sha256=sha256(native),
            profile_tag=1,metadata_sha256=sha256(metadata),model_offsets=row['model_offsets'],
            native_profile_scalar_hex=row['native_profile_scalar_hex'],independently_selectable=False))
    expanded=copy.deepcopy(prior['furniture']['expanded_tables']);previous=expanded['expanded_code']
    defines=tuple(f[2:] for f in previous['flags'] if f.startswith('-D'))+('AF_V3_HELD_CATALOGUE=1',)
    code,compiled=compile_part('furniture_expanded',output/'furniture_expanded',
        defines=defines,primary_source='overlays/v3/furniture.c',extra_sources=('overlays/v3/furniture_entry.S',))
    if (sha256(blob[0x5800:0x5800+previous['bytes']])!=previous['sha256'] or
            any(blob[0x5800+previous['bytes']:0x6000]) or len(code)>0x800 or
            compiled['symbols']['af_v3_held_item_collection']!=equipment['collection']['identity_code']['symbols']['af_v3_held_item_collection']):
        raise ValueError('Changed expanded reader reservation or held collection ABI')
    blob[0x5800:0x6000]=code+bytes(0x800-len(code))
    for hook in expanded['public_entries']:
        target=compiled['symbols'][hook['name']];after=struct.pack('>2I',jump(target),0)
        replace_checked(blob,hook['entry']-0x80460000,bytes.fromhex(hook['after']),after)
        hook.update(before=hook['after'],after=after.hex(),target=target)
    banks=copy.deepcopy(prior['furniture']['bank_pool']);owner=bytearray(files[room.VROM].extract(base))
    hook=banks['hook'];before=bytes.fromhex(hook['after'])
    # Placement is the latest shared installer to own this complete overlay;
    # the bank receipt predates its checked address/relocation changes.
    placement=copy.deepcopy(prior['furniture_placement'])
    source_owner_sha=sha256(owner)
    if (source_owner_sha!=placement['owner_sha256'] or
            sha256(files[room.RELOC].extract(base))!=placement['relocation_sha256'] or
            u32(before,4)!=jump(previous['symbols']['af_v3_furniture_secure_banks'],link=True)):
        raise ValueError('Changed complete room owner or bank initializer call')
    after=before[:4]+struct.pack('>I',jump(compiled['symbols']['af_v3_furniture_secure_banks'],link=True))+before[8:]
    replace_checked(owner,hook['address']-room.RAM,before,after)
    hook.update(before=before.hex(),after=after.hex())
    banks.update(source_owner_sha256=source_owner_sha,output_owner_sha256=sha256(owner))
    placement.update(owner_sha256=sha256(owner))
    expanded.update(expanded_code=compiled,output_sha256=sha256(owner))
    native=catalogue.sources(stable)[0]
    table=native[catalogue.UMBRELLA_TABLE-catalogue.RAM:catalogue.UMBRELLA_TABLE-catalogue.RAM+64]
    if (sha256(table)!='c9cc20d285ce8a4f3e694d41a8905883955451c59ea27a4af3febb2087f43e89' or
            struct.unpack_from('>2I',native,catalogue.UMBRELLA_POINTER-catalogue.RAM)!=(catalogue.UMBRELLA_TABLE,32)):
        raise ValueError('Changed complete native umbrella catalogue')
    installed.sort(key=lambda r:r['donor_position'])
    table+=b''.join(struct.pack('>H',r['catalogue_index']) for r in installed)
    cat=dict(native_rows=32,total_rows=32+len(installed),imports=installed,
        category='umbrella',preview_scale=1.0,preview_height=36.0,preview_model_y=0.0,
        profile_selection_required=True,source_evidence=evidence)
    furniture=copy.deepcopy(prior['furniture']);furniture.update(expanded_tables=expanded,bank_pool=banks)
    changes,cat_report=shared_catalogue.install_catalogue(base,stable,prior,
        furniture['imports']+[prior['speed_bag']],output,source.rel,source.symbols.encode(),
        reviewed_rows=prior['catalogue']['imports'],handheld=(table,cat))
    if cat_report['code']['symbols']['af_v3_catalogue_item_price']!=prior['furniture_items']['code']['symbols']['af_v3_item_price']:
        raise ValueError('Changed shared item-price ABI')
    changes[room.VROM]=bytes(owner)
    report=copy.deepcopy(equipment)
    report['catalogue']=dict(format='AFV3-HELD-CATALOGUE-1',imports=installed,evidence=evidence,
        profile_bits_enabled=0,additional_resident_bytes=0,artwork_bytes=sum(len(d) for _,_,d in prepared),
        ordinary_catalogue_tested=False,saved_format_changed=False)
    report['collection']['catalogue_rows_installed']=True
    return report,changes,dict(furniture=furniture,catalogue=cat_report,furniture_placement=placement)
