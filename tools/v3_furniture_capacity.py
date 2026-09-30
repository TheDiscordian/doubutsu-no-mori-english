"""Extend complete static-model capacity in room banks and catalogue previews."""
import copy
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_import_storage import replace_checked, jump
import v3_catalogue as catalogue
import v3_furniture_runtime as room

OLD_BYTES, MODEL_BYTES = 0x2400, 0x3000
DATA, COUNT = 0x80500010, 100
FLAG = 'AF_V3_LARGE_MODEL_BANKS=1'
ALLOC_FIRST, ALLOC_END, STRIDE = 0x808A9748, 0x808A9798, 0x808A9784
ALLOC_SHA = '35db5a6769412e96285a98e9a23ce4e2a805069995cc490cf076fec78968bdcc'
POOL_WORD = 0x800C4B10
SOURCES = ('tools/v3_furniture_capacity.py', 'overlays/v3/furniture_banks.h',
           'overlays/v3/furniture.c', 'tools/v3_furniture_install.py',
           'tools/v3_furniture_pipeline.py', 'tools/v3_garden_runtime.py')


def catalogue_stride(data, before, after):
    if before not in (OLD_BYTES, MODEL_BYTES) or after not in (OLD_BYTES, MODEL_BYTES):
        raise ValueError('Unknown complete-model capacity')
    data = bytearray(data)
    window = bytearray(data[ALLOC_FIRST-catalogue.RAM:ALLOC_END-catalogue.RAM])
    at = STRIDE-ALLOC_FIRST
    if len(window) != ALLOC_END-ALLOC_FIRST or u32(window, at) != 0x24630000|before:
        raise ValueError('Changed native two-preview allocation stride')
    struct.pack_into('>I', window, at, 0x24630000|OLD_BYTES)
    if sha256(window) != ALLOC_SHA:
        raise ValueError('Changed complete native preview allocation loop')
    struct.pack_into('>I', data, STRIDE-catalogue.RAM, 0x24630000|after)
    return bytes(data)


