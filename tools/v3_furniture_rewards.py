"""Bind source acquisition categories to unchanged native NPC gift handovers."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, ITEMS, slot
from v3_furniture_pipeline import REWARDS

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


def install(original, base, prior, blob, imports, source, output):
    previous = prior.get('furniture_rewards')
    old_routes = {} if not previous else {r['route']:r for r in previous['routes']}
    active = {REWARDS[r['donor_list']] for r in imports if r.get('donor_list') in REWARDS}
    if not active and not previous:
        return {}, None
    if not active <= ROUTES.keys() or not old_routes.keys() <= active:
        raise ValueError('Missing reward category binding')
    functions = {**DONOR_FUNCTIONS, **{ROUTES[r]['donor_gift']:ROUTES[r]['donor_gift_sha256'] for r in active}}
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
            if (row.get('catalogue_orderable') or row.get('reward_route')!=route or
                    row['donor_list_sha256']!=sha256(source.raw(ROUTES[route]['donor_list']))):
                raise ValueError('Reward descriptor differs from source category')
            records.append(dict(item_id=row['item_id'],runtime_index=row['runtime_index'],route=route))
        blob[at+27] = route
    native_files,files=by_vrom(original),by_vrom(base)
    native_code=native_files[CODE_VROM].extract(original)
    current_code=files[CODE_VROM].extract(base)
    changes, routes = {}, []
    for route in sorted(active):
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
    return changes, dict(code=compiled,entry=RAM,imports=records,routes=routes,
        donor_functions=donor_receipts,reservation_start=FIRST,reservation_end=END,
        reservation_sha256=sha256(reservation),additional_resident_bytes=0,
        selected_profile_aware=True,ordinary_handover_tested=False)
