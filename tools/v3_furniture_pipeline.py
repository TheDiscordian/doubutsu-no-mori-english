"""Discover and convert furniture by format and behaviour, not by item name.

All generated donor data stays under build/. Unsupported cases get explicit
per-item reasons; no callbacks or resource dependencies are silently dropped.
"""
import argparse
from bisect import bisect_right
from collections import Counter
import json
import math
from pathlib import Path
import re
import struct

from aflib import sha256, u32
from apply_translation import write_new
from gc_names import rel_sections
from item_identity_sheet import SHEET_SHA, sheet_rows
from map_artwork import compile_commands
from title_assets import model_texture_shape, pack4, untile
from v3_asset_loader import ROOT
from v3_furniture_art import SEGMENT, command_source, parse_model, verify_sources
from v3_registry import FURNITURE
from v3_villager_art import native_palette, normalise_vertex_flags

VERSION = 2
LAYERS = ('opaque', 'opaque1', 'translucent', 'translucent1')
BEHAVIOURS = {0: 'static', 1: 'front-seat', 2: 'any-direction-seat', 4: 'front-sofa',
              8: 'single-bed', 16: 'double-bed'}
STOCK = {'ftr_listA': 0, 'ftr_listB': 1, 'ftr_listC': 2,
         'ftr_listEvent': 3, 'ftr_listLottery': 5}
# Reviewed complete GAFE01-r0 draw implementation, not an item allowlist.
# It selects two opaque models and a palette using (actor index - base) * 12.
INDEXED_STATIC_DRAW_SHA = '612998bdab7cb941114e08d66db7100ded74894f8c1ccfdbdffe4bb9fbb44917'


class ReviewRequired(ValueError):
    """A valid donor feature lacks a supported conversion/runtime category."""


