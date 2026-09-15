"""Install source-faithful islander arrival rooms without enabling town move-ins."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, DMA_START, apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from gamecube import rarc_files
from gc_names import symbol_data
from gc_text import decoder_tables, decode_gc
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_import_catalog import DECODER_SHA, DONOR_FILES, REL_SHA, SYMBOLS_SHA, read_donor
from v3_registry import villager_actor, villager_house_layers
from v3_villager_houses import HOUSE, STRIDE, item_dependencies, layers, surface_match, DONOR_FG_SHA

ABI=56
BASE=ROOT/'build/v3-aloha-outfits-03'
BASE_SHA='53e94b2cfdc960854bb2520e9bc381886e57fb8051f1bf10e34ef8514b76208c'
FG=0x03F60000
FG_STORAGE=0xE3000
ISLANDERS=tuple(range(216,232))+(233,234)
SOURCES=('tools/v3_islander_houses.py','tools/v3_villager_houses.py','tools/v3_registry.py',
         'overlays/v3/startup.c','overlays/v3/startup.ld')
CONSUMERS={
    'l_island_npc_best_fg_id':'5c7fc72e7f95921a087856d7a2e9079a2c679509c8c94b199abc1f2ec7f36cea',
    'mNpc_IslandNpcRoomDataSet':'1ab24f04a6c5f3455af52774a56d944bc522d3976504778d35145b2626c5088b',
    'mNpc_ChangeIslandRoom':'a79c687f6520fa1c1828d5aa4871e8e25597df1b798694f4426f40c6d992e5b7',
    'npc_grow_list':'1acb00c5ea2dac3e17eac2f20ae7392d15592ca62591bb05b154dc438f35c16e',
}


def source_rooms(native,donor,symbols):
    verified_rom(native)
    if (sha256(donor['rel'])!=REL_SHA or sha256(symbols)!=SYMBOLS_SHA or
            sha256(donor['forest_2nd.arc'])!=DONOR_FILES['forest_2nd.arc'][1]):
        raise ValueError('Islander houses require the pinned donor resources')
    for name,digest in CONSUMERS.items():
        if sha256(symbol_data(donor['rel'],symbols.decode(),name))!=digest:
            raise ValueError('Changed islander house consumer or growth table')
    members=dict(rarc_files(donor['forest_2nd.arc']))
    foreground=members['data/fgnpcdata.bin']
    houses=symbol_data(donor['rel'],symbols.decode(),'npc_house_list')
    names=members['data/npc_name_str_table.bin']
    growth=symbol_data(donor['rel'],symbols.decode(),'npc_grow_list')
    wishlist=symbol_data(donor['rel'],symbols.decode(),'l_island_npc_best_fg_id')
    decoder=ROOT/'local/ac-decomp/tools/msg_tool.py'
    if (len(houses)!=238*8 or len(names)!=236*8 or sha256(foreground)!=DONOR_FG_SHA
            or sha256(houses)!='5cdf9e3185e60ed5a1a776de3ad19c5b9a4723395f6f4e56b20bff0268a5aade'
            or sha256(decoder.read_bytes())!=DECODER_SHA
            or tuple(i for i in range(236) if growth[i]==2)!=ISLANDERS):
        raise ValueError('Changed complete islander identity or house table')
    tables=decoder_tables(decoder)
    source=layers(foreground)
    files=by_vrom(native)
    surfaces={}
    all_items=set()
    for index in ISLANDERS:
        for number in struct.unpack_from('>2H',houses,index*8+4):
            all_items.update(struct.unpack_from('>256H',source[number],2))
    all_items.discard(0)  # Arrival-room zeroes are checked as outside-room padding below.
    dependencies=item_dependencies(native,donor,symbols.decode(),all_items)
    if len(dependencies)!=18 or any(len(r['reviewed_native_items'])!=1 for r in dependencies):
        raise ValueError('An arrival-room furnishing lacks an existing reviewed identity')
    mappings={int(r['donor_item'],16):int(r['reviewed_native_items'][0],16) for r in dependencies}
    mappings.update({0:0xFFFF,0xFFFE:0xFFFE,0xFFFF:0xFFFF,0x4080:0x4080})
    outside={z*16+x for z in range(16) for x in range(16)
             if not (z<8 and x<8 or z==8 and x in (3,4))}
    converted={};records=[]
    for slot,index in enumerate(ISLANDERS):
        raw=houses[index*8:index*8+8]
        kind,palette,wall,floor,main,secondary=struct.unpack('>4B2H',raw)
        best=struct.unpack_from('>2H',wishlist,slot*4)
        if kind>=5 or palette>=5 or (main,secondary)==best or any(n not in source for n in best):
            raise ValueError('Arrival room confused with an island gift-system layout')
        room_surfaces=[]
        for label,number,stride,bank in (('wall',wall,0x1020,0x0182A000),('floor',floor,0x2020,0x017A1000)):
            key=(label,number)
            if key not in surfaces:
                surfaces[key]=surface_match(files,native,members['data/player_room_'+label+'.bin'],number,stride)
            matched=surfaces[key]
            if len(matched['native_matches'])!=1 or matched['native_matches'][0]['vrom']!=f'{bank:08X}':
                raise ValueError('Islander room surface lacks its exact complete native image')
            room_surfaces.append(matched)
        room_layers=[]
        for donor_id,target in zip((main,secondary),villager_house_layers(index)):
            row=source[donor_id]
            cells=struct.unpack_from('>256H',row,2)
            if ({i for i,value in enumerate(cells) if value==0}!=outside or len(outside)!=190
                    or any(0xFEB3<=value<=0xFEC2 for value in cells)):
                raise ValueError('Unreviewed arrival-room padding or dynamic island furniture')
            occupied=[(i,value) for i,value in enumerate(cells) if value not in (0,0xFFFE,0xFFFF,0x4080)]
            if len(occupied)!=(1 if donor_id==main else 0):
                raise ValueError('Changed authentic arrival-room contents')
            data=struct.pack('>H256H',target,*(mappings[v] for v in cells))+row[514:]
            if len(data)!=STRIDE:raise ValueError('Partial islander layer')
            converted[target]=data
            room_layers.append({'donor_layer':donor_id,'target_layer':target,
                'donor_sha256':sha256(row),'converted_sha256':sha256(data),
                'normalised_outside_empty_cells':190,
                'furniture':[{'x':i%16,'z':i//16,'donor_item':f'{v:04X}',
                              'native_item':f'{mappings[v]:04X}'} for i,v in occupied]})
        name=decode_gc(names[index*8:index*8+8],tables).rstrip(' ')
        native_row=struct.pack('>4B2H',kind,palette,
            *(s['native_matches'][0]['index'] for s in room_surfaces),*villager_house_layers(index))
        records.append({'name':name,'donor_index':index,'actor_id':f'{villager_actor(index):04X}',
            'donor_house_hex':raw.hex(),'native_house_hex':native_row.hex(),
            'wall':room_surfaces[0],'floor':room_surfaces[1],'layers':room_layers,
            'donor_wishlist_layers':list(best),'house_mode':'authentic_arrival',
            'installed':True,'move_in_enabled':False,'town_behaviour_adapted':False})
    return records,converted,dependencies


def build(output):
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Islander outputs belong in ignored build/')
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
    previous=json.loads((BASE/'build.json').read_text())
    if sha256(base)!=BASE_SHA or previous['output_sha256']!=BASE_SHA:
        raise ValueError('Changed corrected aloha input cartridge')
    native=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    donor=read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    rooms,converted,dependencies=source_rooms(native,donor,symbols)
    files=by_vrom(base);old_house=previous['villager_houses']
    houses=bytearray(files[HOUSE].extract(base));fg=bytearray(files[FG].extract(base))
    if (sha256(houses)!=old_house['output_house_sha256'] or sha256(fg)!=old_house['output_fg_sha256']
            or len(houses)!=0x770 or len(fg)!=225848 or len(layers(fg))!=436
            or set(converted)&set(layers(fg))):
        raise ValueError('Changed pilot houses or occupied islander layer slots')
    for row in rooms:
        at=(int(row['actor_id'],16)&255)*8
        if houses[at:at+8]!=bytes(8):raise ValueError('Islander house slot is already occupied')
        houses[at:at+8]=bytes.fromhex(row['native_house_hex'])
    for number in sorted(converted):fg.extend(converted[number])
    if (len(fg)!=472*STRIDE or len(fg)%16 or len(layers(fg))!=472
            or not set(range(856,896)).issubset(layers(fg)) or FG+len(fg)>0x03FA0000):
        raise ValueError('Complete foreground exceeds fixed sparse-table or virtual bounds')
    blob=bytearray(files[BLOB].extract(base))
    if len(blob)>FG_STORAGE or any(blob[0x1E60:0x1E74]):
        raise ValueError('Changed final storage or enabled move-ins')
    blob.extend(bytes(FG_STORAGE-len(blob))+fg)
    struct.pack_into('>I',blob,4,ABI)
    code=bytearray(files[CODE_VROM].extract(base));patches=[]
    end=FG+len(fg)
    for address,before,after in ((0x80086100,0x3C0B03F9,0x3C0B0000|((end+0x8000)>>16)),
                                  (0x80086104,0x256B7238,0x256B0000|(end&65535))):
        if struct.unpack_from('>I',code,address-CODE_RAM)[0]!=before:
            raise ValueError('Changed complete foreground-loader end pointer')
        struct.pack_into('>I',code,address-CODE_RAM,after)
        patches.append({'address':f'{address:08X}','before':f'{before:08X}','after':f'{after:08X}'})
    output.mkdir(parents=True,exist_ok=False)
    startup,compiled=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1','AF_V3_ACCESSORY_BYTES=61440'))
    module=bytearray(files[MODULE].extract(base));prior=previous['startup']
    if (sha256(module[STARTUP:STARTUP+prior['bytes']])!=prior['sha256']
            or any(module[STARTUP+prior['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed or overflowing startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    image=bytearray(base);storage=files[BLOB]
    physical_end=max(e.pend or e.pstart+e.size for e in files.values() if e.pstart!=0xFFFFFFFF)
    if (storage.pend or physical_end!=storage.pstart+storage.size or len(blob)>0x200000
            or storage.pstart+len(blob)>len(base) or any(base[physical_end:storage.pstart+len(blob)])
            or any(e.vstart<BLOB+len(blob) and BLOB<e.vend for v,e in files.items() if v!=BLOB)):
        raise ValueError('Read-only foreground storage cannot extend the final allocation safely')
    for vrom,data in ((HOUSE,houses),(CODE_VROM,code),(MODULE,module)):
        entry=files[vrom]
        if entry.pend or entry.size!=len(data):raise ValueError('Changed fixed resource extent')
        image[entry.pstart:entry.pstart+entry.size]=data
    image[storage.pstart:storage.pstart+len(blob)]=blob
    for entry,start,stop,physical in ((storage,BLOB,BLOB+len(blob),storage.pstart),
            (files[FG],FG,FG+len(fg),storage.pstart+FG_STORAGE)):
        struct.pack_into('>4I',image,DMA_START+entry.index*16,start,stop,physical,0)
    fix_checksum(image);image=bytes(image)
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image:raise ValueError('Islander-house patch reconstruction failed')
    house_report=copy.deepcopy(old_house)
    house_report['houses']+=rooms
    house_report['appended_layers'] += [{'id':number,'sha256':sha256(data),'bytes':len(data)}
                                       for number,data in sorted(converted.items())]
    house_report.update({'installed_villagers':sorted(old_house['installed_villagers']+[r['actor_id'] for r in rooms]),
        'foreground_bytes':len(fg),'foreground_records':472,'foreground_extra_allocation_bytes':len(fg)-223776,
        'output_house_sha256':sha256(houses),'output_fg_sha256':sha256(fg)})
    text_report=copy.deepcopy(previous['villager_text'])
    text_report['remaining']=['explicit islander town behaviour','ordinary move-in and persistence']
    report={**previous,'build':'v3-islander-arrival-houses','runtime_abi':ABI,'input_build_sha256':BASE_SHA,
        'output_sha256':sha256(image),'patch_sha256':sha256(patch),'startup':compiled,
        'blob_sha256':sha256(blob),'blob_file_bytes':len(blob),'storage':{**previous['storage'],'bytes':len(blob)},
        'villager_houses':house_report,'villager_text':text_report,'islander_houses':{'rooms':rooms,'dependencies':dependencies,
            'source_consumers':CONSUMERS,'loader_patches':patches,
            'foreground_storage_offset':FG_STORAGE,'foreground_physical':storage.pstart+FG_STORAGE,
            'shared_read_only_physical_storage':True,'resident_growth_bytes':0,
            'foreground_allocation_growth_bytes':len(fg)-files[FG].size,'sparse_pointer_growth_bytes':0,
            'move_in_enabled':[],'saved_formats_and_profile_changed':False,'native_test':'pending'},
        'native_test':'pending for complete arrival-room initialization and foreground loading',
        'sources':{**previous['sources'],**{p:sha256((ROOT/p).read_bytes()) for p in SOURCES}}}
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=build(args.output)
    print(json.dumps({k:r[k] for k in ('runtime_abi','output_sha256','patch_sha256')}))
