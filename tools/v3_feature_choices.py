"""Describe installed optional features and their automatic item requirements."""


def options(catalog, report):
    from v3_import_scope import availability
    admitted = {key for key, value in availability(catalog, report).items() if value['selectable']}
    groups = report.get('equipment_resources', {}).get('npc_extra', {}).get('events', {}).get('selection', {}).get('groups', [])
    definitions = []

    def add(key, name, description, items):
        items = sorted(set(items))
        if items and set(items) <= admitted:
            definitions.append(dict(id='feature/'+key, name=name, description=description, required_imports=items))

    add('cedar-trees', 'Cedar trees', 'Plant and grow cedar trees. Cedar saplings can be obtained using Animal Crossing item codes at Nook’s shop.', ['GAFE01-r0/item/2901'])
    add('coconut-palms', 'Coconut palms', 'Obtain coconuts using Animal Crossing item codes at Nook’s shop, then plant them to grow fruit-bearing palm trees near the coast. Coconuts do not wash ashore.', ['GAFE01-r0/item/2807'])
    add('golden-tools', 'Golden tools',
        'Add the golden shovel, net, rod, and axe, with their original acquisition routes. The shovel comes from a golden tree, the net and rod are rewards for completing their collections, and Farley awards the axe for maintaining a perfect town.',
        ['GAFE01-r0/item/'+item for item in ('2239','223A','223B','223C')])
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


def runtime_groups(groups, definitions):
    """Replace item-triggered event activation with explicit feature choices."""
    available = {row['id'] for row in definitions}
    for group in groups:
        feature = {'carried-quest':'feature/wisp', 'diary-holidays':'feature/gamecube-events'}.get(group['id'])
        if feature in available:
            group.update(any_imports=[], any_behaviours=[], any_features=[feature])
    return groups
