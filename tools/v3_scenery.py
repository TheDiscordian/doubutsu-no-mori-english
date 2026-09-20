"""Prepare shared seasonal scenery dependencies through the model converter.

Foreground tables select complete descriptors; descriptors select body lists,
shadow lists, and caller-owned vertices. These are dependencies, not new items
or installed acquisition routes. All generated donor data stays under build/.
"""
import json
import math
import re
import struct

from aflib import sha256, u32
from apply_translation import write_new
from v3_furniture_pipeline import prepare_material_pair, compile_models
from v3_villager_art import native_palette

SEASONS = ('cherry', 'ordinary', 'winter', 'xmas')
TYPE_OWNERS = ('bgCherryItem', 'bgItem', 'bgWinterItem', 'bgXmasItem')
PENDING = ('Scenery resources are prepared, not installed. Native seasonal rendering, '
           'planting, growth/death, collision, cutting/shaking, and selected-only '
           'golden-shovel acquisition still require integration.')
# Complete consumer contracts, independent of particular foreground identities.
CONTRACTS = {
    'bg_item_common_palload': (68, (
        'bff7f1acf11591ebe8b1a86887f9bc8740f7ac39fd27017bece4310b119693df',)*4),
    'bIT_copy_vtx': (84, (
        '608a37679f5b9e272507444635ccb73f872ccac505c270e80103c3223503fb27',)*4),
    'bg_item_common_draw_loop_type1': (228, (
        '4e0a7d08fc7f4de374fc2dc36674d34f066089b488c58ef7b044939c7d66c062',
        '60571ad34bfc5d72e8a418f057c6b6d143538fc39b5b32a1191c12a32299c269',
        '5855f5955f3c99d469ae98b953ffde3dd9b9489797a8c9ab3d86f726c4b316cb',
        '587d837adf2db46b0afe24d9d9d563253ba8352ebb533678540d3d1c50a3e37d')),
    'bg_item_common_s_draw_loop_type1': (228, (
        '9584489e96b8878bfaef4bf1af256fce5613888db0c2c77f66d3b71fca686a21',
        'e77f4ec901c653a8363d57c34ae9535e8cbe3e762bc8b910bad6717bf34d7347',
        '3b97aedffbb5ff1900c02a86d9841e3f1047647223ceb43e28e8713c2a08d875',
        '4ae8f3853134fe1f12032c3eb03c03c75714b80af886c6f25ff863b8d9b90030')),
    'bg_item_common_draw_item_body': (124, (
        'c21b263f7e2276e1ed2a28c57dd424d023b1e6c806f5e2471d9de788976dd782',
        '9e41762fa38707c21679dcbe1d50f8ec12a68a1837a9e291a585b6cec705aad0',
        '2b7784eb1a955a9f6091a4fd0a4cefbc7de6952ca8e65448717b859f48ad1049',
        '0a1cf69362f3fe58890b51c461988d6be9223330c59ab929c6b5fc8040d027ea')),
    'bg_item_common_draw_item_shadow': (284, (
        '339b81bff203926c4d26a564a72c16333ca293cd1f57df8c3db705a5a85896a1',
        'dd0adaee0f40159fcac90a8fff6814af6611c63bb55da3bf7ab9090e1ce27728',
        'b227f218da4da84d7f09eb313b45c2891e3940dd74a89dd21c70961466654a7f',
        'a5e9ff68f9c7a7a6a14f8781b1a822259263f5861377a3f33126ed250d189f6b')),
    'mFM_SetFGPal': (316, (
        'a786e668c8895eedca40c97f66a795f2924fef1fdee289ab9dfa62d9373bd377',)),
}


def resource(source, at, *, size=None, pointers=False):
    name, at, n = source.containing(at, exact=True)
    if size is not None and n != size:
        raise ValueError('Changed complete scenery resource size')
    refs = source.pointers(at, n)
    if refs and not pointers:
        raise ValueError('Unexpected scenery resource pointers')
    raw = source.data[at:at+n]
    return dict(symbol=name, donor_offset=at, bytes=n, sha256=sha256(raw),
                **({'pointers':refs} if pointers else {'hex':raw.hex()}))


def consumers(source):
    result = {}
    for name, (size, digests) in CONTRACTS.items():
        offsets = sorted(at for at, rows in source.functions.items()
                         if any(n == name for n, _ in rows))
        if len(offsets) != len(digests):
            raise ValueError('Missing or ambiguous scenery consumer')
        receipts = []
        for at, digest in zip(offsets, digests, strict=True):
            raw, receipt = source.function(at)
            if len(raw) != size or sha256(raw) != digest:
                raise ValueError('Changed complete scenery consumer')
            receipts.append(receipt)
        result[name] = receipts
    return result


