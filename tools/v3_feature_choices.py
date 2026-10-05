"""Describe installed optional features and their automatic item requirements."""
import struct


def item_codes_installed(report):
    p=report.get('equipment_resources',{}).get('passwords',{})
    return bool(p.get('acquisition_installed') and p.get('keyboard_installed') and
        p.get('name_conversion_installed') and p.get('nook',{}).get('installed') and
        p.get('conversation',{}).get('native_bindings_installed'))


def item_code_patches(image, report):
    """Restore each native dispatcher, its relocation, and both root captions."""
    from aflib import by_vrom,sha256,u32
    from v3_event_text import MESSAGE,TABLE
    from textbanks import Bank
    if not item_codes_installed(report):return []
    files=by_vrom(image);n=report['equipment_resources']['passwords']['nook'];result=[]
    if set(n['native']['owners'])!={'cranny','conv','super','depart'}:
        raise ValueError('Incomplete item-code counter feature')
    for name,binding in n['native']['owners'].items():
        owner=report['shop_actors']['owners'][name]
        entry=files[owner['vrom']];rel_entry=files[binding['installed_reloc_vrom']]
        data=entry.extract(image);rel=rel_entry.extract(image)
        if (entry.pend or rel_entry.pend or sha256(data)!=binding['overlay_sha256'] or
                sha256(rel)!=binding['relocation_sha256'] or len(binding['patches'])!=3):
            raise ValueError('Changed complete item-code counter owner: '+name)
        frame=binding['frame']-owner['ram'];patches=binding['patches']
        if (patches[0]['offset']!=frame or patches[0]['before']!='8e190940' or
                patches[1]['offset']!=frame+12 or patches[1]['before']!='0320f809' or
                patches[2]['offset']!=binding['profile']-owner['ram']+0x14):
            raise ValueError('Changed item-code dispatcher contract: '+name)
        for patch in patches:
            at=patch['offset']
            if data[at:at+4].hex()!=patch['after']:raise ValueError('Changed item-code binding')
            result.append(dict(offset=entry.pstart+at,before=patch['after'],after=patch['before']))
        # A JAL relocation cannot remain on the restored original JALR.
        count=u32(rel,16);records=list(struct.unpack_from('>'+str(count)+'I',rel,20))
        target=0x44000000|(frame+12)
        if records.count(target)!=1:raise ValueError('Missing unique item-code dispatch relocation')
        keep=[value for value in records if value!=target]
        restored=(rel[:16]+struct.pack('>I',len(keep))+struct.pack('>'+str(len(keep))+'I',*keep)
            +bytes(len(rel)-24-4*len(keep))+rel[-4:])
        result.append(dict(offset=rel_entry.pstart,before=rel.hex(),after=restored.hex()))
    message=files[MESSAGE];table=files[TABLE].extract(image)
    if message.pend:raise ValueError('Compressed item-code dialogue cannot be selected')
    entries=Bank('messages',0,0,message.extract(image),table).entries()
    current=bytes.fromhex('7f180009000a01c4')+struct.pack('>H',n['dialogue']['first_choice']+1)
    original=bytes.fromhex('7f180009000a01c4000b')
    for root in n['dialogue']['root_edits']:
        row=entries[root['id']]
        if sha256(row)!=root['sha256'] or row.count(current)!=1:
            raise ValueError('Changed item-code root dialogue')
        restored=row.replace(current,original)
        if sha256(restored)!=root['before_sha256']:
            raise ValueError('Item-code disabling does not restore the original dialogue')
        start=0 if root['id']==0 else u32(table,(root['id']-1)*4)
        result.append(dict(offset=message.pstart+start+row.index(current),before=current.hex(),after=original.hex()))
    return result