def checked(base, report):
    """Bind a capacity to actual installed code, buffers, and pool reservation."""
    binding = report.get('furniture_capacity')
    furniture = report['furniture']; pool = furniture['bank_pool']
    if not binding:
        if (pool['bank_bytes'], pool['catalogue_preview_bytes'], furniture['native_bank_bytes']) != (OLD_BYTES,)*3:
            raise ValueError('Model capacity has no checked native installation')
        return OLD_BYTES
    files = by_vrom(base)
    helper = furniture['expanded_tables']['expanded_code']
    blob = files[BLOB].extract(base)
    owner = files[room.VROM].extract(base)
    cat = files[catalogue.VROM].extract(base)
    pool_patch = binding['pool_patch']
    if (binding['format'] != 'AFV3-FURNITURE-CAPACITY-1' or
            binding['model_bytes'] != MODEL_BYTES or '-D'+FLAG not in helper['flags'] or
            not 0 < helper['bytes'] <= 0x800 or
            sha256(blob[0x5800:0x5800+helper['bytes']]) != helper['sha256'] or
            any(blob[0x5800+helper['bytes']:0x6000]) or
            pool['data'] != DATA or pool['banks'] != COUNT or
            pool['bank_bytes'] != MODEL_BYTES or pool['guard'] != DATA+COUNT*MODEL_BYTES or
            pool['end'] != pool['guard']+16 or pool['end'] > 0x807DA800 or
            pool['catalogue_preview_bytes'] != MODEL_BYTES or furniture['native_bank_bytes'] != MODEL_BYTES or
            binding['additional_pool_bytes'] != 2*(MODEL_BYTES-OLD_BYTES) or
            pool_patch['address'] != POOL_WORD or pool_patch['after']-pool_patch['before'] != binding['additional_pool_bytes']):
        raise ValueError('Changed complete installed model-capacity contract')
    # Subsequent submenu additions may extend the same word; validate the chain.
    word = pool_patch['after']
    chain = report['catalogue'].get('retained_submenu_pool_patches', [])
    seen = False
    for patch in chain:
        if patch == pool_patch:
            seen = True
        elif seen:
            if patch['address'] != POOL_WORD or patch['before'] != word or patch['after'] <= word:
                raise ValueError('Broken model-capacity submenu allocation chain')
            word = patch['after']
    extra = report['catalogue'].get('category_pool_bytes',0)
    if extra:
        patch = report['catalogue'].get('category_pool_patch',{})
        if (type(extra) is not int or not 0 < extra <= 1024 or extra%64
                or patch != dict(address=POOL_WORD,before=word,after=word+extra)
                or (word^(word+extra))&0xFFFF8000):
            raise ValueError('Broken category submenu allocation binding')
        word += extra
    diary = report.get('equipment_resources', {}).get('diaries')
    if diary:
        hooks = diary['hooks']; bound = hooks['pool_bound']
        patches = {p['address']: p for p in hooks['arena_patches']}
        core = files[CODE_VROM].extract(base)
        initial_extra=hooks.get('catalogue_pool_bytes_at_install',extra)
        delta=extra-initial_extra
        retained=dict(address=POOL_WORD,before=int(patches[POOL_WORD]['before'],16)-initial_extra,
            after=int(patches[POOL_WORD]['after'],16)-initial_extra)
        in_chain=retained in chain
        # Event menus append after the diary/catalogue pool. Validate every
        # actual allocation record rather than treating the earlier bound as final.
        tail_word=int(patches[POOL_WORD]['after'],16)+delta
        equipment=report.get('equipment_resources',{})
        controls=equipment.get('holiday_items',{}).get('controls')
        allocations=(controls['metadata'] if controls else [])+equipment.get('carried_items',{}).get('menu_allocations',[])
        origin=report['catalogue'].get('menu_category_pool_origin',extra)
        if type(origin) is not int or not 0<=origin<=extra or origin%64:
            raise ValueError('Invalid retained event-menu category allowance')
        late_delta=extra-origin
        late_chain=[dict(address=POOL_WORD,before=r['pool_patch']['before']-origin,
            after=r['pool_patch']['after']-origin) for r in allocations if r['additional_pool_bytes']]
        if allocations:
            parent=files[0x7749C0].extract(base)
            descriptors={}
            for row in allocations:
                patch=row['pool_patch'];growth=row['additional_pool_bytes']
                if (patch!=dict(address=POOL_WORD,before=tail_word-late_delta,after=tail_word+growth-late_delta) or
                        growth<0 or growth%64 or (tail_word^(tail_word+growth))&0xFFFF8000 or
                        len(bytes.fromhex(row['before']))!=32 or len(bytes.fromhex(row['after']))!=32 or
                        (row['offset'] in descriptors and descriptors[row['offset']]!=row['before'])):
                    raise ValueError('Broken event-menu submenu allocation chain')
                descriptors[row['offset']]=row['after']
                tail_word=patch['after']+late_delta
            # Held ordering grows within the catalogue's reserved pool rather
            # than adding another arena increment. Keep the six other words.
            for offset,value in list(descriptors.items()):
                words=list(struct.unpack('>8I',bytes.fromhex(value)))
                if words[0]!=catalogue.VROM:continue
                current=report['catalogue'];size=current['bytes']
                if (size!=len(cat) or sha256(cat)!=current['output_sha256'] or size%16 or
                        current['conservative_pool_required']>current['pool_reserved']):
                    raise ValueError('Catalogue exceeds its retained submenu reservation')
                words[1]=words[0]+size;words[3]=words[2]+size
                descriptors[offset]=struct.pack('>8I',*words).hex()
            if any(parent[offset:offset+32].hex()!=value for offset,value in descriptors.items()):
                raise ValueError('Broken event-menu submenu allocation chain')
        later_extra=tail_word-(int(patches[POOL_WORD]['after'],16)+delta)
        actual_bound=bound+delta+later_extra
        editor=report.get('password_editor')
        if editor:
            keyboard=hooks['menus']['keyboard']
            resize=next(r for r in editor['owner_resizes'] if r['vrom']==editor['vrom'])
            growth=resize['bytes']-resize['previous_bytes']
            if (editor['previous_pool_bound']+late_delta!=actual_bound or
                    editor['pool_bound']+late_delta!=actual_bound+editor['additional_menu_pool_bytes'] or
                    growth!=editor['additional_menu_pool_bytes'] or growth<=0 or growth%64 or
                    keyboard['owner_after'][:4]!=[editor['vrom'],editor['vrom']+resize['bytes'],
                        editor['ram'],editor['ram']+resize['bytes']] or
                    parent[keyboard['owner_at']:keyboard['owner_at']+28]!=struct.pack('>7I',*keyboard['owner_after']) or
                    sha256(files[editor['vrom']].extract(base))!=resize['sha256']):
                raise ValueError('Broken password-editor menu reservation')
            actual_bound=editor['pool_bound']+late_delta
            tail_word=0x25CE0000|(actual_bound&65535)
            late_chain.append(dict(address=POOL_WORD,
                before=(0x25CE0000|((editor['previous_pool_bound']+late_delta)&65535))-extra,
                after=tail_word-extra))
        if equipment.get('bank'):
            from v3_bank_resources import menu_allocation
            bank=menu_allocation(base,report);patch=bank['pool_patch']
            if patch['before']+late_delta!=tail_word:
                raise ValueError('Broken retained bank submenu allocation chain')
            actual_bound+=bank['additional_pool_bytes'];tail_word=patch['after']+late_delta
            late_chain.append(dict(address=POOL_WORD,before=patch['before']-origin,after=patch['after']-origin))
        expected_word=int(patches[POOL_WORD]['after' if in_chain else 'before'],16)+delta
        if in_chain:
            observed=chain[chain.index(retained)+1:]
            if observed:
                if observed!=late_chain:raise ValueError('Broken retained later submenu allocation chain')
                expected_word=tail_word
        if (set(patches) != {0x800C4AFC, POOL_WORD} or
                expected_word != word or
                bound-hooks['previous_pool_bound'] != hooks['additional_pool_bytes'] or
                hooks['additional_pool_bytes'] <= 0 or
                int(patches[POOL_WORD]['after'], 16) != 0x25CE0000|(bound & 0xFFFF) or
                int(patches[0x800C4AFC]['after'], 16) != 0x3C0E0000|((bound+0x8000)>>16) or
                u32(core,0x800C4AFC-CODE_RAM)!=0x3C0E0000|((actual_bound+0x8000)>>16) or
                u32(core,POOL_WORD-CODE_RAM)!=0x25CE0000|(actual_bound&0xFFFF)):
            raise ValueError('Broken diary submenu allocation binding')
        word = tail_word
    if u32(files[CODE_VROM].extract(base), POOL_WORD-CODE_RAM) != word:
        raise ValueError('Model previews lack their complete submenu allocation')
    hook = pool['hook']
    expected = bytes.fromhex(hook['after'])
    if (owner[hook['address']-room.RAM:hook['address']-room.RAM+20] != expected or
            u32(expected, 4) != jump(helper['symbols']['af_v3_furniture_secure_banks'], link=True)):
        raise ValueError('Native room bank allocator is not bound to the expanded helper')
    catalogue_stride(cat, MODEL_BYTES, MODEL_BYTES)
    return MODEL_BYTES


