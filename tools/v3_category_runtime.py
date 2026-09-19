"""Shared category artwork/tables and bounded police/handover consumers.

The seasonal ground owners remain a separate required integration step. This
adapter never enables a parent item or changes a saved/profile identity.
"""
import copy
import json
import struct
import zlib

from aflib import by_vrom,sha256,u32
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_equipment_runtime import RAM,GUARD
from v3_furniture_pipeline import Source,prepare_material_pair
from v3_import_storage import END,jump
from v3_item_categories import discover
from v3_player_actions import native_references

CODE,MAP,TABLE,ART,SIZE=0x7000,0x7200,0x7300,0x7600,0xA000
NATIVE_COUNT=27
SOURCES=('tools/v3_category_runtime.py','tools/v3_item_categories.py',
    'tools/v3_furniture_pipeline.py','tools/v3_furniture_art.py','tools/v3_asset_loader.py',
    'overlays/v3/item_categories.c','overlays/v3/item_categories.ld')
OWNERS=(
    dict(role='police',vrom=0x7E4DF0,reloc=0x7E55B0,ram=0x808EB720,
         sections=(1616,320,48,32),tables=(0x808EBD94,0x808EBE00),call=0x1C8,
         sha256='b50255b015394f6bf7a1ebbc0b9b890b9fa82b0aeef528146e16c21ee3cee3f8',
         reloc_sha256='35be8a875a6b6337a09b41bd09803388079ef2f7c8d5a4322c28c5db088a2f9a'),
    dict(role='handover',vrom=0x858A50,reloc=0x85A180,ram=0x80963DC0,
         sections=(3312,2576,48,48),tables=(0x80964E28,0x80964E94),call=0x7B4,
         sha256='e43ac795201b03dc39c8249268d1656df378f2f4965d66cec3cdba35736f1114',
         reloc_sha256='b0efd203da52f4f6896eeb228438942130507f24df55cf2cab5be6deeac19f8b'))


def prepared(source,path):
    """Reuse complete prepared categories, retaining full source dependencies."""
    path=path.resolve();raw=(path/'art.json').read_bytes();art=json.loads(raw)
    expected=discover(source);by_type={r['source_category']:r for r in expected['rows']}
    if (art['format']!='AFV3-ITEM-CATEGORY-PREPARED-ASSETS-1' or art['version']!=1
            or art['source_rel_sha256']!=sha256(source.rel)
            or art['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed prepared category format/source')
    assets={};rows=[]
    for row in art['objects']:
        category=row['source_category'];reference=by_type.get(category)
        if reference is None or category in assets:raise ValueError('Unknown or duplicate prepared category')
        if any(row[k]!=json.loads(json.dumps(v)) for k,v in reference.items()):
            raise ValueError('Changed complete category source relationships')
        profile,body,resources,_,models,commands,sections=prepare_material_pair(source,reference['models'])
        file=(path/row['object_file']).resolve()
        if file.parent!=path:raise ValueError('Category object escapes prepared directory')
        data=file.read_bytes();cursor=(len(body)+7)&~7
        if (row['profile']!=json.loads(json.dumps(profile)) or row['resources']!=resources
                or len(data)!=row['object_bytes'] or sha256(data)!=row['object_sha256']
                or data[:len(body)]!=body or len(row['compiled_models'])!=2
                or (path/f'category-{category:02X}'/'commands.c').read_text()!=commands):
            raise ValueError('Changed complete prepared category artwork')
        for model,(label,n) in zip(row['compiled_models'],sections):
            if (model['layer']!=label or model['native_offset']!=cursor or model['bytes']!=n
                    or row['model_offsets'].get(label)!=cursor
                    or model['source_sha256']!=models[label]['source_sha256']
                    or model['output_sha256']!=sha256(data[cursor:cursor+n])):
                raise ValueError('Changed split category display lists')
            cursor+=n
        if set(row['model_offsets'])!={'material','geometry'} or any(data[cursor:]):
            raise ValueError('Unexpected category data after complete display lists')
        assets[category]=data;rows.append(copy.deepcopy(row))
    if set(assets)!=set(by_type):raise ValueError('Incomplete prepared shared category set')
    return assets,sorted(rows,key=lambda r:r['source_category']),dict(
        art_directory=str(path.relative_to(ROOT)),art_report_sha256=sha256(raw),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()))


