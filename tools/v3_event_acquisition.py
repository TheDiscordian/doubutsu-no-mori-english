"""Source-derived category stock for additive event acquisition.

One record covers every variant in a donor category. The native constructor
initialises separate stock; menu/payment integration remains explicitly pending.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import ROOT, BLOB, compile_part
from v3_equipment_runtime import RAM, GUARD
from v3_furniture_pipeline import Source
from v3_import_storage import END, jump
from v3_player_actions import native_references

CODE, TABLE, SIZE = 0xB000, 0xBF00, 0xC000
OWNER, RELOC, OWNER_RAM, SLOT = 0x3990000, 0x3998000, 0x80A728C0, 0x80101BC0
SOURCES = ('tools/v3_event_acquisition.py', 'tools/v3_asset_loader.py',
           'overlays/v3/event_acquisition.c', 'overlays/v3/event_acquisition.ld')
EMPTY_RELOCS = '44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
FUNCTIONS = (
    (0x1B6168, 40, 'da5348b783c4a4f42f9a8eab7495855403a04df187416561057b45f41e54e871', EMPTY_RELOCS),
    (0x1B6190, 96, '4d2968716edec752ef48e0b94161ce10b69945fe447414b7fd71d4221bd45dd5', EMPTY_RELOCS),
    (0x1B61F0, 168, 'd25a7b9152c589604f6d34fce6c2f7d2ef89b7189b1857b70931bcb2895fbed7',
     '0137457bfaac3dc41b104fbc03274004ca2c2a8b3de67c4f8b67e14ada209904'),
    (0x1B6298, 60, '8ce03b062321ce7bcff4e6b93327f3c23785f789ab6bc8ceb07ddd23a88e3b53', EMPTY_RELOCS),
    (0x1B6744, 416, '848941a6f57a19b367abe8a5a5f85eaae04b88ac44d7e69392d9924f8f05df0f',
     '8dede59f6885c52281e72f4529dfdf76ce21058511166bdfe7a860a7aa4da6b4'),
    (0x1B6A28, 160, '049b095598a6dcfc04a384a319389b39dfc547baea84b0f5ec7892da3143d0cc',
     '26113efd37b534402ca05845212162b324525daf232ab6ec7416e48610b5ceb0'))
TABLES = (
    ('sell_table$506', '67ae815fee3d751efe4a8fee825ec7ce508754d767f75163887783c14c874aec'),
    ('price$657', '83c7bf421ed6e84620717b4d612f447146a9ec703f9ac4bc8e5b4c20a34722b8'),
    ('msg_no$656', '4f323ecbabdd073db843c79d0d77acaeab33e31c14b278fac08a4470f95b143d'))


def discover(source):
    functions = []
    for at, size, digest, reloc_digest in FUNCTIONS:
        raw, receipt = source.function(at)
        if (len(raw) != size or sha256(raw) != digest or
                sha256(json.dumps(receipt['relocations'], sort_keys=True, separators=(',', ':')).encode()) != reloc_digest):
            raise ValueError('Changed complete donor event stock function/dependencies')
        functions.append(receipt)
    tables, values = [], []
    for name, digest in TABLES:
        at, size = source.symbol(name); raw = source.raw(name)
        if size != 6 or len(raw) != size or sha256(raw) != digest or source.pointers(at, size):
            raise ValueError('Changed complete donor event stock table')
        tables.append(dict(symbol=name, offset=at, bytes=size, sha256=digest))
        values.append(struct.unpack('>3H', raw))
    setup, _ = source.function(FUNCTIONS[2][0])
    count = u32(setup, 0x50) & 65535
    if (count != u32(setup, 0x18) & 65535 or count != u32(setup, 0x34) & 65535 or count != 8 or
            functions[2]['relocations'][0x46][3] != tables[0]['offset'] or
            functions[5]['relocations'][0x46][3] != tables[2]['offset'] or
            functions[5]['relocations'][0x4A][3] != tables[1]['offset']):
        raise ValueError('Changed stock loop/category consumer bindings')
    # The source multiplies fqrand by this complete rodata float before truncation.
    section, at = functions[2]['relocations'][0x42][2:]
    multiplier = struct.unpack_from('>f', source.rel, source.sections[section][0]+at)[0]
    if multiplier != len(values[0]):
        raise ValueError('Donor random selection disagrees with category count')
    names = source.raw('itemName_tool')
    if sha256(names) != 'b2f7827622de6c6db3102080320c79c77268bde1f7e3df7515dd9fa0c92222a8':
        raise ValueError('Changed official event merchandise names')
    rows = []; seen = set()
    for kind, (first, price, message) in enumerate(zip(*values)):
        items = []
        for item in range(first, first+count):
            if item in seen or not 0x2224 <= item < 0x225C:
                raise ValueError('Overlapping or unsupported event stock identity')
            seen.add(item); raw = names[(item-0x2200)*16:(item-0x2200+1)*16]
            items.append(dict(id=f'GAFE01-r0/item/{item:04X}', item_id=f'{item:04X}',
                name=raw.decode('ascii').rstrip(' '), name_sha256=sha256(raw),
                name_source_symbol='itemName_tool', name_source_index=item-0x2200))
        rows.append(dict(kind=kind, first=first, count=count, price=price,
                         message=message, items=items))
    return dict(format='AFV3-EVENT-STOCK-SOURCE-1', source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()), functions=functions, tables=tables,
        rows=rows, stock_bytes=20, sold_out_refills=False, acquisition_installed=False)


def annotate(inventory, source):
    """Attach acquisition to existing identities, without making more choices."""
    evidence = discover(source)
    indexed = {row['item_id']:row for row in inventory['rows']}
    for category in evidence['rows']:
        for item in category['items']:
            row = indexed.get(item['item_id'])
            if row is None or row['name_sha256'] != item['name_sha256']:
                raise ValueError('Event stock does not match the handheld inventory')
            row['acquisition'] = dict(source='fireworks-night-stall', kind=category['kind'],
                price=category['price'], source_message=category['message'],
                stock_slot=int(item['item_id'],16)-category['first'], installed=False)
    inventory['event_acquisition'] = evidence
    return evidence


def native_contract(base, core):
    files = by_vrom(base)
    data, rel = (files[v].extract(base) for v in (OWNER, RELOC))
    if (sha256(data) != '62723bac0721644b1d323a21b7c12cef07f382448b3d64c5995e0d5bac061ee7' or
            sha256(rel) != 'fda2471c89e9d466ed70afe2cb59bdc7d4887a1e99e7a10ca0e462e3220aaef0'):
        raise ValueError('Changed complete translated event owner/relocations')
    native_references(data, rel, expected_sections=(4528,192,0,0))
    if struct.unpack_from('>8I',core,SLOT-16-CODE_RAM) != (
            OWNER,OWNER+4720,OWNER_RAM,OWNER_RAM+4720,0,OWNER_RAM+4528,0,0):
        raise ValueError('Changed event allocation descriptor')
    functions = []
    for at, size, digest in (
            (0x80080080,0x180,'68090afa9f96394f95c3faa4b56ab309bf44e91b9b2c64898ddf1fc2627bfc29'),
            (0x8008033C,0x170,'e3f773780ce82da3b43a46975c07e1c0c37815fbc95bca00f3b00ce8869adec3')):
        raw = core[at-CODE_RAM:at-CODE_RAM+size]
        if sha256(raw) != digest:
            raise ValueError('Changed native event allocation/lookup contract')
        functions.append(dict(address=at, bytes=size, sha256=digest))
    return data, rel, dict(vrom=OWNER, reloc=RELOC, ram=OWNER_RAM, slot=SLOT,
        sha256=sha256(data), reloc_sha256=sha256(rel), native_stock_bytes=20,
        event_payload_bytes=40, added_stock_offset=20, functions=functions)


def install(base, prior, blob, core, original, output):
    old = prior['equipment_resources']; position = old['blob_offset']
    module = bytearray(blob[position:position+old['bytes']])
    if (old.get('event_acquisition') or old['bytes'] != CODE or not old.get('ground_categories') or
            sha256(module) != old['sha256'] or RAM+SIZE > prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed event stock dependency/reservation')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                    (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    description = discover(source)
    data, rel, contract = native_contract(base,core)
    code, compiled = compile_part('event_acquisition',output/'event_acquisition',defines=(
        f'AF_V3_HELD_SELECTED=0x{old["player_actions"]["code"]["symbols"]["af_v3_player_selected_equipment"]:08X}u',))
    records = b''.join(struct.pack('>3H2B',r['first'],r['price'],r['message'],r['count'],r['kind'])
                       for r in description['rows'])
    if len(code) > TABLE-CODE or len(records) != 24:
        raise ValueError('Event stock code/records exceed reserved capacity')
    module.extend(bytes(SIZE-len(module)))
    module[CODE:CODE+len(code)] = code; module[TABLE:TABLE+len(records)] = records
    struct.pack_into('>4I',module,SIZE-16,*([GUARD]*4))
    # Redirect only the actor constructor's save setup call. Its delay slot and
    # the original initializer remain intact; the wrapper resolves the live owner.
    at = 0x80A72980-OWNER_RAM; before = u32(data,at)
    if before != jump(0x80A72D78,link=True):
        raise ValueError('Changed event stock setup call')
    owner = bytearray(data); after = jump(compiled['symbols']['af_v3_event_stock_construct'],link=True)
    struct.pack_into('>I',owner,at,after)
    relocation = bytearray(rel); n = u32(rel,16)
    rows = list(struct.unpack_from('>'+str(n)+'I',rel,20)); removed = 0x44000000 | at
    if rows.count(removed) != 1:
        raise ValueError('Event stock call lacks a unique local relocation')
    rows.remove(removed); struct.pack_into('>I',relocation,16,len(rows))
    relocation[20:20+n*4] = struct.pack('>'+str(n)+'I',*rows,0)
    blob.extend(bytes(-len(blob)%16)); position = len(blob); blob.extend(module)
    if BLOB+len(blob)>END:
        raise ValueError('Event stock module exceeds import storage')
    report = copy.deepcopy(old)
    report['event_acquisition'] = dict(format='AFV3-EVENT-STOCK-RUNTIME-1', source=description,
        code=compiled,code_offset=CODE,table_offset=TABLE,table_bytes=len(records),
        table_sha256=sha256(records),native=contract,constructor_hook=dict(offset=at,before=before,after=after),
        removed_relocation=removed,owner_sha256=sha256(owner),reloc_sha256=sha256(relocation),
        stock_initialization_installed=True,purchase_menu_installed=False,acquisition_installed=False,
        logical_imports_added=0,profile_bits_enabled=0,event_payload_bytes_changed=False,
        native_validation='pending',gameplay_validation='pending')
    report.update(bytes=SIZE,vrom=BLOB+position,blob_offset=position,sha256=sha256(module),
                  crc32=zlib.crc32(module),additional_resident_bytes=SIZE-old['bytes'])
    return report,{OWNER:bytes(owner),RELOC:bytes(relocation)}
