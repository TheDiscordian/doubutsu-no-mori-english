"""Source-discovered held equipment using the shared complete model converter.

This is the player's actual equipment representation, not a catalogue model.
Prepared objects do not enable inventory items, player actions, or acquisition.
"""
from collections import Counter
import json
import re
import struct

from aflib import sha256, u32
from apply_translation import write_new


FUNCTIONS = {
    'item_kind': (0x69914, 'mPlib_Get_ItemNoToItemKind', 680,
        '16977a47b6ceefbb9e55f6f6fe4cdce6d68f1aefa545a0e71a092eedc77f745c', 5, 0x1A),
    'shape': (0x68AF4, 'mPlib_Get_BasicItemShapeIndex_fromItemKind', 44,
        '379203f745c51d20cd81160595f62217b07772631eb42c7292f9c7d016d030bf', 4, 0x16),
    'animation': (0x68B20, 'mPlib_Get_BasicItemAnimeIndex_fromItemKind', 44,
        '379203f745c51d20cd81160595f62217b07772631eb42c7292f9c7d016d030bf', 4, 0x16),
    'data': (0x68AC8, 'mPlib_Get_Item_DataPointer', 44,
        'c680a1a4c11a931f5e25d0f72862b50b9dfd32a08502068981871eadc6151788', 5, 0x1A),
    'type': (0x68B4C, 'mPlib_Get_Item_DataPointerType', 40,
        'f168c50cbb095edfa0c11dfea34422ad106327937e8aa38b90e84d4a6a2e5af6', 4, 0x16),
}
PENDING = ('Prepared held artwork only; native equipment selection, player actions/animation, '
           'inventory/ground readers, acquisition, catalogue/collection, and saved-profile integration remain.')


def pocket_icons(source, equipment, address, capacity):
    """Resolve complete donor tool icons for the installed parent category records."""
    from title_assets import pack4, untile
    from v3_villager_art import native_palette
    _, parents = parent_records(source, equipment)
    if not equipment.get('parent_readers') or parents['rows'] != equipment['parent_readers']['rows']:
        raise ValueError('Pocket icons require the installed source-derived parents')
    functions = []
    for at, size, digest in (
            (0x27DDCC,1364,'6d4d8f5f7c64617bb068d63f77b0b776010670245f113ef466e9494b712c7738'),
            (0x27E320,672,'e357f68f7a995bf8f989c6fb7da6ad47f803b151b1ab9c34662eae8f0b9f1814')):
        raw, receipt = source.function(at)
        if len(raw) != size or sha256(raw) != digest:
            raise ValueError('Changed complete donor pocket icon consumer')
        functions.append(receipt)
    at, size = source.symbol('tool_tex_table$765')
    pointers = source.pointers(at, size)
    owner, owner_size = source.symbol('item_tex_data_table$779')
    if (size != 92*8 or source.raw('tool_tex_table$765') != bytes(size)
            or set(pointers) != set(range(at, at+size, 4)) or owner_size != 64
            or source.pointers(owner, owner_size).get(owner+8) != at):
        raise ValueError('Changed complete tool pocket icon table or category binding')
    data = bytearray(struct.pack('>4I',0x41464943,1,56,8)+bytes(56*8))
    resources, offsets, rows = [], {}, []
    for parent in parents['rows']:
        item = int(parent['item_id'],16); index = item-0x2200
        pair = []
        for lane, kind, n in ((0,'palette',32),(4,'texture',512)):
            target = pointers[at+index*8+lane]
            symbol, begin, length = source.containing(target, exact=True)
            if begin != target or length != n or source.pointers(target,n):
                raise ValueError('Pocket icon resource is not a complete CI4 icon')
            key = (target,kind)
            if key not in offsets:
                raw = source.data[target:target+n]
                converted = native_palette(raw) if kind == 'palette' else pack4(untile(raw,32,32,4))
                data.extend(bytes(-len(data)%32)); offset = len(data)
                offsets[key] = offset; data.extend(converted)
                resources.append(dict(symbol=symbol,donor_offset=target,kind=kind,bytes=n,
                    offset=offset,ram=address+offset,source_sha256=sha256(raw),sha256=sha256(converted)))
            pair.append(address+offsets[key])
        slot = item-0x2224
        struct.pack_into('>2I',data,16+slot*8,*pair)
        rows.append(dict(id=parent['id'],item_id=parent['item_id'],source_index=index,
            descriptor_ram=address+16+slot*8,palette=pair[0],texture=pair[1],
            menu_category=(item>>8)&15,source_type=parent['source_type'],selectable=False))
    if address & 31 or len(data)>capacity:
        raise ValueError('Pocket icon resources exceed the shared reservation')
    return bytes(data),dict(format='AFV3-POCKET-ICONS-1',rows=rows,resources=resources,
        source_functions=functions,source_table=dict(symbol='tool_tex_table$765',offset=at,bytes=size,
            pointers=pointers),ram=address,bytes=len(data),sha256=sha256(data),
        width=32,height=32,format_native='CI4/RGBA5551',profile_bits_enabled=0,
        original_tools_retained=36,ordinary_inventory_tested=False)


