"""Shared installed behaviour choices for the offline and browser composers."""
import copy
import struct
import zlib

from aflib import by_vrom,sha256,u32
from v3_asset_loader import ROOT,BLOB

FORMAT='AFV3-BEHAVIOUR-CHOICES-1'
SOURCES=('tools/v3_creature_choices.py','tools/v3_starting_diary.py','tools/v3_optional_composition.py',
    'tools/v3_browser_composition.py','tools/v3_creature_fish.py','tools/v3_furniture_pipeline.py',
    'overlays/v3/surface_bootstrap.c','experimental/imports/composer.mjs',
    'experimental/imports/worker.mjs','experimental/imports/app.mjs')
CHOICES=(
    dict(id='fish-population',name='Fish population',binding='spawn_mode',
         symbol='af_v3_fish_spawn_mode',scope='Original and imported fish',
         description='N64 keeps the original fish population rules and adds selected species. GameCube uses its seasonal blending, environmental weighting, and event rules.'),
    dict(id='coastal-fish-movement',name='Imported coastal fish movement',binding='patrol_mode',
         symbol='af_v3_fish_patrol_mode',scope='Imported coastal fish only',
         description='Choose N64 movement or GameCube swimming and shoreline avoidance for imported coastal fish. Original N64 fish keep their movement. This setting has no effect without an imported coastal fish.'),
)
INSECT_CHOICE=dict(id='insect-population',name='Insect population',binding='spawn_mode',
    symbol='af_v3_insect_spawn_mode',scope='Original and imported insects',
    description='N64 keeps two wild insect slots and its original population rules, adding selected species. GameCube uses eight wild slots, seasonal blending, habitat weights, and groups. Both keep a separate release slot.')
FISHING_CHOICE=dict(id='tournament-measurements',name='Fishing tournament measurements',binding='requested_units',
    symbol='af_hf_requested_units',scope='Fishing tournament measurements and records',
    description='N64 measures tournament fish in centimetres; GameCube uses inches. An ongoing tournament or an undelivered winner keeps its recorded units. A new setting starts with an empty tournament and no pending records.')
PAPER_CHOICE=dict(id='paper-quantities',name='Paper quantities',binding='paper_mode',
    symbol='af_carried_paper_mode',scope='All original and imported stationery',
    description='N64 gives single sheets. GameCube gives four-sheet packs. This applies to all paper styles, shops, catalogue orders, gifts, and rewards. Packs can be split or combined, and writing a letter uses one sheet.')
BIRTHDAY_CHOICE=dict(id='birthday-presentation',name='Birthday presentation',binding='birthday_mode',
    symbol='af_rw_birthday_mode',scope='Birthday gift presentation and accompanying birthday mail',
    description='N64 retains its birthday mail without a doorstep presentation. GameCube adds its villager gift presentation when the date, friendship, pocket space, and work eligibility allow it, and excludes the presenting villager from accompanying birthday mail. The annual giver and year are saved. This setting does not require a golden tool.')
SAVE_NOTE=('These behaviour settings keep the same saved layout and imported identities. '
    'Saved seasonal state and existing tournament measurements are retained. '
    'A native save/reload after switching settings is not yet verified.')


def save_note(report):
    paper=report.get('equipment_resources',{}).get('carried_items',{}).get('paper',{}).get('quantities')
    if paper:
        return ('Existing seasonal state and tournament measurements are retained. '
            'A save written in four-sheet mode needs four-sheet mode to load again; '
            'single-sheet mode rejects it without modifying the save. Keep a backup when changing settings.')
    return SAVE_NOTE


