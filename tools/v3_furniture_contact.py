"""Source-shaped contact/floor lifecycles and explicit room-surface dependencies.

Floor indices are identities, not interchangeable numbering across editions.
Preparing a callback never enables a parent whose complete floor bindings are
missing. Use the ordinary pipeline's lifecycle representation for preparation.
"""
import copy
import json
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import ROOT, compile_part

CATEGORY = 'contact-floor-alpha'
FLOOR_VROM = 0x17A1000
FLOOR_SOURCE = ROOT/'build/gamecube/files/forest_2nd.arc.unpacked/data/player_room_floor.bin'
FLOOR_SHA = '2d3eda53f23337b06e17e37179d4934514354bd348e978c6cc61ab5802a57301'
NATIVE_BLOCKS = (
    ('room_clip_registration', 0x82D7F0, 0x80936710, 0x80939050, 332,
     '829a1b5c83b3284fe2e0174932f22be1ad56e184b4540017259fe6b229ed381a'),
    ('contact_direction', 0x82D7F0, 0x80936710, 0x8093CE38, 268,
     'f6b14572e7eded317ebbebe1aeed651426c61b6311a60c5eb73189b52fa0c3a9'),
    ('contact_writer', 0x82D7F0, 0x80936710, 0x8093CF44, 624,
     '78681ed6001cca1cc9e5336df04c4594c300415a775da6efbc8d7e46c441b2f7'),
    ('contact_layers', 0x82D7F0, 0x80936710, 0x80941FA0, 468,
     '07797ec301b413f65a16007c01c16884354a9a534089bc94ec2a6add654038c3'),
    ('floor_initializer', 0x846860, 0x80951A70, 0x80951E64, 88,
     '63c7f281d148ba373011ff686e5fb9896c24326aadf7921c25ea46a9ab633270'),
    ('add_calc', CODE_VROM, CODE_RAM, 0x8009A570, 328,
     'e71f52138d84282c22bfeda3a80af89faca4404bdc727a4609120c9497704dd7'),
)


def source_lifecycle(source, profile):
    from v3_furniture_scroll import CATEGORY as SCROLL
    adapter = profile.get('callback_adapter', {})
    functions = copy.deepcopy(adapter.get('functions', {}))
    move = functions.get('move')
    if adapter.get('category') != SCROLL or not move or move['bytes'] != 184:
        return None
    if (set(functions) != {'create', 'move', 'draw'} or profile['contact_action'] or
            profile['interaction_flags'] or adapter['pending_profile_fields'] or
            (adapter['scrolling']['colour'] or {}).get('multiplier') != 255.0 or
            adapter['scrolling']['colour'].get('room_f32_offset') != 0x834):
        raise ValueError('Unsupported complete contact/floor profile')
    raw, actual = source.function(move['offset'])
    if actual != move:
        raise ValueError('Changed complete contact/floor callback')
    module = u32(source.rel, 0)
    constants = {}

    def constant(receipt, hi, lo, label, expected):
        pointer = receipt['relocations'].get(hi)
        if (not pointer or pointer[:3] != (6, module, 4) or pointer[3] & 3 or
                receipt['relocations'].get(lo) != (4, module, 4, pointer[3])):
            raise ValueError('Changed contact/floor constant binding')
        start, size = source.sections[4]
        offset = pointer[3]
        if not 0 <= offset <= size-4:
            raise ValueError('Contact/floor constant exceeds complete source')
        value = source.rel[start+offset:start+offset+4]
        if value.hex() != expected:
            raise ValueError('Unsupported contact/floor easing constant')
        record = dict(offset=offset, hex=value.hex(), value=struct.unpack('>f', value)[0])
        if label in constants and constants[label] != record:
            raise ValueError('Contact/floor constants disagree')
        constants[label] = record
        return {hi: pointer, lo: (4, module, 4, offset)}

    create = functions['create']
    reloc = constant(create, 2, 6, 'zero', '00000000')
    source.checked_callback_code(create, 16,
        '971214405ed275f02bea5cb5314160b726e55cf8f57ba309dd57b24453f88792',
        reloc, {}, 'contact/floor initializer')
    reloc = {0x1A: (6, module, 6, 48192), 0x22: (4, module, 6, 48192)}
    for hi, lo, label, value in (
            (0x1E, 0x26, 'zero', '00000000'), (0x72, 0x76, 'one', '3f800000'),
            (0x86, 0x92, 'fraction', '3d23d70a'), (0x8A, 0x9E, 'maximum_step', '3dcccccd'),
            (0x8E, 0x96, 'minimum_step', '3a83126f')):
        reloc.update(constant(move, hi, lo, label, value))
    floors = [struct.unpack_from('>H', raw, at)[0] for at in (0x36, 0x3E)]
    if len(set(floors)) != 2 or any(n >= 128 for n in floors):
        raise ValueError('Invalid signed-byte source floor identities')
    helpers = source.checked_callback_code(move, 184,
        '19e0ce149364531b0de55dde71f3995fae6e80dad2f3c13adb83a040ab84d4e6', reloc,
        {0x14: (0x103BC4, 'aMR_GetContactInfoLayer1'), 0xA0: (0x4AFF0, 'add_calc')},
        'contact/floor alpha', dict(zip((0x36, 0x3E), floors)), internal_branches=True)
    contact = helpers['aMR_GetContactInfoLayer1']
    if (contact['bytes'] != 52 or contact['sha256'] !=
            'db0a6978f69d604ba28b26684d101066aebdeb796c8c1972909e1f1062de4006' or
            contact['relocations'] != {2: (6, module, 6, 48192), 6: (4, module, 6, 48192)}):
        raise ValueError('Changed complete source room contact getter')
    easing = helpers['add_calc']
    if (easing['bytes'] != 228 or easing['sha256'] !=
            '359dc44aa01a58167db714cebdf511184f871bbd151298261ddb220ad2417580' or
            easing['relocations'] != {86: (6, module, 4, 5104), 94: (4, module, 4, 5104),
                                    150: (6, module, 4, 5104), 154: (4, module, 4, 5104)} or
            source.rel[source.sections[4][0]+5104:source.sections[4][0]+5108] != bytes(4)):
        raise ValueError('Changed complete source easing helper')
    return dict(category=CATEGORY, functions=functions, helpers=helpers, constants=constants,
        source_floors=floors, source_steps_per_native_update=2, source_colour_offset=0x834,
        state_offset=0x3C, states=[1, 2, 3, 4], contact_direction=0,
        source_contact_offset=0x178, contact_direction_offset=0x28,
        source_floor_offset=0x28591, start_disabled=False, callback_installed=False)


