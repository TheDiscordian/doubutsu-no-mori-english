"""Shared seasonal ground integration for installed item-category resources."""
import copy
import struct
import zlib

from aflib import CODE_RAM, by_vrom, sha256, u32
from v3_asset_loader import ROOT, BLOB, compile_part
from v3_equipment_runtime import RAM, GUARD
from v3_furniture_room import query, branch_target
from v3_import_storage import END, jump
from v3_player_actions import native_references

CODE, CONFIG, SIZE = 0xA000, 0xAC00, 0xB000
SOURCES = ('tools/v3_ground_categories.py', 'tools/v3_asset_loader.py',
           'overlays/v3/ground_categories.c', 'overlays/v3/ground_categories.ld',
           'overlays/v3/item_categories.c', 'overlays/v3/item_categories.ld')
# These are renderer contracts, not item-specific definitions.
OWNERS = (
    dict(role='cherry', vrom=0x7E5880, reloc=0x7EF1F0, ram=0x808EC1D0,
         sections=(31472,7568,240,1168), slot=0x80101680, table=0x808F5524,
         actor=0x12EA8, constructor=0x808F3900, common=0x174, count=64,
         refs=((0x46BC,0x46D8),(0x4CA0,0x4CBC),(0x7890,0x7894),(0x7AC4,0x7AC8)),
         sha256='a929190ff42834e01990383f5e1fc1337a9ea13dd9f7d7618e2dcd6843e87a60',
         reloc_sha256='4f5f75a8d4dedb2fc7411ebe2a40a329dd0b5424145f4d5844e2eb13e84dfcf9'),
    dict(role='winter', vrom=0x7F0350, reloc=0x7F9D60, ram=0x808F7130,
         sections=(31664,7504,272,1168), slot=0x801016A0, table=0x80900508,
         actor=0x12EA0, constructor=0x808FE880, common=0x174, count=63,
         refs=((0x46BC,0x46D8),(0x4CA0,0x4CBC),(0x7944,0x7950),(0x7B80,0x7B84)),
         sha256='06eeb848760b5c4a1a3a358dee7bb60a2ff9563e0b8b14026a0bde91d9cbde12',
         reloc_sha256='29e7d02da7cb2d906dd8e2448d0b3b9d46ec193a754fc258e921d9470fb5f7fb'),
    dict(role='xmas', vrom=0x7FAEB0, reloc=0x804CC0, ram=0x80902120,
         sections=(32656,7568,240,1168), slot=0x801016C0, table=0x8090B914,
         actor=0x13EB8, constructor=0x80909850, common=0x1384, count=64,
         refs=((0x46BC,0x46D8),(0x4CA0,0x4CBC),(0x7A30,0x7A3C),(0x7D34,0x7D38)),
         sha256='cc824887dc3f9b6142ea186a8c1227620e07942ef5a4a083d7507cf4d41dafac',
         reloc_sha256='ea5c0b6eff8535039cda1651938d0b6be4cf2759b2d732f08bbb9f011b6ad048'),
    dict(role='ordinary', vrom=0x805E30, reloc=0x80F760, ram=0x8090D530,
         sections=(31440,7536,240,1168), slot=0x80100CC0, table=0x8091684C,
         actor=0x12EA8, constructor=0x80914C60, common=0x174, count=64,
         refs=((0x46BC,0x46D8),(0x4CA0,0x4CBC),(0x7880,0x788C),(0x7AA0,0x7AA4)),
         sha256='adc9de9ce7c664265fb80c8f3d379e09a0aa706894d27134d09a05e23fd0e522',
         reloc_sha256='2a64fe752b8cecc4f4d6df214aafe34e1d5d36500dc3a65e53e8f6040141bb76'))
WINDOWS = ((0x2358,(0x308CF000,0x000C6B03),12,13),
           (0x24EC,(0x00095303,0x15410004),None,10),
           (0x47C0,(0x3082F000,0x00021303),2,2))


def return_to(spec, offset):
    if not 0<=offset<0x8000: raise ValueError('Ground continuation exceeds signed offset')
    slot=spec['slot']
    return ['addiu $sp,$sp,-16', 'sd $ra,8($sp)', f'lui $ra,0x{(slot+0x8000)>>16:04x}',
            f'lw $ra,{struct.unpack(">h",struct.pack(">H",slot&65535))[0]}($ra)',
            f'addiu $ra,$ra,{offset}', 'addiu $sp,$sp,16', 'jr $ra','ld $ra,-8($sp)']