def install(base,prior,blob):
    e=copy.deepcopy(prior['equipment_resources']);fish=e['creature_fish'];world=fish['world']
    if not world.get('collection_ui_installed') or world.get('behaviour_choices'):
        raise ValueError('Behaviour choices require the completed collection/message consumers')
    p=world['packet'];packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    if sha256(packet)!=p['sha256'] or zlib.crc32(packet)!=p['crc32']:
        raise ValueError('Changed complete fish behaviour packet')
    options=[]
    for choice in CHOICES:
        binding=world[choice['binding']];ram=world['compiled']['symbols'][choice['symbol']]
        if (binding['ram']!=ram or binding['value']!=0 or binding['values']!={'N64':0,'GameCube':1} or
                not p['ram']<=ram<p['ram']+world['compiled']['bytes'] or u32(packet,ram-p['ram'])!=0):
            raise ValueError('Behaviour choice lacks its installed runtime binding')
        options.append(dict(choice,ram=ram,default='N64',values=dict(N64=0,GameCube=1)))
        binding['browser_selection_installed']=True
    world['behaviour_choices']=dict(format=FORMAT,options=options,save_note=SAVE_NOTE,
        defaults={r['id']:r['default'] for r in options},saved_layout_changed=False,
        experimental=True,web_patcher_enabled=False,native_switch_reload_tested=False)
    fish.update(additional_resident_bytes=0,sources={path:sha256((ROOT/path).read_bytes())
        for path in (*fish['sources'],*SOURCES)},
        pending=['Controller Pak collection transport','per-species composition','ordinary gameplay'])
    return e,{}