def native_contract(image):
    files = by_vrom(image)
    blocks = []
    for name, vrom, ram, address, size, digest in NATIVE_BLOCKS:
        raw = files[vrom].extract(image)[address-ram:address-ram+size]
        if len(raw) != size or sha256(raw) != digest:
            raise ValueError('Changed complete native contact/floor dependency: '+name)
        blocks.append(dict(name=name, vrom=vrom, address=address, bytes=size, sha256=digest))
    return dict(blocks=blocks, room_clip=0x80136F2C, room_owner_offset=0,
        contact_offset=0x178, direction_offset=0x28, floor_ram=0x80137655,
        alpha_offset=0x1A4, add_calc=0x8009A570, saved_fields_changed=False)


def floor_bindings(image, contract, report=None):
    from v3_villager_houses import surface_match
    raw = FLOOR_SOURCE.read_bytes()
    if sha256(raw) != FLOOR_SHA:
        raise ValueError('Changed complete donor floor artwork')
    files = by_vrom(image)
    records = []
    for index in contract['source_floors']:
        match = surface_match({FLOOR_VROM: files[FLOOR_VROM]}, image, raw, index, 0x2020)
        candidates = match['native_matches']
        record=dict(source_index=index, native_index=candidates[0]['index'] if len(candidates)==1 else None,
            status='complete-native-artwork-match' if len(candidates)==1 else
                   'missing-additive-floor-import' if not candidates else 'ambiguous-native-floor-identity',
            evidence=match)
        if not candidates and report and report.get('room_surfaces',{}).get('optional_selection'):
            from v3_asset_loader import BLOB
            from v3_registry import surface_identity
            from v3_room_surfaces import convert_record
            from v3_surface_selection import options
            blob=files[BLOB].extract(image);surface=report['room_surfaces']
            key=f'GAFE01-r0/item/{0x2600+index:04X}'
            available=options(blob,report)
            matches=[r for r in surface['rows'] if r['id']==key]
            if key in available:
                if len(matches)!=1:raise ValueError('Ambiguous installed contact floor identity')
                row=matches[0];target,item=surface_identity(0x2600+index)
                start=index*0x2020;original=raw[start:start+0x2020]
                converted=convert_record(original,4);at=row['blob_offset']
                if (row['kind']!='floor' or row['source_index']!=index or
                        row['destination_index']!=target or row['destination_item_id']!=f'{item:04X}' or
                        row['vrom']!=BLOB+at or row['bytes']!=len(converted) or
                        row['source_sha256']!=sha256(original) or
                        row['converted_sha256']!=sha256(converted) or
                        blob[at:at+len(converted)]!=converted or not row['room_texture_installed'] or
                        not surface['room_texture_readers_installed'] or
                        not surface['catalogue_texture_reader_installed'] or
                        not surface['arrange_room_reader_installed']):
                    raise ValueError('Changed complete additive contact floor binding')
                record.update(native_index=target,status='complete-additive-floor-import',
                    additive=dict(id=key,item_id=f'{item:04X}',native_index=target,vrom=row['vrom'],
                        bytes=len(converted),source_sha256=sha256(original),sha256=sha256(converted),
                        independent_optional_selection=True))
        records.append(record)
    return records


