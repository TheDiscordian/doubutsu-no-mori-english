"""Admit complete source holiday gifts through the installed shared owner.

Initial acquisition stays with Tortimer. The source reorderable list remains
orderable after collection, without inserting rewards into ordinary shop stock.
"""
import json
import struct

from aflib import by_vrom,sha256
from v3_asset_loader import ROOT

SOURCES=('tools/v3_holiday_acquisition.py','tools/v3_holiday_rewards.py',
    'tools/v3_holiday_world.py','tools/v3_holiday_selection.py',
    'tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py','tools/v3_catalogue.py')


def providers_installed(report):
    """Readiness of the retained complete gift/diary provider, not a V4 label."""
    n=report.get('equipment_resources',{}).get('npc_extra',{})
    events=n.get('events',{})
    return bool(n.get('installed') and n.get('world',{}).get('installed') and
        n.get('actor_callbacks_bound') and n.get('lifecycle',{}).get('callbacks_installed') and
        n.get('dialogue',{}).get('installed') and n.get('optional_dialogue',{}).get('installed') and
        events.get('selection',{}).get('installed') and
        events.get('calendar',{}).get('actor_admission_bound') and
        events.get('dispatch',{}).get('complete_dependency_preflight') and
        events.get('festivals',{}).get('native_services_bound') and
        events.get('participants',{}).get('unbound_services')==[])


def installed_items(report):
    """Admit the connected Mayor gifts; the separate exercise prize is reviewed separately."""
    if not providers_installed(report):return set()
    group=next((g for g in report['equipment_resources']['npc_extra']['events']['selection']['groups']
                if g['id']=='diary-holidays'),None)
    if not group:return set()
    return {r['item_id'] for r in report['furniture']['imports']
        if r.get('holiday_acquisition',{}).get('route')=='holiday' and
        r['holiday_acquisition'].get('native_delivery_installed') and
        r['holiday_acquisition'].get('destination_item')==r['item_id'] and
        r['holiday_acquisition'].get('events') and not r['holiday_acquisition'].get('dependencies') and
        r['id'] in group['any_imports'] and r.get('runtime_installed') and
        not set(r.get('remaining',[]))-{'representative native execution','ordinary gameplay and save/restart'}}


def verify_installed_items(image,report):
    """Authenticate all admitted gift identities, providers, English text, and ordering."""
    items=installed_items(report)
    if not items:return items
    from v3_furniture_pipeline import Source
    from v3_furniture_install import catalogue_record,order_mask
    from v3_import_storage import ITEMS
    from v3_registry import furniture_source
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    binding=checked(source,image,report)
    if binding is None:raise ValueError('Missing installed holiday acquisition')
    from v3_holiday_selection import groups
    from v3_npc_registry import TABLE
    n=report['equipment_resources']['npc_extra'];events=n['events']
    group=next(g for g in groups(image,report) if g['id']=='diary-holidays')
    expected={(n['packet']['ram']+TABLE+16+44*i+4,3,1) for i in range(5)}
    expected.add((events['festivals']['code']['symbols']['af_hp_available'],1,0))
    expected.add((events['dispatch']['bindings']['af_holiday_decoration_ready'],31,7))
    if (len(group['fields'])!=7 or
        {(f['ram'],f['enabled'],f['disabled']) for f in group['fields']}!=expected):
        raise ValueError('Incomplete installed holiday provider activation fields')
    from v3_asset_loader import BLOB
    blob=by_vrom(image)[BLOB].extract(image)
    for row in report['furniture']['imports']:
        if row['item_id'] not in items:continue
        donor,_=furniture_source(row);destination=binding['destinations'].get(donor)
        record=catalogue_record(row);slot=row['runtime_index']-1024
        metadata=blob[ITEMS+slot*32:ITEMS+(slot+1)*32]
        if (not destination or destination['item']!=int(row['item_id'],16) or
            destination['index']!=row['runtime_index'] or not catalogue_source(source,donor,slot,record) or
            row['donor_list_sha256']!=sha256(source.raw(row['donor_list'])) or
            row['ordinary_stock'] or row['stock_group']!=255 or row['reward_route']!=0 or
            struct.unpack_from('>2H',metadata)!=(row['runtime_index'],destination['item']) or
            metadata[7]!=1 or metadata[24]!=order_mask(record) or metadata[27]!=0):
            raise ValueError('Changed installed holiday gift identity, source membership, or metadata')
    return items


def contract(source):
    from v3_holiday_rewards import discover
    if not hasattr(source,'holiday_reward_contract'):
        source.holiday_reward_contract=discover(source)
    return source.holiday_reward_contract


