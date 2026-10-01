"""Bind source acquisition categories to unchanged native NPC gift handovers."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, ITEMS, slot
from v3_furniture_pipeline import REWARDS
from v3_registry import furniture_source

RAM, FIRST, END = 0x80474BC0, 0x80474BB0, 0x80474FF0
GUARD = bytes.fromhex('AFF9C0DE')*4
SOURCES = ('tools/v3_furniture_rewards.py', 'overlays/v3/furniture_rewards.c',
           'overlays/v3/furniture_rewards.ld', 'tools/v3_asset_loader.py')
# Per-category call contracts. No item definitions or theme switches.
ROUTES = {
    12: dict(donor_list='ftr_listJonason', fallback=2, vrom=0x00958220,
        reloc=0x009590A0, ram=0x80A97FB0, resident=3712, actor=0xA8,
        owner_sha256='ce9419250491765b143c4019080f66c966ce121f15f39236530301aa39d1ff9d',
        relocation_sha256='fa0a29b0dd781d86f295e4a6af62dcbba78850c43be6f0c104870310a6d18043',
        argument=0x80A983BC, call=0x80A983D8,
        donor_gift='aEDZ_ageru',
        donor_gift_sha256='786e8c916bddae8dac2ce458e2e33a387182e49b79c89aa1ee7bf269c7672b48'),
}
DONOR_FUNCTIONS = {
    'mSP_SelectRandomItem_New': '9d17117981beb7afe86d3773783ea73c43fcaec1e24cd49c76468ccb7ff42b35',
    'mSP_CountElementInCommonList_collect': '2389abd1d02c8314d9bf7d16110d05a58f877e48b97855385992b589e41f7d78',
}


def summer_installed(report):
    """Require the connected installed camper route, not old preparation flags."""
    requirements = {
        'campsite': ('scene_loading_installed',),
        'campsite_calendar': ('calendar_installed', 'manager_installed'),
        'campsite_manager': ('manager_installed',),
        'campsite_placement': ('manager_installed',),
        'camper': ('npc_reader_installed', 'manager_installed'),
        'camper_quest': ('summer_english_message_selection',),
        'camper_text': ('summer_selector_installed', 'native_expression_and_trade_operations_retained'),
        'camper_greeting': ('summer_selection_installed', 'selected_rewards_installed', 'last_gift_tracking_installed'),
        'camper_trade': ('summer_selection_installed', 'selected_rewards_installed'),
        'campsite_environment': ('floor_sound_installed', 'point_parameters_installed', 'timed_lamp_installed'),
    }
    return bool(all(all(report.get(section, {}).get(k) for k in fields)
                for section, fields in requirements.items())
            and report.get('camper_movein', {}).get('natural_growth_guard')
            and report.get('camper_movein', {}).get('transferred_villager_guard')
            and report.get('tent_lamp', {}).get('timed_lamp_installed')
            and report.get('campsite_exterior', {}).get('code', {}).get('symbols', {}).get('af_v3_campsite_exterior_ct')
            and report.get('equipment_resources', {}).get('harvest', {}).get('manager', {}).get('installed'))


def existing_system_items(report):
    """Admit complete Gulliver, winter-igloo, and already-built summer routes."""
    owner = report.get('furniture_rewards', {})
    if (not owner.get('selected_profile_aware') or owner.get('entry') != RAM
            or owner.get('reservation_start') != FIRST or owner.get('reservation_end') != END
            or not owner.get('code', {}).get('symbols', {}).get('af_v3_furniture_reward_count')):
        return set()
    routes = {r['route'] for r in owner.get('routes', []) if r['route'] in ROUTES
              and all(r.get(k) == v for k,v in ROUTES[r['route']].items())}
    trade = report.get('camper_trade', {})
    if (trade.get('winter_selection_installed') and trade.get('selected_rewards_installed')
            and 19 in trade.get('shared_reward_categories', [])
            and trade.get('reward_count_entry') == owner['code']['symbols']['af_v3_furniture_reward_count']):
        routes.add(19)
    if (summer_installed(report) and 23 in trade.get('shared_reward_categories', [])
            and trade.get('reward_count_entry') == owner['code']['symbols']['af_v3_furniture_reward_count']):
        routes.add(23)
    installed = {r['item_id']:r for r in report['furniture']['imports']}
    result = set()
    for row in owner.get('imports', []):
        item = installed.get(row['item_id'])
        if (row['route'] in routes and item and item.get('runtime_installed')
                and item.get('reward_route') == row['route']
                and item['runtime_index'] == row['runtime_index']
                and set(item.get('remaining', [])) <= {
                    'representative native execution', 'ordinary gameplay and save/restart'}):
            result.add(row['item_id'])
    return result


def verify_existing_system_items(image, report):
    """Bind selection admission to complete installed resources and donor lists."""
    admitted = existing_system_items(report)
    if not admitted:
        return admitted
    files = by_vrom(image); blob = files[BLOB].extract(image)
    owner = report['furniture_rewards']; compiled = owner['code']
    start = PACKAGE+FIRST-PACKAGE_RAM; end = PACKAGE+END-PACKAGE_RAM
    raw = blob[start:end]
    if (len(raw) != END-FIRST or raw[:16] != GUARD or raw[-16:] != GUARD
            or sha256(raw) != owner['reservation_sha256']
            or not 0 < compiled['bytes'] <= END-RAM-16
            or sha256(raw[RAM-FIRST:RAM-FIRST+compiled['bytes']]) != compiled['sha256']
            or compiled['symbols']['af_v3_furniture_reward_goods'] != RAM):
        raise ValueError('Changed complete existing-system reward helper')
    from v3_furniture_pipeline import Source
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                    (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    installed = {r['item_id']:r for r in report['furniture']['imports']}
    route_rows = {r['route']:r for r in owner['routes']+owner.get('trade_routes', [])}
    for row in owner['imports']:
        if row['item_id'] not in admitted: continue
        item = installed[row['item_id']]; route = route_rows[row['route']]
        donor = source.raw(route['donor_list'])
        members = struct.unpack('>'+str(len(donor)//2)+'H',donor)
        at = ITEMS+slot(int(row['item_id'],16))*32
        if (sha256(donor) != route['donor_list_sha256']
                or item.get('donor_list') != route['donor_list']
                or item.get('donor_list_sha256') != route['donor_list_sha256']
                or members.count(furniture_source(item)[0]) != 1
                or members[-1] or 0 in members[:-1]
                or struct.unpack_from('>2H',blob,at) != (row['runtime_index'],int(row['item_id'],16))
                or blob[at+7] != 1 or blob[at+24] != 0 or blob[at+27] != row['route']):
            raise ValueError('Changed complete existing-system reward membership or metadata')
    core = files[CODE_VROM].extract(image)
    for route in owner['routes']:
        if not any(r['route'] == route['route'] and r['item_id'] in admitted for r in owner['imports']):
            continue
        rule = ROUTES[route['route']]; data = files[route['vrom']].extract(image)
        if (sha256(data) != route['output_sha256']
                or sha256(files[route['reloc']].extract(image)) != rule['relocation_sha256']
                or core[0x80100C90+rule['actor']*32-CODE_RAM:0x80100C90+rule['actor']*32-CODE_RAM+16]
                    != struct.pack('>4I',rule['vrom'],rule['vrom']+len(data),rule['ram'],rule['ram']+rule['resident'])):
            raise ValueError('Changed complete native Gulliver owner or descriptor')
        patches = ((rule['argument'],0x240E0000|rule['fallback'],0x240E0000|(route['route']<<8)|rule['fallback']),
                   (rule['call'],0x0C02FF3C,0x0C000000|((RAM>>2)&0x03FFFFFF)))
        native = bytearray(data)
        for address,before,after in patches:
            at = address-rule['ram']
            if u32(native,at) != after: raise ValueError('Changed native Gulliver reward hook')
            struct.pack_into('>I',native,at,before)
        if sha256(native) != rule['owner_sha256']:
            raise ValueError('Changed native Gulliver handover outside reward selection')
    if any(r['route'] in (19,23) and r['item_id'] in admitted for r in owner['imports']):
        from v3_camper_trade import VROM, RELOC, QUEST, RAM as TRADE_RAM
        trade = report['camper_trade']; data = files[VROM].extract(image)
        relocation = files[RELOC].extract(image)
        code = trade['code']; suffix = data[trade['original_bytes']:trade['original_bytes']+code['bytes']]
        if (not trade.get('selected_rewards_installed') or len(data) != trade['bytes']
                or sha256(data) != trade['sha256'] or sha256(relocation) != trade['relocation_sha256']
                or struct.unpack_from('>5I',relocation) != tuple(trade['sections'])
                or sha256(suffix) != code['sha256']
                or trade['reward_count_entry'] != compiled['symbols']['af_v3_furniture_reward_count']):
            raise ValueError('Changed complete native winter trade owner or selector')
        for hook in trade['hooks']:
            at = hook['address']-TRADE_RAM
            if data[at:at+8].hex() != hook['after']:
                raise ValueError('Changed native winter trade entry')
        quest = files[QUEST].extract(image)
        if (u32(quest,0x2460) != VROM+len(data) or u32(quest,0x2468) != TRADE_RAM+len(data)):
            raise ValueError('Changed complete native winter trade allocation')
        donor = source.raw('ftr_listKamakura')
        if not any(r.get('donor_list') == 'ftr_listKamakura' and r['donor_list_sha256'] == sha256(donor)
                   for r in owner.get('trade_routes', [])):
            raise ValueError('Missing complete native winter reward membership')
    if any(r['route']==23 and r['item_id'] in admitted for r in owner['imports']):
        verify_summer(image, report, files, blob, core)
    return admitted


def verify_summer(image, report, files, blob, core):
    """Authenticate the retained calendar, scene, visitor, dialogue, and handover."""
    from v3_optional_composition import resident_offset
    from v3_harvest_acquisition import verify_manager
    from v3_holiday_selection import packets
    from v3_campsite_manager import VROM, RAM as MANAGER_RAM
    from v3_campsite_runtime import PLAY, PLAY_RAM
    from textbanks import Bank

    def resident(address, size):
        at=resident_offset(blob,address,size)
        return blob[at:at+size]

    def resource(vrom, size):
        if vrom in files:return files[vrom].extract(image)
        at=vrom-BLOB
        if at<0 or at+size>len(blob):raise ValueError('Missing complete summer scene resource')
        return blob[at:at+size]

    def checked(raw, size, digest, label):
        if len(raw)!=size or sha256(raw)!=digest:
            raise ValueError('Changed complete summer '+label)

    def hook(raw, ram, row):
        after=row['after']
        after=struct.pack('>I',after) if isinstance(after,int) else bytes.fromhex(after)
        at=row['address']-ram
        if raw[at:at+len(after)]!=after:
            raise ValueError('Changed actual summer acquisition hook')

    for section, part, start in (
        ('campsite','code',0x804A0100),('campsite_calendar','code',0x804A2740),
        ('campsite_calendar','event_code',0x804A2100),('campsite_exterior','code',0x804A0360),
        ('campsite_placement','code',0x804A2A70),('camper','reader',0x804A29A0),
        ('camper','registration',0x804A2D00),('camper_quest','code',0x804A2EC0),
        ('camper_movein','code',0x80463EE0),('camper_greeting','gift_code',0x804A2F30),
        ('campsite_environment','code',0x804A2F54)):
        code=report[section][part]
        checked(resident(start,code['bytes']),code['bytes'],code['sha256'],section+' '+part)
    for section, address, size, digest in (
        ('scene packet',report['campsite']['packet_ram'],0x1000,report['campsite']['packet_sha256']),
        ('calendar packet',report['campsite_calendar']['packet'],0x100,report['campsite_calendar']['packet_sha256']),
        ('exterior packet',report['campsite_exterior']['packet_ram'],report['campsite_exterior']['packet_bytes'],report['campsite_exterior']['packet_sha256']),
        ('visitor',report['camper']['owner'],report['camper']['owner_bytes'],report['camper']['owner_sha256']),
        ('cleanup',report['campsite_placement']['cleanup'],report['campsite_placement']['cleanup_bytes'],report['campsite_placement']['cleanup_sha256'])):
        checked(resident(address,size),size,digest,section)
    for row in report['campsite']['resources']:
        checked(resource(row['vrom'],row['bytes']),row['bytes'],row['sha256'],'scene resource')
    decorations=report['equipment_resources']['npc_extra']['events']['decorations']['controllers']
    setup=decorations['code']['symbols']
    if setup['af_decor_previous_setup']!=report['campsite_exterior']['code']['symbols']['af_v3_campsite_structure_setup']:
        raise ValueError('Missing actual summer structure setup forwarding')
    for row in report['campsite_exterior']['resource_moves']:
        raw=bytearray(resource(row['vrom'],row['bytes']))
        if row['vrom']==0x8CB690:
            target=setup['af_decor_actor_setup']
            for address,after,before in ((0x809E93F8,0x3C0F0000|((target+0x8000)>>16),0x3C0F804A),
                                         (0x809E9400,0x25EF0000|(target&65535),0x25EF0A90)):
                at=address-0x809E7ED0
                if u32(raw,at)!=after:raise ValueError('Changed current summer structure setup hook')
                struct.pack_into('>I',raw,at,before)
        checked(raw,row['bytes'],row['sha256'],'scene resource')
    for row in report['campsite']['hooks']:
        hook(core,CODE_RAM,row) if row['address']<PLAY_RAM else hook(files[PLAY].extract(image),PLAY_RAM,row)
    for section in ('campsite_placement','camper_movein'):
        for row in report[section]['hooks']:
            if row['address']<0x80400000:hook(core,CODE_RAM,row)
            else:hook(resident(0x80460000,0xC000),0x80460000,row)
    hook(core,CODE_RAM,report['camper']['hook'])
    hook(core,CODE_RAM,report['campsite_environment']['hooks'][1])

    e=report['equipment_resources']
    for p in packets(e):
        checked(image[p['physical']:p['physical']+p['bytes']],p['bytes'],p['sha256'],'calendar dependency packet')
    verify_manager(image,report,e['harvest'])
    manager=files[VROM].extract(image);m=report['campsite_manager'];symbols=m['code']['symbols']
    start=symbols['af_v3_camper_event_start'];size=m['code']['bytes']
    suffix=bytearray(manager[start-MANAGER_RAM:start-MANAGER_RAM+size])
    # The installed directory extender redirects the compiled 16-row lookup to
    # all 64 daily rows. The compiler's zero control reservation is populated.
    for address,before,after in ((0x8096502C,0x2C640010,0x2C640040),
        (0x8096503C,0x3C038014,0x3C03806F),(0x80965040,0x24639F98,0x24631500)):
        at=address-start
        if u32(suffix,at)!=after:raise ValueError('Changed expanded summer daily directory')
        struct.pack_into('>I',suffix,at,before)
    suffix[symbols['af_v3_camper_controls']-start:]=bytes(start+size-symbols['af_v3_camper_controls'])
    checked(suffix,size,m['code']['sha256'],'manager callback object')
    current=e['harvest']['manager'];at=current['table']-MANAGER_RAM+28*32
    expected=struct.pack('>8I',70,*(symbols['af_v3_camper_event_'+name] for name in ('start','stop','in','out')),0,0,0)
    if manager[at:at+32]!=expected or report['campsite_calendar']['today_capacity']!=64:
        raise ValueError('Changed complete summer manager control')

    greeting=report['camper_greeting']
    for key,digest in (('vrom','sha256'),('relocation_vrom','relocation_sha256')):
        raw=files[greeting[key]].extract(image)
        checked(raw,greeting['bytes'] if key=='vrom' else greeting['relocation_bytes'],greeting[digest],'greeting owner')
    for row in greeting['hooks']:
        hook(files[row['vrom']].extract(image),row['ram'],row)
    for row in report['camper_quest']['owners']:
        raw=files[int(row['vrom'],16)].extract(image);at=row['hook']-row['ram']
        expected=bytes.fromhex(row['after'])
        if row['vrom'] in ('008681F0','008798C0'):
            n=e['npc_extra'];p=n['events']['participants']['code']['symbols']
            if (n['code']['symbols']['af_npc_previous_spawn']!=p['af_hp_spawn_profile'] or
                p['af_hp_previous_spawn_profile']!=report['camper_quest']['code']['symbols']['af_v3_camper_profile']):
                raise ValueError('Missing actual summer profile forwarding')
            target=n['code']['symbols']['af_npc_identity_spawn']
            expected=expected[:4]+struct.pack('>I',0x0C000000|((target>>2)&0x3FFFFFF))
        if raw[at:at+len(expected)]!=expected:
            raise ValueError('Changed summer quest profile or talk entry')
    text=report['camper_text']
    for kind,a,b,key,count in (('message',text['message_vrom'],text['message_table_vrom'],'messages',253),
                             ('select',report['import_storage']['choice_vrom'],text['choice_table_vrom'],'choices',49)):
        entries=Bank(kind,a,b,files[a].extract(image),files[b].extract(image)).entries()
        if len(text[key])!=count:raise ValueError('Incomplete official summer dialogue')
        for row in text[key]:
            if row['id']>=len(entries) or sha256(entries[row['id']])!=row['encoded_sha256']:
                raise ValueError('Changed retained official summer dialogue')

    surface=report['room_surfaces']['items'];code=surface['code']
    at=surface['blob_offset']
    checked(blob[at:at+code['bytes']],code['bytes'],code['sha256'],'shared floor reader')
    if code['symbols']['af_surface_prior_floor']!=0x804A2F54:
        raise ValueError('Missing actual summer floor forwarding')
    hook(core,CODE_RAM,report['room_surfaces']['application']['floor_hook'])
    lamp=report['tent_lamp']
    controller=e['room_rigs']['effects']['controller']
    if (not controller.get('installed') or not controller['original']['timed_lamp_retained'] or
        controller['original']['sha256']!=lamp['owner_sha256']):
        raise ValueError('Missing complete retained summer lamp controller')
    raw=files[controller['vrom']].extract(image)
    checked(raw,controller['bytes'],controller['sha256'],'current lamp controller')
    relocation=files[controller['reloc']].extract(image)
    checked(relocation,len(relocation),controller['reloc_sha256'],'current lamp relocation')
    hook(core,CODE_RAM,controller['descriptor'])
    for row in lamp['profile_hooks']:hook(raw,controller['ram'],row)
    checked(resource(lamp['extra_vrom'],lamp['extra_bytes']),lamp['extra_bytes'],lamp['extra_sha256'],'lamp resident packet')
    for row in lamp['native_hooks']:hook(core,CODE_RAM,row)


def install(original, base, prior, blob, imports, source, output):
    previous = prior.get('furniture_rewards')
    old_routes = {} if not previous else {r['route']:r for r in previous['routes']}
    active = {REWARDS[r['donor_list']] for r in imports if r.get('donor_list') in REWARDS}
    if not active and not previous:
        return {}, None
    if not active <= ROUTES.keys() | {19,23} or not old_routes.keys() <= active:
        raise ValueError('Missing reward category binding')
    functions = {**DONOR_FUNCTIONS, **{ROUTES[r]['donor_gift']:ROUTES[r]['donor_gift_sha256'] for r in active & ROUTES.keys()}}
    donor_receipts = []
    for name, expected in functions.items():
        matches = [at for at, rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1: raise ValueError('Ambiguous donor reward implementation')
        _, receipt = source.function(matches[0])
        if receipt['sha256']!=expected: raise ValueError('Changed donor reward semantics')
        donor_receipts.append(receipt)
    begin, end = PACKAGE+FIRST-PACKAGE_RAM, PACKAGE+END-PACKAGE_RAM
    if not PACKAGE+0x1BA0 <= begin < end <= PACKAGE+0x2000:
        raise ValueError('Reward helper overlaps preview data or accessory artwork')
    if previous:
        if (previous['reservation_start']!=FIRST or previous['reservation_end']!=END or
                sha256(blob[begin:end])!=previous['reservation_sha256']):
            raise ValueError('Changed installed reward reservation')
    elif any(blob[begin:end]):
        raise ValueError('Reward helper reservation is occupied')
    code, compiled = compile_part('furniture_rewards', output/'furniture_rewards')
    if len(code)>END-RAM-16: raise ValueError('Reward helper exceeds reservation')
    reservation = GUARD+code+bytes(END-RAM-16-len(code))+GUARD
    blob[begin:end] = reservation
    old_items = {} if not previous else {r['item_id']:r['route'] for r in previous['imports']}
    records=[]
    for row in imports:
        item = int(row['item_id'],16); at = ITEMS+slot(item)*32
        route = REWARDS.get(row.get('donor_list'),0)
        if blob[at+27]!=old_items.get(row['item_id'],0) or any(blob[at+28:at+32]):
            raise ValueError('Changed reward metadata or reserved fields')
        if route:
            raw=source.raw(row['donor_list']);digest=sha256(raw)
            members=struct.unpack('>'+str(len(raw)//2)+'H',raw)
            if (row.get('catalogue_orderable') or row.get('reward_route',route)!=route or
                    row.get('donor_list_sha256',digest)!=digest or members.count(furniture_source(row)[0])!=1 or
                    members[-1] or 0 in members[:-1]):
                raise ValueError('Reward descriptor differs from source category')
            row.update(reward_route=route,donor_list_sha256=digest)
            records.append(dict(item_id=row['item_id'],runtime_index=row['runtime_index'],route=route))
        blob[at+27] = route
    native_files,files=by_vrom(original),by_vrom(base)
    native_code=native_files[CODE_VROM].extract(original)
    current_code=files[CODE_VROM].extract(base)
    changes, routes = {}, []
    for route in sorted(active & ROUTES.keys()):
        rule=ROUTES[route];vrom=rule['vrom'];ram=rule['ram']
        native=native_files[vrom].extract(original);current=files[vrom].extract(base)
        relocation=files[rule['reloc']].extract(base)
        descriptor=0x80100C90+rule['actor']*32-CODE_RAM
        expected_descriptor=struct.pack('>4I',vrom,vrom+len(native),ram,ram+rule['resident'])
        if (sha256(native)!=rule['owner_sha256'] or len(current)!=len(native) or
                sha256(relocation)!=rule['relocation_sha256'] or
                current_code[descriptor:descriptor+32]!=native_code[descriptor:descriptor+32] or
                current_code[descriptor:descriptor+16]!=expected_descriptor):
            raise ValueError('Changed complete reward owner, relocation, or actor descriptor')
        patches = [(rule['argument'],0x240E0000|rule['fallback'],0x240E0000|(route<<8)|rule['fallback']),
                   (rule['call'],0x0C02FF3C,0x0C000000|((RAM>>2)&0x03FFFFFF))]
        sections=struct.unpack_from('>5I',relocation)
        locations={sum(sections[:(r>>30)-1])+(r&0xFFFFFF)
                   for r in struct.unpack_from('>'+str(sections[4])+'I',relocation,20)}
        if locations & {a-ram for a,_,_ in patches}:
            raise ValueError('Reward binding would retain an invalid owner relocation')
        patched=bytearray(native)
        for address,before,after in patches:
            if u32(native,address-ram)!=before: raise ValueError('Changed native single-gift call')
            struct.pack_into('>I',patched,address-ram,after)
        expected=bytes(patched) if route in old_routes else native
        if current!=expected or (route in old_routes and sha256(current)!=old_routes[route]['output_sha256']):
            raise ValueError('Unexpected changes outside reward argument/call')
        changes[vrom]=bytes(patched)
        routes.append(dict(**rule,route=route,encoded=(route<<8)|rule['fallback'],
            output_sha256=sha256(patched), patches=[dict(address=a,before=b,after=c) for a,b,c in patches],
            donor_list_sha256=sha256(source.raw(rule['donor_list']))))
    trade_routes=[dict(route=route,donor_list=name,donor_list_sha256=sha256(source.raw(name)),
                      encoded=(route<<8)|8,fallback=8) for name,route in REWARDS.items() if route in active & {19,23}]
    return changes, dict(code=compiled,entry=RAM,imports=records,routes=routes,trade_routes=trade_routes,
        donor_functions=donor_receipts,reservation_start=FIRST,reservation_end=END,
        reservation_sha256=sha256(reservation),additional_resident_bytes=0,
        selected_profile_aware=True,ordinary_handover_tested=False)
