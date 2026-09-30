"""Bind complete source Harvest lists to the installed Franklin reward owner.

Admission reuses ordinary furniture/surface profiles. It grants no shop stock,
catalogue ordering, native-gameplay evidence, or original-hardware certification.
"""
import json
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import ROOT

SOURCES=('tools/v3_harvest_acquisition.py','tools/v3_harvest_install.py',
    'tools/v3_furniture_pipeline.py','tools/v3_room_rig_runtime.py',
    'tools/v3_surface_selection.py','tools/v3_optional_composition.py')


def installed_items(report):
    """Offer installed rewards and their native table-pickup cutlery resource."""
    from v3_holiday_acquisition import providers_installed
    e=report.get('equipment_resources',{});h=e.get('harvest',{})
    if (not providers_installed(report) or not h.get('installed') or
        not h.get('reward_selection_installed') or not h.get('npc',{}).get('installed') or
        not all(h.get(k,{}).get('installed') for k in ('registry','hiding','shared_motions','manager','text'))):
        return set()
    pickup=e.get('holiday_items',{}).get('pickup',{})
    cards=e.get('carried_items',{}).get('rows',[])
    cutlery=next((r for r in cards if r['family']==3 and not r['state_index']),None)
    if (not pickup.get('installed') or pickup.get('service_ready')!=7 or
        not e['npc_extra']['events'].get('demo',{}).get('installed') or not cutlery or
        not cutlery.get('ready') or h.get('dependencies')!=[cutlery['id']] or
        len(h.get('reward_choices',[]))!=12):return set()
    result={cutlery['id']}
    for row in report['furniture']['imports']:
        a=row.get('harvest_acquisition',{})
        if (a.get('native_delivery_installed') and a.get('destination_item')==row['item_id'] and
            a.get('dependencies')==[cutlery['id']] and row.get('runtime_installed') and
            not set(row.get('remaining',[]))-{'representative native execution','ordinary gameplay and save/restart'}):
            result.add(row['id'])
    result.update(r['id'] for r in report.get('room_surfaces',{}).get('stock',{}).get('harvest',[])
        if r.get('harvest_acquisition',{}).get('native_delivery_installed') and
        r['harvest_acquisition'].get('dependencies')==[cutlery['id']] and
        r['harvest_acquisition'].get('destination_item')==r['item_id'])
    if result-{cutlery['id']} - set(h['reward_choices']):
        raise ValueError('Unreviewed installed Harvest acquisition identity')
    return result