def exercise_contract(source):
    """Read the prize and required card from the complete donor controller."""
    if not hasattr(source,'holiday_exercise_contract'):
        raw,receipt=source.function(0x7C8BC)
        if (receipt['symbol']!='mSC_Radio_Set_Talk_Proc' or len(raw)!=1600 or
                sha256(raw)!='8b8f9951b01fa0318bdfdc36fc29bf041cce0ee8b262f6f056431656e2ad5dfc'):
            raise ValueError('Changed complete summer-exercise source controller')
        # Both finish branches load the same prize; new-card creation loads the
        # actual first state. These are checked PPC instructions, not item lists.
        prize=struct.unpack_from('>I',raw,0x3B8)[0]
        second=struct.unpack_from('>I',raw,0x480)[0]
        card=struct.unpack_from('>I',raw,0x268)[0]
        if prize!=second or prize>>16!=0x3800 or card>>16!=0x3800:
            raise ValueError('Changed complete exercise prize/card creation')
        source.holiday_exercise_contract=dict(item=prize&65535,card=card&65535,
            symbol=receipt['symbol'],sha256=receipt['sha256'],receipt=receipt)
    return source.holiday_exercise_contract


def acquisition_bytes(source,symbol):
    exercise=exercise_contract(source)
    if symbol==exercise['symbol']:return source.function(exercise['receipt']['offset'])[0]
    return source.raw(symbol)


def checked(source,image,report):
    from v3_holiday_rewards import encode
    from v3_holiday_selection import packets,location
    from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE
    from textbanks import Bank
    n=report.get('equipment_resources',{}).get('npc_extra',{})
    if not n.get('world'):return None
    events=n.get('events',{});selection=events.get('selection',{})
    optional=n.get('optional_dialogue',{});world=n['world']
    if (not n.get('installed') or not world.get('installed') or
            not n.get('actor_callbacks_bound') or not n['lifecycle']['callbacks_installed'] or
            not n['dialogue']['installed'] or not optional.get('installed') or
            not selection.get('installed') or not events['calendar']['actor_admission_bound'] or
            not events['dispatch']['complete_dependency_preflight'] or
            not events['festivals']['native_services_bound'] or events['participants']['unbound_services']):
        raise ValueError('Holiday gifts require the complete connected native providers')
    e=report['equipment_resources']
    for p in packets(e):
        if sha256(image[p['physical']:p['physical']+p['bytes']])!=p['sha256']:
            raise ValueError('Changed complete holiday acquisition packet')
    def read(ram,size):
        _,at=location(e,ram,size)
        return image[at:at+size]
    if sha256(read(optional['ram'],optional['bytes']))!=optional['sha256']:
        raise ValueError('Changed complete shared holiday conversation and handover')
    for row in optional['redirects']:
        if read(row['address'],8)!=bytes.fromhex(row['after']):
            raise ValueError('Changed actual holiday world/card redirect')
    description=contract(source)
    if world['reward_contract']['rows']!=description['rows']:
        raise ValueError('Installed holidays differ from the complete source selectors')
    rewards=world['rewards'];raw=read(rewards['ram'],rewards['bytes'])
    if raw!=encode(description) or sha256(raw)!=rewards['sha256']:
        raise ValueError('Changed complete source holiday reward table')
    mapping=world['destinations'];data=read(mapping['ram'],mapping['bytes'])
    rows=mapping['rows']
    expected=struct.pack('>4s6H',b'AFHW',1,len(rows),8,16+8*len(rows),0,0)+b''.join(
        struct.pack('>4H',r['donor_item'],r['item'],r['index'],int(r['diary'])) for r in rows)
    if data!=expected or sha256(data)!=mapping['sha256'] or len(rows)!=66:
        raise ValueError('Changed complete installed holiday destination map')
    # Later categories append to these banks. Check the exact retained records,
    # not obsolete hashes of the shorter historical complete bank.
    files=by_vrom(image)
    choices=n['dialogue']['text']['resources'][2]['vrom']
    for kind,a,b,key in (('message',MESSAGE,TABLE,'rows'),('select',choices,CHOICE_TABLE,'choices')):
        bank=Bank(kind,a,b,files[a].extract(image),files[b].extract(image)).entries()
        for row in n['dialogue']['text'][key]:
            if row['id']>=len(bank) or sha256(bank[row['id']])!=row['sha256']:
                raise ValueError('Changed actual official holiday '+kind)
    candidates={int(i,16) for r in description['rows'] for i in r['source_items']}
    destinations={r['donor_item']:r for r in rows if r['donor_item'] in candidates}
    if len(candidates)!=65 or destinations.keys()!=candidates:
        raise ValueError('Incomplete whole-source holiday destination set')
    exercise=exercise_contract(source)
    owner=events['exercise'];prepared=ROOT/owner['prepared']
    if sha256((prepared/'prepared.json').read_bytes())!=owner['prepared_sha256']:
        raise ValueError('Changed complete exercise acquisition preparation')
    description_card=json.loads((prepared/'prepared.json').read_bytes())
    functions=description_card['card_functions']
    if len(functions)!=17:raise ValueError('Incomplete exercise card function family')
    for expected_function in functions:
        _,actual=source.function(expected_function['offset'])
        if json.loads(json.dumps(actual))!=expected_function:
            raise ValueError('Installed exercise functions differ from complete donor')
    if not any(r['symbol']==exercise['symbol'] for r in functions):
        raise ValueError('Missing exercise source prize controller')
    prizes={r['donor_item']:r for r in rows if r['donor_item']==exercise['item']}
    if len(prizes)!=1:raise ValueError('Missing installed exercise prize destination')
    return dict(destinations=destinations,events=description['rows'],
        exercise_destinations=prizes,exercise=exercise,
        source_table_sha256=description['event_table_sha256'],
        native_delivery_installed=True,ordinary_gameplay_tested=False)


