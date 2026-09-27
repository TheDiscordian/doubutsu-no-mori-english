"""Shared native field frames, fish capture identities, and release consumers.

Retarget tables to one immutable resident packet. Original actor code/state
sizes and the full DMA directory stay intact; only added models use PI storage.
"""
import copy
import json
import struct
import zlib

from aflib import by_vrom,sha256,u32
from v3_asset_loader import BLOB,ROOT,compile_part
from v3_player_actions import native_references
from v3_creature_field import discover,table,FORMAT
import v3_physical_resources as physical

RAM,SIZE,TABLE,GUARD=0x80647000,0x3000,0x1000,0xAF434652
OWNERS={
    'fish':(0x922A10,0x924590,0x80A5AF70,
        '0733c3014ce49a44a7bad76b55fd99f062205efdbed0374c0ce2d9956f23e221',
        '7395ff05bfe2080ab2a4b717b27069d54eab89bbcdee4945628e7af0b7ce9b54'),
    'insect':(0x8DEEC0,0x8E0870,0x80A10210,
        '82311b0592e89b090682900fec29dfae2ce61d1ffc365c067242dd8aabec3ac9',
        '262936d70b55095dc1f4b6516545d538171ee4bc7ec8208cf5b71cb9926a348e'),
    'release':(0x93A920,0x93BBC0,0x80A7A680,
        'cbfc43755a033170c1d43a01d89d2080717431e38f3055844dac1f39b9708893',
        'ec0ff6743b3f0885f9847b29f0d960c803665a335829b896c861c747e882ae83'),
    'uki':(0x924C40,0x927200,0x80A649A0,
        'ef9d5a100ffada1fc1560c513d3161ce37992c4fb2fa965d7cf7efc6156626f1',
        'e536d25cd434db09f771a6957d269ab8f7f887b9a2f3904e8ea09d93af0e69e7'),
    'shadow':(0x941BF0,0x9427D0,0x80A81950,
        'e35d8de3f7325853cecc697e21d77a0c948989754502534a7e28dd4e1b55876d',
        'f97f182d54c1b2be2d1204c6483707cb582113a7f820b6602d3b12e8e3822ba0'),
}
BANKS={'fish':(0x1871000,61344,'2dd8fbcbf9a0059d39e051e8aa665fb687f9cd279fe91640ab94cebb23d14a99'),
       'insect':(0x113D000,39248,'dddec5c835d2055f9342671fad25c959d80e1f655707c22eb2d4aab9bc6e48e8')}
SOURCES=physical.SOURCES+('tools/v3_creature_field_native.py','tools/v3_creature_field.py',
    'tools/v3_furniture_install.py','tools/v3_room_goods.py','tools/v3_asset_loader.py',
    'overlays/v3/creature_field.c','overlays/v3/creature_field.ld',
    'overlays/v3/creature_field_bridge.S','overlays/v3/surface_bootstrap.c')


def actor_index(row):
    index=int(row['item_id'],16)&255
    if row['category']=='fish' and 32<=index<=40:return index+4
    if row['category']=='insect' and 32<=index<=39:return index
    raise ValueError('Unregistered creature field identity')