def palettes(source, functions):
    at, _ = source.symbol('mFM_obj_gold_01_pal_dol')
    bank = resource(source, at, size=14*32)
    term, _ = source.symbol('tree_pal_idx_table$821')
    selector = resource(source, term, size=18*4)
    if (bank['sha256'] != '7dc04db285cb3e84a94e36bb526c1f7cb79e24f31c243608989e351de824408c'
            or selector['sha256'] != '94f144ce4977b3a23f8efd947f308123f6998eb114a13db7b750c6815568c639'):
        raise ValueError('Changed seasonal palette bank or term selector')
    targets = {r[3] for r in functions['mFM_SetFGPal'][0]['relocations'].values() if r[2] == 5}
    if not {at, term} <= targets:
        raise ValueError('Missing seasonal palette consumer binding')
    indices = list(struct.unpack('>18I', source.data[term:term+72]))
    if any(i >= 14 for i in indices): raise ValueError('Seasonal palette index exceeds bank')
    raw = source.data[at:at+bank['bytes']]
    converted = b''.join(native_palette(raw[i:i+32]) for i in range(0, len(raw), 32))
    return dict(bank=bank, selector=selector, term_indices=indices,
                palette_slot=8, palette_count=14, output_sha256=sha256(converted)), converted


def discover(source, category='gold-tree'):
    if category != 'gold-tree': raise ValueError('Unsupported scenery dependency category')
    functions = consumers(source)
    palette, _ = palettes(source, functions)
    tables = sorted(source.names['draw_part_table_a'])
    if len(tables) != 4: raise ValueError('Missing seasonal scenery owners')
    objects, descriptors, bindings, table_receipts = {}, [], [], []

    def draw_list(at, dl, variant, shadow=None):
        name, _, n = source.containing(at, exact=True)
        expected = functions['bg_item_common_s_draw_loop_type1' if shadow else
                             'bg_item_common_draw_loop_type1'][variant]['offset']
        if (n != 8 or u32(source.data, at) or source.data[at+6:at+8] != bytes(2)
                or source.relocations.get(at) != (1, True, 1, expected)
                or any(at < p < at+8 for p in source.relocations)):
            raise ValueError('Unsupported scenery drawing callback or list fields')
        mi, gi = source.data[at+4:at+6]
        if mi*4 not in dl or gi*4 not in dl or mi == gi:
            raise ValueError('Scenery display index exceeds complete table')
        parts = [source.containing(dl[i*4], exact=True) for i in (mi, gi)]
        context = {'external_vertices':shadow} if shadow else {'palette_slot':palette['palette_slot']}
        key = f'model-{parts[0][1]:08X}-{parts[1][1]:08X}'
        row = dict(key=key, models=parts, render_context=context)
        if key in objects and objects[key] != row:
            raise ValueError('Conflicting scenery caller bindings')
        objects[key] = row
        return dict(symbol=name, donor_offset=at, callback=expected,
                    material_index=mi, geometry_index=gi, object=key)

    for variant, (season, owner, table) in enumerate(zip(SEASONS, TYPE_OWNERS, tables, strict=True)):
        root, length = table
        table_receipts.append(resource(source, root, pointers=True))
        roots = source.pointers(root, length)
        if (length % 8 or any((p-root) % 8 for p in roots)
                or any(u32(source.data, p) for p in range(root, root+length, 8))):
            raise ValueError('Incomplete scenery descriptor table')
        selected, display_usage = {}, {}
        for loc, part in sorted(roots.items()):
            name, _, size = source.containing(part, exact=True)
            if not name.startswith('gold_tree'): continue
            if not re.fullmatch(r'gold_tree(00[0-4]|000_dead|_stump00[1-4])_part', name):
                raise ValueError('Unsupported gold-tree descriptor category')
            if size != 32 or source.data[loc+4:loc+8] != bytes(4):
                raise ValueError('Unsupported scenery descriptor fields or flags')
            refs = source.pointers(part, size)
            count, shadow_count = u32(source.data, part+4), u32(source.data, part+12)
            shadow_length = struct.unpack_from('>f', source.data, part+20)[0]
            fields = {part, part+8} | ({part+16, part+24, part+28} if shadow_count else set())
            if (set(refs) != fields or count not in (1, 2) or shadow_count not in (0, 4)
                    or not math.isfinite(shadow_length) or not 0 <= shadow_length <= 60
                    or not shadow_count and any(source.data[part+12:part+32])
                    or any(u32(source.data, p) for p in refs)):
                raise ValueError('Unsupported or incomplete scenery body/shadow dependencies')
            dl = resource(source, refs[part], pointers=True)
            if dl['bytes'] % 8 or set(dl['pointers']) != set(range(refs[part], refs[part]+dl['bytes'], 4)):
                raise ValueError('Incomplete scenery display-list table')
            targets = {p-refs[part]:v for p,v in dl['pointers'].items()}
            usage = display_usage.setdefault(refs[part], (set(targets), set()))
            if usage[0] != set(targets): raise ValueError('Inconsistent scenery display table')
            lists = resource(source, refs[part+8], size=count*4, pointers=True)
            if set(lists['pointers']) != set(range(refs[part+8], refs[part+8]+count*4, 4)):
                raise ValueError('Incomplete scenery body-list table')
            key = f'{season}/{name}'
            row = dict(key=key, season=season, descriptor=resource(source, part, pointers=True),
                       table_index=(loc-root)//8, display_table=dl, list_table=lists,
                       body=[draw_list(p, targets, variant) for _,p in sorted(lists['pointers'].items())],
                       shadow=None)
            if shadow_count:
                vertices = resource(source, refs[part+16], size=shadow_count*16)
                fix = resource(source, refs[part+24], size=shadow_count)
                if any(v not in (0, 1) for v in bytes.fromhex(fix['hex'])):
                    raise ValueError('Unsupported scenery shadow adjustment')
                external = source.containing(refs[part+16], exact=True)
                row['shadow'] = dict(draw=draw_list(refs[part+28], targets, variant, external),
                                     vertices=vertices, fix=fix, length=shadow_length)
            for draw in row['body'] + ([row['shadow']['draw']] if row['shadow'] else []):
                usage[1].update((draw['material_index']*4, draw['geometry_index']*4))
            selected[row['table_index']] = key
            descriptors.append(row)
        if len(selected) != 10: raise ValueError('Incomplete gold-tree scenery descriptors')
        if any(expected != used for expected, used in display_usage.values()):
            raise ValueError('Unconsumed scenery display-list dependency')
        for suffix, first, size in (('', 0, 131*12), ('2', 0x800, 106*12)):
            at, _ = source.symbol('typeData_table_'+owner+suffix)
            receipt = resource(source, at, size=size, pointers=True)
            table_receipts.append(receipt)
            refs = receipt['pointers']
            for i in range(size//12):
                entry = at+i*12
                draw_type = struct.unpack_from('>h', source.data, entry+2)[0]
                if draw_type not in selected: continue
                if (source.data[entry:entry+2] != bytes(2)
                        or {p-entry for p in refs if entry <= p < entry+12} != {4, 8}
                        or any(u32(source.data, entry+p) for p in (4, 8))):
                    raise ValueError('Unsupported scenery type-row flags or position bindings')
                positions = [resource(source, refs[entry+p], size=64) for p in (4, 8)]
                if any(not math.isfinite(v) for r in positions
                       for v in struct.unpack('>16f', bytes.fromhex(r['hex']))):
                    raise ValueError('Non-finite scenery positions')
                bindings.append(dict(season=season, foreground_id=f'{first+i:04X}',
                    type_row_offset=entry, descriptor=selected[draw_type], positions=positions))
    identities = [{r['foreground_id'] for r in bindings if r['season']==season} for season in SEASONS]
    if any(len(ids) != 14 or ids != identities[0] for ids in identities):
        raise ValueError('Incomplete or inconsistent seasonal foreground bindings')
    for row in objects.values():
        prepared = prepare_material_pair(source, row['models'], render_context=row['render_context'])
        row['object_bytes'] = (len(prepared[1])+sum(n for _,n in prepared[6])+15)&~15
        row['triangles'] = sum(len(r.get('triangles', ())) for m in prepared[4].values() for r in m['rows'])
    return dict(format='AFV3-SCENERY-SOURCES-1', category=category,
        source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()),
        functions=functions, tables=table_receipts, palettes=palette, bindings=bindings,
        descriptors=descriptors, objects=list(objects.values()),
        counts=dict(seasons=4, foreground_ids=len(identities[0]), descriptors=len(descriptors),
                    model_pairs=len(objects), object_bytes=sum(r['object_bytes'] for r in objects.values())),
        runtime_installed=False, selectable=False, logical_imports_added=0, pending_reason=PENDING)