class Source:
    """Index the checked donor once; resolve thousands of dependencies cheaply."""
    def __init__(self, rel, symbols):
        verify_sources(rel, symbols)
        self.rel, self.symbols = rel, symbols.decode()
        self.sections = rel_sections(rel)
        self.base, self.size = self.sections[5]
        self.data = rel[self.base:self.base+self.size]
        self.names, self.spans = {}, {}
        for name, address, size in re.findall(
                r'^(\S+) = \.data:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', self.symbols, re.M):
            at, n = int(address, 16), int(size, 16)
            if at+n > self.size or not n: raise ValueError('Invalid donor symbol span')
            self.names.setdefault(name, []).append((at, n))
            self.spans.setdefault((at, n), []).append(name)
        self.starts = sorted({at for at, _ in self.spans})
        self.by_start = {}
        for (at, n), names in self.spans.items():
            self.by_start.setdefault(at, []).append((n, sorted(names)[0]))
        self.functions = {}
        for name, address, size in re.findall(
                r'^(\S+) = \.text:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', self.symbols, re.M):
            at, n = int(address, 16), int(size, 16)
            if not n or at+n > self.sections[1][1]: raise ValueError('Invalid donor function span')
            self.functions.setdefault(at, []).append((name, n))
        self.relocations = self.index_relocations()
        self.relocation_addresses = sorted(self.relocations)
        if sorted(self.names['furniture_quality']) != [(0x39FB4, 5064), (0x7B5B0, 5064)]:
            raise ValueError('Changed complete donor profile tables')
        self.quality = [self.pointers(at, n) for at, n in self.names['furniture_quality']]

    def index_relocations(self):
        rel = self.rel
        module, table, n = u32(rel, 0), u32(rel, 0x28), u32(rel, 0x2C)
        if not n or n%8 or table+n > len(rel): raise ValueError('Invalid import table')
        imports = list(struct.iter_unpack('>II', rel[table:table+n]))
        starts = {row[1] for row in imports}
        if len(starts) != len(imports): raise ValueError('Duplicate relocation streams')
        result, self.code_relocations = {}, {}
        for imported, first in imports:
            if first%4 or not 0 <= first < len(rel): raise ValueError('Invalid relocation stream')
            end = min((s for s in starts if s > first), default=len(rel))
            section, address, ended = None, 0, False
            for at in range(first, end-7, 8):
                delta, kind, target_section, target = struct.unpack_from('>HBBI', rel, at)
                if kind == 203: ended = True; break
                if kind == 202:
                    if target_section >= len(self.sections): raise ValueError('Bad source section')
                    section, address = target_section, 0
                    continue
                if section is None: raise ValueError('Missing source section')
                address += delta
                if address > self.sections[section][1]: raise ValueError('Relocation exceeds section')
                if kind in (0, 201, 204): continue
                if section == 1:
                    if address in self.code_relocations: raise ValueError('Duplicate code relocation')
                    self.code_relocations[address] = (kind, imported, target_section, target)
                if section != 5: continue
                if address in result: raise ValueError('Duplicate data relocation')
                result[address] = (kind, imported == module, target_section, target)
            if not ended: raise ValueError('Unterminated relocation stream')
        return result

    def function(self, target):
        rows = self.functions.get(target, [])
        if len(rows) != 1: raise ReviewRequired('callback has no unique complete function')
        name, n = rows[0]
        base = self.sections[1][0]
        raw = self.rel[base+target:base+target+n]
        relocations = {at-target: row for at,row in self.code_relocations.items() if target <= at < target+n}
        return raw, dict(symbol=name, offset=target, bytes=n, sha256=sha256(raw),
                        relocations=relocations)

    def callback_models(self, profile_at, index):
        """Specialise a checked constant selector; unknown callback effects fail."""
        def reject(reason): raise ReviewRequired('custom callbacks: ' + reason)
        pointer = self.relocations.get(profile_at+48)
        if pointer is None or pointer[:3] != (1, True, 5): reject('invalid vtable pointer')
        name, at, n = self.containing(pointer[3], exact=True)
        if n != 20 or self.data[at:at+n] != bytes(n): reject('unsupported vtable')
        pointers = {p-at: r for p,r in self.relocations.items() if at <= p < at+n}
        if set(pointers) != {0,4,8,12} or any(r[:3] != (1,True,1) for r in pointers.values()):
            reject('unsupported callback slots or DMA callback')
        functions = {}
        for slot, role in enumerate(('create','move','draw','destroy')):
            raw, receipt = self.function(pointers[slot*4][3]); functions[role] = receipt
            if role != 'draw' and (raw != bytes.fromhex('4e800020') or receipt['relocations']):
                reject('lifecycle effects need an adapter')
        draw = functions['draw']
        if draw['sha256'] != INDEXED_STATIC_DRAW_SHA: reject('unrecognised draw implementation')
        raw, _ = self.function(draw['offset'])
        table_pointer = draw['relocations'].get(0x1A)
        if table_pointer is None: reject('missing selector table')
        table = table_pointer[3]
        expected = {0x10:(10,0,4,0x8009AECC), 0xAC:(10,0,4,0x8009AF18),
                    0x1A:(6,u32(self.rel,0),5,table), 0x2A:(4,u32(self.rel,0),5,table)}
        if draw['relocations'] != expected: reject('changed draw dependencies')
        table_name, table, size = self.containing(table, exact=True)
        # addi r0,r6,-base; mulli r7,r0,12. These instructions and every
        # other effect are covered by the complete implementation hash above.
        first = -struct.unpack_from('>h',raw,0x26)[0]
        stride = struct.unpack_from('>H',raw,0x2E)[0]
        selected = index-first
        if stride != 12 or size%stride or not 0 <= selected < size//stride:
            reject('selector index escapes the complete table')
        table_raw = self.data[table:table+size]
        dependencies = self.pointers(table,size)
        if table_raw != bytes(size) or set(dependencies) != set(range(table,table+size,4)):
            reject('incomplete selector table')
        models = {layer:self.containing(dependencies[table+selected*stride+i*4],exact=True)
                  for i,layer in enumerate(LAYERS[:2])}
        palette = self.containing(dependencies[table+selected*stride+8],exact=True)
        if palette[2] != 32: reject('selector palette is not sixteen colours')
        return models, {0x08000000:palette[1]}, dict(
            category='indexed-static-model-palette', vtable_symbol=name, vtable_offset=at,
            functions=functions, table_symbol=table_name, table_offset=table, table_bytes=size,
            table_sha256=sha256(table_raw), table_pointers=dependencies,
            first_runtime_index=first, selected_index=selected, entries=size//stride,
            palette_symbol=palette[0], palette_offset=palette[1])

    def pointers(self, at, n):
        if at < 0 or n <= 0 or at+n > self.size: raise ValueError('Out-of-range dependency')
        start = bisect_right(self.relocation_addresses, at-1)
        end = bisect_right(self.relocation_addresses, at+n-1)
        result = {}
        for location in self.relocation_addresses[start:end]:
            kind, local, section, target = self.relocations[location]
            if (kind != 1 or not local or section != 5 or location%4 or location+4 > at+n
                    or target >= self.size or u32(self.data, location)):
                raise ReviewRequired('non-data or external dependency')
            result[location] = target
        return result

    def symbol(self, name):
        rows = self.names.get(name, [])
        if len(rows) != 1: raise ReviewRequired('missing or ambiguous symbol: ' + name)
        return rows[0]

    def raw(self, name):
        at, n = self.symbol(name)
        return self.data[at:at+n]

    def containing(self, target, *, exact=False):
        index = bisect_right(self.starts, target)-1
        if index < 0: raise ReviewRequired('dependency has no bounded symbol')
        start = self.starts[index]
        candidates = [(n, name) for n, name in self.by_start[start] if start <= target < start+n]
        if len(candidates) != 1 or exact and start != target:
            raise ReviewRequired('ambiguous or interior dependency')
        n, name = candidates[0]
        return name, start, n

    def profile(self, item):
        if type(item) is not int or not 0x3000 <= item < 0x33C8 or item&3:
            raise ReviewRequired('not a canonical donor furniture identity')
        index = 1024 + (item-0x3000)//4
        targets = [table.get(at+index*4) for (at, _), table in zip(self.names['furniture_quality'], self.quality)]
        if targets[0] is None or targets[0] != targets[1]:
            raise ReviewRequired('profile tables disagree or lack the item')
        name, at, n = self.containing(targets[0], exact=True)
        if n != 52: raise ReviewRequired('unsupported furniture profile format')
        raw = self.data[at:at+n]
        # Inspect all fields before asking for .data pointers: callback pointers
        # may target executable code, and must remain an explicit behaviour gap.
        locations = [p-at for p in self.relocations if at <= p < at+n]
        if any(p >= 16 and p != 48 for p in locations):
            features = {16:'dynamic texture', 20:'dynamic palette', 24:'animation rig',
                        28:'texture animation', 48:'custom callbacks'}
            raise ReviewRequired(', '.join(features.get(p, 'unknown profile dependency') for p in locations if p >= 16))
        if raw[:32] != bytes(32) or raw[48:] != bytes(4):
            raise ReviewRequired('unrelocated profile pointers')
        h, scale, shape, collision, rotation, lighting, contact, pad, interaction = struct.unpack_from('>ff6BH', raw, 32)
        if (not math.isfinite(h) or not 0 < h <= 200 or raw[36:40] != struct.pack('>f', .01)
                or shape not in (3, 4, 5) or collision not in (0, 1, 2, 5)
                or rotation not in (0, 1) or lighting not in (0, 1, 2) or pad):
            raise ReviewRequired('unsupported scalar profile category')
        if contact not in BEHAVIOURS or interaction not in (0, 0x10):
            raise ReviewRequired(f'contact/interaction behaviour {contact:02X}/{interaction:04X}')
        extra = {}
        if 48 in locations:
            if locations != [48]: raise ReviewRequired('custom callbacks with additional model dependencies')
            models, bindings, adapter = self.callback_models(at,index)
            extra = dict(palette_bindings=bindings, callback_adapter=adapter)
        else:
            pointers = self.pointers(at, n)
            if not pointers or any(p-at not in (0, 4, 8, 12) for p in pointers):
                raise ReviewRequired('unsupported static model slots')
            models = {LAYERS[(p-at)//4]: self.containing(target, exact=True) for p, target in pointers.items()}
        return dict(profile_symbol=name, profile_offset=at, profile_sha256=sha256(raw),
            scalar_hex=raw[32:48].hex(), behaviour=BEHAVIOURS[contact], contact_action=contact,
            interaction_flags=interaction,
            size_code={3:1, 4:0, 5:2}[shape], shape=shape, models=models, **extra)


def prepare(source, item):
    """Discover every model, texture, palette, and vertex dependency from the ROM."""
    descriptor = source.profile(item)
    palettes, textures, vertex_arrays, raw_models = {}, {}, {}, {}
    bindings, used_bindings = descriptor.get('palette_bindings', {}), set()
    for label, (name, at, n) in descriptor['models'].items():
        if n%8: raise ReviewRequired('unaligned display list')
        raw, pointers = source.data[at:at+n], source.pointers(at, n)
        position = 0
        while position < n:
            a, b = struct.unpack_from('>II', raw, position)
            op = a >> 24
            if op in (0xF0, 0xFD, 0x01):
                target = pointers.get(at+position+4)
                if op == 0xF0 and b in bindings:
                    if target is not None: raise ReviewRequired('relocated constant palette binding')
                    target = bindings[b]; used_bindings.add(b)
                elif target is None or b: raise ReviewRequired('missing model dependency relocation')
                symbol, start, size = source.containing(target, exact=op != 0x01)
                if source.pointers(start, size): raise ReviewRequired('pointer-bearing texture or vertex array')
                if op == 0xF0:
                    if size != 32: raise ReviewRequired('palette is not sixteen colours')
                    palettes[start] = (symbol, size)
                elif op == 0xFD:
                    w, h, fmt, bits = model_texture_shape(raw[position:position+8])
                    if fmt not in (2,4) or bits != 0 or w*h//2 != size or w*h//2 > 2048:
                        raise ReviewRequired('texture is not complete TMEM-sized CI4/I4')
                    if start in textures and textures[start][2:] != (w, h, fmt):
                        raise ReviewRequired('texture has inconsistent dimensions')
                    textures[start] = (symbol, size, w, h, fmt)
                else:
                    if size%16: raise ReviewRequired('invalid complete vertex array')
                    vertex_arrays[start] = (symbol, size)
            if op == 0x0A:
                count = (a >> 17 & 127)+1
                position += (1 + (max(0, count-3)+3)//4)*8
            else: position += 8
            if position > n: raise ReviewRequired('truncated packed model')
        raw_models[label] = name, at, raw, pointers
    if used_bindings != set(bindings): raise ReviewRequired('unused constant palette binding')
    if (any(r[4]==2 for r in textures.values()) and not palettes) or len(vertex_arrays) != 1:
        raise ReviewRequired('static materials need CI4 palettes and one complete vertex array')
    body, resources, offsets = bytearray(), [], {}
    def add(at, name, n, convert, **details):
        raw = source.data[at:at+n]
        converted = convert(raw)
        if len(converted) != n: raise ReviewRequired('resource conversion changes allocation')
        body.extend(bytes(-len(body)%32)); offsets[at] = len(body); body.extend(converted)
        resources.append(dict(symbol=name, donor_offset=at, native_offset=offsets[at], bytes=n,
            source_sha256=sha256(raw), output_sha256=sha256(converted), **details))
    for at, (name, n) in sorted(palettes.items()): add(at, name, n, native_palette, kind='palette')
    for at, (name, n, w, h, fmt) in sorted(textures.items()):
        add(at, name, n, lambda data, w=w, h=h: pack4(untile(data, w, h, 4)), kind='texture', width=w, height=h,
            format='CI4' if fmt==2 else 'I4')
    vertex, (name, n) = next(iter(vertex_arrays.items()))
    add(vertex, name, n, lambda data: normalise_vertex_flags(data)[0], kind='vertices')
    models = {}
    for label, (name, at, raw, pointers) in raw_models.items():
        models[label] = dict(symbol=name, donor_offset=at, source_sha256=sha256(raw),
            rows=parse_model(raw, at, pointers, tuple(palettes),
                {p:(r[2], r[3]) for p,r in textures.items()}, vertex, n, static_4bit=True,
                palette_bindings=bindings))
    # Validate all native emitter rules before creating output files.
    commands, sections = command_source(models, offsets)
    return descriptor, bytes(body), resources, offsets, models, commands, sections


def identity_rows(path):
    if sha256(path.read_bytes()) != SHEET_SHA: raise ValueError('Changed identity worksheet')
    rows = list(sheet_rows(path, 'Items'))
    if any(rows[0][1].get(k) != v for k,v in {'C':'ID (AF)', 'E':'ID (AC)', 'J':'Name (English)'}.items()):
        raise ValueError('Changed identity columns')
    result = {}
    for number, cells in rows[1:]:
        value = cells.get('E', '')
        if not re.fullmatch(r'3[0-9A-F]{3}', value): continue
        item = int(value, 16)
        if item in result: raise ValueError('Ambiguous worksheet donor identity')
        result[item] = number, cells
    return result


def name_metadata(source, item, identity):
    """Keep prepared-asset names tied to the actual English donor too."""
    index = 1024+(item-0x3000)//4
    name_raw = source.raw('ftrName2_table')[(index-1024)*16:(index-1023)*16]
    try: name = name_raw.decode('ascii').rstrip(' ')
    except UnicodeDecodeError: raise ReviewRequired('name needs supported encoding') from None
    if not name or name != identity[1].get('J') or name in ('DUMMY', 'dummy'):
        raise ReviewRequired('name/identity is ambiguous or unused')
    return dict(id=f'GAFE01-r0/item/{item:04X}', item_id=f'{item:04X}', runtime_index=index,
                name=name, name_sha256=sha256(name_raw), name_source_index=index-1024)


def metadata(source, item, profile, identity):
    number, sheet = identity
    if any(sheet.get(k) != '-' for k in ('C', 'H', 'CG', 'CJ')):
        raise ReviewRequired('native identity/artwork correspondence needs review')
    names = name_metadata(source,item,identity); index = names['runtime_index']
    action_sound = source.raw('mRmTp_ftr_se_type')[index]
    if action_sound not in (0,1,2):
        raise ReviewRequired(f'action-sound category {action_sound} needs the shared seating adapter')
    layer_type = source.raw('aMR_layer_set_info')[index]
    if layer_type not in (0, 1, 2):
        raise ReviewRequired(f'unsupported placement-layer category {layer_type}')
    lists = []
    for key in source.names:
        if re.fullmatch(r'ftr_list\w*', key):
            raw = source.raw(key)
            if len(raw)%2: raise ValueError('Incomplete donor stock list')
            ids = struct.unpack('>'+str(len(raw)//2)+'H', raw)
            if item in ids:
                if ids[-1] or 0 in ids[:-1] or ids.count(item) != 1:
                    raise ReviewRequired('ambiguous acquisition list')
                lists.append((key, sha256(raw)))
    if len(lists) != 1 or lists[0][0] not in STOCK:
        raise ReviewRequired('acquisition needs an adapter: ' + ', '.join(r[0] for r in lists))
    catalogue = list(struct.iter_unpack('>HH', source.raw('mCL_furniture_list')))
    entries = [(position, mode) for position,(i,mode) in enumerate(catalogue) if i == index]
    if len(entries) != 1:
        raise ReviewRequired('catalogue preview needs a framing adapter')
    preview = entries[0][1]
    draw = source.raw('furniture_draw_data$436')
    if len(draw) != 328 or not 0 <= preview < len(draw)//8:
        raise ReviewRequired('catalogue preview exceeds the complete donor table')
    framing = draw[preview*8:preview*8+8]
    scale, y = struct.unpack('>ff',framing)
    if not (math.isfinite(scale) and .1 <= scale <= 2 and math.isfinite(y) and -200 <= y <= 100):
        raise ReviewRequired('unsupported catalogue preview framing')
    price = struct.unpack_from('>H', source.raw('ftr_price_table'), index*2)[0]
    hra = u32(source.data, 0x4FAFC+index*4)
    feng = source.data[0x4EBF0+index*2:0x4EBF0+index*2+2]
    birth, surface, series = hra>>8&63, hra>>6&3, hra>>26
    if birth >= 23 or hra&63 or series >= 59:
        raise ReviewRequired('scoring needs an acquisition/category adapter')
    native_hra = (hra&0xFFFFC000)|(birth<<9)|(surface<<7)
    return dict(**names, action_sound=action_sound,
        layer_type=layer_type, interaction_flags=profile['interaction_flags'],
        price=price, size_code=profile['size_code'], footprint=('1x1','2x1','2x2')[profile['size_code']],
        donor_list=lists[0][0], donor_list_sha256=lists[0][1], stock_group=STOCK[lists[0][0]],
        ordinary_stock=STOCK[lists[0][0]] < 3, donor_catalogue_position=entries[0][0], preview_mode=preview,
        donor_preview_scalar_hex=framing.hex(),
        catalogue_orderable=True, donor_hra_hex=f'{hra:08x}', native_hra_hex=f'{native_hra:08x}',
        feng_hex=feng.hex(), series=series, birth_category=birth, surface=surface,
        donor_series_hex=source.raw('mMkRm_series_info')[series*3:series*3+3].hex(),
        identity_worksheet_row=number, behaviour=profile['behaviour'])


def scan(source, worksheet, installed=None):
    installed = set(FURNITURE) if installed is None else set(installed)
    result = []
    for item, identity in sorted(identity_rows(worksheet).items()):
        row = dict(item_id=f'{item:04X}', name=identity[1].get('J'), installed=item in installed,
                   asset_ready=False)
        try:
            profile, body, resources, offsets, models, commands, sections = prepare(source, item)
            estimated = (len(body)+sum(n for _,n in sections)+15)&~15
            if estimated > 9216: raise ReviewRequired('complete object exceeds native model-bank capacity')
            formats={r['format'] for r in resources if r['kind']=='texture'}
            categories = [profile['behaviour'], 'static-4bit', ('1x1','2x1','2x2')[profile['size_code']]]
            categories += ['static-ci4'] if formats=={'CI4'} else ['intensity-materials']
            if 'callback_adapter' in profile: categories.append(profile['callback_adapter']['category'])
            row.update(asset_ready=True, profile=profile,
                object_bytes=estimated, textures=sum(r['kind']=='texture' for r in resources),
                vertices=sum(r['bytes']//16 for r in resources if r['kind']=='vertices'),
                triangles=sum(len(r.get('triangles',[])) for m in models.values() for r in m['rows']),
                categories=categories)
            meta = metadata(source, item, profile, identity)
            row.update(status='supported', metadata=meta, categories=categories+[meta['donor_list']])
        except ValueError as error:
            row.update(status='review', reason=str(error))
        result.append(row)
    return dict(format='AFV3-AUTO-FURNITURE-1', version=VERSION,
                source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()),
                worksheet_sha256=SHEET_SHA, counts=dict(Counter(r['status'] for r in result)), rows=result)


def convert(source, worksheet, output, selected=(), installed=None, *, assets_only=False, category=None):
    inventory = scan(source, worksheet, installed)
    rows = [r for r in inventory['rows'] if (r['asset_ready'] if assets_only else r['status']=='supported') and
            (r['item_id'] in selected if selected else not r['installed']) and
            (category is None or category in r['categories'])]
    if selected and set(selected) != {r['item_id'] for r in rows}:
        missing = sorted(set(selected)-{r['item_id'] for r in rows})
        raise ValueError('Unsupported or filtered requested entries: '+json.dumps(missing))
    if not rows: raise ValueError('No supported uninstalled furniture in the requested category')
    identities = identity_rows(worksheet)
    names = {r['item_id']:name_metadata(source,int(r['item_id'],16),identities[int(r['item_id'],16)]) for r in rows}
    output.mkdir(parents=True, exist_ok=False)
    objects = []
    for row in rows:
        item = int(row['item_id'], 16)
        profile, body, resources, offsets, models, commands, sections = prepare(source, item)
        directory = output/row['item_id']; directory.mkdir()
        source_file = directory/'commands.c'; write_new(source_file, commands.encode())
        compiled = compile_commands(directory/'gbi', source_file, sections)
        asset, destinations, records = bytearray(body), {}, []
        for label, model in models.items():
            asset.extend(bytes(-len(asset)%8)); destinations[label] = len(asset); asset.extend(compiled[label])
            records.append(dict(layer=label, symbol=model['symbol'], source_sha256=model['source_sha256'],
                native_offset=destinations[label], bytes=len(compiled[label]), output_sha256=sha256(compiled[label]),
                triangles=sum(len(r.get('triangles',[])) for r in model['rows'])))
        asset.extend(bytes(-len(asset)%16))
        if len(asset) != row['object_bytes']: raise ValueError('Compiled object size differs from preflight')
        name = row['item_id']+'.n64obj.bin'; write_new(output/name, asset)
        objects.append(dict(**row.get('metadata',names[row['item_id']]), profile=profile, resources=resources, models=records,
            import_ready=row['status']=='supported', pending_reason=row.get('reason'),
            native_profile_scalar_hex=profile['scalar_hex'], model_offsets=destinations,
            object_file=name, object_bytes=len(asset), object_sha256=sha256(asset)))
        print(json.dumps(dict(converted=row['item_id'], name=row['name'], bytes=len(asset))), flush=True)
    report = dict(format=('AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1' if assets_only else
                          'AFV3-AUTO-FURNITURE-ASSETS-1'), version=VERSION,
        source_rel_sha256=inventory['source_rel_sha256'], source_symbols_sha256=inventory['source_symbols_sha256'],
        objects=objects, runtime_installed=False)
    write_new(output/'inventory.json', (json.dumps(inventory, indent=2)+'\n').encode())
    write_new(output/'art.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('scan', 'convert', 'import'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--select', action='append', default=[], help='Canonical donor ID; defaults to all supported new furniture')
    parser.add_argument('--category', help='Restrict to a discovered shared category, without an item list')
    parser.add_argument('--assets-only', action='store_true',
                        help='convert only: prepare artwork even when metadata/acquisition is unsupported; never install')
    parser.add_argument('--base-lock', type=Path, default=ROOT/'config/v3-import-build.json')
    args = parser.parse_args(); output = args.output.resolve()
    if args.assets_only and args.command != 'convert': parser.error('--assets-only requires convert')
    if args.category and args.command == 'scan': parser.error('--category requires convert or import')
    if output.exists() or not output.is_relative_to(ROOT/'build'): raise ValueError('Use a fresh ignored build path')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                    (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    worksheet = ROOT/'build/item-identity-megasheet.xlsx'
    from v3_furniture_install import inputs, build
    _, base_report = inputs(args.base_lock)
    installed = [int(r['item_id'],16) for r in base_report['furniture']['imports']+[base_report['speed_bag']]]
    if args.command == 'scan':
        report = scan(source, worksheet, installed); output.parent.mkdir(parents=True, exist_ok=True)
        write_new(output, (json.dumps(report, indent=2)+'\n').encode())
        print(json.dumps(dict(counts=report['counts'], supported_new=[r['item_id'] for r in report['rows']
                         if r['status']=='supported' and not r['installed']])))
    elif args.command == 'convert': convert(source, worksheet, output, args.select, installed,
                                            assets_only=args.assets_only, category=args.category)
    else:
        output.mkdir(parents=True)
        convert(source,worksheet,output/'assets',args.select,installed,category=args.category)
        report = build(output/'cartridge',output/'assets',args.base_lock)
        print(json.dumps(dict(runtime_abi=report['runtime_abi'],output_sha256=report['output_sha256'])))


if __name__ == '__main__': main()