def prepare_lifecycle(source, profile, image, report=None):
    contract = source_lifecycle(source, profile)
    if contract is None:
        return None
    floors = floor_bindings(image, contract, report)
    return dict(category=CATEGORY,source=contract, native=native_contract(image), floors=floors,
        dependencies_complete=all(r['native_index'] is not None for r in floors),
        runtime_installed=False)


def lifecycle_record(row, prepared):
    """Refuse partial floor bindings; never substitute an equal numerical ID."""
    floors = prepared['floors']
    if (not prepared['dependencies_complete'] or prepared['source']['category'] != CATEGORY or
            len(floors) != 2 or [r['source_index'] for r in floors] != prepared['source']['source_floors'] or
            any(not checked_floor_record(r) for r in floors)):
        raise ValueError('Contact/floor lifecycle needs both complete native floor bindings')
    indices = [r['native_index'] for r in floors]
    if len(set(indices)) != 2:
        raise ValueError('Contact/floor identities must remain distinct')
    return dict(source_item_id=row['source_item_id'], runtime_index=row['runtime_index'],
        mode=3, flags=0, sound=0, on=indices[0], off=indices[1], maximum=0, step=0,
        source=prepared)


def checked_floor_record(row):
    """Validate recorded identities; callers separately rebind complete ROM data."""
    from v3_registry import SURFACES,surface_identity
    index=row['native_index'];matches=row['evidence']['native_matches']
    if type(index) is not int or not 0<=index<128:return False
    if row['status']=='complete-native-artwork-match':
        return (len(matches)==1 and matches[0]['vrom']==f'{FLOOR_VROM:08X}' and
                matches[0]['index']==index and 'additive' not in row)
    item=0x2600+row['source_index']
    if row['status']!='complete-additive-floor-import' or matches or item not in SURFACES:return False
    native,destination=surface_identity(item);proof=row.get('additive',{})
    return (index==native and proof.get('native_index')==native and
        proof.get('id')==f'GAFE01-r0/item/{item:04X}' and proof.get('item_id')==f'{destination:04X}' and
        proof.get('bytes')==0x2020 and proof.get('independent_optional_selection') is True and
        all(isinstance(proof.get(k),str) and len(proof[k])==64 for k in ('source_sha256','sha256')))


def checked_contracts(source,image,report,*,rows=None):
    """Discover all installed draw records using this source-shaped lifecycle.

    A complete alpha callback does not establish the room owner's separate
    movement-sound behaviour, so ordinary profile activation remains gated.
    """
    from v3_furniture_pipeline import prepare
    result={}
    from v3_room_movement import checked_binding
    movement=checked_binding(source,image,report)
    if rows is None:rows=report['equipment_resources']['room_rigs'].get('scrolling',{}).get('rows',[])
    for row in rows:
        contract=prepare_lifecycle(source,prepare(source,int(row['source_item_id'],16))[0],image,report)
        if contract and contract['dependencies_complete']:
            if row['source_item_id'] in movement:contract['movement']=movement[row['source_item_id']]
            lifecycle_record(row,contract)
            result[row['source_item_id']]=contract
    return result


def prepare_batch(source, image, inventory, output, selected=(), category=None, report=None):
    from apply_translation import write_new
    if category not in (None, CATEGORY):
        raise ValueError('Unsupported lifecycle preparation category')
    rows = []
    for row in inventory['rows']:
        if row['installed'] or selected and row['item_id'] not in selected:
            continue
        prepared = prepare_lifecycle(source, row.get('profile', {}), image, report)
        if prepared is not None:
            rows.append(dict(source_item_id=row['item_id'], name=row['name'], **prepared))
    if not rows or selected and set(selected) != {r['source_item_id'] for r in rows}:
        raise ValueError('Empty or unsupported lifecycle preparation selection')
    output.mkdir(parents=True, exist_ok=False)
    code, compiled = compile_part('room_scroll', output/'room_scroll',
        defines=('AF_V3_ROOM_SCROLL_LIFECYCLE=1', 'AF_V3_ROOM_CONTACT=1'))
    if len(code) > 4096:
        raise ValueError('Contact/floor callbacks exceed existing shared code reservation')
    report = dict(format='AFV3-FURNITURE-LIFECYCLES-PREPARED-1', base_sha256=sha256(image),
        source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()),
        rows=rows, code=compiled, runtime_installed=False, native_execution_tested=False,
        sources={name:sha256((ROOT/name).read_bytes()) for name in (
            'tools/v3_furniture_contact.py','tools/v3_furniture_pipeline.py','tools/v3_furniture_scroll.py',
            'tools/v3_villager_houses.py','tools/v3_villager_art.py','tools/v3_asset_loader.py',
            'overlays/v3/room_scroll.c','overlays/v3/room_scroll.h','overlays/v3/room_scroll.ld')},
        complete_dependencies=sum(r['dependencies_complete'] for r in rows))
    write_new(output/'lifecycles.json', (json.dumps(report, indent=2)+'\n').encode())
    return report
