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


def existing_system_items(report):
    """Admit existing Gulliver and winter-igloo routes, not the new summer scene."""
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
    if any(r['route'] == 19 and r['item_id'] in admitted for r in owner['imports']):
        from v3_camper_trade import VROM, RELOC, QUEST, RAM as TRADE_RAM
        trade = report['camper_trade']; data = files[VROM].extract(image)
        relocation = files[RELOC].extract(image)
        code = trade['code']; suffix = data[trade['original_bytes']:trade['original_bytes']+code['bytes']]
        if (not trade.get('winter_selection_installed') or len(data) != trade['bytes']
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
    return admitted


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