def parent_records(source, equipment):
    """Names/prices for implemented equipment categories; never enable an item."""
    _,selection=selection_records(source,equipment)
    installed=equipment['player_actions'].get('equipment_selection')
    if not installed or json.loads(json.dumps(selection['rows']))!=installed['rows']:
        raise ValueError('Parent readers require the installed source-derived selection records')
    tables={}
    for name,size,digest in (
            ('tool_price_table',186,'74a75db25db4e9eaf805f08d6b8475794acaea3a7bd990537805f5ecf03e8f45'),
            ('item1_2_tableNo',92,'d07c0e001d578fc1bb754c8b24ad7eb782c6bf94ba1ddff2b2c3239f97767975'),
            ('itemName_tool',1472,'b2f7827622de6c6db3102080320c79c77268bde1f7e3df7515dd9fa0c92222a8'),
            ('mSP_item1_start_idx_table',32,'4ba8d1ef30f8a15cb8db96b9a6f4c7ecb008b99b66302e7863f1e22a7550e05c')):
        data=source.raw(name)
        if len(data)!=size or sha256(data)!=digest:raise ValueError('Changed complete parent table: '+name)
        tables[name]=dict(offset=source.symbol(name)[0],bytes=size,sha256=digest)
    functions=[]
    for at,size,digest in (
            (0x784E0,544,'3f45cc5bf10f883d41575bc4f66cd1f8cfa1f86e46795ec386baaf412a7edb2b'),
            (0x78408,36,'7bf2f0cfba36247d0178e9df17c8462a710ab2dbb629273dfc3bfe865e094ca3'),
            (0x58E00,168,'63c24d921f9fd6a69471682d6593883ceb329b3f22af5a725b5cd73f441c6d8f')):
        raw,receipt=source.function(at)
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete parent reader')
        functions.append(receipt)
    links=[]
    for container,offset,target in (('l_price_info',8,'l_tool_price_info'),
            ('l_tool_price_info',0,'tool_price_table'),('item1_tableNo$430',8,'item1_2_tableNo')):
        at=source.symbol(container)[0]+offset;pointer=source.relocations.get(at)
        if source.data[at:at+4]!=bytes(4) or pointer!=(1,True,5,source.symbol(target)[0]):
            raise ValueError('Changed parent metadata pointer dependency')
        links.append(dict(container=container,offset=offset,target=target))
    names=source.raw('itemName_tool');prices=source.raw('tool_price_table');types=source.raw('item1_2_tableNo')
    if prices[-2:]!=b'\xff\xff' or b'\xff\xff' in [prices[i:i+2] for i in range(0,184,2)]:
        raise ValueError('Changed bounded parent price sentinel')
    table=bytearray(struct.pack('>4I',0x41464849,1,56,24)+bytes(56*24));rows=[]
    for selected in selection['rows']:
        original=selected['source'];item=int(selected['item_id'],16);index=item-0x2200
        name=names[index*16:index*16+16];price=struct.unpack_from('>H',prices,index*2)[0]
        if sha256(name)!=original['name_sha256'] or name.decode('ascii').rstrip(' ')!=original['name']:
            raise ValueError('Parent name disagrees with selected source identity')
        raw=struct.pack('>HHHBB',item,price,int(selected['display_item_id'],16),selected['native_kind'],types[index])+name
        table[16+(index-36)*24:16+(index-35)*24]=raw
        rows.append(dict(id=original['id'],item_id=selected['item_id'],name=original['name'],
            name_sha256=original['name_sha256'],name_source_symbol='itemName_tool',name_source_index=index,
            price=price,price_source_symbol='tool_price_table',price_source_index=index,
            source_type=types[index],native_kind=selected['native_kind'],
            display_item_id=selected['display_item_id'],profile_byte=selected['profile_byte'],
            profile_mask=selected['profile_mask'],record_sha256=sha256(raw),selectable=False))
    return bytes(table),dict(format='AFV3-HELD-PARENTS-1',rows=rows,source_tables=tables,
        source_functions=functions,pointer_dependencies=links,table_bytes=len(table),table_sha256=sha256(table),
        names_installed=True,prices_installed=True,native_inventory_category_installed=False,
        acquisition_installed=False,collection_installed=False,logical_imports_added=0,profile_bits_enabled=0)