def retain_catalogue(prior, data, report):
    binding = prior.get('furniture_capacity')
    if not binding:
        return data, report
    data = catalogue_stride(data, OLD_BYTES, MODEL_BYTES)
    report.update(output_sha256=sha256(data), model_buffer_bytes=MODEL_BYTES)
    return data, report


def install(base, prior, blob, core, output):
    if checked(base, prior) != OLD_BYTES:
        raise ValueError('Complete model capacity is already installed')
    files = by_vrom(base)
    furniture = copy.deepcopy(prior['furniture'])
    expanded = furniture['expanded_tables']; old = expanded['expanded_code']
    defines = tuple(f[2:] for f in old['flags'] if f.startswith('-D'))+(FLAG,)
    helper, compiled = compile_part('furniture_expanded', output/'furniture_capacity',
        defines=defines, primary_source='overlays/v3/furniture.c',
        extra_sources=('overlays/v3/furniture_entry.S',))
    if (sha256(blob[0x5800:0x5800+old['bytes']]) != old['sha256'] or
            any(blob[0x5800+old['bytes']:0x6000]) or len(helper) > 0x800):
        raise ValueError('Changed complete-model reader reservation')
    blob[0x5800:0x6000] = helper+bytes(0x800-len(helper))
    for entry in expanded['public_entries']:
        target = compiled['symbols'][entry['name']]
        after = struct.pack('>2I', jump(target), 0)
        replace_checked(blob, entry['entry']-0x80460000, bytes.fromhex(entry['after']), after)
        entry.update(before=entry['after'], after=after.hex(), target=target)
    pool = furniture['bank_pool']; hook = pool['hook']
    owner = bytearray(files[room.VROM].extract(base))
    previous_owner = sha256(owner)
    before = bytes.fromhex(hook['after'])
    if u32(before, 4) != jump(old['symbols']['af_v3_furniture_secure_banks'], link=True):
        raise ValueError('Changed room bank constructor binding')
    after = before[:4]+struct.pack('>I', jump(compiled['symbols']['af_v3_furniture_secure_banks'], link=True))+before[8:]
    replace_checked(owner, hook['address']-room.RAM, before, after)
    hook.update(before=before.hex(), after=after.hex())
    pool.update(bank_bytes=MODEL_BYTES, guard=DATA+COUNT*MODEL_BYTES,
        end=DATA+COUNT*MODEL_BYTES+16, reservation_bytes=COUNT*MODEL_BYTES+32,
        source_owner_sha256=previous_owner, output_owner_sha256=sha256(owner),
        catalogue_preview_bytes=MODEL_BYTES, native_test='pending changed bank sizing')
    furniture['native_bank_bytes'] = MODEL_BYTES
    expanded.update(expanded_code=compiled, output_sha256=sha256(owner))
    placement = copy.deepcopy(prior['furniture_placement'])
    placement['owner_sha256'] = sha256(owner)
    cat = catalogue_stride(files[catalogue.VROM].extract(base), OLD_BYTES, MODEL_BYTES)
    extra = 2*(MODEL_BYTES-OLD_BYTES)
    before_word = u32(core, POOL_WORD-CODE_RAM)
    after_word = before_word+extra
    if before_word & 0xFFFF0000 != 0x25CE0000 or (before_word^after_word) & 0xFFFF8000:
        raise ValueError('Expanded catalogue model allocation crosses its signed immediate')
    struct.pack_into('>I', core, POOL_WORD-CODE_RAM, after_word)
    patch = dict(address=POOL_WORD, before=before_word, after=after_word)
    cat_report = copy.deepcopy(prior['catalogue'])
    cat_report.update(output_sha256=sha256(cat), model_buffer_bytes=MODEL_BYTES,
        pool_reserved=cat_report['pool_reserved']+extra,
        conservative_pool_required=cat_report['conservative_pool_required']+extra,
        retained_submenu_pool_patches=cat_report.get('retained_submenu_pool_patches', [])+[patch])
    receipt = dict(format='AFV3-FURNITURE-CAPACITY-1', model_bytes=MODEL_BYTES,
        previous_model_bytes=OLD_BYTES, additional_pool_bytes=extra, pool_patch=patch,
        additional_resident_bytes=COUNT*(MODEL_BYTES-OLD_BYTES),
        allocation_loop_sha256=ALLOC_SHA, stride_address=STRIDE,
        saved_format_changed=False, sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return {room.VROM:bytes(owner), catalogue.VROM:cat}, dict(furniture=furniture,
        furniture_placement=placement, catalogue=cat_report, furniture_capacity=receipt)
