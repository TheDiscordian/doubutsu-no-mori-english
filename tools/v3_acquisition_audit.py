#!/usr/bin/env python3
"""Compare original acquisition membership with the installed cartridge.

This checks acquisition separately from resource readiness and code delivery.
It does not certify gameplay, hardware, or completeness of unrelated behaviours.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT
from v3_furniture_pipeline import Source
from v3_registry import furniture_source
from v3_surface_stock import list_items
from v3_password_acquisition import carried_items as carried_code_items


def donor_source():
    return Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())


def source_lists(source, prefix):
    result = {}
    for name, spans in source.names.items():
        if name.startswith(prefix) and len(spans) == 1:
            raw = source.raw(name)
            if len(raw) % 2:
                raise ValueError('Unaligned acquisition list: '+name)
            values = list_items(raw, 0)
            if len(values) != len(set(values)) or len(raw) != 2*(len(values)+1):
                raise ValueError('Unbounded acquisition list: '+name)
            result[name] = dict(items=values, bytes=len(raw), sha256=sha256(raw))
    return result


def audit(image, report, catalog, source):
    files = by_vrom(image)
    core = files[CODE_VROM].extract(image)
    blob = files[BLOB].extract(image)
    rows = []

    def loaded(packet, address, length):
        if not packet['ram'] <= address <= packet['ram']+packet['bytes']-length:
            raise ValueError('Acquisition data outside its complete resident packet')
        if 'physical' in packet:
            raw = image[packet['physical']:packet['physical']+packet['bytes']]
        else:
            raw = blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
        if sha256(raw) != packet['sha256']:
            raise ValueError('Changed complete acquisition packet')
        at = address-packet['ram']
        return raw[at:at+length]

    def record(key, route, established, evidence, consumers=None):
        rows.append(dict(id=key, name=catalog[key]['name'], kind=catalog[key]['kind'],
            route=route, status='installed' if established else 'missing',
            evidence=evidence, consumers=consumers or []))

    lists = source_lists(source, 'ftr_list')
    furniture = {r['id']: r for r in report['furniture']['imports']+[report['speed_bag']]}
    from v3_furniture_rewards import existing_system_items
    rewards = existing_system_items(report)
    from v3_password_acquisition import installed_items as code_items
    codes = code_items(report)
    from v3_holiday_acquisition import installed_items as holiday_items, exercise_items
    from v3_hra_rewards import installed_items as hra_items
    from v3_harvest_acquisition import installed_items as harvest_items
    special = ({r['id'] for r in furniture.values()
        if r['item_id'] in holiday_items(report) | hra_items(report)}
        | exercise_items(report) | harvest_items(report))
    stock = {}
    goods = files[0x11E6000].extract(image)
    for group, pointer in enumerate(struct.unpack_from('>12I', goods, report['shops']['table_offset'])):
        stock[group] = list_items(goods, pointer & 0xFFFFFF) if pointer else []
    seasonal = report['equipment_resources'].get('seasonal_stock', {})
    for key, row in catalog.items():
        if row['kind'] != 'furniture':
            continue
        item = furniture.get(key)
        if item is None:
            raise ValueError('Furniture lacks an installed identity: '+key)
        donor, index = furniture_source(item)
        expected = [name for name, data in lists.items() if donor in data['items']]
        for name in expected:
            proof = lists[name]
            matching = [r for r in report['shops']['imports']
                if r['item_id'] == item['item_id'] and r['donor_list'] == name]
            if matching:
                ok = all(int(item['item_id'], 16) in stock[r['group']] for r in matching)
            elif name == 'ftr_listTrain':
                ok = bool(seasonal.get('installed') and any(r['id'] == key
                    for r in seasonal.get('source', {}).get('imports', [])))
            elif name in ('ftr_listJonason', 'ftr_listKamakura', 'ftr_listTent'):
                ok = item['item_id'] in rewards and item.get('donor_list') == name
            elif name == 'ftr_listHomePage':
                ok = key in codes
            else:
                ok = key in special
            if name == 'ftr_listPostoffice':
                # The actual table binds these rewards to saved bank balances,
                # not to ordinary mail delivery or the furniture raffle.
                gift = source.raw('l_mml_postoffice_info')
                gifts = list(struct.iter_unpack('>IHHII', gift))
                match = [g for g in gifts if g[1] == donor]
                if len(match) != 1 or match[0][-1] not in (1000000,10000000,100000000,999999999):
                    raise ValueError('Changed original savings-reward dependency')
                from v3_bank_mail import checked as savings_checked, installed_items as savings_items
                if savings_checked(source,image,report) and item['item_id'] in savings_items(report):
                    record(key,'savings-account reward',True,dict(source=proof,
                        reward_table_sha256=sha256(gift),required_balance=match[0][-1]),
                        ['saved account balance','initial mail scheduling','selected reward',
                         'native mailbox/post-office receipt','success-only saved acknowledgement'])
                    continue
                rows.append(dict(id=key, name=row['name'], kind=row['kind'], status='V4-dependency',
                    route='savings-account reward', evidence=dict(source=proof,
                        reward_table_sha256=sha256(gift), required_balance=match[0][-1]),
                    consumers=['unavailable savings-account system'], personal_exception=False))
                continue
            record(key, name, ok, dict(source=proof, donor_item=f'{donor:04X}'),
                ['selection', 'delivery'] if name not in ('ftr_listA','ftr_listB','ftr_listC','ftr_listEvent','ftr_listLottery')
                else ['stock list', 'native selector'])
        if not expected:
            birth = source.raw('mRmTp_birth_type')[index]
            ok = key in special or (birth == 34 and key in codes)
            record(key, 'birth category '+str(birth), ok,
                dict(symbol='mRmTp_birth_type', index=index, birth=birth), ['reward/code provider'])

    for kind, prefix in (('floor', 'carpet_list'), ('wall', 'wall_list')):
        groups = source_lists(source, prefix)
        resources = [r for r in report['room_surfaces'].get('stock', {}).get('resources', []) if r['kind'] == kind]
        for key, row in catalog.items():
            if row['kind'] != kind:
                continue
            donor = int(key.rsplit('/', 1)[1], 16)
            for name, data in groups.items():
                if donor not in data['items']:
                    continue
                ok = False
                for resource in resources:
                    raw = blob[resource['blob_offset']:resource['blob_offset']+resource['bytes']]
                    if sha256(raw) != resource['sha256']:
                        raise ValueError('Changed surface stock bytes')
                    for entry in resource['imports']:
                        if entry['id'] == key and entry['source_symbol'] == name:
                            pointer = u32(raw, resource['table_offset']+entry['group']*4)
                            ok |= int(row['item_id'],16) in list_items(raw, pointer & 0xFFFFFF)
                ok |= name.endswith('HomePage') and key in codes
                ok |= name.endswith('Harvest') and key in harvest_items(report)
                record(key, name, bool(ok), dict(source=data), ['stock/reward membership'])

    clothing_lists = source_lists(source, 'cloth_list')
    clothes = report['clothing']['stock']
    clothing_raw = files[0x11E5000].extract(image)
    for key, row in catalog.items():
        if row['kind'] != 'clothing':
            continue
        donor = int(key.rsplit('/', 1)[1], 16)
        matches = [name for name, data in clothing_lists.items() if donor in data['items']]
        if not matches:
            from v3_import_scope import availability
            dependency = availability(catalog, report)[key]['dependency_only']
            record(key, 'authentic starting outfit', dependency,
                dict(standalone_stock=False), ['villager outfit dependency'])
        for name in matches:
            group = ord(name[-1])-ord('A')
            descriptor = clothes['groups'][group] if 0 <= group < len(clothes['groups']) else None
            ok = False
            if descriptor:
                offset = descriptor['segment'] & 0xFFFFFF
                values = struct.unpack_from('>'+str(sum(descriptor['counts']))+'H', clothing_raw, offset)
                ok = int(row['item_id'],16) in values
            record(key, name, ok, dict(source=clothing_lists[name]), ['seasonal stock membership'])

    e = report['equipment_resources']
    paper_lists = source_lists(source, 'binsen_list')
    # The native paper descriptor is independent of item-code permissions.
    paper_vrom, paper_end, paper_table = struct.unpack_from('>3I', core, 0x8010DAAC-CODE_RAM)
    owner = files.get(paper_vrom)
    paper = owner.extract(image) if owner else blob[paper_vrom-BLOB:paper_end-BLOB]
    if len(paper) != paper_end-paper_vrom:
        raise ValueError('Missing complete stationery stock owner')
    paper_table &= 0xFFFFFF
    for key, row in catalog.items():
        if row['kind'] == 'carried' and key.startswith('GAFE01-r0/item/20'):
            donor = int(key.rsplit('/',1)[1],16)
            for name, data in paper_lists.items():
                members = [v for v in data['items'] if v & 63 == donor & 63]
                if not members:
                    continue
                group = ord(name[-1])-ord('A')
                pointer = u32(paper, paper_table+group*4)
                values = list_items(paper, pointer & 0xFFFFFF)
                destination = int(row['item_id'],16)
                record(key, name, any(destination <= v < destination+4 for v in values),
                    dict(source=data, donor_quantity_items=members),
                    ['stock list', 'quantity creation', 'purchase'])

    diary_lists = source_lists(source, 'diary_list')
    diary = e.get('normal_acquisition', {}).get('diaries', {})
    if diary:
        expected = []
        for name in ('diary_listA','diary_listB','diary_listC'):
            values = [item+0x10 for item in diary_lists[name]['items']]+[0]
            expected.extend(values+[0]*(7-len(values)))
        raw = struct.pack('>21H',*expected)
        actual = loaded(e['normal_acquisition']['packet'],diary['table_ram'],len(raw))
        if actual != raw or sha256(actual) != diary['table_sha256']:
            raise ValueError('Changed complete original diary stock table')
    for key, row in catalog.items():
        if row['kind'] != 'diary':
            continue
        donor = int(key.rsplit('/',1)[1],16)
        for name, data in diary_lists.items():
            if donor in data['items']:
                record(key, name, bool(diary.get('installed') and key in diary.get('identities', [])),
                    dict(source=data, minimum_shop_level=2, excludes_grab_bag_sale=True),
                    ['daily stock', 'paper-space placement', 'purchase', 'sold state'])

    normal = e.get('normal_acquisition', {})
    cedar = normal.get('cedars', {})
    if cedar:
        code = normal['code']
        if sha256(loaded(normal['packet'],code['ram'],code['bytes'])) != code['sha256']:
            raise ValueError('Changed complete normal-acquisition code')
        for hook in normal['hooks']:
            if u32(core,hook['address']-CODE_RAM) != hook['after']:
                raise ValueError('Changed normal-acquisition native hook')
        for consumer in cedar['consumers']:
            if (sha256(files[consumer['vrom']].extract(image)) != consumer['owner']['owner_sha256'] or
                    sha256(files[consumer['reloc']].extract(image)) != consumer['owner']['relocation_sha256']):
                raise ValueError('Changed connected normal-acquisition shop consumer')
        if normal.get('paper') and (sha256(paper) != normal['paper']['sha256'] or
                len(paper) != normal['paper']['bytes']):
            raise ValueError('Changed connected normal-acquisition stationery stock')
    for key in catalog:
        carried = next((r for r in e.get('carried_items', {}).get('rows', [])
            if r['id'] == key and not r['state_index']), None)
        if not carried or carried['native_category'] != 48:
            continue
        for route, address, field, consumers in (
            ('ordinary cedar sapling stock', 0x78CA8, 'shop_installed',
             ['daily stock', 'plant-space placement', 'purchase', 'sold state']),
            ('new-town cedar generation', 0x3E20, 'new_town_installed',
             ['new-town initialization', 'northern-acre conversion'])):
            raw, proof = source.function(address)
            record(key, route, bool(cedar.get(field)), dict(proof, sha256=sha256(raw)), consumers)

    # Regenerate category acquisition data from the original source and compare
    # actual loaded bytes. Preparations' historical installed=False fields are
    # not the authority for whether a live consumer exists.
    from v3_creature_spawns import calendars, insect_calendars
    from v3_creature_items import source_records
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    expected, calendar = calendars(source, native)
    fish = e['creature_fish']['world']
    fish_ok = loaded(fish['packet'], fish['calendar_ram'], len(expected)) == expected
    identities, _ = source_records(source)
    for item in identities:
        if item['category'] != 'fish' or item['id'] not in catalog:
            continue
        actor = calendar['actor_mapping'][item['source_index']]
        active = [(term, [list(v) for v in values if v[0] == actor])
            for term, values in enumerate(calendar['calendars']) if any(v[0] == actor for v in values)]
        record(item['id'], 'original fish seasons, times, habitats, and weights',
            bool(fish_ok and active and fish['spawn_manager_installed']),
            dict(calendar_sha256=sha256(expected), source_actor=item['source_index'],
                native_actor=actor, active_lists=active), ['native spawn manager', 'selected species filter'])
    expected, calendar = insect_calendars(source)
    insects = e['creature_insects']
    insect_ok = loaded(insects['packet'], insects['compiled']['symbols']['af_insect_calendar'], len(expected)) == expected
    manager = insects['manager']
    owner = files[manager['owner_vrom']].extract(image)
    if (sha256(owner) != manager['owner_sha256'] or
            owner[manager['address']-manager['owner_ram']:manager['address']-manager['owner_ram']+8].hex() != manager['after']):
        raise ValueError('Changed actual native insect spawn consumer')
    for item in identities:
        if item['category'] != 'insect' or item['id'] not in catalog:
            continue
        actor = item['source_index']
        active = [term for term, values in enumerate(calendar['calendars'][:72])
            if any(v[0] == actor for v in values)]
        extra = [row for row in calendar['additional_spawns'] if row[0] == actor]
        record(item['id'], 'original insect calendar or food spawn',
            bool(insect_ok and (active or extra) and manager['installed']),
            dict(calendar_sha256=sha256(expected), source_actor=actor,
                active_lists=active, food_spawns=extra), ['native spawn manager', 'habitat/filter', 'food spawn'])
    from v3_event_acquisition import discover
    description = discover(source)
    event = e['event_acquisition']
    expected = b''.join(struct.pack('>3H2B',r['first'],r['price'],r['message'],r['count'],r['kind'])
        for r in description['rows'])
    stock = blob[e['blob_offset']+event['table_offset']:e['blob_offset']+event['table_offset']+len(expected)]
    for category in description['rows']:
        for item in category['items']:
            if item['id'] in catalog:
                record(item['id'], 'original festival-stall stock',
                    stock == expected and event['acquisition_installed'] and event['purchase_menu_installed'],
                    dict(source_category=category['kind'], price=category['price'], table_sha256=sha256(expected)),
                    ['stock initialization', 'purchase transaction', 'sold state'])
    golden = e['golden_tools']
    reward = e['carried_items']['quest']['rewards']
    reward_code = reward['code']
    if sha256(loaded(reward['packet'],reward_code.get('ram',reward['ram']),reward_code['bytes'])) != reward_code['sha256']:
        raise ValueError('Changed golden-tool and reward acquisition code')
    for hook in reward['installed_hooks']:
        raw = files[hook['vrom']].extract(image)
        if u32(raw,hook['address']-hook['ram']) != hook['after']:
            raise ValueError('Changed connected golden-tool reward consumer')
    for key, item in golden['items'].items():
        if key in catalog:
            record(key, item['acquisition'], bool(golden['shared_behaviour_installed'] and not item['pending']),
                dict(provider='installed shared golden-tool and carried-quest rewards'),
                ['source reward conditions', 'selected tool', 'award delivery', 'earned flag'])
    villagers = report['villager_selection']
    from v3_asset_loader import BLOB_RAM
    code = villagers['code']; start = code['symbols']['af_v3_unseen_personality']-BLOB_RAM
    if sha256(blob[start:start+code['bytes']]) != villagers['compiled_sha256']:
        raise ValueError('Changed actual villager population selector')
    for hook in villagers['hooks']:
        at = int(hook['entry'],16)-CODE_RAM
        if core[at:at+8].hex() != hook['after']:
            raise ValueError('Changed connected native villager population hook')
    for key, item in catalog.items():
        if item['kind'] == 'villager':
            record(key, 'initial population and subsequent move-ins',
                item['actor_id'] in villagers['content_ready'] and item['actor_id'] in villagers['move_in_enabled'],
                dict(actor_id=item['actor_id'], selector_sha256=villagers['compiled_sha256']),
                ['original personality selection', 'selected roster', 'house/outfit dependency'])
    from v3_carried_selection import verify_quest_items
    spirit = verify_quest_items(image,report)
    for key, route, available, consumers in (
        ('GAFE01-r0/item/2523','original aerobics card handover',exercise_items(report),
            ['event greeting', 'card handover', 'attendance stamps', 'completed-card reward']),
        ('GAFE01-r0/item/2530','original Harvest cutlery handover',harvest_items(report),
            ['holiday participants', 'cutlery handover', 'turkey exchange', 'reward']),
        ('GAFE01-r0/item/2D28','original Wisp spirit-catching quest',spirit,
            ['Wisp appearance', 'natural spirit spawn', 'catching', 'quest handover', 'reward'])):
        record(key,route,key in available,dict(provider='authenticated installed source-bound event/quest provider'),consumers)
    for key in catalog:
        if key == 'GAFE01-r0/item/2807':
            rows.append(dict(id=key, kind='carried', name=catalog[key]['name'], status='V4-dependency',
                route='island fruit', evidence=dict(code_route_installed=key in carried_code_items(report)),
                consumers=['unavailable island system'], personal_exception=False))
    covered = {row.get('id') for row in rows}
    if set(catalog)-covered:
        raise ValueError('Acquisition audit omitted installed choices: '+str(sorted(set(catalog)-covered)))
    return dict(format='AFV3-ACQUISITION-AUDIT-1', runtime_abi=report['runtime_abi'],
        rom_sha256=sha256(image), donor_sha256=sha256(source.rel),
        counts=dict(Counter(row['status'] for row in rows)), rows=rows,
        complete=not any(row['status'] in ('missing','requires-consumer-review') for row in rows),
        scope='Original acquisition versus installed consumers; not gameplay or hardware certification')


def deferred_content(source, candidates):
    """Classify all remaining worksheet content from original dependencies."""
    from v3_registry import furniture_source_index
    birth = source.raw('mRmTp_birth_type')
    names = {19:'savings accounts',24:'e-Reader cards',25:'island facilities',
        26:'island NES rewards',29:'Museum building',30:'lighthouse quest'}
    result = []
    for item in candidates:
        if item['selectable']: continue
        donor = int(item['id'].rsplit('/',1)[1],16)
        if donor == 0x251E:
            dependency = 'custom designs'; evidence = dict(carried_item='sign board')
        else:
            index = furniture_source_index(donor); category = birth[index]
            dependency = names.get(category)
            evidence = dict(symbol='mRmTp_birth_type',source_index=index,category=category,
                table_sha256=sha256(birth))
            if category == 30:
                raw, proof = source.function(0x7D7C0)
                if sha256(raw) != '334237101eb430399de80f4680438edd2bc30eddcc9aef9c8a5e47a310af6ca9':
                    raise ValueError('Changed complete lighthouse reward source')
                if donor not in (u32(raw,4)&65535,u32(raw,28)&65535):
                    raise ValueError('Lighthouse reward does not match the original selector')
                evidence['reward_selector'] = proof
        result.append(dict(id=item['id'],name=item['name'],kind=item['kind'],
            status='V4-dependency' if dependency else 'requires-consumer-review',
            dependency=dependency,evidence=evidence,resources_prepared=item['imported']))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock', type=Path)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--output',type=Path,help='Write the generated audit under build/')
    args = parser.parse_args()
    import v3_optional_composition as composition
    from v3_import_progress import current_lock
    composition.use_build_lock(args.base_lock or current_lock())
    image, report = composition.inputs()
    source=donor_source()
    result = audit(image, report, composition.catalogue(image, report), source)
    from v3_import_progress import measure
    content = measure(args.base_lock or current_lock())
    result['deferred_content'] = deferred_content(source,content['rows'])
    result['complete'] &= not any(r['status']=='requires-consumer-review' for r in result['deferred_content'])
    if args.output:
        destination=args.output.resolve()
        if not destination.is_relative_to(ROOT/'build'):
            raise ValueError('Generated acquisition evidence belongs under build/')
        from apply_translation import write_new
        write_new(destination,(json.dumps(result,indent=2)+'\n').encode())
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print('Acquisition audit:', result['counts'])
        for row in result['rows']:
            if row['status'] != 'installed':
                print(row['status']+': '+row.get('name', row['kind'])+' — '+row['route'])
        print('Remaining content dependencies:',dict(Counter(r['status'] for r in result['deferred_content'])))


if __name__ == '__main__':
    main()