def selection_records(source, equipment, *, categories=None):
    """Build shared item/kind/profile records from implemented source categories.

    The parent's canonical collection identity owns its one profile bit. These
    records do not set that bit, install inventory readers, or add web choices.
    """
    from v3_room_aliases import discover as room_aliases
    from v3_registry import furniture_identity
    inventory=discover(source);aliases=room_aliases(source)
    raw,visibility=source.function(0x1707E4)
    if (visibility['symbol']!='Player_actor_Get_ItemKind' or len(raw)!=232
            or sha256(raw)!='929013de1a36bb0912b94a5804290ce08a49a6fe3607f8f562b848355de0f58f'):
        raise ValueError('Changed complete donor held-item visibility rules')
    actions=equipment['player_actions']
    if categories is None:
        categories=actions.get('equipment_selection',{}).get('categories',[23])
    categories=sorted(set(categories))
    if not categories or set(categories)-{22,23}:
        raise ValueError('Unimplemented held selection category')
    if (actions['enabled_imported_actions']!=[109] or not actions.get('fan_activation')
            or not actions['held_dispatch']['net_reset']['installed']):
        raise ValueError('Equipment selection requires the complete fan action category')
    if 22 in categories:
        rigs=equipment.get('held_rig_actions',{})
        preview=equipment.get('inventory_preview',{})
        if (22 not in rigs.get('category_indices',[]) or not rigs.get('loop_sound_installed')
                or not preview.get('animated_rigs_installed')):
            raise ValueError('Animated selection requires complete actions, sound, and inventory')
    kinds={r['item_id']:r for r in equipment['kind_readers']['rows']}
    source_rows={r['id']:r for r in inventory['rows']}
    category_names={22:'pinwheel',23:'fan'}
    expected={a['parent_item_id'] for a in aliases['rows']
        if a['category'] in {category_names[c] for c in categories}}
    if {r['item_id'] for r in kinds.values() if r['item_main'] in categories}!=expected:
        raise ValueError('Installed kinds omit a complete source category')
    records=[];table=bytearray(struct.pack('>4I',0x41464853,1,92,8)+bytes(92*8))
    for alias in aliases['rows']:
        if alias['parent_item_id'] not in expected:continue
        item=int(alias['parent_item_id'],16);row=source_rows[alias['parent_id']];kind=kinds[row['item_id']]
        display=int(alias['display_item_id'],16);index,_=furniture_identity(display)
        animated=kind['item_main']==22
        bank_limit=equipment['animated_rigs']['allocation']['bank_bytes'] if animated else 4376
        if (not 0x2224<=item<0x225C or kind['source_kind']!=row['equipment_kind']
                or kind['native_kind']!=36+row['equipment_kind']
                or not kind['resource_ready'] or not kind['shape_installed']
                or kind['combined_bank_bytes']>bank_limit
                or alias['category']!=category_names[kind['item_main']]
                or (animated and kind['native_kind'] not in equipment['held_rig_actions']['native_kinds'])
                or not 99<=kind['native_kind']<115
                or alias['context_outputs']['room_placement']!=[row['item_id']]
                or alias['context_outputs']['collection_record']!=[alias['display_item_id']]):
            raise ValueError('Incomplete source-held category dependency or identity')
        slot=index-1024;byte=32+slot//8;mask=1<<(slot%8)
        struct.pack_into('>HbBHBB',table,16+(item-0x2200)*8,item,kind['native_kind'],1,byte,mask,1)
        records.append(dict(id=row['id'],item_id=row['item_id'],native_kind=kind['native_kind'],
            passive=True,profile_byte=byte,profile_mask=mask,display_item_id=alias['display_item_id'],
            collection_index=index,room_placement_uses_display=False,equipment_ready=True,
            inventory_installed=False,selectable=False,source=row,alias=alias))
    if (not records or {r['item_id'] for r in records}!=expected
            or len({r['native_kind'] for r in records})!=len(records)):
        raise ValueError('Incomplete shared held selection categories')
    return bytes(table),dict(format='AFV3-HELD-SELECTION-1',rows=records,
        categories=categories,
        donor_visibility=visibility,source_functions=inventory['functions'],
        source_tables=inventory['tables'],alias_functions=aliases['functions'],
        source_rel_sha256=sha256(source.rel),table_bytes=len(table),table_sha256=sha256(table),
        original_items_retained=36,logical_imports_added=0,profile_bits_enabled=0)


