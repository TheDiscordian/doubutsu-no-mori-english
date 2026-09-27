"""Shared installed behaviour choices for the offline and browser composers."""
import copy
import struct
import zlib

from aflib import by_vrom,sha256,u32
from v3_asset_loader import ROOT,BLOB

FORMAT='AFV3-BEHAVIOUR-CHOICES-1'
SOURCES=('tools/v3_creature_choices.py','tools/v3_optional_composition.py',
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
SAVE_NOTE=('These behaviour settings keep the same saved layout and imported identities. '
    'Changing them changes fish population or movement rules; the saved seasonal state is retained. '
    'A native save/reload after switching settings is not yet verified.')


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
    return result


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
    return [dict(offset=at,before=image[at:at+4].hex(),start=start,length=p['bytes'])]


def update_report(image,blob,report,resolved):
    world=report['equipment_resources']['creature_fish']['world'];p=world['packet']
    packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
    world['compiled']['sha256']=sha256(packet[:world['compiled']['bytes']])
    world['behaviour_choices']['resolved']=resolved
    for row in world['behaviour_choices']['options']:
        value=row['values'][resolved[row['id']]]
        if u32(packet,row['ram']-p['ram'])!=value:raise ValueError('Lost composed behaviour setting')
        world[row['binding']]['value']=value
    e=report['equipment_resources'];ep=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
    e.update(sha256=sha256(ep),crc32=zlib.crc32(ep))
    for boot in (e['surface_bootstrap'],report['room_surfaces']['items']['bootstrap']):
        c=boot['code'];start=c['symbols']['af_v3_surface_init']-e['ram']
        c['sha256']=sha256(ep[start:start+c['bytes']])
