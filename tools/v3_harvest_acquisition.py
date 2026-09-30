"""Bind complete source Harvest lists to the installed Franklin reward owner.

Admission reuses ordinary furniture/surface profiles. It grants no shop stock,
catalogue ordering, native-gameplay evidence, or original-hardware certification.
"""
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import ROOT

SOURCES=('tools/v3_harvest_acquisition.py','tools/v3_harvest_install.py',
    'tools/v3_furniture_pipeline.py','tools/v3_room_rig_runtime.py',
    'tools/v3_surface_selection.py','tools/v3_optional_composition.py')


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
    files=by_vrom(image);manager=h['manager']
    if (not manager['installed'] or manager['control_count']!=75 or manager['daily_type_bound']!=117 or
            sha256(files[manager['vrom']].extract(image))!=manager['sha256'] or
            sha256(files[manager['reloc']].extract(image))!=manager['relocation_sha256']):
        raise ValueError('Harvest requires its complete native manager and cleanup')
    core=files[CODE_VROM].extract(image)
    for patch in manager['core_patches']:
        at=patch['address']-CODE_RAM;after=bytes.fromhex(patch['after'])
        if core[at:at+len(after)]!=after:raise ValueError('Changed native Harvest calendar binding')
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
    for row in h['text']['resources']:
        if sha256(files[row['vrom']].extract(image))!=row['sha256']:
            raise ValueError('Changed complete official Harvest dialogue bank')
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