def verify_installed_items(image,report,catalog):
    """Authenticate existing acquisition, live destinations, and non-stock policy."""
    items=installed_items(report)
    if not items:return items
    from v3_furniture_pipeline import Source
    from v3_furniture_install import catalogue_record,order_mask
    from v3_import_storage import ITEMS
    from v3_asset_loader import BLOB
    from v3_registry import furniture_source
    from v3_holiday_selection import packets,location
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    binding=checked(source,image,report);files=by_vrom(image);blob=files[BLOB].extract(image)
    e=report['equipment_resources'];h=e['harvest'];pickup=e['holiday_items']['pickup']
    for p in packets(e):
        if sha256(image[p['physical']:p['physical']+p['bytes']])!=p['sha256']:
            raise ValueError('Changed complete Harvest acquisition dependency packet')
    _,at=location(e,pickup['ram'],pickup['bytes'])
    if sha256(image[at:at+pickup['bytes']])!=pickup['code']['sha256']:
        raise ValueError('Changed complete Harvest cutlery pickup')
    core=files[CODE_VROM].extract(image)
    for _,start,end,digest in pickup['native_functions']:
        function=bytearray(core[start-CODE_RAM:end-CODE_RAM])
        if sha256(function)!=digest:
            from v3_import_storage import jump
            demo=e['npc_extra']['events']['demo']
            hooks=[p for p in demo['hooks'] if p['address']==start and
                   p['symbol'] in ('af_holiday_demo_request','af_holiday_demo_message')]
            if len(hooks)!=1:raise ValueError('Missing exact Harvest cutlery native-service supersession')
            hook=hooks[0];target=demo['code']['symbols'][hook['symbol']]
            after=struct.pack('>2I',jump(target),0)
            if bytes.fromhex(hook['after'])!=after or function[:8]!=after:
                raise ValueError('Changed actual Harvest cutlery native-service redirect')
            from v3_holiday_scene import DEMO_RAM
            size=demo['code']['bytes'];_,at=location(e,DEMO_RAM,size)
            if sha256(image[at:at+size])!=demo['code']['sha256']:
                raise ValueError('Changed complete Harvest cutlery native-service wrapper')
            function[:8]=bytes.fromhex(hook['before'])
        if sha256(function)!=digest:
            raise ValueError('Changed actual Harvest cutlery native service')
    for hook in pickup['hooks']:
        owner=files[hook['vrom']].extract(image);at=hook['address']-hook['ram']
        if owner[at:at+4]!=bytes.fromhex(hook['after']):
            raise ValueError('Changed actual Harvest cutlery player hook')
    prepared=json.loads((ROOT/h['preparation']/'connected.json').read_bytes())['preparation']
    functions=[f for owner in prepared['family'] for f in owner['functions']]
    if len(functions)!=39:raise ValueError('Incomplete whole-source Harvest owner')
    for expected in functions:
        if json.loads(json.dumps(source.function(expected['offset'])[1]))!=expected:
            raise ValueError('Changed complete source Harvest owner')
    for row in report['furniture']['imports']:
        if row['id'] not in items:continue
        donor,_=furniture_source(row);a=row['harvest_acquisition'];slot=row['runtime_index']-1024
        record=catalogue_record(row);metadata=blob[ITEMS+slot*32:ITEMS+(slot+1)*32]
        if (a!=acquisition(binding,donor,'ftr_listHarvest') or
            row['donor_list']!='ftr_listHarvest' or row['donor_list_sha256']!=binding['lists']['ftr_listHarvest']['sha256'] or
            row['ordinary_stock'] or row['catalogue_orderable'] or row['stock_group']!=255 or row['reward_route']!=0 or
            struct.unpack_from('>2H',metadata)!=(row['runtime_index'],int(a['destination_item'],16)) or
            metadata[7]!=1 or metadata[24]!=order_mask(record) or metadata[27]!=0 or
            catalog[row['id']]['dependencies']!=binding['dependencies']):
            raise ValueError('Changed installed Harvest furniture identity or metadata')
    for row in report['room_surfaces']['stock'].get('harvest',[]):
        if row['id'] not in items:continue
        symbol='carpet_listHarvest' if catalog[row['id']]['kind']=='floor' else 'wall_listHarvest'
        donor=int(row['id'].rsplit('/',1)[1],16)
        if (row['harvest_acquisition']!=acquisition(binding,donor,symbol) or row['group']!=20 or
            row['ordinary_stock'] or row['catalogue_orderable'] or
            row['item_id']!=catalog[row['id']]['item_id'] or
            catalog[row['id']]['dependencies']!=binding['dependencies']):
            raise ValueError('Changed installed Harvest surface identity or acquisition')
    return items


