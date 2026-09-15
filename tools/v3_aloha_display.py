"""Complete imported-shirt mannequins, item conversions, and catalogue readers."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,DMA_START,apply_ups,by_vrom,fix_checksum,make_ups,sha256,verified_rom
from apply_translation import write_new
from gc_names import symbol_data
from v3_asset_loader import BLOB,CONFIG,MODULE,ROOT,STARTUP,compile_part
from v3_clothing_display import profile_dependency
from v3_clothing_catalogue import NATIVE_COUNT,NATIVE_SHA,TABLE as CLOTH_TABLE
from v3_import_catalog import read_donor
from v3_registry import CLOTHING_DISPLAYS,clothing_slot
import v3_catalogue as catalogue

ABI=58
BASE=ROOT/'build/v3-town-residents-03'
BASE_SHA='8ea1dd5de03a2d03db7e8bcafc58099a963a9ff2d5bdb8057e538e0100d92b58'
DONOR_SHA='3eb4ab9626f6da11b6222e5707201bef8d69cea6583824f58022cb786874d4aa'
DISPLAY_ROWS={0x241A:0x6540,0x241B:0x6590}
SOURCES=('tools/v3_aloha_display.py','tools/v3_registry.py','tools/v3_catalogue.py',
    'tools/v3_asset_loader.py','overlays/v3/clothing_display.h','overlays/v3/display_roster.c',
    'overlays/v3/display_roster.ld','overlays/v3/clothing_roster.S','overlays/v3/furniture.c',
    'overlays/v3/furniture_expanded.ld','overlays/v3/furniture_entry.S',
    'overlays/v3/furniture_tables.c','overlays/v3/furniture_tables.ld',
    'overlays/v3/display_items.c','overlays/v3/display_items.ld','overlays/v3/display_conversion.c',
    'overlays/v3/display_conversion.ld','overlays/v3/catalogue.c','overlays/v3/catalogue.ld',
    'overlays/v3/catalogue_bridge.S','overlays/v3/startup.c','overlays/v3/startup.ld')


def clothing_table(stable,rel,symbols,previous):
    data,_,_=catalogue.sources(stable)
    original=data[CLOTH_TABLE-catalogue.RAM:CLOTH_TABLE-catalogue.RAM+NATIVE_COUNT*2]
    donor=symbol_data(rel,symbols.decode(),'mCL_cloth_idx_list')
    conversion=symbol_data(rel,symbols.decode(),'mRmTp_Item1ItemNo2FtrItemNo_AtPlayerRoom')
    if (sha256(original)!=NATIVE_SHA or sha256(donor)!=DONOR_SHA or
            sha256(conversion)!='5228a779089eca94c3f751a814e169f74ff085a57626673c86d7d789fadd6c66'
            or conversion[80:84]!=bytes.fromhex('380317ac')):
        raise ValueError('Changed full native clothing catalogue or actual donor conversion')
    values=list(struct.unpack('>'+str(len(donor)//2)+'H',donor));rows=[]
    for item in (0x24BF,0x241A,0x241B):
        index,display=CLOTHING_DISPLAYS[item];pocket,resource,_=clothing_slot(item)
        donor_index=491+item-0x2400
        if (values.count(donor_index)!=1 or index!=1024+((display&0xFFF)>>2)
                or display!=0x3800+(pocket-0x3400)*4):
            raise ValueError('Changed fixed garment/display identity or donor catalogue presence')
        rows.append({'donor_item_id':f'{item:04X}','item_id':f'{display:04X}',
            'pocket_item_id':f'{pocket:04X}','runtime_index':index,'resource_index':resource,
            'catalogue_index':(display-0x1000)//4,'donor_runtime_index':donor_index,
            'donor_position':values.index(donor_index),'independently_selectable':False,
            'profile_ram':f'{0x80460000+DISPLAY_ROWS.get(item,0x6600)+8:08X}'})
    table=original+b''.join(struct.pack('>H',r['catalogue_index']) for r in rows)
    if sha256(table[:-4])!=previous['catalogue']['clothing']['table_sha256']:
        raise ValueError('Original and cherry-shirt catalogue records changed')
    return table,{'imports':rows,'native_rows':NATIVE_COUNT,'total_rows':NATIVE_COUNT+3,
        'native_table_sha256':NATIVE_SHA,'donor_table_sha256':DONOR_SHA,'donor_rows':len(values),
        'preview_scale':1.0,'preview_height':38.0,'preview_model_y':-4.0,
        'aloha_ordinary_shop_stock_added':False,'ordinary_order_payment_tested':False}


def build(output):
    if not output.resolve().is_relative_to(ROOT/'build'):raise ValueError('Ignored build/ output required')
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
    prior=json.loads((BASE/'build.json').read_text())
    if sha256(base)!=BASE_SHA or prior['output_sha256']!=BASE_SHA or prior['runtime_abi']!=57:
        raise ValueError('Changed complete town integration parent')
    native=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    stable=(ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable)!='8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed translation-only baseline')
    files=by_vrom(base);blob=bytearray(files[BLOB].extract(base));code=bytearray(files[CODE_VROM].extract(base))
    before_blob=bytes(blob);display=copy.deepcopy(prior['clothing']['display'])
    furniture=copy.deepcopy(prior['furniture']);expanded=furniture['expanded_tables']
    output.mkdir(parents=True,exist_ok=False)
    compiled={};parts={}
    specs=(('display_roster',('AF_V3_DISPLAY_ROSTER_BRIDGE=1',),('overlays/v3/clothing_roster.S',),None),
           ('furniture_expanded',('AF_V3_FURNITURE_TABLES=1','AF_V3_CLOTHING_DISPLAY=1',
                                  'AF_V3_SPEED_BAG=1','AF_V3_ALOHA_DISPLAY=1'),
                                  ('overlays/v3/furniture_entry.S',),'overlays/v3/furniture.c'),
           ('furniture_tables',('AF_V3_CLOTHING_DISPLAY=1','AF_V3_ALOHA_DISPLAY=1'),(),None),
           ('display_items',('AF_V3_ALOHA_DISPLAY=1',),(),None),
           ('display_conversion',('AF_V3_ALOHA_DISPLAY=1',),(),None))
    for part,defines,extra,source in specs:
        parts[part],compiled[part]=compile_part(part,output/part,defines=defines,extra_sources=extra,primary_source=source)

    def install_region(part,at,end,old):
        data=parts[part];old_size=old['bytes']
        if (sha256(blob[at:at+old_size])!=old['sha256'] or any(blob[at+old_size:end])
                or not data or len(data)>end-at):raise ValueError('Changed bounded region: '+part)
        blob[at:end]=data+bytes(end-at-len(data))

    install_region('furniture_expanded',0x5800,0x6000,expanded['expanded_code'])
    install_region('furniture_tables',0xA000,0xA200,expanded['initializer'])
    install_region('display_items',0x6C00,0x6F00,display['readers']['code'])
    install_region('display_conversion',0x6270,0x6380,display['conversion']['code'])
    if any(blob[0x6380:0x65E0]) or not 0<len(parts['display_roster'])<=0x1C0:
        raise ValueError('Display policy or profiles overlap native conversion bridges')
    blob[0x6380:0x6380+len(parts['display_roster'])]=parts['display_roster']
    hooks=[]
    def hook(buffer,at,expected,target,label):
        before=bytes(buffer[at:at+8]);after=struct.pack('>2I',0x08000000|(target>>2&0x3FFFFFF),0)
        if before.hex()!=expected:raise ValueError('Changed current entry: '+label)
        buffer[at:at+8]=after
        hooks.append({'location':'core' if buffer is code else 'blob','offset':at,
                      'before':before.hex(),'after':after.hex(),'target':f'{target:08X}','label':label})
        return after.hex()

    if sha256(blob[0x6200:0x6270])!=display['code']['sha256']:
        raise ValueError('Changed complete original display-index helper')
    index_target=compiled['display_roster']['symbols']['af_v3_all_display_clothing_index_bridge']
    hook(blob,0x6200,blob[0x6200:0x6208].hex(),index_target,'display index')
    for row in expanded['public_entries']:
        row['target']=compiled['furniture_expanded']['symbols'][row['name']]
        row['after']=hook(blob,row['entry']-0x80460000,row['after'],row['target'],row['name'])
    for group,prefix in (('item_hooks','af_v3_display_item_'),('collection_hooks','af_v3_display_catalogue_')):
        for row in display['readers'][group]:
            row['target']=compiled['display_items']['symbols'][prefix+row['helper']] if group=='item_hooks' else \
                compiled['display_items']['symbols'][prefix+('record' if row['entry']==0x804699C0 else 'owned')]
            row['after']=hook(blob,row['entry']-0x80460000,row['after'],row['target'],group)
    for row in display['conversion']['hooks']:
        row['target']=compiled['display_conversion']['symbols']['af_v3_room_'+row['kind']+'_item']
        row['after']=hook(code,row['entry']-CODE_RAM,row['after'],row['target'],'native '+row['kind'])

    profile=bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if blob[0x20:0xE0]!=profile or profile[99]&12:raise ValueError('Changed display profile reservation')
    prototype=bytes(blob[0x6608:0x664C])
    if len(prototype)!=68 or sha256(prototype)!=display['profile_sha256']:
        raise ValueError('Changed complete native mannequin profile')
    for item,at in DISPLAY_ROWS.items():
        index,ident=CLOTHING_DISPLAYS[item]
        packed=struct.pack('>HHI',index,ident,1)+prototype+bytes(4)
        blob[at:at+80]=packed
    profile[99]|=12;blob[0x20:0xE0]=profile

    donor=read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    ordering,records=catalogue.table(stable,donor['rel'],symbols,prior['catalogue']['imports'])
    cloth,cloth_report=clothing_table(stable,donor['rel'],symbols,prior)
    assembly=('.section .rodata.catalogue_order\n.balign 4\n.globl af_v3_catalogue_order\n'
              'af_v3_catalogue_order:\n.byte '+','.join(str(n) for n in ordering)+'\n'
              '.balign 2\n.globl af_v3_catalogue_clothing_order\naf_v3_catalogue_clothing_order:\n.byte '+
              ','.join(str(n) for n in cloth)+'\n')
    write_new(output/'catalogue_tables.S',assembly.encode())
    suffix,cat_compiled=compile_part('catalogue',output/'catalogue',
        extra_sources=('overlays/v3/catalogue_bridge.S',str((output/'catalogue_tables.S').resolve().relative_to(ROOT))),
        defines=('AF_V3_FURNITURE_TABLES=1','AF_V3_CLOTHING_CATALOGUE=1','AF_V3_ALOHA_DISPLAY=1'))
    # Rebuild the owner from the immutable V2 source, retaining all current
    # parent edits except the checked catalogue size descriptor.
    parent=bytearray(files[catalogue.PARENT].extract(base));_,_,source_parent=catalogue.sources(stable)
    current_descriptor=parent[catalogue.OWNER:catalogue.OWNER+32]
    expected_descriptor=bytearray(source_parent[catalogue.OWNER:catalogue.OWNER+32])
    struct.pack_into('>I',expected_descriptor,4,catalogue.VROM+prior['catalogue']['bytes'])
    struct.pack_into('>I',expected_descriptor,12,catalogue.RAM+prior['catalogue']['bytes'])
    if current_descriptor!=expected_descriptor:raise ValueError('Changed current catalogue parent descriptor')
    parent[catalogue.OWNER:catalogue.OWNER+32]=source_parent[catalogue.OWNER:catalogue.OWNER+32]
    changes,cat_report=catalogue.install(stable,parent,suffix,cat_compiled,ordering,records,
        prior['collection']['code'],prior['save_runtime']['code'],prior['furniture_room']['code'],
        clothing=(cloth,cloth_report))
    for vrom,digest in ((catalogue.VROM,prior['catalogue']['output_sha256']),
                        (catalogue.RELOC,prior['catalogue']['relocation_sha256'])):
        if sha256(files[vrom].extract(base))!=digest:raise ValueError('Changed current catalogue resource')
    # Read-only physical sharing keeps the blob as the final allocation and
    # preserves every existing object/audio source location.
    moved=[]
    for vrom in (catalogue.VROM,catalogue.RELOC):
        blob.extend(bytes((-len(blob))&15));offset=len(blob);data=changes.pop(vrom);blob.extend(data)
        moved.append({'vrom':vrom,'blob_offset':offset,'bytes':len(data),
                      'physical':files[BLOB].pstart+offset,'sha256':sha256(data)})
    if files[BLOB].pstart+len(blob)>len(base) or len(blob)>0x200000:
        raise ValueError('Catalogue append exceeds current cartridge storage')
    struct.pack_into('>I',blob,4,ABI)
    startup,start_report=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1','AF_V3_ACCESSORY_BYTES=61440'))
    module=bytearray(files[MODULE].extract(base));old_start=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old_start['bytes']])!=old_start['sha256'] or
            any(module[STARTUP+old_start['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup code or bounds')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    image=bytearray(base)
    old_end=files[BLOB].pstart+len(before_blob);new_end=files[BLOB].pstart+len(blob)
    if any(image[old_end:new_end]):raise ValueError('Appended catalogue overwrites live physical data')
    changes.update({BLOB:blob,CODE_VROM:code,MODULE:module})
    for vrom,data in changes.items():
        entry=files[vrom]
        if entry.pend or (vrom!=BLOB and entry.size!=len(data)):raise ValueError('Unexpected allocation resize')
        image[entry.pstart:entry.pstart+len(data)]=data
    struct.pack_into('>I',image,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in moved:
        struct.pack_into('>4I',image,DMA_START+files[row['vrom']].index*16,
                         row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    fix_checksum(image);image=bytes(image);patch=make_ups(native,image)
    if apply_ups(native,patch)!=image:raise ValueError('Aloha catalogue cartridge reconstruction failed')
    display.update(imports=cloth_report['imports'],roster_code=compiled['display_roster'])
    display['code']={**display['code'],'sha256':sha256(blob[0x6200:0x6270])}
    display['readers']['code']=compiled['display_items'];display['conversion']['code']=compiled['display_conversion']
    for key in ('item_id','pocket_item_id','name','price'):
        display['readers'].pop(key,None)
    for key in ('pocket_item_id','display_item_id'):
        display['conversion'].pop(key,None)
    display['readers']['imports']=display['conversion']['imports']=cloth_report['imports']
    display.pop('save_profile_dependency',None)
    display['save_profile_dependencies']=[{'byte':119,'mask':128},{'byte':99,'mask':12}]
    expanded.update(expanded_code=compiled['furniture_expanded'],initializer=compiled['furniture_tables'])
    furniture['display_imports']=cloth_report['imports']
    clothing=copy.deepcopy(prior['clothing']);clothing['display']=display
    for row in clothing['imports']:
        if row['item_id'] in ('341A','341B'):
            row.update(display_installed=True,catalogue_installed=True,
                remaining=['ordinary acquisition, placement, and persistence'])
    report={**prior,'build':'v3-aloha-display','runtime_abi':ABI,'input_build_sha256':BASE_SHA,
        'output_sha256':sha256(image),'patch_sha256':sha256(patch),'blob_bytes':len(blob),'blob_sha256':sha256(blob),
        'startup':start_report,'furniture':furniture,'clothing':clothing,'catalogue':{**cat_report,'code':cat_compiled},
        'save_runtime':{**prior['save_runtime'],'profile_hex':profile.hex(),'profile_sha256':sha256(profile)},
        'aloha_display':{'code':compiled,'hooks':hooks,'rows':cloth_report['imports'],'resource_moves':moved,
            'saved_format_changed':False,'saved_profile_changed':True,
            'older_builds_accept_new_saves':False,'native_test':'pending',
            'catalogue_capacity_used_growth_bytes':cat_report['conservative_pool_required']-prior['catalogue']['conservative_pool_required'],
            'additional_pool_allocation':0,'not_a_playtest_handoff':True,
            'compatibility':'New profiles require both aloha display identities; preceding builds reject these saves. Keep backups.'},
        'native_test':'pending for complete imported-shirt display/catalogue integration',
        'sources':{**prior['sources'],**{p:sha256((ROOT/p).read_bytes()) for p in SOURCES}}}
    write_new(output/'animal-forest-v3-asset-loader.z64',image);write_new(output/'asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    r=build(parser.parse_args().output)
    print(json.dumps({k:r[k] for k in ('runtime_abi','output_sha256','patch_sha256')}))