def selector_tables(source, specifications):
    """Read complete bounded tables through their verified donor consumers."""
    functions, tables, values = {}, {}, {}
    byte_tables = {}
    for name, location, span in re.findall(
            r'^(\S+) = \.rodata:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ',
            source.symbols,re.M):
        byte_tables.setdefault(int(location,16),[]).append((name,int(span,16)))
    for role, (address, symbol, size, digest, section, low) in specifications.items():
        raw, receipt = source.function(address)
        high = receipt['relocations'].get(0x12)
        if (receipt['symbol'] != symbol or len(raw) != size or sha256(raw) != digest
                or high is None or high[:3] != (6,1,section)
                or receipt['relocations'] != {0x12:high,low:(4,1,section,high[3])}):
            raise ValueError('Changed handheld equipment selector: '+role)
        count = u32(raw,8)&0xFFFF
        if role == 'item_kind': count += 1
        stride = 4 if section == 5 else 1
        at, n = high[3], count*stride
        base, length = source.sections[section]
        if not count or at+n > length:
            raise ValueError('Handheld selector table escapes donor section')
        data = source.data[at:at+n] if section == 5 else source.rel[base+at:base+at+n]
        if section == 5 and source.containing(at,exact=True)[1:] != (at,n):
            raise ValueError('Handheld selector does not use a complete table')
        pointers = {}
        if section == 5:
            pointers = {key-at:row for key,row in source.relocations.items() if at <= key < at+n}
            expected_section = 1 if role == 'item_kind' else 5
            if (data != bytes(n) or set(pointers) != set(range(0,n,4)) or
                    any(row[:3] != (1,True,expected_section) for row in pointers.values())):
                raise ValueError('Incomplete or external handheld table pointers')
        else:
            # These are complete immutable byte tables, not pointer arrays.
            # Their bounds come from the verified consumer, not an item count.
            matches = byte_tables.get(at,[])
            if len(matches)!=1 or matches[0][1]!=n:
                raise ValueError('Handheld selector does not use a complete byte table')
        functions[role] = receipt
        tables[role] = dict(section=section,offset=at,bytes=n,count=count,sha256=sha256(data),
                            pointers=pointers)
        values[role] = data
    return functions, tables, values


def discover(source):
    """Follow item -> equipment kind -> shape/animation -> actual resource root."""
    functions, tables, values = selector_tables(source, FUNCTIONS)

    count=tables['data']['count']
    if tables['type']['count'] != count or tables['shape']['count'] != tables['animation']['count']:
        raise ValueError('Handheld table counts disagree')
    raw,_=source.function(FUNCTIONS['item_kind'][0])
    first=-struct.unpack_from('>h',raw,6)[0]
    rows=[]; rejected=[]
    names=source.raw('itemName_tool')
    if first>>8 != 0x22 or len(names) != tables['item_kind']['count']*16:
        raise ValueError('Handheld selector/name inventory disagrees')
    for i in range(tables['item_kind']['count']):
        target=tables['item_kind']['pointers'][i*4][3]
        relative=target-FUNCTIONS['item_kind'][0]
        if (relative<0x28 or relative%8 or relative+8>len(raw)
                or u32(raw,relative)&0xFFFF0000 != 0x38600000
                or u32(raw,relative+4)!=0x4E800020):
            raise ValueError('Handheld switch target is not a complete constant return')
        kind=struct.unpack_from('>h',raw,relative+2)[0]
        item=first+i
        if kind==-1:
            rejected.append(f'{item:04X}');continue
        if not 0<=kind<tables['shape']['count']-1:
            raise ValueError('Handheld equipment kind escapes complete tables')
        shape=struct.unpack_from('b',values['shape'],kind)[0]
        animation=struct.unpack_from('b',values['animation'],kind)[0]
        if not -1<=shape<count or not -1<=animation<count:
            raise ValueError('Handheld shape/animation escapes resource table')
        name_raw=names[(item&255)*16:(item&255)*16+16]
        name=name_raw.decode('ascii').rstrip(' ')
        if not name or len(name_raw)!=16:
            raise ValueError('Handheld parent has no complete name')
        row=dict(id=f'GAFE01-r0/item/{item:04X}',item_id=f'{item:04X}',name=name,
            name_sha256=sha256(name_raw),name_source_symbol='itemName_tool',name_source_index=item&255,
            equipment_kind=kind,shape_index=shape,
            animation_index=animation,runtime_installed=False,selectable=False)
        if shape==-1:
            row.update(category='separate-equipment-owner',
                       reason='The donor selects no root here; umbrella ownership needs its separate adapter.')
        else:
            root=tables['data']['pointers'][shape*4][3]
            name,at,n=source.containing(root,exact=True)
            data_type=values['type'][shape]
            if data_type not in (0,1):
                raise ValueError('Handheld shape selects an animation or unknown resource type')
            row.update(data_type=data_type,model_root=dict(symbol=name,offset=at,bytes=n),
                       category='static-held-model' if data_type==0 else 'animated-held-model')
            if data_type!=0:
                row['reason']='Actual held skeleton/animation and player behaviour need integration; not a static model.'
        rows.append(row)
    return dict(format='AFV3-HANDHELD-SOURCES-1',source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()),functions=functions,tables=tables,
        rejected_item_ids=rejected,rows=rows)