def verify_manager(image,report,h):
    """Check retained controls and exact supersession, not an obsolete size."""
    from v3_campsite_manager import CONTROL_COUNT,METADATA
    from v3_import_storage import jump
    files=by_vrom(image);m=h['manager'];core=files[CODE_VROM].extract(image)
    data=files[m['vrom']].extract(image);reloc=files[m['reloc']].extract(image)
    if (not m['installed'] or m['control_count'] not in (75,76) or m['daily_type_bound']!=117 or
        len(data)!=m['bytes'] or sha256(data)!=m['sha256'] or sha256(reloc)!=m['relocation_sha256'] or
        struct.unpack_from('>I',data,CONTROL_COUNT-m['ram'])[0]!=m['control_count'] or
        m['table']-m['ram']+32*m['control_count']!=len(data)):
        raise ValueError('Harvest requires its complete native manager and cleanup')
    patches={p['address']:p for p in m['core_patches']}
    if m['control_count']==76:
        extension=m.get('bank_april',{});bank=report['equipment_resources'].get('bank',{})
        if (not extension.get('installed') or extension!=bank.get('april_entries') or
            extension.get('retained_controls')!=75 or extension.get('control_count')!=76 or
            extension.get('daily_type_bound')!=118 or extension.get('additional_owner_bytes')!=32):
            raise ValueError('Incomplete retained Harvest manager extension')
        prefix=bytearray(data[:-32]);oldrel=bytearray(reloc)
        struct.pack_into('>I',prefix,CONTROL_COUNT-m['ram'],75)
        struct.pack_into('>I',oldrel,0,len(prefix))
        callbacks=extension['callbacks']
        if (sha256(prefix)!='d075c6a4e3847edf166e5ccd61b5759c34a677018b40c2d3d26402c5815caede' or
            sha256(oldrel)!='d01f8df69836529cbc3ffbd3be4b108c30126f411d3ae0c3af96c4327c97fbe3' or
            data[-32:]!=struct.pack('>8I',117,callbacks['af_bank_april_manager_start'],
                callbacks['af_bank_april_manager_stop'],0,0,0,0,0)):
            raise ValueError('Changed retained Harvest controls or relocations')
        packet=bank['packet'];b=bank['code'];symbols=b['symbols']
        raw=image[packet['physical']:packet['physical']+packet['bytes']]
        at=b['ram']-packet['ram']
        if not bank.get('installed') or sha256(raw)!=packet['sha256'] or sha256(raw[at:at+b['bytes']])!=b['sha256']:
            raise ValueError('Changed complete retained Harvest calendar/descriptor wrapper')
        # Both complete wrappers forward Harvest independently of account mode.
        for name,size,digest,offset,target,link in (
            ('af_bank_april_calendar_before_cleanup',124,
             '5408ef34239bc8e9b22952c755b3aadaf2f195152c5572ad825cf6253f8942fa',12,
             h['code']['symbols']['af_hr_calendar_before_cleanup'],True),
            ('af_bank_april_descriptor',176,
             '3d541c3982c3d7536beafc0bd57d5e4e710888aeec68ac5c81c31924eda02e3e',12,
             report['equipment_resources']['npc_extra']['events']['participants']['code']['symbols']['af_hp_descriptor'],False)):
            start=symbols[name]-packet['ram'];function=raw[start:start+size]
            if (callbacks[name]!=symbols[name] or sha256(function)!=digest or
                struct.unpack_from('>I',function,offset)[0]!=jump(target,link=link)):
                raise ValueError('Changed actual retained Harvest calendar/descriptor forwarding')
        expected={
            0x8007F630:struct.pack('>2I',jump(symbols['af_bank_april_calendar_before_cleanup'],link=True),0),
            0x8007F640:struct.pack('>I',0x24110076),0x8007F660:struct.pack('>I',0x24110076),
            0x80057E4C:struct.pack('>2I',jump(symbols['af_bank_april_descriptor'],link=True),0x00C02025),
            METADATA:struct.pack('>4I',m['vrom'],m['vrom']+len(data),m['ram'],m['ram']+len(data))}
        extended={p['address']:p for p in extension['core_patches']}
        if extended.keys()!=expected.keys():raise ValueError('Incomplete actual Harvest manager hooks')
        for address,after in expected.items():
            patch=extended[address]
            if bytes.fromhex(patch['after'])!=after or (address in patches and patch['before']!=patches[address]['after']):
                raise ValueError('Changed actual Harvest hook supersession')
        patches.update(extended)
    for patch in patches.values():
        at=patch['address']-CODE_RAM;after=bytes.fromhex(patch['after'])
        if core[at:at+len(after)]!=after:raise ValueError('Changed native Harvest calendar binding')