def options(image,report):
    world=report.get('equipment_resources',{}).get('creature_fish',{}).get('world',{})
    choices=world.get('behaviour_choices')
    if choices is None:return []
    if choices.get('format')!=FORMAT or choices.get('web_patcher_enabled') is not False:
        raise ValueError('Unknown experimental behaviour choices')
    p=world['packet'];files=by_vrom(image);blob=files[BLOB];start=blob.pstart+p['blob_offset']
    if sha256(image[start:start+p['bytes']])!=p['sha256']:
        raise ValueError('Changed complete selectable fish world packet')
    result=[]
    if len(choices['options'])!=len(CHOICES):raise ValueError('Incomplete installed behaviour choices')
    for definition,row in zip(CHOICES,choices['options'],strict=True):
        if (any(row.get(k)!=v for k,v in definition.items()) or row['default']!='N64' or
                row['values']!={'N64':0,'GameCube':1} or
                row['ram']!=world['compiled']['symbols'][row['symbol']]):
            raise ValueError('Changed shared behaviour definition')
        at=start+row['ram']-p['ram']
        if image[at:at+4]!=bytes(4):raise ValueError('Changed pinned behaviour default')
        result.append({**row,'offset':at,'before':image[at:at+4].hex()})
        if row['id']=='coastal-fish-movement':
            # Preserve the pinned packet's layout while removing its shared
            # origin gate in GameCube mode. All six coastal callbacks call
            # this one helper; N64 mode retains the exact original instructions.
            helper=start+world['compiled']['symbols']['donor']-p['ram']
            mode=row['ram']
            expected=struct.pack('>9I',0x908301DA,0x10600005,0x00001025,
                0x3C020000|((mode+0x8000)>>16),0x8C420000|(mode&65535),
                0x38420001,0x2C420001,0x03E00008,0)
            if image[helper:helper+36]!=expected:
                raise ValueError('Changed complete coastal movement origin/mode guard')
            result[-1].update(id='fish-movement',name='Fish swimming',scope='All original and imported river, pond, and ocean fish',
                description='Choose N64 or GameCube swimming, waiting, and escape behaviour for all fish.',
                patches=[dict(offset=helper+4,before='10600005',after='00000000'),
                         *freshwater_patches(image,report)])
    reward=report.get('equipment_resources',{}).get('carried_items',{}).get('quest',{}).get('rewards')
    if reward and reward.get('birthday_choice'):
        row=reward['birthday_choice'];p=reward['packet'];code=reward['code'];start=p['physical']
        if (not reward['installed'] or any(row.get(k)!=v for k,v in BIRTHDAY_CHOICE.items()) or
                row['default']!='N64' or row['values']!={'N64':0,'GameCube':1} or
                row['ram']!=code['symbols'][row['symbol']] or
                not code['ram']<=row['ram']<code['ram']+code['bytes'] or
                sha256(image[start:start+p['bytes']])!=p['sha256']):
            raise ValueError('Changed complete installed birthday presentation choice')
        at=start+row['ram']-p['ram']
        if image[at:at+4]!=bytes(4):raise ValueError('Changed pinned N64 birthday presentation default')
        result.append({**row,'offset':at,'before':image[at:at+4].hex()})
    insects=report.get('equipment_resources',{}).get('creature_insects')
    if insects and insects.get('behaviour_choice'):
        row=insects['behaviour_choice'];p=insects['packet'];start=p['physical']
        if (not insects['installed'] or not insects['population']['installed'] or
                any(row.get(k)!=v for k,v in INSECT_CHOICE.items()) or row['default']!='N64' or
                row['values']!={'N64':0,'GameCube':1} or
                row['ram']!=insects['compiled']['symbols'][row['symbol']] or
                not p['ram']<=row['ram']<p['ram']+insects['compiled']['bytes'] or
                sha256(image[start:start+p['bytes']])!=p['sha256']):
            raise ValueError('Changed installed insect population choice')
        at=start+row['ram']-p['ram']
        if image[at:at+4]!=bytes(4):raise ValueError('Changed pinned insect population default')
        result.append({**row,'offset':at,'before':image[at:at+4].hex()})
    fishing=report.get('equipment_resources',{}).get('holiday_fishing',{})
    live=fishing.get('live',{});row=live.get('measurement_choice')
    if row:
        p=fishing['packet'];start=p['physical'];code=live['loaded_code']
        if (any(row.get(k)!=v for k,v in FISHING_CHOICE.items()) or row['default']!='N64' or
                row['values']!={'N64':0,'GameCube':1} or
                row['ram']!=live['code']['symbols'][row['symbol']] or
                not code['ram']<=row['ram']<code['ram']+code['bytes'] or
                sha256(image[start:start+p['bytes']])!=p['sha256']):
            raise ValueError('Changed installed tournament measurement choice')
        at=start+row['ram']-p['ram']
        if image[at:at+4]!=bytes(4):raise ValueError('Changed pinned tournament measurement default')
        # A prepared provider is not a selectable gameplay setting. Admit it
        # only together with the connected tournament and its delivery service.
        if live.get('service_admission') and live.get('actors_active') and live.get('mail',{}).get('enabled'):
            result.append({**row,'offset':at,'before':image[at:at+4].hex()})
    from v3_holiday_selection import location, groups
    selection=report.get('equipment_resources',{}).get('npc_extra',{}).get('events',{}).get('selection')
    if selection:
        groups(image,report)  # Bind the actual installed admission, not only a label.
        row=selection['calendar'];p,at=location(report['equipment_resources'],row['ram'],4)
        if image[at:at+4]!=bytes(4):raise ValueError('Changed default holiday calendar')
        result.append({**row,'offset':at,'before':image[at:at+4].hex()})
    paper=report.get('equipment_resources',{}).get('carried_items',{}).get('paper',{}).get('quantities')
    if paper:
        row=paper['choice'];p=paper['packet'];code=paper['code'];start=p['physical']
        if (not paper['installed'] or any(row.get(k)!=v for k,v in PAPER_CHOICE.items()) or
                row['default']!='N64' or row['values']!={'N64':0,'GameCube':1} or
                row['ram']!=code['symbols'][row['symbol']] or
                not paper['ram']<=row['ram']<paper['ram']+code['bytes'] or
                sha256(image[start:start+p['bytes']])!=p['sha256']):
            raise ValueError('Changed installed global stationery quantity choice')
        at=start+row['ram']-p['ram']
        if image[at:at+4]!=bytes(4):raise ValueError('Changed pinned stationery quantity default')
        result.append({**row,'offset':at,'before':image[at:at+4].hex()})
    from v3_seasonal_stock import option
    seasonal=option(image,report)
    if seasonal:result.append(seasonal)
    from v3_starting_diary import option as starting_diary
    starter=starting_diary(image,report)
    if starter:result.append(starter)
    return result


