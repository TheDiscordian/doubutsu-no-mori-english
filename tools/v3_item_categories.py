"""Shared source category artwork for ground, police, and item handover owners.

Category tables, not item names, select complete material/geometry pairs. This
preparation does not extend native tables or enable any item/profile choice.
"""
from collections import defaultdict
import json
import struct

from aflib import sha256,u32
from apply_translation import write_new
from v3_furniture_pipeline import prepare_material_pair,compile_models
from v3_handheld_items import discover as equipment

# Complete consumer contracts, independent of which parent items use a category.
FUNCTIONS=(
    (0x58E00,168,'63c24d921f9fd6a69471682d6593883ceb329b3f22af5a725b5cd73f441c6d8f'),
    (0x144248,452,'1e2b12284cbc315b888a76faf3997cdc0c0e894a64bccf8dbe6e1916bf7c465a'),
    (0x14B5CC,452,'d5209e0e30f762e95ec2256e662f73c2f5e3f991097f4cd6a08d6e900c065cb3'),
    (0x1530C4,452,'e3924684b79970a2c84397fb8974e24f6c276b8ecb58f5a69981bd469e395e05'),
    (0x15A4DC,452,'151542cbb1a17c962719ac5c591966fec5bd52301b469b7bddf0561004000788'),
    (0x14645C,228,'4e0a7d08fc7f4de374fc2dc36674d34f066089b488c58ef7b044939c7d66c062'),
    (0x14D7E0,228,'60571ad34bfc5d72e8a418f057c6b6d143538fc39b5b32a1191c12a32299c269'),
    (0x1552D8,228,'5855f5955f3c99d469ae98b953ffde3dd9b9489797a8c9ab3d86f726c4b316cb'),
    (0x15C6F0,228,'587d837adf2db46b0afe24d9d9d563253ba8352ebb533678540d3d1c50a3e37d'),
    (0x14E1A4,184,'fe86d4eb018bc6ac91202234cffa90f847ba587e2bc342d11eb54c55d8dc437f'),
    (0xB6E04,332,'45f639b4908e57d3eaba7ee4b4d1da7c9525a8e8e089ef18a3eabc15281b33ef'),
    (0xB7120,604,'8dfd037f492c520fa965dff2d91bf1597240c9e7e747c27bf9743cb1c88966d3'))
PENDING='Native seasonal ground, police, and handover table/array integration is required; no item is enabled.'