def rebase_art(data,row,ram):
    """Use segment-zero physical resources, independent of caller segment six."""
    if ram%16 or not 0x80400000<=ram<ram+len(data)<=0x80800000:
        raise ValueError('Category artwork outside reserved Expansion Pak memory')
    result=bytearray(data);resources={r['native_offset']:r for r in row['resources']};fixes=[]
    for model in row['compiled_models']:
        start=model['native_offset'];end=start+model['bytes']
        for at in range(start,end,8):
            op=data[at]
            if op not in (0x01,0xFD):continue
            pointer=u32(data,at+4);resource=resources.get(pointer&0xFFFFFF)
            # LoadBlock uses a 16-bit transfer for CI4 too. Texture format,
            # not the transfer width, distinguishes the RGBA palette load.
            kind='vertices' if op==1 else 'palette' if (u32(data,at)>>21)&7==0 else 'texture'
            if pointer>>24!=6 or resource is None or resource['kind']!=kind:
                raise ValueError('Unbound category vertex/texture/palette pointer')
            target=(ram&0x1FFFFFFF)+resource['native_offset']
            struct.pack_into('>I',result,at+4,target)
            fixes.append(dict(offset=at+4,before=pointer,after=target,resource_kind=kind))
    if {f['before']&0xFFFFFF for f in fixes}!=set(resources):
        raise ValueError('Category rebasing misses a complete resource')
    return bytes(result),fixes


def police_capacity(count):
    """Keep the native unrolled copy, extending its stack and actor together."""
    if count<=NATIVE_COUNT or count>255 or (count-3)%4:
        raise ValueError('Police capacity must preserve the complete unrolled copy')
    delta=2*(count-NATIVE_COUNT)
    # count == 3 mod 4 keeps actor matrices four-byte aligned and SP eight-byte aligned.
    frame=96+delta
    changes=[(0x808EB73C,0x2401001B,0x2DC10000|(count-1)), # unsigned type < count-1
             (0x808EB744,0x11C1003F,0x1020003F),
             (0x808EB954,0x27BDFFA0,0x27BD0000|((-frame)&65535)),
             (0x808EB970,0x27A4005C,0x27A40000|(0x5C+delta)),
             (0x808EB9D0,0x2404001B,0x24040000|count),
             (0x808EBA20,0x27BD0060,0x27BD0000|frame),
             (0x808EBCC8,0x2415001B,0x24150000|count),
             (0x808EBD7C,0x00004634,0x4634+delta)]
    # Incoming argument slots move with the frame; locals/RA stay below 0x28.
    for at,word in ((0x808EB95C,0xAFA40060),(0x808EB960,0xAFA50064),
                    (0x808EB964,0xAFA60068),(0x808EB968,0x8FA30064),
                    (0x808EB9A4,0x8FA40064),(0x808EB9A8,0x8FA50068),
                    (0x808EB9B4,0x8FA20064),(0x808EBA0C,0x8FAB0060)):
        changes.append((at,word,word+delta))
    # All draw_pos and trailing item_tbl consumers, including the profile size.
    for at,word in ((0x808EB888,0x248E007C),(0x808EB974,0x24630038),
                    (0x808EBA44,0x8E5045F0),(0x808EBA4C,0x265145F4),
                    (0x808EBAD4,0x248445F0),(0x808EBB9C,0x26520038)):
        changes.append((at,word,word+delta))
    return changes,dict(native_count=NATIVE_COUNT,count=count,start_indices=count-1,
        actor_bytes=0x4634+delta,actor_growth_bytes=delta,stack_bytes=frame,
        start_array_offset=4,draw_positions_offset=0x38+delta,
        draw_position_count=257,draw_position_bytes=68,item_table_offset=0x45F0+delta)


def patch_owner(owner,rel,spec,table_addresses,entry,count):
    if sha256(owner)!=spec['sha256'] or sha256(rel)!=spec['reloc_sha256']:
        raise ValueError('Changed complete category owner/relocations: '+spec['role'])
    groups,absolute,records,locations,slots=native_references(owner,rel,expected_sections=spec['sections'])
    patched=bytearray(owner);patches=[];removed=set();tables=[]
    def patch(at,before,after):
        if u32(patched,at)!=before:raise ValueError('Changed category patch instruction')
        patches.append(dict(offset=at,before=before,after=after))
        struct.pack_into('>I',patched,at,after)
    for role,target,address in zip(('material','geometry'),spec['tables'],table_addresses):
        pairs=[]
        for hi,lows in groups.items():
            if any(target<=p<target+4*NATIVE_COUNT for _,p in lows):
                if any(p!=target for _,p in lows):raise ValueError('Shared/interior category table reference')
                pairs.extend((hi,lo) for lo,_ in lows)
        if len(pairs)!=1 or any(target<=p<target+4*NATIVE_COUNT for p in absolute.values()):
            raise ValueError('Incomplete category table reference coverage')
        for hi,lo in pairs:
            for at,part in ((hi,(address+0x8000)>>16),(lo,address&65535)):
                if at in removed:raise ValueError('Overlapping category table references')
                patch(at,u32(owner,at),u32(owner,at)&0xFFFF0000|part);removed.add(at)
        tables.append(dict(role=role,native=target,ram=address,
            references=[(spec['ram']+a,spec['ram']+b) for a,b in pairs]))
    if spec['call'] in slots:raise ValueError('Unexpected category call relocation')
    patch(spec['call'],jump(0x800A5630,link=True),jump(entry,link=True))
    capacity=None
    if spec['role']=='police':
        changes,capacity=police_capacity(count)
        for at,before,after in changes:
            if at-spec['ram'] in slots:raise ValueError('Relocated police capacity instruction')
            patch(at-spec['ram'],before,after)
    kept=[r for r in records if r not in {locations[p] for p in removed}]
    relocation=bytearray(rel);struct.pack_into('>I',relocation,16,len(kept))
    relocation[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(rel)-24-4*len(kept))
    return bytes(patched),bytes(relocation),dict(spec,tables=tables,patches=patches,
        output_sha256=sha256(patched),output_reloc_sha256=sha256(relocation),
        removed_relocations=[locations[p] for p in sorted(removed)],capacity=capacity)