def prepared_pool(source,directory):
    """Reuse source-bound frame objects; relocate only graphics address words."""
    from v3_furniture_pipeline import prepare_models
    directory=directory.resolve();report=json.loads((directory/'art.json').read_bytes())
    inventory=discover(source)
    if report['format']!=FORMAT or report['inventory']!=json.loads(json.dumps(inventory)):
        raise ValueError('Changed complete prepared creature category')
    if len(report['objects'])!=17:raise ValueError('Incomplete prepared field objects')
    rows=[];pool=bytearray();ends={k:v[1] for k,v in BANKS.items()}
    for row,expected in zip(report['objects'],inventory['rows'],strict=True):
        if any(row[k]!=json.loads(json.dumps(v)) for k,v in expected.items()):
            raise ValueError('Changed prepared field identity or frame binding')
        data=bytearray((directory/row['object_file']).read_bytes())
        part=prepare_models(source,expected['descriptor'])
        if (len(data)!=row['object_bytes'] or sha256(data)!=row['object_sha256'] or
                row['resources']!=part[2] or data[:len(part[1])]!=part[1] or
                row['frame_offsets']!=[row['model_offsets'][k] for k in row['frame_labels']]):
            raise ValueError('Changed prepared creature frame resources')
        category=row['category'];bank=BANKS[category][0];start=ends[category]
        base=start+8;capacity=0xA00 if category=='fish' else 0xC00
        if len(data)>capacity:raise ValueError('Creature field object exceeds native buffer')
        for model in row['models']:
            at,n=model['native_offset'],model['bytes']
            if (at&7 or n&7 or not 0<=at<at+n<=len(data) or
                    sha256(data[at:at+n])!=model['output_sha256']):
                raise ValueError('Changed complete converted field display list')
            for p in range(at,at+n,8):
                first,target=struct.unpack_from('>2I',data,p);op=first>>24
                if op in (1,0xFD,0xDE):
                    if target>>24!=6 or (target&0xFFFFFF)>=len(data):
                        raise ValueError('Unbounded creature segment-six reference')
                    struct.pack_into('>I',data,p+4,target+base)
        offset=len(pool);pool.extend(data)
        # Each native object has an eight-byte header. No header is transferred;
        # its virtual span exists solely for the native segment-base convention.
        end=base+len(data);ends[category]=end
        rows.append(dict(item_id=row['item_id'],source_item_id=row['source_item_id'],
            category=category,source_index=row['source_index'],actor_index=actor_index(row),
            start=0x06000000+start,end=0x06000000+end,vrom=bank+base,
            pool_offset=offset,bytes=len(data),capacity=capacity,sha256=sha256(data),crc32=zlib.crc32(data),
            frames=[0x06000000+base+i for i in row['frame_offsets']],
            animation=row.get('animation'),release_animation=row.get('release_animation'),
            height_correction=row.get('height_correction'),program_type=row.get('program_type'),
            prepared_sha256=row['object_sha256']))
    return bytes(pool),rows,inventory


def retarget(owner,reloc,ram,targets,patches):
    """Remove only relocations replaced by references to immutable resident data."""
    sections=struct.unpack_from('>4I',reloc)
    groups,absolute,records,locations,_=native_references(owner,reloc,expected_sections=sections)
    image=bytearray(owner);removed=set();changes=[];seen=set()
    for hi,refs in groups.items():
        if not any(t in targets for _,t in refs):continue
        if any(t not in targets for _,t in refs):
            raise ValueError('Resident creature table shares an unrelated high half')
        high={(targets[t]+0x8000)>>16&65535 for _,t in refs}
        if len(high)!=1:raise ValueError('Resident creature tables span conflicting high halves')
        words={hi:(u32(owner,hi)&0xFFFF0000)|high.pop()}
        words.update({lo:(u32(owner,lo)&0xFFFF0000)|(targets[t]&65535) for lo,t in refs})
        for at,word in words.items():
            struct.pack_into('>I',image,at,word);removed.add(locations[at])
            changes.append(dict(address=ram+at,before=u32(owner,at),after=word))
        seen.update(t for _,t in refs)
    if seen!=set(targets) or any(t in targets for t in absolute.values()):
        raise ValueError('Incomplete creature table reader inventory')
    for address,before,after in patches:
        at=address-ram
        if not 0<=at<=len(owner)-4 or u32(image,at)!=before or at in locations:
            raise ValueError('Changed native creature instruction or relocated hook')
        struct.pack_into('>I',image,at,after)
        changes.append(dict(address=address,before=before,after=after))
    keep=[r for r in records if r not in removed]
    fixed=(struct.pack('>5I',*sections,len(keep))+struct.pack('>'+str(len(keep))+'I',*keep)
           +bytes(len(reloc)-24-4*len(keep))+struct.pack('>I',len(reloc)))
    native_references(image,fixed,expected_sections=sections)
    return bytes(image),fixed,dict(patches=changes,removed_relocations=sorted(removed),
        sections=sections,bytes=len(image),sha256=sha256(image),reloc_sha256=sha256(fixed))