def kind_bindings(source):
    """All kind-indexed player consumers, derived once for every equipment ID."""
    functions,tables,values=selector_tables(source, {
        'player_default': (0x68A74,'mPlib_Get_BasicPlayerAnimeIndex_fromItemKind',40,
            '02499ead02c19ebf1b8904dc7cd7e88ef792ad61daec146dc9322b91019b713f',4,0x16),
        'item_main': (0x1708CC,'Player_actor_Get_BasicItemMainIndex_fromItemKind',44,
            'ea396731baec36f2c7a5f9077819b555b31db357f74e88a9e7023407bf99b275',4,0x16),
        'tumble': (0x177A14,'Player_actor_Get_PlayerAnimeIndex_fromItemKind_Tumble',40,
            'd817723fa836715ae2fa26d12412f3aa13db1b6dd0bc62f93cc86283655e5986',4,0x16),
        'getup': (0x178144,'Player_actor_Get_PlayerAnimeIndex_fromItemKind_Tumble_getup',40,
            'afe5f139d75452dc292039e34272d90d1ae154a4f4ebad83162f85b39a5f55bc',4,0x16),
    })
    equipment=discover(source);count=equipment['tables']['shape']['count']-1
    if any(t['count']!=count+1 for t in tables.values()):
        raise ValueError('Equipment kind consumer tables have inconsistent complete bounds')
    rows=[];seen=set()
    for row in sorted(equipment['rows'],key=lambda r:r['equipment_kind']):
        kind=row['equipment_kind']
        if kind in seen:raise ValueError('Ambiguous equipment kind identity')
        seen.add(kind)
        rows.append(dict(item_id=row['item_id'],source_kind=kind,
            player_animation=values['player_default'][kind],item_main=values['item_main'][kind],
            shape=row['shape_index'],animation=row['animation_index'],
            tumble=values['tumble'][kind],getup=values['getup'][kind]))
    if seen!=set(range(count)):raise ValueError('Incomplete equipment kind namespace')
    return dict(functions=functions,tables=tables,rows=rows,equipment=equipment)