def discover(source):
    functions=[]
    for at,n,digest in FUNCTIONS:
        raw,receipt=source.function(at)
        if len(raw)!=n or sha256(raw)!=digest:raise ValueError('Changed complete category consumer')
        functions.append(receipt)
    parent_inventory=equipment(source)
    types=source.raw('item1_2_tableNo');type_at,_=source.symbol('item1_2_tableNo')
    if len(types)!=92 or sha256(types)!='d07c0e001d578fc1bb754c8b24ad7eb782c6bf94ba1ddff2b2c3239f97767975':
        raise ValueError('Changed complete equipment categories')
    main=source.symbol('item1_tableNo$430')[0]
    if (functions[0]['relocations']!={134:(6,1,5,main),142:(4,1,5,main)} or
            source.pointers(main,64).get(main+8)!=type_at):
        raise ValueError('Changed equipment category binding')
    tables=[]
    for role in ('mode_DL_table','vtx_DL_table'):
        spans=sorted(source.names[role])
        if len(spans)!=2:raise ValueError('Incomplete handover/police category owners')
        for at,n in spans:
            pointers=source.pointers(at,n)
            if n!=53*4 or u32(source.data,at) or set(pointers)!=set(range(at+4,at+n,4)):
                raise ValueError('Incomplete category material/geometry table')
            tables.append(dict(role=role,offset=at,bytes=n,pointers=pointers,
                               sha256=sha256(source.data[at:at+n])))
    parents=defaultdict(list)
    for row in parent_inventory['rows']:
        item=int(row['item_id'],16)
        if item>=0x2224:parents[types[item&255]].append(row)
    grounds=sorted(source.names['draw_part_table_a'])
    if len(grounds)!=4:raise ValueError('Incomplete seasonal ground owners')
    rows=[]
    for category,users in sorted(parents.items()):
        roots=[]
        for role in ('mode_DL_table','vtx_DL_table'):
            pointers=[t['pointers'][t['offset']+4*category] for t in tables if t['role']==role]
            if len(set(pointers))!=1:raise ValueError('Ground/handover category artwork disagrees')
            roots.append(pointers[0])
        parts=[source.containing(p,exact=True) for p in roots]
        descriptors=[]
        for variant,(at,n) in enumerate(grounds):
            entries=source.pointers(at,n);matches=[]
            for entry,part in entries.items():
                if (entry-at)%8:raise ValueError('Ground table pointer is not a row start')
                _,_,width=source.containing(part,exact=True)
                if width!=32:raise ValueError('Changed ground drawing descriptor size')
                refs=source.pointers(part,width);dl=refs.get(part)
                if dl is None:continue
                _,_,dl_bytes=source.containing(dl,exact=True)
                if dl_bytes!=8:continue
                if list(source.pointers(dl,8).values())!=roots:continue
                raw=source.data[part:part+32];lists=refs.get(part+8)
                if (set(refs)!={part,part+8} or u32(raw,4)!=1 or any(raw[12:]) or
                        source.containing(lists,exact=True)[2]!=4):
                    raise ValueError('Category drawing has additional lists or shadow dependencies')
                linked=source.pointers(lists,4)
                if set(linked)!={lists}:raise ValueError('Missing category draw-list binding')
                one=linked[lists]
                if source.containing(one,exact=True)[2]!=8 or source.data[one+4:one+8]!=b'\0\1\0\0':
                    raise ValueError('Changed category material/geometry draw indices')
                callback=source.relocations.get(one)
                if callback!=(1,True,1,FUNCTIONS[5+variant][0]) or u32(source.data,one):
                    raise ValueError('Unimplemented category drawing callback')
                flags=source.data[entry+4:entry+8]
                if flags!=b'\0\1\0\0':raise ValueError('Changed category ground flags')
                matches.append(dict(table_offset=at,table_bytes=n,index=(entry-at)//8,
                    category_base=(entry-at)//8-category,part_offset=part,part_hex=raw.hex(),
                    list_table=lists,list_offset=one,list_hex=source.data[one:one+8].hex(),
                    callback=callback[3],display_lists=dl,flags_hex=flags.hex()))
            if len(matches)!=1:raise ValueError('Missing or ambiguous seasonal category descriptor')
            descriptors.extend(matches)
        prepared=prepare_material_pair(source,parts)
        _,body,resources,_,models,_,sections=prepared
        rows.append(dict(source_category=category,parent_item_ids=[r['item_id'] for r in users],
            parents=[dict(id=r['id'],item_id=r['item_id'],name=r['name'],name_sha256=r['name_sha256'],
                          name_source_symbol=r['name_source_symbol'],name_source_index=r['name_source_index']) for r in users],
            models=parts,ground_descriptors=descriptors,object_bytes=(len(body)+sum(n for _,n in sections)+15)&~15,
            vertices=sum(r['bytes']//16 for r in resources if r['kind']=='vertices'),
            triangles=sum(len(r.get('triangles',[])) for m in models.values() for r in m['rows']),
            asset_ready=True,runtime_installed=False,selectable=False,pending_reason=PENDING))
    return dict(format='AFV3-ITEM-CATEGORY-SOURCES-1',source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()),functions=functions,tables=tables,rows=rows,
        category_count=len(rows),parent_record_count=sum(len(r['parents']) for r in rows),
        native_tables_installed=False,logical_imports_added=0)


def convert(source,output,selected=()):
    inventory=discover(source);requested=set(selected)
    available={item for row in inventory['rows'] for item in row['parent_item_ids']}
    if requested-available:raise ValueError('Unknown or original-only item-category selection')
    rows=[r for r in inventory['rows'] if not requested or requested.intersection(r['parent_item_ids'])]
    output.mkdir(parents=True,exist_ok=False);objects=[]
    for row in rows:
        key=f'category-{row["source_category"]:02X}';directory=output/key;directory.mkdir()
        prepared=prepare_material_pair(source,row['models'])
        asset,locations,models,sequence=compile_models(directory,prepared)
        if sequence is not None or len(asset)!=row['object_bytes']:
            raise ValueError('Category compilation disagrees with complete preflight')
        filename=key+'.n64obj.bin';write_new(output/filename,asset)
        objects.append(dict(**row,profile=prepared[0],resources=prepared[2],compiled_models=models,
            model_offsets=locations,object_file=filename,object_sha256=sha256(asset)))
        print(json.dumps(dict(converted=key,parents=len(row['parents']),bytes=len(asset))),flush=True)
    report=dict(format='AFV3-ITEM-CATEGORY-PREPARED-ASSETS-1',version=1,
        source_rel_sha256=inventory['source_rel_sha256'],source_symbols_sha256=inventory['source_symbols_sha256'],
        objects=objects,runtime_installed=False,selectable=False,pending_reason=PENDING)
    write_new(output/'inventory.json',(json.dumps(inventory,indent=2)+'\n').encode())
    write_new(output/'art.json',(json.dumps(report,indent=2)+'\n').encode())
    return report