def freshwater_patch(image,report):
    """Adapt the donor's two 60-Hz heading additions to one native 30-Hz tick.

    Both games divide the target heading by target/step. GameCube advances
    the phase by step/2, so it adds that increment twice per native tick.
    The N64 speed/phase advance already matches the elapsed GameCube time.
    Preserve N64 mode, callbacks, actor layout, and all native relocations.
    """
    from v3_npc_clothing import guard_incoming
    from v3_npc_draw import relocation_offsets
    files=by_vrom(image)
    owner=next(r for r in report['equipment_resources']['creature_fish']['owners'] if r['name']=='river')
    data=files[owner['vrom']].extract(image);reloc=files[owner['reloc']].extract(image)
    at=0x80932090-owner['ram']
    before='84ef00de84f8022c01f8c8211000001ca4f900de'
    after='84ef00de84f8022c0018c04001f8c821a4f900de'
    if (owner['vrom']!=0x828C50 or owner['ram']!=0x809317D0 or files[owner['vrom']].pend or
            sha256(data)!=owner['sha256'] or sha256(reloc)!=owner['reloc_sha256'] or
            data[at:at+20].hex()!=before or data[at+20:at+32].hex()!='46006032c7aa002445020019'):
        raise ValueError('Changed complete freshwater swimming owner or turning path')
    guard_incoming(data,u32(reloc,0),owner['ram'],[(at,20)])
    if set(range(at,at+20,4)) & relocation_offsets(reloc,len(data)):
        raise ValueError('Freshwater turning patch overlaps a native relocation')
    return dict(offset=files[owner['vrom']].pstart+at,before=before,after=after)


def freshwater_patches(image,report):
    world=report['equipment_resources']['creature_fish']['world']
    fresh=world.get('freshwater')
    if fresh is None:return [freshwater_patch(image,report)]
    from v3_freshwater_movement import RAM,END,TAIL,TAIL_END,GUARD,BINDINGS
    files=by_vrom(image);p=world['packet'];packet=files[BLOB].pstart+p['blob_offset']
    code=fresh['code'];row=next(r for r in report['equipment_resources']['creature_fish']['owners'] if r['name']=='river')
    data=files[row['vrom']].extract(image);rel=files[row['reloc']].extract(image)
    if (fresh['format']!='AFV3-FRESHWATER-PATROL-1' or not fresh['installed'] or
            code['ram']!=RAM or code['symbols']['af_fresh_main_end']>END-16 or
            code['symbols']['af_fresh_tail_start']!=TAIL or code['symbols']['af_fresh_tail_end']>TAIL_END-16 or
            files[row['vrom']].pend or files[row['reloc']].pend or
            sha256(data)!=fresh['original_owner_sha256'] or sha256(rel)!=fresh['original_reloc_sha256'] or
            rel.hex()!=fresh['relocation']['before'] or len(fresh['callbacks'])!=6):
        raise ValueError('Changed complete freshwater movement choice or native alternative')
    for fragment in code['fragments']:
        at=packet+fragment['ram']-p['ram']
        if sha256(image[at:at+fragment['bytes']])!=fragment['sha256']:
            raise ValueError('Changed complete freshwater movement code')
    for end in (END,TAIL_END):
        if image[packet+end-p['ram']-16:packet+end-p['ram']]!=struct.pack('>4I',*([GUARD]*4)):
            raise ValueError('Changed freshwater movement guard')
    patches=[]
    for callback,(address,before,name) in zip(fresh['callbacks'],BINDINGS,strict=True):
        target=code['symbols']['af_v3_freshwater_'+name];at=address-row['ram']
        if callback!=dict(address=address,before=before,after=target) or u32(data,at)!=before:
            raise ValueError('Changed complete freshwater callback binding')
        patches.append(dict(offset=files[row['vrom']].pstart+at,
            before=struct.pack('>I',before).hex(),after=struct.pack('>I',target).hex()))
    patches.append(dict(offset=files[row['reloc']].pstart,**fresh['relocation']))
    return patches