def motion(source):
    """Discover complete held rigs and equipment-related player animations."""
    from v3_keyframes import animation, skeleton
    functions, tables, values = selector_tables(source, {
        'player_data': (0x68A44, 'mPlib_Get_Pointer_Animation', 48,
            '869d78d47d9b401bab78a6b6c6ede7327e07c65aec23380d7927258b7b59ebc1', 5, 0x1A),
        'player_default': (0x68A74, 'mPlib_Get_BasicPlayerAnimeIndex_fromItemKind', 40,
            '02499ead02c19ebf1b8904dc7cd7e88ef792ad61daec146dc9322b91019b713f', 4, 0x16),
    })
    equipment = discover(source)
    if tables['player_default']['count'] != equipment['tables']['shape']['count']:
        raise ValueError('Player and equipment kind tables disagree')
    types_at = source.sections[4][0]+equipment['tables']['type']['offset']
    types = source.rel[types_at:types_at+equipment['tables']['type']['count']]
    rigs, animations = {}, {}
    for index, kind in enumerate(types):
        root = equipment['tables']['data']['pointers'][index*4][3]
        if kind == 1:
            rigs[index] = skeleton(source, root)
        elif kind in (2,3,4,5):
            animations[index] = dict(resource_type=kind, **animation(source, root))
        elif kind != 0:
            raise ValueError('Unknown equipment motion resource type')
    parents, player_indices = [], set()
    for row in equipment['rows']:
        index = values['player_default'][row['equipment_kind']]
        if index >= tables['player_data']['count']:
            raise ValueError('Equipment player animation exceeds its source table')
        player_indices.add(index)
        parent = dict(item_id=row['item_id'], equipment_kind=row['equipment_kind'],
                      player_default_animation=index)
        if row['category'] == 'animated-held-model':
            shape, initial = row['shape_index'], row['animation_index']
            if initial not in animations:
                raise ValueError('Held rig has no real default animation')
            family = animations[initial]['resource_type']
            variants = [i for i,a in animations.items() if a['resource_type']==family]
            if any(animations[i]['joints'] != rigs[shape]['joints'] for i in variants):
                raise ValueError('Equipment animation family does not fit its held rig')
            parent.update(shape_index=shape, default_animation=initial, animation_resources=variants)
        parents.append(parent)
    # The complete fan setup requests player animation r5=0x8C at its actual
    # split-body initializer call. This adds the swing, not just the idle pose.
    raw, fan_setup = source.function(0x1962B0)
    if (fan_setup['symbol'] != 'Player_actor_setup_main_Swing_fan'
            or len(raw)!=172 or sha256(raw) !=
            '752b1ac4425874027cec62ed68b4d76afbebcbf0a29797301b599a843cd7f0bb'
            or sha256(json.dumps({str(k):v for k,v in fan_setup['relocations'].items()},
                sort_keys=True,separators=(',',':')).encode()) !=
            '8710fe69485d835b21b7fd8395bbcb9f6083d73c2ebb112d826e211311329414'):
        raise ValueError('Changed complete fan animation setup')
    swing = u32(raw, 0x6C)&0xFFFF
    if swing >= tables['player_data']['count']:
        raise ValueError('Fan swing exceeds player animation table')
    player_indices.add(swing)
    player = {index:animation(source,tables['player_data']['pointers'][index*4][3],joints=26)
              for index in sorted(player_indices)}
    return dict(format='AFV3-HELD-MOTION-SOURCES-1',
        source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()),
        selector_functions=functions, selector_tables=tables, fan_setup=fan_setup,
        fan_swing_animation=swing, equipment=equipment, parents=parents,
        skeletons=rigs, equipment_animations=animations, player_animations=player,
        runtime_installed=False, selectable=False)


