"""Connect the complete donor seasonal pair through the existing Nook stock path."""
import copy
import struct
import zlib

from aflib import CODE_RAM, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_furniture_pipeline import Source
from v3_import_storage import jump
from v3_private_save_bank import refresh_aliases
from v3_registry import furniture_source

RAM, END, GUARD = 0x804F3500, 0x804F3810, 0xAF53544B
FORMAT = 'AFV3-SEASONAL-STOCK-1'
CHOICE = dict(id='late-december-stock', name='Late-December seasonal stock', binding='stock_mode',
    symbol='af_v3_seasonal_stock_mode', scope='Nook seasonal furniture from December 26 to 31',
    description='N64 mixes selected festive imports with the original New Year pair, keeping both obtainable. GameCube prioritises the selected festive candle and flag. Unselected replacements use native items. Other seasonal dates are unchanged.')
SOURCES = ('tools/v3_seasonal_stock.py', 'overlays/v3/seasonal_stock.c',
    'overlays/v3/seasonal_stock.ld', 'tools/v3_asset_loader.py',
    'tools/v3_furniture_install.py', 'tools/v3_creature_choices.py', 'tools/v3_import_scope.py')
CONTRACTS = ((0x800BF770,0x800BF7EC,'f3943375af0bf15845846fc242a500dc90796054af9a66addc78046ada38e5c9'),
    (0x800BF7EC,0x800BF8E8,'47abde7abb4857d64c866f2c0a599fc664f51c4668f557de102c096c7735030b'),
    (0x800C0684,0x800C088C,'de646ffc1d55e3022da8fe28c4055f18df2750280bcdb6e46d83cab47295ffeb'))