def convert(source, output, selected=(), *, category='gold-tree'):
    if selected: raise ValueError('Scenery dependencies are whole categories, not selectable items')
    inventory = discover(source, category)
    output.mkdir(parents=True, exist_ok=False)
    objects = []
    for row in inventory['objects']:
        directory = output/row['key']; directory.mkdir()
        prepared = prepare_material_pair(source, row['models'], render_context=row['render_context'])
        asset, offsets, models, sequence = compile_models(directory, prepared)
        if sequence is not None or len(asset) != row['object_bytes']:
            raise ValueError('Scenery compilation differs from complete preflight')
        filename = row['key']+'.n64obj.bin'; write_new(output/filename, asset)
        objects.append(dict(**row, profile=prepared[0], resources=prepared[2], compiled_models=models,
                            model_offsets=offsets, object_file=filename, object_sha256=sha256(asset)))
        print(json.dumps(dict(converted=row['key'], bytes=len(asset))), flush=True)
    palette, data = palettes(source, inventory['functions'])
    filename = 'seasonal-palettes.rgba16.bin'; write_new(output/filename, data)
    report = dict(inventory, format='AFV3-SCENERY-PREPARED-ASSETS-1', version=1,
                  objects=objects, palettes=dict(palette, object_file=filename))
    write_new(output/'inventory.json', (json.dumps(inventory, indent=2)+'\n').encode())
    write_new(output/'art.json', (json.dumps(report, indent=2)+'\n').encode())
    return report