def convert_motion(source, output):
    from v3_keyframes import compile_animations
    description = motion(source)
    rows = [{k:v for k,v in row.items() if k!='resource_type'}
            for row in description['equipment_animations'].values()]
    rows += list(description['player_animations'].values())
    # Shared source roots remain a single resource regardless of consumers.
    unique = {row['header']['donor_offset']:row for row in rows}
    asset, compiled = compile_animations(source, list(unique.values()))
    report = dict(format='AFV3-HELD-MOTION-PREPARED-1', version=1,
        object_file='held-motion.n64obj.bin', object_bytes=len(asset), object_sha256=sha256(asset),
        **compiled, source=description, selectable=False,
        pending_reason='Motion data only; native rig bindings, player actions, and selected ownership remain.')
    output.mkdir(parents=True,exist_ok=False)
    write_new(output/report['object_file'],asset)
    write_new(output/'art.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def annotate_inventory(items,held):
    """Attach actual equipment dependencies to the single donor inventory."""
    by_id={row['donor_item_id']:row for row in items}
    if len(by_id)!=len(items):raise ValueError('Duplicate donor inventory identity')
    for row in held['rows']:
        target=by_id.get(row['item_id'])
        if target is None or target['name_sha256']!=row['name_sha256'] or target['selectable']:
            raise ValueError('Handheld source does not bind the complete donor inventory')
        target['handheld']=row


def descriptor(row):
    if row['category']!='static-held-model' or row.get('data_type')!=0:
        raise ValueError('Handheld skeletons/owners cannot become static substitutes')
    model=row['model_root']
    return dict(kind='static-held-model',shape_index=row['shape_index'],
                models={'opaque':(model['symbol'],model['offset'],model['bytes'])})


def rig_descriptor(row, rig):
    """Follow every shown joint, deduplicating shared roots without flattening."""
    root = row['model_root']
    if (row['category'] != 'animated-held-model' or row.get('data_type') != 1 or
            (root['symbol'], root['offset'], root['bytes']) !=
            (rig['header']['symbol'], rig['header']['donor_offset'], rig['header']['bytes'])):
        raise ValueError('Animated handheld root does not match its complete skeleton')
    models, labels, bindings = {}, {}, []
    for joint in rig['rows']:
        if 'model' not in joint:
            continue
        model = joint['model']; at = model['donor_offset']
        if at not in labels:
            label = 'joint'+str(joint['index']); labels[at] = label
            models[label] = model['symbol'], at, model['bytes']
        bindings.append(dict(joint_index=joint['index'], model_label=labels[at]))
    return dict(kind='animated-held-model', shape_index=row['shape_index'],
                skeleton=rig, joint_models=bindings, models=models)


def scan(source):
    from v3_furniture_pipeline import prepare_models
    from v3_event_acquisition import annotate
    from v3_keyframes import compile_animations
    report=discover(source)
    annotate(report,source)
    motions=motion(source)
    animation_sizes={i:len(compile_animations(source,[{k:v for k,v in r.items() if k!='resource_type'}])[0])
                     for i,r in motions['equipment_animations'].items()}
    motion_parents={r['item_id']:r for r in motions['parents']}
    prepared={}
    for row in report['rows']:
        row['asset_ready']=False
        if row['category'] not in ('static-held-model','animated-held-model'):continue
        index=row['shape_index']
        if index not in prepared:
            try:
                rig = motions['skeletons'][index] if row['data_type']==1 else None
                desc = rig_descriptor(row,rig) if rig else descriptor(row)
                _,body,resources,_,models,_,sections=prepare_models(source,desc)
                artwork_bytes=(len(body)+sum(n for _,n in sections)+15)&~15
                total=artwork_bytes+((rig['joint_table']['bytes']+8+15)&~15 if rig else 0)
                prepared[index]=dict(asset_ready=True,object_bytes=total,
                    vertices=sum(r['bytes']//16 for r in resources if r['kind']=='vertices'),
                    triangles=sum(len(r.get('triangles',[])) for m in models.values() for r in m['rows']),
                    reason=PENDING)
                if rig:
                    variants=motion_parents[row['item_id']]['animation_resources']
                    maximum=max(animation_sizes[i] for i in variants)
                    prepared[index].update(joints=rig['joints'],shown_joints=rig['shown_joints'],
                        artwork_bytes=artwork_bytes,maximum_animation_bytes=maximum,
                        maximum_model_animation_bytes=total+maximum)
            except ValueError as error:
                prepared[index]=dict(asset_ready=False,reason=str(error))
        row.update(prepared[index])
        if row['category']=='animated-held-model':row['motion_binding']=motion_parents[row['item_id']]
    report['counts']=dict(Counter(r['category'] for r in report['rows']))
    report['counts']['prepared_model_roots']=sum(r['asset_ready'] for r in prepared.values())
    report['counts']['usable_imports']=0
    return report


def convert_rigs(source,output,selected=()):
    """Compile the supported animated category through shared graphics and rigs."""
    from v3_furniture_pipeline import prepare_models,compile_models
    from v3_keyframes import compile_skeleton
    inventory=scan(source);requested=set(selected)
    candidates=[r for r in inventory['rows'] if r['category']=='animated-held-model'
                and (not requested or r['item_id'] in requested)]
    if requested and (requested!={r['item_id'] for r in candidates} or
                      any(not r['asset_ready'] for r in candidates)):
        raise ValueError('Unsupported or unknown selected animated handheld item')
    candidates=[r for r in candidates if r['asset_ready']]
    if not candidates:raise ValueError('No supported animated handheld models')
    motions=motion(source)
    # Preflight every complete object before creating an output directory.
    prepared={i:prepare_models(source,rig_descriptor(next(r for r in candidates if r['shape_index']==i),
        motions['skeletons'][i])) for i in sorted({r['shape_index'] for r in candidates})}
    output.mkdir(parents=True,exist_ok=False);objects=[]
    for index,part in prepared.items():
        parents=[r for r in candidates if r['shape_index']==index]
        key=f'data-{index:04X}';directory=output/key;directory.mkdir()
        artwork,locations,models,sequence=compile_models(directory,part)
        if sequence is not None:raise ValueError('Animated joints cannot use a flattened draw sequence')
        roots={root[1]:locations[label] for label,root in part[0]['models'].items()}
        suffix,rig=compile_skeleton(source,motions['skeletons'][index],roots,start=len(artwork))
        asset=artwork+suffix
        if len(asset)!=parents[0]['object_bytes']:
            raise ValueError('Animated compilation differs from shared preflight')
        filename=key+'.n64obj.bin';write_new(output/filename,asset)
        objects.append(dict(shape_index=index,resource_type=1,parent_item_ids=[r['item_id'] for r in parents],
            profile=part[0],resources=part[2],models=models,model_offsets=locations,
            artwork_bytes=len(artwork),skeleton=rig,root_offset=rig['header']['native_offset'],
            motion_bindings=[r['motion_binding'] for r in parents],
            maximum_animation_bytes=parents[0]['maximum_animation_bytes'],
            maximum_model_animation_bytes=parents[0]['maximum_model_animation_bytes'],
            object_file=filename,object_bytes=len(asset),object_sha256=sha256(asset)))
        print(json.dumps(dict(converted=key,parents=[r['item_id'] for r in parents],bytes=len(asset))),flush=True)
    report=dict(format='AFV3-ANIMATED-HELD-PREPARED-1',version=1,
        source_rel_sha256=inventory['source_rel_sha256'],source_symbols_sha256=inventory['source_symbols_sha256'],
        objects=objects,runtime_installed=False,selectable=False,pending_reason=PENDING)
    write_new(output/'inventory.json',(json.dumps(inventory,indent=2)+'\n').encode())
    write_new(output/'art.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def convert(source,output,selected=(),*,category=None):
    from v3_furniture_pipeline import prepare_models,compile_models
    if category == 'item-category-art':
        from v3_item_categories import convert as convert_categories
        return convert_categories(source,output,selected)
    if category == 'held-motion':
        if selected:raise ValueError('Held-motion preparation uses the complete source dependency bundle')
        return convert_motion(source,output)
    if category == 'animated-held-model':
        return convert_rigs(source,output,selected)
    if category not in (None,'static-held-model'):
        raise ValueError('Unsupported handheld conversion category')
    inventory=scan(source)
    requested=set(selected)
    candidates=[r for r in inventory['rows'] if r['category']=='static-held-model'
                and (not requested or r['item_id'] in requested)]
    if requested and (requested!={r['item_id'] for r in candidates} or
                      any(not r['asset_ready'] for r in candidates)):
        raise ValueError('Unsupported or unknown selected handheld item')
    candidates=[r for r in candidates if r['asset_ready']]
    if not candidates:raise ValueError('No supported handheld models')
    output.mkdir(parents=True,exist_ok=False);objects=[]
    for index in sorted({r['shape_index'] for r in candidates}):
        parents=[r for r in candidates if r['shape_index']==index]
        prepared=prepare_models(source,descriptor(parents[0]))
        key=f'data-{index:04X}';directory=output/key;directory.mkdir()
        asset,locations,models,sequence=compile_models(directory,prepared)
        if sequence is not None or len(asset)!=parents[0]['object_bytes']:
            raise ValueError('Handheld compilation differs from shared preflight')
        filename=key+'.n64obj.bin';write_new(output/filename,asset)
        objects.append(dict(shape_index=index,parent_item_ids=[r['item_id'] for r in parents],
            profile=prepared[0],resources=prepared[2],models=models,model_offsets=locations,
            object_file=filename,object_bytes=len(asset),object_sha256=sha256(asset)))
        print(json.dumps(dict(converted=key,parents=[r['item_id'] for r in parents],bytes=len(asset))),flush=True)
    report=dict(format='AFV3-HANDHELD-PREPARED-ASSETS-1',version=1,
        source_rel_sha256=inventory['source_rel_sha256'],source_symbols_sha256=inventory['source_symbols_sha256'],
        objects=objects,runtime_installed=False,selectable=False,pending_reason=PENDING)
    write_new(output/'inventory.json',(json.dumps(inventory,indent=2)+'\n').encode())
    write_new(output/'art.json',(json.dumps(report,indent=2)+'\n').encode())
    return report