def resolve(options,requested=None):
    requested={} if requested is None else requested
    if not isinstance(requested,dict) or set(requested)-{r['id'] for r in options}:
        raise ValueError('Unknown or unavailable behaviour setting')
    result={}
    for row in options:
        value=requested.get(row['id'],row['default'])
        if not isinstance(value,str) or value not in row['values']:
            raise ValueError('Unsupported value for behaviour setting: '+row['id'])
        result[row['id']]=value
    return dict(sorted(result.items()))


def changed(options,resolved):
    return any(resolved[r['id']]!=r['default'] for r in options)


def checksum_fields(image,report):
    world=report.get('equipment_resources',{}).get('creature_fish',{}).get('world',{})
    if not world.get('behaviour_choices'):return []
    e=report['equipment_resources'];p=world['packet'];files=by_vrom(image);blob=files[BLOB]
    boot=e['surface_bootstrap']['code'];ram=boot['symbols']['af_v3_fish_world_crc_expected']
    at=blob.pstart+e['blob_offset']+ram-e['ram'];start=blob.pstart+p['blob_offset']
    if at&3 or u32(image,at)!=p['crc32'] or zlib.crc32(image[start:start+p['bytes']])!=p['crc32']:
        raise ValueError('Changed installed editable world checksum')
    fields=[dict(offset=at,before=image[at:at+4].hex(),start=start,length=p['bytes'])]
    insects=e.get('creature_insects')
    if insects and insects.get('behaviour_choice'):
        p=insects['packet'];ram=boot['symbols']['af_v3_insect_crc_expected']
        at=blob.pstart+e['blob_offset']+ram-e['ram'];start=p['physical']
        if u32(image,at)!=p['crc32'] or zlib.crc32(image[start:start+p['bytes']])!=p['crc32']:
            raise ValueError('Changed installed insect checksum')
        fields.append(dict(offset=at,before=image[at:at+4].hex(),start=start,length=p['bytes']))
    fishing=e.get('holiday_fishing',{})
    if fishing.get('live',{}).get('measurement_choice'):
        p=fishing['packet'];ram=boot['symbols']['holiday_state_crc']
        at=blob.pstart+e['blob_offset']+ram-e['ram'];start=p['physical']
        if u32(image,at)!=p['crc32'] or zlib.crc32(image[start:start+p['bytes']])!=p['crc32']:
            raise ValueError('Changed installed tournament checksum')
        fields.append(dict(offset=at,before=image[at:at+4].hex(),start=start,length=p['bytes']))
    paper=e.get('carried_items',{}).get('paper',{}).get('quantities')
    if paper:
        p=paper['packet'];ram=boot['symbols']['carried_quest_crc']
        at=blob.pstart+e['blob_offset']+ram-e['ram'];start=p['physical']
        if u32(image,at)!=p['crc32'] or zlib.crc32(image[start:start+p['bytes']])!=p['crc32']:
            raise ValueError('Changed installed global stationery checksum')
        fields.append(dict(offset=at,before=image[at:at+4].hex(),start=start,length=p['bytes']))
    from v3_seasonal_stock import checksum_field
    fields.extend(checksum_field(image,report))
    return fields


