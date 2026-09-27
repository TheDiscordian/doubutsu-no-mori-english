"""One optional parent/display/save selection for each implemented creature."""
import copy
import struct
import zlib

from aflib import by_vrom,sha256,u32
from v3_asset_loader import ROOT,BLOB
from v3_import_storage import ROWS,ITEMS,slot
from v3_creature_items import RAM,TABLE,encode,checked

FORMAT='AFV3-CREATURE-SELECTION-1'
SOURCES=('tools/v3_creature_selection.py','tools/v3_creature_items.py',
    'tools/v3_creature_fish.py','tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py',
    'tools/v3_optional_composition.py','tools/v3_browser_composition.py',
    'overlays/v3/surface_bootstrap.c','experimental/imports/composer.mjs',
    'experimental/imports/app.mjs','experimental/imports/index.html')


def profile(rows):
    result=bytearray(4)
    for row in rows:
        item=int(row['item_id'],16)
        index=item-0x2320 if row['kind']=='fish' else item-0x2D20+9 if row['kind']=='insect' else -1
        if (not 0<=index<17 or row['kind']=='fish' and index>=9 or
                row['kind']=='insect' and index<9 or result[index//8]&(1<<(index&7))):
            raise ValueError('Invalid or duplicate added creature profile identity')
        result[index//8]|=1<<(index&7)
    return bytes(result)


def selected_identities(creatures):
    selection=creatures.get('optional_selection',{})
    expected=sorted(r['id'] for r in creatures['rows'] if r['category']=='fish')
    selected=selection.get('selected_identities')
    if (selection.get('format')!=FORMAT or selection.get('categories')!=['fish'] or
            selection.get('identities')!=expected or not isinstance(selected,list) or
            selected!=sorted(set(selected)) or set(selected)-set(expected) or
            selection.get('web_patcher_enabled') is not False or selection.get('playable_handoff') is not False):
        raise ValueError('Changed complete experimental creature selection contract')
    bits=profile([dict(kind=r['category'],item_id=r['item_id']) for r in creatures['rows'] if r['id'] in selected])
    if bits.hex()!=selection.get('profile_hex') or sha256(bits)!=selection.get('profile_sha256'):
        raise ValueError('Changed creature selection/save profile')
    return set(selected)


def install(base,prior,blob):
    from v3_furniture_pipeline import Source
    e=copy.deepcopy(prior['equipment_resources']);r=e['creature_items'];fish=e['creature_fish'];w=fish['world']
    if r.get('optional_selection'):raise ValueError('Creature selections are already installed')
    if not all(w.get(k) for k in ('spawn_manager_installed','catch_records_installed',
            'pocket_icons','collection_ui_installed','behaviour_choices')):
        raise ValueError('Fish selection requires the connected field/catch/UI/behaviour consumers')
    if (not e['creature_field']['installed'] or not all(r.get(k) for k in (
            'names_prices_categories_installed','room_conversion_installed','room_profiles_installed')) or
            prior['save_codec']['format_version']!=7):
        raise ValueError('Creature selection lacks complete identity/field/save support')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    checked(base,prior,source)
    p=r['packet'];packet=bytearray(blob[p['blob_offset']:p['blob_offset']+p['bytes']])
    if sha256(packet)!=p['sha256']:raise ValueError('Changed prepared parent packet')
    selected={row['id'] for row in r['rows'] if row['category']=='fish'}
    if len(selected)!=9:raise ValueError('Incomplete connected fish category')
    displays={row['parent_item_id']:row for row in r['profiles']}
    for row in r['rows']:
        active=row['id'] in selected;row['ready']=row['selected']=active
        display=displays[row['item_id']];index=slot(int(display['item_id'],16));offset=ROWS+index*80
        if active:
            if u32(blob,offset+4)!=0 or blob[0x40+index//8]&(1<<(index&7)):
                raise ValueError('Creature enable overwrites an active saved identity')
            struct.pack_into('>I',blob,offset+4,1);blob[0x40+index//8]|=1<<(index&7)
        display['selected']=active;display['profile_record_sha256']=sha256(blob[offset:offset+80])
    table=encode(r['rows']);packet[TABLE:TABLE+len(table)]=table
    blob[p['blob_offset']:p['blob_offset']+p['bytes']]=packet
    p.update(sha256=sha256(packet),crc32=zlib.crc32(packet));r['table_sha256']=sha256(table)
    bits=profile([dict(kind=row['category'],item_id=row['item_id']) for row in r['rows'] if row['selected']])
    r.update(ready_items=9,profile_bits_enabled=9,optional_selection=dict(format=FORMAT,categories=['fish'],
        identities=sorted(selected),selected_identities=sorted(selected),profile_hex=bits.hex(),
        profile_sha256=sha256(bits),experimental=True,web_patcher_enabled=False,playable_handoff=False,
        ordinary_gameplay_tested=False,native_save_reload_tested=False,controller_pak_supported=False),
        remaining=['added insect field behaviours','Controller Pak transport','ordinary gameplay and save/reload'])
    fish.update(selectable=True,additional_resident_bytes=0,
        pending=['Controller Pak collection transport','ordinary gameplay and native save/reload'],
        sources={path:sha256((ROOT/path).read_bytes()) for path in (*fish['sources'],*SOURCES)})
    save=copy.deepcopy(prior['save_runtime']);save.update(profile_hex=blob[0x20:0xE0].hex(),
        profile_sha256=sha256(blob[0x20:0xE0]))
    return e,{},dict(save_runtime=save,clothing=copy.deepcopy(prior['clothing']))


def options(blob,report):
    r=report.get('equipment_resources',{}).get('creature_items',{})
    if not r.get('optional_selection'):return {}
    selected=selected_identities(r);p=r['packet'];packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    if sha256(packet)!=p['sha256'] or zlib.crc32(packet)!=p['crc32']:
        raise ValueError('Changed complete creature selection packet')
    if packet[TABLE:TABLE+r['table_bytes']]!=encode(r['rows']):
        raise ValueError('Changed complete creature identity/name/selection table')
    displays={v['parent_item_id']:v for v in r['profiles']};result={}
    for i,row in enumerate(r['rows']):
        active=row['id'] in selected;d=displays[row['item_id']];n=slot(int(d['item_id'],16));at=ROWS+n*80
        if (row['selected']!=active or row['ready']!=active or d['selected']!=active or
                struct.unpack_from('>HHI',blob,at)!=(row['runtime_index'],int(row['display_item_id'],16),int(active)) or
                blob[at+8:at+76].hex()!=d['profile_hex'] or sha256(blob[at:at+80])!=d['profile_record_sha256'] or
                sha256(blob[ITEMS+n*32:ITEMS+(n+1)*32])!=d['item_record_sha256'] or
                bool(blob[0x40+n//8]&(1<<(n&7)))!=active):
            raise ValueError('Changed creature parent/display/profile binding')
        if not active:continue
        result[row['id']]=dict(id=row['id'],name=row['name'],kind=row['category'],item_id=row['item_id'],
            dependencies=[],enable_offset=at+4,enable_bytes=4,display_item_id=row['display_item_id'],
            display_runtime_index=row['runtime_index'],carried_enable_offset=p['blob_offset']+TABLE+16+i*28+8)
    if set(result)!=selected:raise ValueError('Incomplete creature options')
    return result


def checksum_fields(image,report):
    e=report.get('equipment_resources',{});r=e.get('creature_items',{})
    if not r.get('optional_selection'):return []
    p=r['packet'];f=by_vrom(image);start=f[BLOB].pstart+p['blob_offset']
    ram=e['surface_bootstrap']['code']['symbols']['af_v3_creature_items_crc_expected']
    at=f[BLOB].pstart+e['blob_offset']+ram-e['ram']
    if u32(image,at)!=p['crc32'] or zlib.crc32(image[start:start+p['bytes']])!=p['crc32']:
        raise ValueError('Changed selectable creature checksum field')
    return [dict(offset=at,before=image[at:at+4].hex(),start=start,length=p['bytes'])]


def update_report(blob,report,selection):
    r=report['equipment_resources']['creature_items'];selected=set(selection['enabled']);p=r['packet']
    packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    for row in r['rows']:row['ready']=row['selected']=row['id'] in selected
    for row in r['profiles']:
        parent=next(v for v in r['rows'] if v['item_id']==row['parent_item_id'])
        row['selected']=parent['selected'];at=ROWS+slot(int(row['item_id'],16))*80
        row['profile_record_sha256']=sha256(blob[at:at+80])
    r['ready_items']=r['profile_bits_enabled']=sum(row['selected'] for row in r['rows'])
    r['optional_selection'].update(selected_identities=sorted(selected&set(r['optional_selection']['identities'])),
        profile_hex=selection['creature_profile_hex'],profile_sha256=selection['creature_profile_sha256'])
    p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
    r['table_sha256']=sha256(packet[TABLE:TABLE+r['table_bytes']])
    if r.get('room_scoring'):
        scoring=r['room_scoring']
        for row in scoring['rows']:row['installed']=row['id'] in selected
        scoring['installed_identities']=sorted(row['id'] for row in scoring['rows'] if row['installed'])
    selected_identities(r)


def install_scoring(base,prior,blob):
    """Use the ordinary scoring converter for every creature representation."""
    from v3_furniture_pipeline import Source
    from v3_furniture_install import scoring
    from v3_hra_birth import donor_categories
    import v3_hra as hra
    import v3_feng_shui as feng
    e=copy.deepcopy(prior['equipment_resources']);r=e['creature_items']
    if not r.get('optional_selection') or r.get('room_scoring'):
        raise ValueError('Creature scoring requires selected parents without installed scoring')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    checked(base,prior,source);_,categories=donor_categories(source)
    if (sha256(source.data[0x4FAFC:0x4FAFC+1266*4])!=hra.DONOR_SHA or
            sha256(source.data[0x4EBF0:0x4EBF0+1266*2])!=feng.DONOR_SHA):
        raise ValueError('Changed complete donor creature room-evaluation tables')
    parents={row['item_id']:row for row in r['rows']};rows=[]
    for display in r['profiles']:
        item=int(display['source_item_id'],16);index=(item-0x1000)//4 if item<0x3000 else (item-0x3000)//4+1024
        value=u32(source.data,0x4FAFC+index*4);birth=value>>8&63;surface=value>>6&3;series=value>>26
        if birth>=len(categories) or value&63:raise ValueError('Unreviewed creature scoring category')
        native=(value&0xFFFFC000)|(categories[birth]<<9)|(surface<<7)
        rows.append(dict(id=parents[display['parent_item_id']]['id'],item_id=display['item_id'],
            source_item_id=display['source_item_id'],source_index=index,runtime_index=display['runtime_index'],
            donor_hra_hex=f'{value:08x}',native_hra_hex=f'{native:08x}',
            feng_hex=source.data[0x4EBF0+index*2:0x4EBF2+index*2].hex(),
            donor_birth_category=birth,birth_category=categories[birth],surface=surface,series=series,
            donor_series_hex=source.raw('mMkRm_series_info')[series*3:series*3+3].hex(),
            installed=parents[display['parent_item_id']]['selected']))
    active=[row for row in rows if row['installed']]
    changes,updates=scoring(base,prior,active,source)
    r['room_scoring']=dict(format='AFV3-CREATURE-ROOM-SCORING-1',rows=rows,
        installed_identities=sorted(row['id'] for row in active),
        donor_hra_sha256=hra.DONOR_SHA,donor_feng_sha256=feng.DONOR_SHA,
        native_evaluation_tested=False,additional_resident_bytes=0)
    updates['clothing']=copy.deepcopy(prior['clothing'])
    fish=e['creature_fish'];fish.update(additional_resident_bytes=0,
        sources={path:sha256((ROOT/path).read_bytes()) for path in (*fish['sources'],
            'tools/v3_creature_selection.py','tools/v3_optional_composition.py')})
    return e,changes,updates
