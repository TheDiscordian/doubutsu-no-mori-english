"""Connect source-supported normal stock and natural generation consumers."""
import copy
import struct
import zlib

from aflib import CODE_RAM, by_vrom, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_furniture_pipeline import Source
from v3_import_storage import jump
from v3_paper_consumers import append_hook, native_owner
from v3_private_save_bank import refresh_aliases

RAM, END = 0x806E3600, 0x806E3FF0
CONTRACTS = (
    (0x800C0AAC, 0x800C0BA0, '742a49224c966355ef84fdd1fda9fd262f4d18847d19b63e4c664e6609776339'),
    (0x800C0BA0, 0x800C0CB4, '838578de865b4aa8041312b84e17c1ec3a5832c7910fd06cd5ab72e20e4462ae'),
    (0x800C34D0, 0x800C37BC, '6adbb8dc8c9a715ce87a19ebaf7c91d91afce92d0945929f96f426a98eef4f9e'),
    (0x800BFFC0, 0x800C0194, 'e3e70dcdfe12565449f5a9a9a53b32d619326d76e90772d7880551abaa0f3eb5'),
)
DONOR = (
    (0x78CA8, '96e307f9640cea2c186afabc45b289df1b62e4667c99e14f599c2e18137252e7'),
    (0x3E20, '59fc84d78333f0f5368f798353154b3afd8636e00479563f5b998ed814fba234'),
    (0x3C50, 'ed0e525baccb01a72d570c71ef5ff50e3ff369a1743b6bfa9ae69193107d0f26'),
    (0x388C, '957256b24369583be952784cd42f6ba5f36eddecdae6509a9677dcbc53da5a03'),
    (0x380A8, '6d89484835f95aaa55f418279f5de1271ba123a13fe70a2d56722d777e05e8d3'),
    (0x78850, '0a46cf7dfa5ada0a65787f2e0f2110513e89e3d2f59fc7790be033dc80c8866d'),
    (0x77A1C, '0e0fc7e44767c722c832ae6a5bf27cc0735b1a7ee2cef58db16b117c73233197'),
    (0x77CB8, '2389abd1d02c8314d9bf7d16110d05a58f877e48b97855385992b589e41f7d78'),
    (0x79D58, '5903f3eab3c4254046d968af5bb9d7c7bee48bd63717ae29b6ae8a260e732f00'),
    (0x7821C, '9d17117981beb7afe86d3773783ea73c43fcaec1e24cd49c76468ccb7ff42b35'),
)
SOURCES = ('tools/v3_normal_acquisition.py', 'overlays/v3/normal_acquisition.c',
    'overlays/v3/normal_acquisition.ld', 'tools/v3_asset_loader.py', 'tools/v3_furniture_install.py',
    'tools/v3_import_scope.py', 'tools/v3_feature_choices.py', 'tools/v3_acquisition_audit.py')


def source_contract():
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    functions = []
    for at, digest in DONOR:
        code, receipt = source.function(at)
        if sha256(code) != digest:
            raise ValueError('Changed complete normal acquisition donor: '+receipt['symbol'])
        functions.append(receipt)
    # Resolve the actual cedar-count table through the complete donor function.
    references = functions[1]['relocations']
    if references.get(26) != (6, 1, 5, 240) or references.get(42) != (4, 1, 5, 240):
        raise ValueError('Changed source cedar-count dependency')
    at = source.sections[5][0]+240
    counts = source.rel[at:at+16]
    if struct.unpack('>4I', counts) != (6, 4, 2, 0):
        raise ValueError('Changed complete source cedar-count table')
    lists = []
    groups = []
    for name, expected in (
        ('diary_listA', '2b012b042b072b0a2b0d0000'),
        ('diary_listB', '2b022b052b082b0b2b0e0000'),
        ('diary_listC', '2b032b062b092b0c2b0f2b000000'),
        ('binsen_listA', '20c020c320c720ca20cd20d120d420d720db20e020e120e420e820eb20ee20f120f420f720fa20fd0000')):
        raw = source.raw(name)
        if raw.hex() != expected:
            raise ValueError('Changed original normal-stock list: '+name)
        lists.append(dict(symbol=name, bytes=len(raw), sha256=sha256(raw)))
        if name.startswith('diary'):
            values = [item+0x10 if item else 0 for item, in struct.iter_unpack('>H', raw)]
            groups.extend(values+[0]*(7-len(values)))
    return functions, counts, struct.pack('>21H', *groups), lists