def assembly(count):
    lines=['/* Generated shared seasonal type windows. */','.set noreorder','.set noat','.set gp=64','.text']
    for spec in OWNERS:
        for at,words,temporary,destination in WINDOWS:
            name=f'af_v3_ground_{spec["role"]}_{at:04x}'
            lines += [f'.globl {name}',f'{name}:']
            if temporary is not None: lines += [f'.word 0x{words[0]:08x}']
            lines += query(4,destination,2)
            if temporary is None:
                lines += [f'bne $10,$at,{name}_taken','move $v0,$zero']
                lines += return_to(spec,at+12)+[f'{name}_taken:']+return_to(spec,at+24)
            else: lines += return_to(spec,at+8)
        if spec['role']=='xmas':
            lines += ['.globl af_v3_ground_xmas_indices','af_v3_ground_xmas_indices:',
                      f'lui $ra,{spec["actor"]>>16}',f'ori $ra,$ra,{spec["actor"]&65535}',
                      'addu $ra,$ra,$s0',f'addiu $s1,$zero,{spec["count"]+count-27}']
            lines += return_to(spec,0x80909998-spec['ram'])
    return '\n'.join(lines)+'\n'


def layout(owner, rel, spec, count, objects):
    if sha256(owner)!=spec['sha256'] or sha256(rel)!=spec['reloc_sha256']:
        raise ValueError('Changed complete seasonal renderer: '+spec['role'])
    groups,absolute,records,locations,slots=native_references(owner,rel,expected_sections=spec['sections'])
    target=spec['table']; pairs=[]
    for hi,lows in groups.items():
        if any(target<=p<target+spec['count']*8 for _,p in lows):
            if any(p!=target for _,p in lows): raise ValueError('Shared/interior ground table reference')
            pairs.extend((hi,lo) for lo,_ in lows)
    if sorted(pairs)!=sorted(spec['refs']) or any(target<=p<target+spec['count']*8 for p in absolute.values()):
        raise ValueError('Changed complete ground table-reference inventory')
    type_base=spec['count']-27
    for at,word in ((0x4908,0x24580000|type_base),(0x4940,0x244B0000|type_base)):
        if u32(owner,at)!=word: raise ValueError('Changed seasonal category base')
    # Resolve the complete native ordinary-item descriptor and its relocated callback.
    part_at=target-spec['ram']+8*(type_base+1)
    pointer=u32(owner,part_at)
    if part_at not in absolute or u32(owner,part_at+4)!=0x00010000:
        raise ValueError('Changed native ground reference row')
    part=pointer-spec['ram'];dl,n,lists,*shadow=struct.unpack_from('>8I',owner,part)
    if n!=1 or any(shadow) or any(x not in absolute for x in (part,part+8,lists-spec['ram'])):
        raise ValueError('Unsupported native reference descriptor')
    draw_list=u32(owner,lists-spec['ram'])-spec['ram']
    loop=u32(owner,draw_list)-spec['ram']
    if (draw_list not in absolute or u32(owner,draw_list+4)!=0x00010000
            or not 0<=loop<spec['sections'][0] or not spec['ram']<=dl<spec['ram']+len(owner)):
        raise ValueError('Changed native ground callback/list')
    profile=spec['sections'][0]
    if u32(owner,profile+12)!=spec['actor'] or absolute.get(profile+16)!=spec['constructor']:
        raise ValueError('Changed native actor constructor/allocation')
    total=spec['count']+count-27;extension=(sum(spec['sections'])+15)&~15
    empty=extension+total*8;parts=empty+32;resident=(parts+52*objects+15)&~15
    if total>255 or (total-spec['count'])%4 or resident>=0x10000:
        raise ValueError('Ground capacity exceeds checked index/copy/owner bounds')
    cfg=(spec['slot'],spec['constructor']-spec['ram'],target-spec['ram'],spec['count'],total,
         extension,parts,loop,type_base)
    return cfg,dict(count=total,type_base=type_base,table_offset=extension,parts_offset=parts,empty_offset=empty,
        callback_offset=loop,resident_bytes=resident,bss_bytes=resident-len(owner),
        actor_bytes=spec['actor']+total*8,index_offset=spec['actor'],index_stride=total*2,
        actor_growth_bytes=total*8,stack_bytes=176+2*(count-27)),(groups,absolute,records,locations,slots)