def install(base,prior,blob,core,original,output,art_path):
    old=prior['equipment_resources'];position=old['blob_offset'];module=bytearray(blob[position:position+old['bytes']])
    if (old.get('item_categories') or not old.get('inventory_preview') or old['bytes']!=CODE
            or sha256(module)!=old['sha256'] or RAM+SIZE>prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed category module dependencies/reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    assets,rows,receipt=prepared(source,art_path)
    # Fixed source numbering, not selection order. Pad capacity for native copy unrolling.
    count=max(NATIVE_COUNT+r['source_category']+1 for r in rows)
    count+=(-count+3)%4
    if TABLE+count*8>ART:raise ValueError('Category tables exceed reservation')
    code,compiled=compile_part('item_categories',output/'item_categories',defines=(
        f'AF_V3_CATEGORY_COUNT={count}',
        f'AF_V3_HELD_SELECTED=0x{old["player_actions"]["code"]["symbols"]["af_v3_player_selected_equipment"]:08X}u'))
    if len(code)>MAP-CODE:raise ValueError('Category code overlaps data')
    module.extend(bytes(SIZE-len(module)));module[CODE:CODE+len(code)]=code
    mapping=bytearray(struct.pack('>4I',0x41464354,1,count,53)+bytes(53))
    cursor=ART
    for row in rows:
        category=row['source_category'];cursor=(cursor+15)&~15
        data,fixes=rebase_art(assets[category],row,RAM+cursor)
        if cursor+len(data)>SIZE-16:raise ValueError('Category art overlaps end guard')
        module[cursor:cursor+len(data)]=data;mapping[16+category]=NATIVE_COUNT+category
        row.update(native_category=NATIVE_COUNT+category,ram=RAM+cursor,offset=cursor,
            installed_sha256=sha256(data),pointer_relocations=fixes,
            handover_police_installed=True,ground_installed=False,runtime_installed=False)
        cursor+=len(data)
    files=by_vrom(base);tables=[]
    for index,role in enumerate(('material','geometry')):
        originals=[files[s['vrom']].extract(base)[s['tables'][index]-s['ram']:
                    s['tables'][index]-s['ram']+4*NATIVE_COUNT] for s in OWNERS]
        if originals[0]!=originals[1] or len(originals[0])!=4*NATIVE_COUNT:
            raise ValueError('Native police/handover categories disagree')
        values=list(struct.unpack('>27I',originals[0]))+[0]*(count-NATIVE_COUNT)
        for row in rows:values[row['native_category']]=(row['ram']&0x1FFFFFFF)+row['model_offsets'][role]
        raw=struct.pack('>'+str(count)+'I',*values);at=TABLE+len(tables)*count*4
        module[at:at+len(raw)]=raw
        tables.append(dict(role=role,ram=RAM+at,offset=at,bytes=len(raw),sha256=sha256(raw)))
    module[MAP:MAP+len(mapping)]=mapping
    struct.pack_into('>4I',module,SIZE-16,*([GUARD]*4))
    changes={};owners=[]
    for spec in OWNERS:
        owner,rel,record=patch_owner(files[spec['vrom']].extract(base),files[spec['reloc']].extract(base),
            spec,[t['ram'] for t in tables],compiled['symbols']['af_v3_equipment_category'],count)
        changes[spec['vrom']]=owner;changes[spec['reloc']]=rel;owners.append(record)
    blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(module)
    if BLOB+len(blob)>END:raise ValueError('Category module exceeds import storage')
    receipt.update(format='AFV3-ITEM-CATEGORY-RUNTIME-1',code=compiled,code_offset=CODE,
        map_offset=MAP,map_bytes=len(mapping),map_sha256=sha256(mapping),count=count,
        tables=tables,objects=rows,owners=owners,additional_resident_bytes=SIZE-old['bytes'],
        ground_installed=False,selectable=False,profile_bits_enabled=0,
        saved_format_changed=False,ordinary_handover_police_tested=False)
    report=copy.deepcopy(old);report['item_categories']=receipt
    report.update(bytes=SIZE,vrom=BLOB+position,blob_offset=position,sha256=sha256(module),
        crc32=zlib.crc32(module),additional_resident_bytes=SIZE-old['bytes'])
    return report,changes