def furniture(source,item,index,lists):
    del index
    events=[r for r in contract(source)['rows'] if f'{item:04X}' in r['source_items']]
    exercise=exercise_contract(source);card_prize=item==exercise['item']
    if (not events and not card_prize) or item>>8==0x2B:return None
    if (card_prize and lists) or (lists and (len(lists)!=1 or lists[0][0]!='ftr_listEventPresentChumon')):
        raise ValueError('Holiday reward has an unsupported additional acquisition list')
    binding=getattr(source,'holiday_acquisition',None)
    if binding is None:
        from v3_furniture_pipeline import ReviewRequired
        raise ReviewRequired('acquisition needs an adapter: complete native holiday delivery')
    destination=binding['exercise_destinations' if card_prize else 'destinations'][item]
    symbol=exercise['symbol'] if card_prize else (lists[0][0] if lists else 'event_table')
    orderable=bool(lists)
    return dict(donor_list=symbol,donor_list_sha256=sha256(acquisition_bytes(source,symbol)),
        stock_group=255,reward_route=0,ordinary_stock=False,catalogue_orderable=orderable,
        holiday_acquisition=dict(route='exercise-card' if card_prize else 'holiday',destination_item=f'{destination["item"]:04X}',
            events=[r['event'] for r in events],
            dependencies=[f'GAFE01-r0/item/{exercise["card"]:04X}'] if card_prize else [],
            native_delivery_installed=True,ordinary_gameplay_tested=False))


def catalogue_source(source,item,index,row):
    expected=[r['event'] for r in contract(source)['rows'] if f'{item:04X}' in r['source_items']]
    acquisition=row.get('holiday_acquisition',{})
    symbol=row.get('donor_acquisition_list')
    exercise=exercise_contract(source)
    if item==exercise['item']:
        return (index>=0 and symbol==exercise['symbol'] and row.get('catalogue_orderable') is False and
            acquisition==dict(route='exercise-card',destination_item=row['item_id'],events=[],
                dependencies=[f'GAFE01-r0/item/{exercise["card"]:04X}'],
                native_delivery_installed=True,ordinary_gameplay_tested=False))
    listed=struct.unpack('>'+str(len(source.raw('ftr_listEventPresentChumon'))//2)+'H',
        source.raw('ftr_listEventPresentChumon'))
    orderable=item in listed
    return (bool(expected) and item>>8!=0x2B and index>=0 and
        symbol==('ftr_listEventPresentChumon' if orderable else 'event_table') and
        row.get('catalogue_orderable') is orderable and
        acquisition.get('events')==expected and acquisition.get('destination_item')==row['item_id'] and
        acquisition.get('native_delivery_installed') is True)


def admit(report):
    """The same provider group serves gifts, diaries, cards, and cutlery."""
    rows=[r for r in report['furniture']['imports'] if r.get('holiday_acquisition')]
    if not rows:return
    group=next(g for g in report['equipment_resources']['npc_extra']['events']['selection']['groups']
        if g['id']=='diary-holidays')
    group['any_imports']=sorted(set(group['any_imports'])|{r['id'] for r in rows})