def patch_owner(owner,rel,spec,capacity,refs,symbols):
    groups,absolute,records,locations,slots=refs
    data=bytearray(owner);patches=[]
    def patch(at,before,after):
        if u32(data,at)!=before: raise ValueError(f'Changed ground instruction {spec["role"]}+{at:04X}')
        struct.pack_into('>I',data,at,after);patches.append(dict(offset=at,before=before,after=after))
    total=capacity['count'];delta=2*(total-spec['count']);frame=176+delta
    table=spec['ram']+capacity['table_offset']
    for hi,lo in spec['refs']:
        patch(hi,u32(owner,hi),u32(owner,hi)&0xFFFF0000|((table+0x8000)>>16))
        patch(lo,u32(owner,lo),u32(owner,lo)&0xFFFF0000|(table&65535))
    # Each seasonal local array and every incoming SP-relative argument grow together.
    for at,word in ((0x5E1C,0xAFA700BC),(0x5E5C,0x8FAE00BC),(0x5E60,0x8FAF00C0),
                    (0x5E68,0xAFA500B4),(0x5E78,0x8FA500B4)):
        patch(at,word,word+delta)
    winter=spec['role']=='winter'
    for at,before,after in ((0x5E14,0x27BDFF50,0x27BD0000|((-frame)&65535)),
            (0x5E2C,0x29010000|spec['count'],0x29010000|total),
            (0x5E98 if winter else 0x5E84,0x24040000|spec['count'],0x24040000|total),
            (0x5EE8 if winter else 0x5EC8,0x27BD00B0,0x27BD0000|frame)):
        patch(at,before,after)
    profile=spec['sections'][0]
    patch(profile+12,spec['actor'],capacity['actor_bytes'])
    patch(profile+16,spec['constructor'],symbols['af_v3_ground_'+spec['role']])
    # Append new arrays: no common state, matrix node, or Christmas light record moves.
    if spec['role']=='ordinary':
        changes=[(0x80914E38,0x34212CA8,0x34210000|(spec['actor']&65535)),
                 (0x80914E40,0x24040040,0x24040000|total)]
        changes += [(at,word,(word&0xFFFF0000)|capacity['index_stride']) for at,word in
                    ((0x80914E4C,0x24A30080),(0x80914E54,0x24630080),(0x80914E64,0x24630080))]
    elif spec['role'] in ('cherry','winter'):
        starts=(0x808F3AE0,0x808F3AF4,0x808F3B0C,0x808F3B18) if not winter else (0x808FEAFC,0x808FEB10,0x808FEB24,0x808FEB30)
        changes=[(at,0x34210000|(0x2CA8+i*spec['count']*2),
                  0x34210000|((spec['actor']+i*capacity['index_stride'])&65535)) for i,at in enumerate(starts)]
        changes.append((0x808FEAD0 if winter else 0x808F3AFC,
                        0x24050000|spec['count'],0x24050000|total))
    else:
        changes=[(0x80909990,0x261F0578,jump(symbols['af_v3_ground_xmas_indices'])),
                 (0x80909994,0x24110040,0),
                 (0x80909B24,0x27FF0484,0x27FF0000|capacity['index_stride'])]
    for at,before,after in changes: patch(at-spec['ram'],before,after)
    interiors={at+4 for at,*_ in WINDOWS}
    if spec['role']=='xmas': interiors.add(0x80909994-spec['ram'])
    for at in range(0,spec['sections'][0],4):
        word=u32(owner,at);op=word>>26;target=None
        if op in (1,4,5,6,7,20,21,22,23) or (op==17 and word>>21&31==8):
            target=branch_target(spec['ram']+at,word)-spec['ram']
        elif op in (2,3): target=(0x80000000|(word&0x3FFFFFF)<<2)-spec['ram']
        if target in interiors: raise ValueError('Incoming branch enters seasonal detour interior')
    if any(p-spec['ram'] in interiors for p in absolute.values()):
        raise ValueError('Relocated pointer enters seasonal detour interior')
    ordinary_words=(0x0811AB80,0x0811AB93,0x0811ABAF)
    for i,(at,words,_,_) in enumerate(WINDOWS):
        if slots&{at,at+4}: raise ValueError('Relocated ground type detour')
        before=(ordinary_words[i],0) if spec['role']=='ordinary' else words
        patch(at,before[0],jump(symbols[f'af_v3_ground_{spec["role"]}_{at:04x}']))
        patch(at+4,before[1],0)
    if u32(owner,0x24F4)!=0x00001025: raise ValueError('Changed alternate type branch delay')
    # Retain original table HI/LO relocations: the new tables are owner-local BSS.
    removed=locations[profile+16];kept=[r for r in records if r!=removed]
    relocation=bytearray(rel);struct.pack_into('>2I',relocation,12,capacity['bss_bytes'],len(kept))
    relocation[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(rel)-24-4*len(kept))
    if len(kept)!=len(records)-1: raise ValueError('Changed ground constructor relocation')
    return bytes(data),bytes(relocation),dict(spec,capacity=capacity,patches=patches,
        removed_relocations=[removed],output_sha256=sha256(data),output_reloc_sha256=sha256(relocation))