def checked(source,image,report):
    h=report.get('equipment_resources',{}).get('harvest')
    if not h:return None
    p=h['packet'];raw=image[p['physical']:p['physical']+p['bytes']]
    if (not h.get('installed') or sha256(raw)!=p['sha256'] or raw[-16:]!=b'AFHV'*4 or
            not h['registry'].get('installed') or h['registry']['owner_count']!=28 or
            not h['shared_motions'].get('installed') or not h['hiding'].get('installed')):
        raise ValueError('Harvest requires the complete installed owner and world services')
    for part in ('code','pool'):
        row=h[part];at=row['ram']-p['ram']
        if sha256(raw[at:at+row['bytes']])!=row['sha256']:
            raise ValueError('Changed complete Harvest '+part)
    files=by_vrom(image);verify_manager(image,report,h)
    table=h['object_table'];at=table['ram']-p['ram'];objects=raw[at:at+table['bytes']]
    if table['count']!=462 or sha256(objects)!=table['sha256']:
        raise ValueError('Changed complete Harvest object table')
    reservations=table.get('native_model_reservations',[])
    if len(reservations)!=2 or {r['vrom'] for r in reservations}!={0x8681F0,0x8798C0}:
        raise ValueError('Harvest requires both complete native model reservations')
    for row in reservations:
        owner=files[row['vrom']].extract(image)
        if row['reserved_model_bytes']<12480 or not row['streaming_clamp_unchanged']:
            raise ValueError('Incomplete native Harvest model capacity')
        for patch in row['patches']:
            at=patch['address']-row['ram']
            if owner[at:at+4]!=bytes.fromhex(patch['after']):
                raise ValueError('Changed actual native Harvest model allocation or caller')
    for row in table['native_streaming_rebindings']:
        at=row['address']-row['ram'];owner=files[row['vrom']].extract(image)
        if owner[at:at+8]!=bytes.fromhex(row['after']):raise ValueError('Changed native Harvest object reader')
    npc=report['equipment_resources']['npc_extra']
    banks=[b for b in npc['banks'] if b['bank'] in (460,461)]
    if len(banks)!=2 or sorted(b['bytes'] for b in banks)!=[4128,12480]:
        raise ValueError('Incomplete whole Franklin artwork')
    for b in banks:
        if (sha256(image[b['physical']:b['physical']+b['bytes']])!=b['sha256'] or
                struct.unpack_from('>2I',objects,b['bank']*8)!=(b['vrom'],b['vrom']+b['bytes'])):
            raise ValueError('Changed whole Franklin artwork bank')
    if not h['text']['installed'] or len(h['text']['rows'])!=36:
        raise ValueError('Incomplete official Harvest dialogue')
    from textbanks import Bank
    from v3_event_text import MESSAGE,TABLE
    entries=Bank('message',MESSAGE,TABLE,files[MESSAGE].extract(image),files[TABLE].extract(image)).entries()
    for row in h['text']['rows']:
        if row['id']>=len(entries) or sha256(entries[row['id']])!=row['sha256']:
            raise ValueError('Changed retained official Harvest dialogue')
    from v3_carried_selection import options
    cutlery=options(image,report).get('GAFE01-r0/item/2530')
    if not cutlery or cutlery['item_id']!='2530':raise ValueError('Harvest requires complete selectable cutlery')
    rewards=h['rewards'];lists={};destinations={}
    for symbol,kind,count in (('ftr_listHarvest','Furniture',10),
            ('carpet_listHarvest','Carpet',1),('wall_listHarvest','Wallpaper',1)):
        data=source.raw(symbol);ids=struct.unpack('>'+str(len(data)//2)+'H',data)
        rows=[r for r in rewards if r['kind']==kind]
        if (len(rows)!=count or len(ids)!=count+1 or ids[-1] or
                list(ids[:-1])!=[r['source_item'] for r in rows] or len(set(ids))!=len(ids)):
            raise ValueError('Changed complete source Harvest reward category')
        lists[symbol]=dict(sha256=sha256(data),items=list(ids[:-1]))
        for row in rows:
            if row['source_item'] in destinations:raise ValueError('Duplicated Harvest reward identity')
            destinations[row['source_item']]=row['item']
    if len(rewards)!=12 or len(destinations)!=12:raise ValueError('Incomplete source Harvest family')
    at=h['code']['symbols']['af_hr_reward_items']-p['ram']
    if raw[at:at+24]!=struct.pack('>12H',*(r['item'] for r in rewards)):
        raise ValueError('Changed actual Harvest reward destination table')
    return dict(lists=lists,destinations=destinations,dependencies=[cutlery['id']],
        native_delivery_installed=True,ordinary_gameplay_tested=False,packet_sha256=p['sha256'])


def acquisition(binding,item,symbol):
    if binding is None or symbol not in binding['lists'] or item not in binding['lists'][symbol]['items']:
        raise ValueError('Unbound complete source Harvest reward')
    return dict(route='harvest',source_symbol=symbol,dependencies=binding['dependencies'],
        destination_item=f'{binding["destinations"][item]:04X}',
        native_delivery_installed=True,ordinary_gameplay_tested=False)


def furniture(source,item,index,lists):
    del index
    if len(lists)!=1 or lists[0][0]!='ftr_listHarvest':return None
    binding=getattr(source,'harvest_acquisition',None)
    if binding is None:
        from v3_furniture_pipeline import ReviewRequired
        raise ReviewRequired('acquisition needs an adapter: complete native Harvest delivery')
    symbol=lists[0][0]
    return dict(donor_list=symbol,donor_list_sha256=binding['lists'][symbol]['sha256'],
        stock_group=255,reward_route=0,ordinary_stock=False,catalogue_orderable=False,
        harvest_acquisition=acquisition(binding,item,symbol))