def install(base, prior, blob, core, module, output):
    del blob, module
    e = copy.deepcopy(prior['equipment_resources'])
    if e.get('normal_acquisition'):
        raise ValueError('Normal acquisition is already installed')
    for start, end, digest in CONTRACTS:
        if sha256(core[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError(f'Changed complete normal acquisition consumer {start:08X}')
    functions, counts, diaries, source_lists = source_contract()
    packet = copy.deepcopy(e['diary_items']['packet'])
    payload = bytearray(base[packet['physical']:packet['physical']+packet['bytes']])
    if (sha256(payload) != packet['sha256'] or zlib.crc32(payload) != packet['crc32']
            or packet['ram'] != 0x806E0000 or len(payload) != 0x4000
            or payload[-16:] != bytes.fromhex('41464447')*4
            or any(payload[RAM-packet['ram']:END-packet['ram']])):
        raise ValueError('Normal acquisition overlaps retained diary, travel, art, or guard bytes')
    generated = output/'normal_acquisition_records.S'
    write_new(generated, ('.section .rodata.cedar_max,"a",@progbits\n.balign 4\n'
        '.globl af_normal_cedar_max\naf_normal_cedar_max:\n.word '+
        ','.join(str(x) for x in struct.unpack('>4I', counts))+'\n'
        '.globl af_normal_diaries\naf_normal_diaries:\n.half '+
        ','.join(str(x) for x in struct.unpack('>21H', diaries))+'\n').encode())
    code, compiled = compile_part('normal_acquisition', output/'normal_acquisition',
        extra_sources=(str(generated.relative_to(ROOT)),), link_symbols=dict(
            af_normal_category=e['player_travel']['compiled']['bindings']['af_carried_category'],
            af_normal_shop_level=0x800C165C, af_normal_halloween=0x800C2E80,
            af_normal_native_plants=0x800C0AAC, af_normal_native_fruit=0x80056310,
            af_normal_random=0x8002C9AC, af_normal_goods=0x80135BC2,
            af_normal_foreground=0x8012D148,
            af_normal_selected_diaries=e['diary_items']['code']['symbols']['af_diary_native_selected'],
            af_normal_prior_select=e['carried_items']['paper']['quantities']['code']['symbols']['af_carried_paper_select'],
            af_normal_prior_stock_list=0x804BFE68,
            af_normal_priorities=0x800C1BF0, af_normal_goods_power=0x800B8C9C))
    if len(code) > END-RAM:
        raise ValueError('Normal acquisition exceeds retained packet padding')
    payload[RAM-packet['ram']:RAM-packet['ram']+len(code)] = code
    replacement = dict(packet, sha256=sha256(payload), crc32=zlib.crc32(payload))
    refresh_aliases(e, packet, replacement)
    records = copy.deepcopy(prior['physical_resources'])
    record = next(r for r in records if r['id'] == packet['id'])
    record['sha256'] = replacement['sha256']
    hooks = []
    for address, before, target in (
        (0x800C0C98, jump(0x800C0AAC, link=True), compiled['symbols']['af_normal_shop_plants']),
        (0x800C3598, jump(0x80056310, link=True), compiled['symbols']['af_normal_new_town']),
        # Cedar uses the saved goods array, never plant_quantity[10], which is
        # the first byte of the existing saved shop-level/notice field.
        (0x800C0024, 0x2841290B, None)):
        at = address-CODE_RAM
        if u32(core, at) != before:
            raise ValueError('Changed normal acquisition hook')
        after = jump(target, link=True) if target else 0x2841290A
        struct.pack_into('>I', core, at, after)
        hooks.append(dict(address=address, before=before, after=after, delay_slot=u32(core, at+4)))

    files = by_vrom(base)
    changes = {}
    for address, target in (
        (0x800BFCF0, compiled['symbols']['af_normal_shop_select']),
        (0x800BF8E8, compiled['symbols']['af_normal_stock_list'])):
        at = address-CODE_RAM
        before = struct.unpack_from('>2I', core, at)
        expected = (jump(e['carried_items']['paper']['quantities']['code']['symbols']['af_carried_paper_select']), 0) if address==0x800BFCF0 else (jump(0x804BFE68), 0)
        if before != expected:
            raise ValueError('Changed complete stock-selector entry')
        struct.pack_into('>2I', core, at, jump(target), 0)
        hooks.extend(dict(address=address+i*4, before=word,
            after=jump(target) if i==0 else 0) for i,word in enumerate(before))
        for patch in e['carried_items']['paper']['quantities']['supply']['core_patches']:
            if patch['address']==address:
                patch['after']=struct.pack('>2I',jump(target),0).hex()
    paper_descriptor = 0x8010DAAC-CODE_RAM
    if struct.unpack_from('>3I',core,paper_descriptor)!=(0x11E3000,0x11E30C0,0x06000088):
        raise ValueError('Changed complete native stationery stock descriptor')
    paper = bytearray(files[0x11E3000].extract(base))
    pointer = u32(paper,0x88)&0xFFFFFF
    from v3_surface_stock import list_items
    original = list_items(paper,pointer)
    if any(0x2040<=item<0x2044 for item in original):
        raise ValueError('Orange paper already stocked')
    list_offset = len(paper)
    paper.extend(struct.pack('>'+str(len(original)+2)+'H',*original,0x2040,0))
    paper.extend(bytes(-len(paper)%16))
    struct.pack_into('>I',paper,0x88,0x06000000|list_offset)
    struct.pack_into('>I',core,paper_descriptor+4,0x11E3000+len(paper))
    changes[0x11E3000]=bytes(paper)
    updates = {k: copy.deepcopy(prior[k]) for k in ('shop_floor', 'shop_actors')}
    consumers = e['carried_items']['paper']['quantities']['native_consumers']
    actual = []
    for row in consumers:
        if row['name'] != 'shop-floor' and not row['name'].startswith('shop-'):
            continue
        vrom, reloc, ram = row['installed_vrom'], row['installed_reloc'], row['ram']
        data, rel = files[vrom].extract(base), files[reloc].extract(base)
        if (sha256(data) != row['owner']['owner_sha256'] or
                sha256(rel) != row['owner']['relocation_sha256']):
            raise ValueError('Changed complete normal-stock shop consumer')
        from shop_units import PRICE_BIASES
        constants = (PRICE_BIASES[row['vrom']],) if row['vrom'] in PRICE_BIASES else ()
        owner = native_owner(data, rel, ram, address_constants=constants)
        if row['name'] == 'shop-floor':
            binding = append_hook(owner, ram, (0xAFA40000, 0x3084FFFF),
                [0xAFA40000,0x3084FFFF,0x3C028013,0x8C427944,0x1440000C,0,
                 0x2481D4F0,0x2C210010,0x10200003,0,0x03E00008,0x24021F28,
                 0x2401290A,0x14810003,0,0x03E00008,0x24021F2D,
                 jump(ram+8), 0], local_jumps=(17,))
            floor = row['hooks'][1]['address']
            sold = row['hooks'][2]['address']
            append_hook(owner,floor,(0x2461D1C0,0x2C2100C0),
                [0x2461D4F0,0x2C210010,0x10200003,0,
                 jump(0x80954918),0,0x2461D1C0,0x2C2100C0,jump(floor+8),0],
                local_jumps=(4,8))
            append_hook(owner,sold,(0x2461D1C0,0x2C2100C0),
                [0x2461D4F0,0x2C210010,0x10200005,0,0x24011F34,
                 0xA7A1003A,jump(0x80954C00),0x3C188013,
                 0x2461D1C0,0x2C2100C0,jump(sold+8),0],local_jumps=(6,10))
            owner.patch(0x809548F4, 0x2861290A, 0x2861290B)
            owner.patch(0x80954A18, 0x2861290A, 0x2861290B)
        else:
            old = row['hooks']['address']
            binding = append_hook(owner, old, (0x97A2003A, 0x2441DFC0),
                [0x97A2003A,0x2401290A,0x14410002,0,0x24022900,
                 0x2441D4F0,0x2C210010,0x10200002,0,0x24022000,
                 0x2441DFC0,jump(old+8),0],local_jumps=(11,))
        updated, rel, receipt = owner.finish()
        changes.update({vrom: updated, reloc: rel})
        descriptor = row['descriptor']-CODE_RAM
        if struct.unpack_from('>4I', core, descriptor) != (vrom, vrom+len(data), ram, ram+len(data)):
            raise ValueError('Changed complete normal-stock overlay descriptor')
        struct.pack_into('>4I', core, descriptor, vrom, vrom+len(updated), ram, ram+len(updated))
        row['owner'] = receipt
        if row['name'] == 'shop-floor':
            updates['shop_floor'].update(output_sha256=sha256(updated), relocation_sha256=sha256(rel))
        else:
            name = row['name'][5:]
            updates['shop_actors']['owners'][name].update(output_sha256=sha256(updated),
                relocation_sha256=sha256(rel), allocation_bytes=len(updated))
            nook = e['passwords']['nook']['native']['owners'].get(name)
            if nook:
                nook.update(overlay_sha256=sha256(updated), relocation_sha256=sha256(rel))
        actual.append(dict(name=row['name'], vrom=vrom, reloc=reloc, ram=ram,
            source=owner.source, owner=receipt, hook=binding))
    e['normal_acquisition'] = dict(format='AFV3-NORMAL-ACQUISITION-1', code=dict(compiled, ram=RAM),
        packet=replacement, source_functions=functions, cedar_counts_sha256=sha256(counts), hooks=hooks,
        source_lists=source_lists,
        diaries=dict(installed=True,identities=['GAFE01-r0/item/'+f'{item:04X}' for item in range(0x2B00,0x2B10)],
            table_ram=compiled['symbols']['af_normal_diaries'],table_bytes=len(diaries),table_sha256=sha256(diaries),
            minimum_shop_level=2, paper_spaces_replaced=1, consumers=actual),
        paper=dict(installed=True,vrom=0x11E3000,bytes=len(paper),sha256=sha256(paper),
            table_offset=0x88,list_offset=list_offset,item_id='2040',disabled_stock_filter=True),
        cedars=dict(shop_installed=True, new_town_installed=True, item_id='290A',
            minimum_shop_level=2, northern_rows=3, acres_per_row=5, counts=list(struct.unpack('>4I', counts)[:3]),
            consumers=actual, saved_stock='existing 31-item goods array', ordinary_sapling_spaces_replaced=1),
        saved_format_changed=False, native_execution_verified=False,
        sources={p: sha256((ROOT/p).read_bytes()) for p in SOURCES})
    resizes = [
        dict(vrom=v, previous_bytes=files[v].size, previous_sha256=sha256(files[v].extract(base)),
            bytes=len(raw), sha256=sha256(raw)) for v, raw in changes.items() if len(raw) != files[v].size]
    from v3_furniture_install import relocate_resource_plan
    growth = []
    for row in resizes:
        _, plan = relocate_resource_plan(base, files, row['vrom'], changes[row['vrom']],
            minimum_physical=0x100000, reservations=records+growth,
            append_only=False, allow_compressed=True)
        growth.append(plan)
    updates.update(physical_resources=records, runtime_owner_resizes=resizes, resource_growth=growth)
    return e, changes, updates, [(dict(record, previous_sha256=packet['sha256']), bytes(payload))]