def source_contract(source, prior, core):
    functions = []
    for offset, digest, expected in (
        (0x77934,'a882f7746d6d36ee1e08fb26d863591cdb7876a6123b2044a9d16773b857471c',
         {16:(10,0,4,2148118228),52:(10,0,4,2147863796),88:(10,0,4,2148118304),
          58:(6,1,4,8208),62:(4,1,4,8208)}),
        (0x779A0,'78ac014bbe3f7729204ac7b59a83c0032e9045900d0ab20221e4bed2ae9da20f',
         {10:(6,1,6,48192),18:(4,1,6,48192)})):
        raw, receipt = source.function(offset)
        if sha256(raw) != digest or receipt['relocations'] != expected:
            raise ValueError('Changed complete donor seasonal stock function or dependencies')
        functions.append(receipt)
    # The complete selector supplies the actual pair, not a hand-maintained item
    # list. Its pinned code also supplies December and the 26th-day threshold.
    raw, _ = source.function(0x779A0)
    pairs = [w & 65535 for (w,) in struct.iter_unpack('>I',raw) if w >> 16 in (0x38A0,0x38C0)]
    if len(pairs) != 4 or u32(raw,0x58) != 0x2805001A:
        raise ValueError('Changed complete seasonal pair/date operands')
    probability_offset = source.sections[4][0] + 8208
    probability = source.rel[probability_offset:probability_offset+4]
    if probability != bytes.fromhex('3f000000'):
        raise ValueError('Changed donor single-slot seasonal probability')
    fallback = [u32(core,a-CODE_RAM)&65535 for a in (0x800BF8CC,0x800BF8D4)]
    records = []
    for item in pairs[2:]:
        matches = [r for r in prior['furniture']['imports'] if furniture_source(r)[0] == item]
        if len(matches) != 1:
            raise ValueError('Seasonal donor pair lacks a complete installed import')
        row = matches[0]
        shop = [r for r in prior['shops']['imports'] if r['item_id'] == row['item_id']]
        if (len(shop) != 1 or shop[0]['group'] != 4 or shop[0]['donor_list'] != 'ftr_listTrain'
                or not row.get('runtime_installed') or row.get('remaining') and
                    any(x not in ('representative native execution','ordinary gameplay and save/restart') for x in row['remaining'])):
            raise ValueError('Incomplete seasonal item behaviour or installed acquisition list')
        donor = source.raw('ftr_listTrain')
        if shop[0]['donor_list_sha256'] != sha256(donor) or struct.unpack('>'+str(len(donor)//2)+'H',donor).count(item) != 1:
            raise ValueError('Changed complete donor seasonal membership')
        records.append(dict(id=row['id'], item_id=row['item_id'], donor_item_id=f'{item:04X}',
            runtime_index=row['runtime_index'], profile_ram=row['profile_ram'],
            model_sha256=row['object_sha256']))
    if {r['item_id'] for r in records} != {r['item_id'] for r in prior['shops']['imports'] if r['group']==4}:
        raise ValueError('Incomplete matching seasonal stock batch')
    return dict(functions=functions, imports=records, native_fallback=fallback,
        month=12, first_day=26, last_day=31, donor_single_slot_probability_hex=probability.hex(),
        n64_additive_adaptation='Equal native/imported pair choice when any late-December import is selected')


def install(base, prior, blob, core, module, output):
    del blob, module
    e = copy.deepcopy(prior['equipment_resources'])
    if e.get('seasonal_stock') or not e.get('scene_arena',{}).get('installed'):
        raise ValueError('Seasonal stock requires the checked complete scene/startup owner')
    for start,end,digest in CONTRACTS:
        if sha256(core[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError('Changed complete native seasonal stock consumer')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    contract = source_contract(source,prior,core)
    packet = copy.deepcopy(e['console_storage']['packet'])
    raw = bytearray(base[packet['physical']:packet['physical']+packet['bytes']])
    scene = e['scene_arena']
    if (sha256(raw) != packet['sha256'] or zlib.crc32(raw) != packet['crc32']
            or packet['ram']+len(raw) != 0x804F4980
            or scene['code']['ram']+scene['code']['bytes'] > RAM
            or END > scene['borrowed_state']['ram'] or any(raw[RAM-packet['ram']:END-packet['ram']])):
        raise ValueError('Seasonal stock overlaps complete retained code/state')
    generated = output/'seasonal_records.S'
    ids = [int(r['item_id'],16) for r in contract['imports']] + contract['native_fallback']
    write_new(generated, ('.section .rodata.seasonal_records,"a",@progbits\n.balign 4\n'
        '.globl af_seasonal_items\naf_seasonal_items:\n.half '+','.join(hex(x) for x in ids)+'\n').encode())
    code, compiled = compile_part('seasonal_stock',output/'seasonal_stock',
        extra_sources=(str(generated.relative_to(ROOT)),), link_symbols=dict(
            af_seasonal_rtc=0x80136FBC,af_seasonal_random=0x8002C9AC,
            af_seasonal_original=0x800BF7EC,af_seasonal_pair=0x800BF770,
            af_v3_furniture_import_profile=prior['furniture']['code']['symbols']['af_v3_furniture_import_profile']))
    if len(code)>END-RAM-16 or compiled['symbols'][CHOICE['symbol']] != 0x804F37F0:
        raise ValueError('Seasonal stock exceeds checked startup gap')
    raw[RAM-packet['ram']:RAM-packet['ram']+len(code)] = code
    raw[END-16-packet['ram']:END-packet['ram']] = struct.pack('>4I',*([GUARD]*4))
    replacement = dict(packet,sha256=sha256(raw),crc32=zlib.crc32(raw))
    refresh_aliases(e,packet,replacement)
    records = copy.deepcopy(prior['physical_resources'])
    record = next(r for r in records if r['id']==packet['id']); record['sha256']=replacement['sha256']
    address=0x800C073C; at=address-CODE_RAM; before=u32(core,at)
    if before != jump(0x800BF7EC,link=True):
        raise ValueError('Changed native seasonal call')
    after = jump(compiled['symbols']['af_v3_seasonal_stock'],link=True)
    struct.pack_into('>I',core,at,after)
    e['seasonal_stock']=dict(format=FORMAT,installed=True,source=contract,
        code=dict(compiled,ram=RAM),packet=replacement,
        reservation=dict(ram=RAM,bytes=END-RAM,guard=END-16,guard_value=GUARD),
        choice=dict(CHOICE,ram=compiled['symbols'][CHOICE['symbol']],default='N64',values=dict(N64=0,GameCube=1)),
        hook=dict(address=address,before=before,after=after,delay_slot=u32(core,at+4)),
        native_consumers=[dict(start=a,end=b,sha256=h) for a,b,h in CONTRACTS],
        artwork_changed=False,saved_format_changed=False,native_execution_verified=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return e,{},dict(physical_resources=records),[(dict(record,previous_sha256=packet['sha256']),bytes(raw))]


def option(image, report):
    owner=report.get('equipment_resources',{}).get('seasonal_stock')
    if not owner:return None
    row=owner['choice'];p=owner['packet'];at=p['physical']+row['ram']-p['ram']
    if (owner.get('format') != FORMAT or not owner['installed']
            or any(row.get(k)!=v for k,v in CHOICE.items()) or row['default']!='N64'
            or row['values']!=dict(N64=0,GameCube=1) or u32(image,at)!=0
            or sha256(image[p['physical']:p['physical']+p['bytes']])!=p['sha256']):
        raise ValueError('Changed complete installed seasonal stock choice')
    return dict(row,offset=at,before=image[at:at+4].hex())


def checksum_field(image, report):
    owner=report.get('equipment_resources',{}).get('seasonal_stock')
    if not owner:return []
    from aflib import by_vrom
    from v3_asset_loader import BLOB
    e=report['equipment_resources'];p=owner['packet'];boot=e['surface_bootstrap']['code']
    at=by_vrom(image)[BLOB].pstart+e['blob_offset']+boot['symbols']['storage_crc']-e['ram']
    if u32(image,at)!=p['crc32'] or zlib.crc32(image[p['physical']:p['physical']+p['bytes']])!=p['crc32']:
        raise ValueError('Changed seasonal stock startup checksum')
    return [dict(offset=at,before=image[at:at+4].hex(),start=p['physical'],length=p['bytes'])]


def update_report(image, report, resolved):
    e=report['equipment_resources'];owner=e.get('seasonal_stock')
    if not owner:return
    old=copy.deepcopy(owner['packet']);row=owner['choice'];at=old['physical']+row['ram']-old['ram']
    if u32(image,at)!=row['values'][resolved[row['id']]]:
        raise ValueError('Lost seasonal stock behaviour choice')
    raw=image[old['physical']:old['physical']+old['bytes']]
    new=dict(old,sha256=sha256(raw),crc32=zlib.crc32(raw));refresh_aliases(e,old,new)
    row['resolved']=resolved[row['id']]
    owner['code']['sha256']=sha256(raw[RAM-old['ram']:RAM-old['ram']+owner['code']['bytes']])
    next(r for r in report['physical_resources'] if r['id']==old['id'])['sha256']=new['sha256']