def update_report(image,blob,report,resolved):
    from v3_seasonal_stock import update_report as update_seasonal
    update_seasonal(image,report,resolved)
    world=report['equipment_resources']['creature_fish']['world'];p=world['packet']
    packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
    world['compiled']['sha256']=sha256(packet[:world['compiled']['bytes']])
    world['behaviour_choices']['resolved']=resolved
    for row in world['behaviour_choices']['options']:
        key='fish-movement' if row['id']=='coastal-fish-movement' else row['id']
        value=row['values'][resolved[key]]
        if u32(packet,row['ram']-p['ram'])!=value:raise ValueError('Lost composed behaviour setting')
        world[row['binding']]['value']=value
    river=next(r for r in report['equipment_resources']['creature_fish']['owners'] if r['name']=='river')
    data=by_vrom(image)[river['vrom']].extract(image)
    fresh=world.get('freshwater');gc=resolved['fish-movement']=='GameCube'
    if fresh:
        reloc=by_vrom(image)[river['reloc']].extract(image)
        for row in fresh['callbacks']:
            if u32(data,row['address']-river['ram'])!=row['after' if gc else 'before']:
                raise ValueError('Lost complete freshwater movement callback')
        if reloc.hex()!=fresh['relocation']['after' if gc else 'before']:
            raise ValueError('Lost freshwater movement relocation choice')
        river.update(reloc_sha256=sha256(reloc))
        fresh['resolved']=resolved['fish-movement']
    else:
        at=0x80932090-river['ram']
        expected='84ef00de84f8022c0018c04001f8c821a4f900de' if gc else '84ef00de84f8022c01f8c8211000001ca4f900de'
        if data[at:at+20].hex()!=expected:raise ValueError('Lost freshwater movement choice')
    river.update(sha256=sha256(data),movement_choice=resolved['fish-movement'])
    world['patrol_mode']['scope']='all original and imported river, pond, and ocean fish'
    e=report['equipment_resources'];ep=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
    insects=e.get('creature_insects')
    if insects and insects.get('behaviour_choice'):
        p=insects['packet'];packet=image[p['physical']:p['physical']+p['bytes']]
        row=insects['behaviour_choice'];value=resolved[row['id']]
        if u32(packet,row['ram']-p['ram'])!=row['values'][value]:raise ValueError('Lost insect behaviour setting')
        row['resolved']=value;p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
        insects['compiled']['sha256']=sha256(packet[:insects['compiled']['bytes']])
        insects['physical_resource']['sha256']=p['sha256']
        resource=next(r for r in report['physical_resources'] if r['id']==insects['physical_resource']['id'])
        resource['sha256']=p['sha256']
    fishing=e.get('holiday_fishing',{});live=fishing.get('live',{});row=live.get('measurement_choice')
    if row:
        p=fishing['packet'];packet=image[p['physical']:p['physical']+p['bytes']]
        value=resolved.get(row['id'],row['default'])
        if u32(packet,row['ram']-p['ram'])!=row['values'][value]:raise ValueError('Lost tournament measurement setting')
        row['resolved']=value;p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
        code=live['loaded_code'];at=code['ram']-p['ram']
        code['sha256']=sha256(packet[at:at+code['bytes']]);live['code']['sha256']=code['sha256']
        e['holiday_state']['packet']=copy.deepcopy(p)
        resource=next(r for r in report['physical_resources'] if r['id']==p['id'])
        resource['sha256']=p['sha256']
    e.update(sha256=sha256(ep),crc32=zlib.crc32(ep))
    paper=e.get('carried_items',{}).get('paper',{}).get('quantities')
    if paper:
        p=paper['packet'];packet=image[p['physical']:p['physical']+p['bytes']]
        row=paper['choice'];value=resolved[row['id']]
        if u32(packet,row['ram']-p['ram'])!=row['values'][value]:raise ValueError('Lost global stationery quantity setting')
        row['resolved']=value;p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
        start=paper['ram']-p['ram'];paper['code']['sha256']=sha256(packet[start:start+paper['code']['bytes']])
        e['carried_items']['quest']['packet']=copy.deepcopy(p)
        e['carried_items']['spawning']['packet']=copy.deepcopy(p)
        next(r for r in report['physical_resources'] if r['id']==p['id'])['sha256']=p['sha256']
    reward=e.get('carried_items',{}).get('quest',{}).get('rewards')
    if reward and reward.get('birthday_choice'):
        row=reward['birthday_choice'];p=reward['packet'];value=resolved[row['id']]
        packet=image[p['physical']:p['physical']+p['bytes']]
        if u32(packet,row['ram']-p['ram'])!=row['values'][value]:raise ValueError('Lost birthday presentation choice')
        row['resolved']=value
    for boot in (e['surface_bootstrap'],report['room_surfaces']['items']['bootstrap']):
        c=boot['code'];start=c['symbols']['af_v3_surface_init']-e['ram']
        c['sha256']=sha256(ep[start:start+c['bytes']])