def options(catalog, report):
    from v3_import_scope import availability
    bank = report.get('equipment_resources', {}).get('bank', {})
    savings_keys = {'GAFE01-r0/item/'+row['item'] for row in bank.get('mail', {}).get('source', {}).get('rewards', [])}
    admitted = {key for key, value in availability(catalog, report).items() if value['selectable']}
    groups = report.get('equipment_resources', {}).get('npc_extra', {}).get('events', {}).get('selection', {}).get('groups', [])
    definitions = []
    cedars = report.get('equipment_resources', {}).get('normal_acquisition', {}).get('cedars', {})
    cedar_stock = cedars.get('shop_installed') and cedars.get('new_town_installed')
    if item_codes_installed(report):
        from v3_password_acquisition import installed_items,carried_items
        plants = {'GAFE01-r0/item/2807'}
        if not cedar_stock: plants.add('GAFE01-r0/item/2901')
        code_items = (installed_items(report) | (carried_items(report) & plants))-savings_keys
        definitions.append(dict(id='feature/item-codes',name='Animal Crossing item codes',
            description='Enter Animal Crossing item codes at Nook’s shop to receive items enabled in your game.',
            required_imports=[],required_by_imports=sorted(code_items & admitted)))

    def add(key, name, description, items):
        items = sorted(set(items))
        if items and set(items) <= admitted:
            definitions.append(dict(id='feature/'+key, name=name, description=description, required_imports=items))

    add('cedar-trees', 'Cedar trees',
        'Cedar trees grow in the northern acres of new towns. Nook sells cedar saplings at supermarket size and above.'
        if cedar_stock else 'Plant and grow cedar trees. Cedar saplings can be obtained using Animal Crossing item codes at Nook’s shop.',
        ['GAFE01-r0/item/2901'])
    add('coconut-palms', 'Coconut palms', 'Obtain coconuts using Animal Crossing item codes at Nook’s shop, then plant them to grow fruit-bearing palm trees near the coast. Coconuts do not wash ashore.', ['GAFE01-r0/item/2807'])
    add('golden-tools', 'Golden tools',
        'Add the golden shovel, net, rod, and axe, with their original acquisition routes.',
        ['GAFE01-r0/item/'+item for item in ('2239','223A','223B','223C')])
    from v3_bank_mail import installed_items as savings_items
    if savings_items(report):
        add('savings-account', 'Savings account and rewards',
            'After paying off your house, deposit and withdraw Bells at the post office. Receive the original savings rewards by mail as your balance grows.',
            ['GAFE01-r0/item/'+row['item'] for row in bank['mail']['source']['rewards']])
    from v3_furniture_rewards import summer_installed
    if summer_installed(report):
        add('summer-camping', 'Summer camping',
            'A visiting camper can set up a tent in your town during June, July, and August. Talk and play games with the camper to obtain camping furniture.',
            ['GAFE01-r0/item/'+row['item_id'] for row in report['furniture']['imports']
             if row.get('reward_route')==23])
    quest = next((group for group in groups if group['id']=='carried-quest'), None)
    if quest:
        add('wisp', 'Wisp', 'Wisp can visit your town, and you can catch spirits for his quest. Spirits are not sold in shops.', quest['any_imports'])
    events = next((group for group in groups if group['id']=='diary-holidays'), None)
    if events:
        items = {key for key in events['any_imports'] if key in admitted and catalog[key]['kind']!='diary'}
        items.update(key for key in admitted if set(catalog[key]['dependencies']) & items)
        add('gamecube-events', 'GameCube holidays and events',
            'Add the GameCube holiday visitors, morning aerobics, and Harvest Festival. Includes their event items and rewards.', items)
    return definitions


def requests(catalog, definitions, selected):
    """Keep feature choices separate from items supplied by those features."""
    owned = {item for row in definitions for item in row['required_imports']}
    return sorted((set(selected)-owned) | {row['id'] for row in definitions})


def update_report(image, report, selection):
    """Record the actual composed counter bindings without changing resources."""
    from aflib import by_vrom,sha256
    from v3_event_text import MESSAGE,TABLE
    from textbanks import Bank
    if not item_codes_installed(report):return
    files=by_vrom(image);n=report['equipment_resources']['passwords']['nook']
    n['feature_enabled']='feature/item-codes' in selection.get('enabled_features',selection['requested'])
    for name,binding in n['native']['owners'].items():
        owner=report['shop_actors']['owners'][name]
        binding['overlay_sha256']=sha256(files[owner['vrom']].extract(image))
        binding['relocation_sha256']=sha256(files[binding['installed_reloc_vrom']].extract(image))
        owner.update(output_sha256=binding['overlay_sha256'],relocation_sha256=binding['relocation_sha256'])
    entries=Bank('messages',0,0,files[MESSAGE].extract(image),files[TABLE].extract(image)).entries()
    for row in n['dialogue']['root_edits']:row['sha256']=sha256(entries[row['id']])
    for row in n['dialogue']['resources']:row['sha256']=sha256(files[row['vrom']].extract(image))


def runtime_groups(groups, definitions):
    """Replace item-triggered event activation with explicit feature choices."""
    available = {row['id'] for row in definitions}
    for group in groups:
        feature = {'carried-quest':'feature/wisp', 'diary-holidays':'feature/gamecube-events',
            'savings-account':'feature/savings-account'}.get(group['id'])
        if feature in available:
            group.update(any_imports=[], any_behaviours=[], any_features=[feature])
    return groups
