"""Generate shared room aliases from installed parent/display records.

This category adapter changes no item identity, artwork, acquisition, or save
format. Unsupported parents never become enabled merely because art is ready.
"""
import copy
import struct

from aflib import CODE_RAM, sha256
from v3_asset_loader import compile_part, ROOT
from v3_import_storage import ITEMS, ITEMS_RAM, PACKAGE, PACKAGE_RAM, slot, replace_checked, jump

RAM, LIMIT, CAPACITY, MAGIC = 0x804A0010, 0x804A0100, 58, 0x41464431
OFFSET = PACKAGE+RAM-PACKAGE_RAM
SOURCES = ('tools/v3_display_aliases.py', 'overlays/v3/display_aliases.h',
    'overlays/v3/display_items.c', 'overlays/v3/display_items.ld',
    'overlays/v3/display_conversion.c', 'overlays/v3/display_conversion.ld',
    'overlays/v3/display_roster.c', 'overlays/v3/display_roster.ld',
    'overlays/v3/clothing_roster.S')


def records(prior, blob):
    """Consume the installed parent category, not another maintained item list."""
    display=prior['clothing']['display']
    parents={r['item_id']:r for r in prior['clothing']['imports']}
    result=[]
    for row in display['imports']:
        parent=parents[row['pocket_item_id']]
        item=int(row['item_id'],16); pocket=int(parent['item_id'],16)
        index=row['runtime_index']; at=int(row['profile_ram'],16)-0x80460000-8
        # These existing profiles all use the complete native mannequin and
        # its verified footprint. Other categories supply their own records;
        # no tool/fan is accepted as a garment by numerical proximity alone.
        if (index!=1024+slot(item) or parent['donor_item_id']!=row['donor_item_id']
                or parent['resource_index']!=row['resource_index']
                or not 0x3400<=pocket<0x3500 or row['resource_index']!=0x1000+pocket-0x3400
                or item!=0x3800+(pocket-0x3400)*4
                or struct.unpack_from('>HHI',blob,at)!=(index,item,1)
                or struct.unpack_from('>I',blob,at+72)[0]!=0x80466150
                or display['readers']['native_footprint_equivalent']!='17AC'):
            raise ValueError('Changed installed garment/display dependency')
        result.append(dict(parent_item_id=f'{pocket:04X}',display_item_id=f'{item:04X}',
            runtime_index=index,category='clothing',native_footprint_item='17AC',
            profile_ram=row['profile_ram'],metadata_ram=f'{ITEMS_RAM+slot(item)*32:08X}',
            parent_source=copy.deepcopy(parent),independently_selectable=False))
    return sorted(result,key=lambda r:r['parent_item_id'])


def encode(rows):
    """One bounded forward index; inverse/footprint data use canonical slots."""
    if not rows or len(rows)>CAPACITY: raise ValueError('Room-alias index capacity exceeded')
    parents=[int(r['parent_item_id'],16) for r in rows]
    displays=[int(r['display_item_id'],16) for r in rows]
    if (parents!=sorted(set(parents)) or len(set(displays))!=len(displays)
            or any(not 0<p<0xFFFF for p in parents)
            or any(p&0xFFFC in displays for p in parents)):
        raise ValueError('Duplicate, unordered, invalid, or recursive room alias')
    table=struct.pack('>II',MAGIC,len(rows)); metadata={}
    for row,parent,item in zip(rows,parents,displays):
        index=1024+slot(item); footprint=int(row['native_footprint_item'],16)
        if row['runtime_index']!=index or footprint and (footprint&3 or not 0x1000<=footprint<0x2000):
            raise ValueError('Invalid alias index or native footprint')
        table+=struct.pack('>HH',parent,item)
        metadata[item]=struct.pack('>HH',parent,footprint)
    return table.ljust(LIMIT-RAM,b'\0'),metadata