def install(base,prior,blob,core,original,output):
    old=prior['equipment_resources'];categories=old['item_categories']
    position=old['blob_offset'];module=bytearray(blob[position:position+old['bytes']])
    if (old.get('ground_categories') or old['bytes']!=CODE or sha256(module)!=old['sha256']
            or categories['count']!=71 or RAM+SIZE>prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed seasonal ground dependencies/reservation')
    count=categories['count'];objects=categories['objects'];files=by_vrom(base)
    map_at=categories['map_offset'];mapping=module[map_at+16:map_at+16+53]
    if ({i:c for i,c in enumerate(mapping) if c}!={r['source_category']:r['native_category'] for r in objects}
            or any(r['native_category']!=27+r['source_category'] for r in objects)
            or sha256(module[map_at:map_at+categories['map_bytes']])!=categories['map_sha256']):
        raise ValueError('Changed complete installed category map')
    config=bytearray();layouts=[]
    for spec in OWNERS:
        data,rel=(files[v].extract(base) for v in (spec['vrom'],spec['reloc']))
        cfg,capacity,refs=layout(data,rel,spec,count,len(objects));layouts.append((data,rel,spec,capacity,refs))
        config.extend(struct.pack('>9I',*cfg))
    (output/'ground-windows.S').write_text(assembly(count))
    code,compiled=compile_part('ground_categories',output/'ground_categories',
        extra_sources=(str((output/'ground-windows.S').relative_to(ROOT)),),defines=(f'AF_V3_CATEGORY_COUNT={count}',))
    category_code,category_compiled=compile_part('item_categories',output/'category_reader',defines=(
        f'AF_V3_CATEGORY_COUNT={count}','AF_V3_CATEGORY_ORIGINAL=0x8046744Cu',
        f'AF_V3_HELD_SELECTED=0x{old["player_actions"]["code"]["symbols"]["af_v3_player_selected_equipment"]:08X}u'))
    if len(code)>CONFIG-CODE or len(category_code)>0x200 or len(config)>SIZE-CONFIG-16:
        raise ValueError('Seasonal ground code/configuration overlaps its reservation')
    previous=categories['code'];start=categories['code_offset']
    if sha256(module[start:start+previous['bytes']])!=previous['sha256'] or any(module[start+previous['bytes']:start+0x200]):
        raise ValueError('Changed category fallback code/padding')
    # The core entry can now serve all six owners. Bypass it in the fallback to avoid recursion.
    at=0x800A5630-CODE_RAM
    if struct.unpack_from('>2I',core,at)!=(jump(0x8046744C),0):
        raise ValueError('Changed original translated category wrapper')
    struct.pack_into('>I',core,at,jump(category_compiled['symbols']['af_v3_equipment_category']))
    module[start:start+0x200]=category_code+bytes(0x200-len(category_code))
    module.extend(bytes(SIZE-len(module)));module[CODE:CODE+len(code)]=code
    module[CONFIG:CONFIG+len(config)]=config
    struct.pack_into('>4I',module,SIZE-16,*([GUARD]*4))
    changes={};owners=[]
    for data,rel,spec,capacity,refs in layouts:
        owner,relocation,record=patch_owner(data,rel,spec,capacity,refs,compiled['symbols'])
        descriptor=spec['slot']-16-CODE_RAM
        expected=(spec['vrom'],spec['vrom']+len(data),spec['ram'],spec['ram']+sum(spec['sections']),
                  0,spec['ram']+spec['sections'][0],0,0)
        if struct.unpack_from('>8I',core,descriptor)!=expected:
            raise ValueError('Changed complete ground allocation descriptor')
        struct.pack_into('>I',core,descriptor+12,spec['ram']+capacity['resident_bytes'])
        record['allocation_descriptor']=spec['slot']-16
        changes[spec['vrom']]=owner;changes[spec['reloc']]=relocation;owners.append(record)
    blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(module)
    if BLOB+len(blob)>END: raise ValueError('Ground module exceeds import storage')
    report=copy.deepcopy(old)
    report['item_categories'].update(ground_installed=True,code=category_compiled)
    for row in report['item_categories']['objects']:
        row.update(ground_installed=True,runtime_installed=True)
    report['ground_categories']=dict(format='AFV3-GROUND-CATEGORIES-1',code=compiled,code_offset=CODE,
        config_offset=CONFIG,config_bytes=len(config),config_sha256=sha256(config),owners=owners,
        global_type_entry=0x800A5630,original_type_fallback=0x8046744C,
        profile_bits_enabled=0,saved_format_changed=False,ordinary_ground_gameplay_tested=False)
    report.update(bytes=SIZE,vrom=BLOB+position,blob_offset=position,sha256=sha256(module),
        crc32=zlib.crc32(module),additional_resident_bytes=SIZE-old['bytes'])
    return report,changes