def install(base,prior,blob,output,directory):
    from v3_furniture_pipeline import Source
    from v3_console_disk_install import reservations
    from v3_console_image_native import PI_SHA
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    equipment=copy.deepcopy(prior['equipment_resources']);files=by_vrom(base)
    if equipment.get('creature_field') or not equipment.get('creature_items'):
        raise ValueError('Field integration requires installed creature parents, once')
    if any(a<RAM+SIZE and RAM<b for a,b in reservations(prior)) or RAM+SIZE>0x807DA800:
        raise ValueError('Creature field packet overlaps a retained allocation')
    pool,rows,inventory=prepared_pool(source,directory)
    for v,n,digest in BANKS.values():
        data=files[v].extract(base)
        if len(data)!=n or sha256(data)!=digest:raise ValueError('Changed complete native creature bank')
    boot=files[0x1060].extract(base)
    if sha256(boot[0x80026500-0x80025C60:0x800266C4-0x80025C60])!=PI_SHA:
        raise ValueError('Changed synchronous native physical reader')
    records=copy.deepcopy(prior.get('physical_resources',[]))
    record=physical.allocate(base,records,pool,'creature-field-GAFE01-r0');records.append(record)
    code,compiled=compile_part('creature_field',output/'creature_field',
        extra_sources=('overlays/v3/creature_field_bridge.S',),defines=(
            f'AF_FIELD_POOL_ROM=0x{record["physical"]:X}u',f'AF_FIELD_POOL_BYTES={len(pool)}u'))
    if len(code)>TABLE:raise ValueError('Creature field code exceeds reserved bounds')
    packet=bytearray(code.ljust(TABLE,b'\0'))
    packet.extend(struct.pack('>4I',0x41464346,1,len(rows),24))
    for row in rows:packet.extend(struct.pack('>6I',row['vrom'],row['bytes'],row['pool_offset'],
        row['crc32'],row['capacity'],int(row['item_id'],16)))
    bindings=[]
    def put(name,data):
        packet.extend(bytes(-len(packet)%4));at=len(packet);packet.extend(data)
        bindings.append(dict(name=name,ram=RAM+at,bytes=len(data),sha256=sha256(data)))
        return RAM+at
    owners={}
    for name,(v,r,ram,sha,rsha) in OWNERS.items():
        owner,reloc=files[v].extract(base),files[r].extract(base)
        if sha256(owner)!=sha or sha256(reloc)!=rsha:raise ValueError('Changed complete creature owner: '+name)
        owners[name]=(owner,reloc,ram)
    def raw(name,address,n):
        owner,_,ram=owners[name];data=owner[address-ram:address-ram+n]
        if len(data)!=n:raise ValueError('Truncated native creature table')
        return data
    targets={name:{} for name in OWNERS};patches={name:[] for name in OWNERS}
    shared={}
    for name,category,count,starts,ends,models in (
        ('fish','fish',36,0x80A5C568,0x80A5C5F8,0x80A5C82C),
        ('release','fish',36,0x80A7B444,0x80A7B4D4,0x80A7B708),
        ('insect','insect',32,0x80A116B8,0x80A11738,0x80A119B8)):
        added=[r for r in rows if r['category']==category];pointers=[]
        for i in range(count):
            address=u32(raw(name,models,count*4),i*4)
            if not address:pointers.append(0);continue
            data=raw(name,address,12 if category=='fish' else 16)
            if any(not 0x06000000<=u32(data,j)<0x06000000+BANKS[category][1]
                   for j in range(0,len(data),4)):
                raise ValueError('Changed native field-frame pointer bounds')
            key=(category,i)
            if key in shared:
                previous,p=shared[key]
                if data!=previous:raise ValueError('Native fish consumers disagree on original frames')
            else:
                p=put(f'{category}-native-frames-{i}',data);shared[key]=(data,p)
            pointers.append(p)
        for r in added:
            key=(category,r['actor_index']);data=struct.pack('>'+str(len(r['frames']))+'I',*r['frames'])
            if key not in shared:shared[key]=(data,put(f'{category}-import-frames-{r["actor_index"]}',data))
            pointers.append(shared[key][1])
        for label,address,values in (('starts',starts,[r['start'] for r in added]),
                                     ('ends',ends,[r['end'] for r in added])):
            data=raw(name,address,count*4)+struct.pack('>'+str(len(values))+'I',*values)
            targets[name][address]=put(name+'-'+label,data)
        targets[name][models]=put(name+'-models',struct.pack('>'+str(len(pointers))+'I',*pointers))
    fish=[r for r in rows if r['category']=='fish']
    for name,address,field in (('fish',0x80A5C984,'animation'),('release',0x80A7B7C8,'release_animation')):
        targets[name][address]=put(name+'-animation',raw(name,address,36*4)+struct.pack('>9I',*[r[field] for r in fish]))
    targets['fish'][0x80A5CA14]=put('fish-height',raw('fish',0x80A5CA14,36*4)+
        struct.pack('>9f',*[r['height_correction'] for r in fish]))
    donor,params_receipt=table(source,0x3581C,45*8,'gyoei_type')
    params=bytearray(raw('release',0x80A7B324,36*8))
    for r in fish:
        size,search,bite=struct.unpack_from('>HHI',donor,r['source_index']*8)
        if size>6 or bite>4:raise ValueError('Unsupported complete creature release parameter')
        params.extend(struct.pack('>HHI',size,search,(10,11,12,15,45)[bite]))
    targets['release'][0x80A7B324]=put('fish-release-params',params)
    scale,scale_receipt=table(source,0x35C3C,32,'aGYO_shadow_scale')
    for name,address in (('release',0x80A7B858),('shadow',0x80A824A0)):
        if raw(name,address,24)!=scale[:24]:raise ValueError('Changed native/source shadow scale prefix')
        targets[name][address]=put(name+'-shadow-scale',scale[:28])
    for address,axis in ((0x80A7B870,'x'),(0x80A7B888,'z')):
        data=raw('release',address,24)
        targets['release'][address]=put('release-shadow-'+axis,data+data[-4:])
    identities=raw('uki',0x80A66E00,72)
    if identities!=struct.pack('>36H',*range(0x2300,0x2320),0x250E,0x250F,0x2510,0x2316):
        raise ValueError('Changed native capture identities including rubbish and salmon')
    targets['uki'][0x80A66E00]=put('fish-capture-identities',identities+struct.pack('>9H',*[int(r['item_id'],16) for r in fish]))
    patches['uki'].append((0x80A64BB8,0x28610024,0x2861002D))
    symbols=compiled['symbols'];load=0x0C000000|(symbols['af_v3_creature_graphics_load']>>2&0x3FFFFFF)
    for name,address in (('fish',0x80A5B200),('insect',0x80A103D0),('release',0x80A7A7D0)):
        patches[name].append((address,0x0C009B84,load))
    bridge=0x0C000000|(symbols['af_v3_creature_release_index']>>2&0x3FFFFFF)
    patches['release'] += [(0x80A7A934,0x25CFDD00,bridge),(0x80A7A938,0xAE0F0178,0)]
    transform=0x0C000000|(symbols['af_v3_creature_insect_transform']>>2&0x3FFFFFF)
    # Replace the complete native scale/X/Y block, retaining translation and
    # the actual native matrix/display-list consumer immediately after it.
    before=(0xC60C005C,0xC60E0060,0x8E060064,0x0C038107,0x24070001,
            0x87A4003E,0x0C038140,0x24050001,0x87A4003C,0x0C0381A6,0x24050001)
    after=(0x8FA5004C,transform,0x02002025,*([0]*8))
    patches['insect'] += [(0x80A11320+i*4,a,b) for i,(a,b) in enumerate(zip(before,after,strict=True))]
    changes={};receipts=[]
    for name,(owner,reloc,ram) in owners.items():
        data,fixed,receipt=retarget(owner,reloc,ram,targets[name],patches[name])
        v,r,_,sha,rsha=OWNERS[name];changes[v]=data;changes[r]=fixed
        receipts.append(dict(receipt,name=name,vrom=v,reloc=r,ram=ram,
            original_sha256=sha,original_reloc_sha256=rsha,targets=targets[name]))
    if len(packet)>SIZE-16:raise ValueError('Creature field tables exceed resident bounds')
    packet.extend(bytes(SIZE-16-len(packet)));packet.extend(struct.pack('>4I',*([GUARD]*4)))
    blob.extend(bytes(-len(blob)%16));offset=len(blob);blob.extend(packet)
    equipment['creature_field']=dict(format='AFV3-CREATURE-FIELD-NATIVE-1',compiled=compiled,
        packet=dict(ram=RAM,bytes=SIZE,blob_offset=offset,vrom=BLOB+offset,sha256=sha256(packet),crc32=zlib.crc32(packet)),
        rows=rows,tables=bindings,owners=receipts,pool=record,source=inventory['source'],
        source_release_params=params_receipt,source_shadow_scale=scale_receipt,
        shadow_xxl_adaptation='Retain the largest defined correction for the added XXL entry; the donor has no bounded entry.',
        additional_resident_bytes=SIZE,additional_scene_bytes=0,installed=True,
        native_execution_tested=False,selectable=False,
        pending=['field behaviours and spawn readers','collection/profile persistence','pocket icons','ordinary gameplay'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return equipment,changes,dict(physical_resources=records),[(record,pool)]