def install(prior, blob, core, output, *, held_items=False, held_collection=False):
    held_items=bool(held_items or prior.get('equipment_resources',{}).get('parent_readers'))
    held_collection=bool(held_collection or prior.get('equipment_resources',{}).get('collection'))
    rows=records(prior,blob); table,metadata=encode(rows)
    previous=prior.get('display_aliases')
    display=copy.deepcopy(prior['clothing']['display'])
    if previous:
        if (previous['rows']!=rows or previous['table_sha256']!=sha256(table)
                or blob[OFFSET:OFFSET+len(table)]!=table):
            raise ValueError('Changed installed alias records/table')
    elif any(blob[OFFSET:OFFSET+len(table)]):
        raise ValueError('Alias index overlaps occupied package bytes')
    # Preserve the earlier package guard immediately before the reserved index,
    # and the campsite code starting immediately after it.
    if blob[OFFSET-16:OFFSET]!=bytes.fromhex('AFACC0DE')*4:
        raise ValueError('Changed alias-index predecessor guard')
    blob[OFFSET:OFFSET+len(table)]=table
    for item,payload in metadata.items():
        at=ITEMS+slot(item)*32
        expected=struct.pack('>HH',1024+slot(item),item)+bytes(24)+payload
        if previous:
            if blob[at:at+32]!=expected: raise ValueError('Changed display-only metadata')
        elif any(blob[at:at+32]): raise ValueError('Display metadata would overwrite an item')
        # Disabled as independent furniture: readers delegate to the selected
        # parent. This does not create another name, price, or ownership bit.
        blob[at:at+32]=expected
    if (previous and display['readers'].get('held_parent_readers',False)==held_items
            and display['readers'].get('held_collection',False)==held_collection
            and all(prior['sources'].get(p)==sha256((ROOT/p).read_bytes()) for p in SOURCES)):
        return display,copy.deepcopy(previous)

    parts={}
    for part,at,end,old in (
            ('display_items',0x6C00,0x6F00,display['readers']['code']),
            ('display_conversion',0x6270,0x6380,display['conversion']['code']),
            ('display_roster',0x6380,0x6540,display['roster_code'])):
        if (sha256(blob[at:at+old['bytes']])!=old['sha256'] or any(blob[at+old['bytes']:end])):
            raise ValueError('Changed complete alias-code reservation: '+part)
        defines=('AF_V3_DISPLAY_ALIASES=1',)
        if part=='display_items' and held_items:defines+=('AF_V3_HELD_ITEMS=1',)
        if part=='display_items' and held_collection:defines+=('AF_V3_HELD_COLLECTION=1',)
        extra=()
        if part=='display_roster':
            defines+=('AF_V3_DISPLAY_ROSTER_BRIDGE=1',);extra=('overlays/v3/clothing_roster.S',)
        code,receipt=compile_part(part,output/part,defines=defines,extra_sources=extra)
        if len(code)>end-at: raise ValueError('Alias helper exceeds its checked reservation')
        blob[at:end]=code+bytes(end-at-len(code));parts[part]=receipt

    def redirect(buffer,at,before,target):
        after=struct.pack('>II',jump(target),0)
        replace_checked(buffer,at,bytes.fromhex(before),after)
        return after.hex()

    old=display['roster_code']['symbols']['af_v3_all_display_clothing_index_bridge']
    target=parts['display_roster']['symbols']['af_v3_all_display_clothing_index_bridge']
    redirect(blob,0x6200,struct.pack('>II',jump(old),0).hex(),target)
    for group,prefix in (('item_hooks','af_v3_display_item_'),('collection_hooks','af_v3_display_catalogue_')):
        for row in display['readers'][group]:
            suffix=row['helper'] if group=='item_hooks' else ('record' if row['entry']==0x804699C0 else 'owned')
            target=parts['display_items']['symbols'][prefix+suffix]
            row.update(after=redirect(blob,row['entry']-0x80460000,row['after'],target),target=target)
    for row in display['conversion']['hooks']:
        target=parts['display_conversion']['symbols']['af_v3_room_'+row['kind']+'_item']
        row.update(after=redirect(core,row['entry']-CODE_RAM,row['after'],target),target=target)
    display['readers']['code']=parts['display_items']
    display['readers']['held_parent_readers']=held_items
    display['readers']['held_collection']=held_collection
    display['conversion']['code']=parts['display_conversion']
    display['roster_code']=parts['display_roster']
    return display,dict(format='AFV3-DISPLAY-ALIASES-1',rows=rows,table_ram=RAM,
        table_bytes=len(table),capacity=CAPACITY,table_sha256=sha256(table),
        record_offsets=dict(parent=28,native_footprint=30),additional_resident_bytes=0,
        saved_format_changed=False,saved_profile_changed=False,new_logical_imports=0,
        native_test='pending shared display conversion/readers',web_patcher_enabled=False)
